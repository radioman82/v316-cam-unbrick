/* Allwinner V316 Cam display writeback -> JPEG CGI. No video device or sdvcam changes. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <time.h>
#include <unistd.h>
#define STB_IMAGE_WRITE_IMPLEMENTATION
#define STBI_WRITE_NO_STDIO
#define STB_IMAGE_WRITE_STATIC
#include "vendor/stb_image_write.h"
#include "display_capture.h"

#define MAX_PIXELS (640 * 480)
static unsigned char bmp[MAX_PIXELS * 4 + 4096];
static unsigned char rgb[MAX_PIXELS * 3];
static unsigned char jpeg[MAX_PIXELS * 4];
static size_t jpeg_size;
static int jpeg_overflow;
static char capture_path[96];
static int lock_fd = -1;
static volatile sig_atomic_t running = 1;

static void stop(int sig) { (void)sig; running = 0; }
static void cleanup(void) { unlink(capture_path); display_close(); }
static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}
static int sysfs_write(const char *path, const char *value) {
    int fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    size_t len = strlen(value);
    ssize_t n = write(fd, value, len);
    int rc = close(fd);
    return n == (ssize_t)len && rc == 0 ? 0 : -1;
}
static void jpeg_write(void *context, void *data, int size) {
    (void)context;
    if (size < 0 || (size_t)size > sizeof(jpeg) - jpeg_size) {
        jpeg_overflow = 1;
        return;
    }
    memcpy(jpeg + jpeg_size, data, (size_t)size);
    jpeg_size += (size_t)size;
}
static int encode_jpeg(int w, int h, int quality) {
    const unsigned char *pixels = rgb;
    /* The factory display buffer is portrait; the camera UI is landscape. */
    if (w < h) {
        for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) {
            size_t src = ((size_t)y * w + x) * 3;
            size_t dst = ((size_t)(w - 1 - x) * h + y) * 3;
            memcpy(bmp + dst, rgb + src, 3);
        }
        pixels = bmp;
        int tmp = w; w = h; h = tmp;
    }
    jpeg_size = 0;
    jpeg_overflow = 0;
    return stbi_write_jpg_to_func(jpeg_write, NULL, w, h, 3, pixels, quality) &&
           !jpeg_overflow && jpeg_size > 0 ? 0 : -1;
}
static int capture(int quality) {
    if (display_fd >= 0 && dma_pixels != MAP_FAILED) {
        if (display_capture(rgb, lock_fd) < 0) return -1;
        return encode_jpeg(capture_width, capture_height, quality);
    }
    if (flock(lock_fd, LOCK_EX) < 0) return -1;
    /* This kernel refuses existing dump files: reusing one freezes the image. */
    unlink(capture_path);
    int rc = sysfs_write("/sys/class/disp/disp/attr/disp", "0\n");
    char request[100];
    snprintf(request, sizeof(request), "%s\n", capture_path);
    if (rc == 0) rc = sysfs_write("/sys/class/disp/disp/attr/capture_dump", request);
    flock(lock_fd, LOCK_UN);
    if (rc < 0) return -1;
    FILE *f = fopen(capture_path, "rb");
    if (!f) return -1;
    size_t n = fread(bmp, 1, sizeof(bmp), f);
    int extra = fgetc(f);
    fclose(f);
    unlink(capture_path);
    if (n < 54 || extra != EOF || memcmp(bmp, "BM", 2) ||
        le32(bmp + 14) < 40 || bmp[26] != 1 || bmp[27] != 0 || le32(bmp + 30) != 0)
        return -1;
    int32_t w = (int32_t)le32(bmp + 18), h = (int32_t)le32(bmp + 22);
    unsigned bpp = bmp[28] | (unsigned)bmp[29] << 8;
    uint32_t offset = le32(bmp + 10);
    if (w <= 0 || w > 640 || h == 0 || h < -480 || h > 480 ||
        (bpp != 24 && bpp != 32)) return -1;
    int height = h < 0 ? -h : h;
    size_t stride = ((size_t)w * bpp + 31) / 32 * 4;
    if (offset < 54 || offset > n || stride * height > n - offset) return -1;
    for (int y = 0; y < height; ++y) {
        const unsigned char *src = bmp + offset + stride * (h < 0 ? y : height - 1 - y);
        unsigned char *dst = rgb + (size_t)y * w * 3;
        for (int x = 0; x < w; ++x, src += bpp / 8, dst += 3) {
            dst[0] = src[2]; dst[1] = src[1]; dst[2] = src[0];
        }
    }
    return encode_jpeg(w, height, quality);
}
static int send_jpeg(void) {
    /* Bound blocked clients; a closed browser cannot leave an endless producer. */
    alarm(10);
    int ok = fwrite(jpeg, 1, jpeg_size, stdout) == jpeg_size &&
             fwrite("\r\n", 1, 2, stdout) == 2 && fflush(stdout) == 0;
    alarm(0);
    return ok ? 0 : -1;
}
static int stream_options(int *quality, int *fps) {
    const char *query = getenv("QUERY_STRING");
    unsigned seen = 0;
    if (!query || !*query) return 0;
    while (*query) {
        const char *end = strchr(query, '&');
        if (!end) end = query + strlen(query);
        const char *equal = memchr(query, '=', (size_t)(end - query));
        if (!equal || equal + 1 == end) return -1;
        size_t key = (size_t)(equal - query);
        int value = 0;
        int timestamp = key == 1 && query[0] == 't';
        if (end - equal > 21) return -1;
        for (const char *p = equal + 1; p < end; ++p) {
            if (*p < '0' || *p > '9') return -1;
            if (!timestamp) {
                if (value > 100) return -1;
                value = value * 10 + *p - '0';
            }
        }
        unsigned bit;
        if (key == 3 && !memcmp(query, "fps", 3)) {
            if (value < 1 || value > 15) return -1;
            bit = 1; *fps = value;
        } else if (key == 7 && !memcmp(query, "quality", 7)) {
            if (value < 20 || value > 90) return -1;
            bit = 2; *quality = value;
        } else if (timestamp) bit = 4;
        else return -1;
        if (seen & bit) return -1;
        seen |= bit;
        if (!*end) break;
        query = end + 1;
        if (!*query) return -1;
    }
    return 0;
}
int main(int argc, char **argv) {
    int snapshot = argc > 1 && strcmp(argv[1], "--snapshot") == 0;
    int quality = 65, fps = 15;
    if (stream_options(&quality, &fps) < 0) {
        fputs("Status: 400 Bad Request\r\nContent-Type: text/plain\r\n"
              "Cache-Control: no-store\r\n\r\nExpected fps=1..15 and quality=20..90.\n", stdout);
        return 1;
    }
    snprintf(capture_path, sizeof(capture_path), "/tmp/v316cm-capture-%ld.bmp", (long)getpid());
    atexit(cleanup);
    signal(SIGPIPE, SIG_IGN);
    signal(SIGTERM, stop);
    signal(SIGINT, stop);
    lock_fd = open("/tmp/v316cm-capture.lock", O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    if (display_open() < 0) {
        display_close();
        display_fd = ion_fd = dma_fd = ion_handle = -1;
        dma_pixels = MAP_FAILED;
    }
    if (lock_fd < 0 || capture(quality) < 0) {
        fputs("Status: 503 Service Unavailable\r\nContent-Type: text/plain\r\n"
              "Cache-Control: no-store\r\n\r\nDisplay capture failed; retry when preview is active.\n", stdout);
        return 1;
    }
    if (snapshot) {
        printf("Content-Type: image/jpeg\r\nContent-Length: %zu\r\nCache-Control: no-store\r\n\r\n", jpeg_size);
        /* Snapshot Content-Length excludes the multipart separator. */
        alarm(10);
        int ok = fwrite(jpeg, 1, jpeg_size, stdout) == jpeg_size && fflush(stdout) == 0;
        return ok ? 0 : 1;
    }
    fputs("Content-Type: multipart/x-mixed-replace; boundary=v316cmframe\r\n"
          "Cache-Control: no-store, no-cache, must-revalidate\r\n"
          "X-Content-Type-Options: nosniff\r\n\r\n", stdout);
    unsigned long frame = 0;
    double next_frame = now();
    do {
        printf("--v316cmframe\r\nContent-Type: image/jpeg\r\nContent-Length: %zu\r\n"
               "X-Frame-Number: %lu\r\n\r\n", jpeg_size, ++frame);
        if (send_jpeg() < 0) break;
        if (!running || capture(quality) < 0) break;
        next_frame += 1.0 / fps;
        double delay = next_frame - now();
        if (delay > 0) {
            struct timespec wait = {0, (long)(delay * 1e9)};
            nanosleep(&wait, NULL);
        }
        else next_frame = now(); /* Slow clients do not build up old frames. */
        if (!running) break;
    } while (running);
    if (running && !ferror(stdout)) {
        fputs("--v316cmframe--\r\n", stdout);
        fflush(stdout);
    }
    close(lock_fd);
    return 0;
}
