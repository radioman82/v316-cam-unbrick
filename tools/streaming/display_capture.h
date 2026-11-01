/* ARM32 ABI declarations from the Allwinner disp2 and legacy ION interfaces.
 * Reference links and tested hardware are recorded in README.md. */
#include <sys/ioctl.h>
#include <sys/mman.h>

struct ion_alloc { size_t len, align; unsigned heap_mask, flags; int handle; };
struct ion_map { int handle, fd; };
struct cap_size { uint32_t width, height; };
struct cap_rect { int32_t x, y; uint32_t width, height; };
struct cap_info2 {
    struct cap_rect window;
    struct {
        uint32_t format;
        struct cap_size size[3];
        struct cap_rect crop;
        int fd;
    } out;
};
_Static_assert(sizeof(struct cap_info2) == 64, "disp2 capture ABI size");
_Static_assert(sizeof(struct ion_alloc) == 20, "ION allocation ABI size");
static int display_fd = -1, ion_fd = -1, dma_fd = -1, ion_handle = -1;
static unsigned char *dma_pixels = MAP_FAILED;
static size_t dma_length;
static int capture_width, capture_height;

static void display_close(void) {
    if (dma_pixels != MAP_FAILED) munmap(dma_pixels, dma_length);
    if (dma_fd >= 0) close(dma_fd);
    if (ion_handle >= 0) ioctl(ion_fd, _IOWR('I', 1, int), &ion_handle);
    if (ion_fd >= 0) close(ion_fd);
    if (display_fd >= 0) close(display_fd);
}
static int display_open(void) {
    unsigned long args[4] = {0};
    display_fd = open("/dev/disp", O_RDWR | O_CLOEXEC);
    if (display_fd < 0) return -1;
    capture_width = ioctl(display_fd, 0x07, args);
    capture_height = ioctl(display_fd, 0x08, args);
    if (capture_width < 1 || capture_width > 640 || capture_height < 1 || capture_height > 480)
        return -1;
    dma_length = (size_t)capture_width * capture_height * 4;
    ion_fd = open("/dev/ion", O_RDWR | O_CLOEXEC);
    if (ion_fd < 0) return -1;
    /* Uncached DMA/carveout allocation. Only this process's buffer is mapped. */
    struct ion_alloc alloc = {dma_length, 4096, (1u << 4) | (1u << 2), 0, 0};
    if (ioctl(ion_fd, _IOWR('I', 0, struct ion_alloc), &alloc) < 0) return -1;
    ion_handle = alloc.handle;
    struct ion_map map = {ion_handle, -1};
    if (ioctl(ion_fd, _IOWR('I', 2, struct ion_map), &map) < 0) return -1;
    dma_fd = map.fd;
    dma_pixels = mmap(NULL, dma_length, PROT_READ | PROT_WRITE, MAP_SHARED, dma_fd, 0);
    return dma_pixels == MAP_FAILED ? -1 : 0;
}
/* Guard scanline ends in our own DMA buffer. The opaque ARGB writeback
 * replaces these impossible marker pixels when the corresponding rows finish.
 * Poll completion instead of always sleeping 55 ms; retain a bounded retry. */
static void capture_mark_rows(void) {
    volatile uint32_t *pixels = (volatile uint32_t *)dma_pixels;
    for (int y = 0; y < capture_height; ++y) {
        pixels[y * capture_width] = 0xa5a5a5a5u;
        pixels[(y + 1) * capture_width - 1] = 0xa5a5a5a5u;
    }
}
static int capture_rows_complete(void) {
    volatile const uint32_t *pixels = (volatile const uint32_t *)dma_pixels;
    for (int y = 0; y < capture_height; ++y) {
        if (pixels[y * capture_width] == 0xa5a5a5a5u ||
            pixels[(y + 1) * capture_width - 1] == 0xa5a5a5a5u) return 0;
    }
    return 1;
}
static void capture_wait_rows(void) {
    struct timespec start, current;
    clock_gettime(CLOCK_MONOTONIC, &start);
    volatile const uint32_t *pixels = (volatile const uint32_t *)dma_pixels;
    for (;;) {
        /* Usually only one uncached read per poll. Check all marked row ends
         * once the last pixel changed; no assumptions about row ordering. */
        if (pixels[capture_width * capture_height - 1] != 0xa5a5a5a5u &&
            capture_rows_complete()) return;
        clock_gettime(CLOCK_MONOTONIC, &current);
        int64_t elapsed = (int64_t)(current.tv_sec - start.tv_sec) * 1000000000 +
                          current.tv_nsec - start.tv_nsec;
        if (elapsed >= 55000000) return;
        struct timespec pause = {0, 1000000};
        while (nanosleep(&pause, &pause) < 0 && errno == EINTR) {}
    }
}
static int display_capture(unsigned char *rgb_out, int capture_lock) {
    unsigned long args[4] = {0};
    if (flock(capture_lock, LOCK_EX) < 0) return -1;
    int complete = 0;
    for (int attempt = 0; attempt < 2; ++attempt) {
        capture_mark_rows();
        int rc = ioctl(display_fd, 0x140, args); /* DISP_CAPTURE_START */
        if (rc < 0) break;
        struct cap_info2 info = {0};
        info.out.format = 0; /* ARGB8888, opaque writeback on this board. */
        info.out.size[0].width = capture_width;
        info.out.size[0].height = capture_height;
        info.out.crop.width = capture_width;
        info.out.crop.height = capture_height;
        info.out.fd = dma_fd;
        args[1] = (unsigned long)&info;
        rc = ioctl(display_fd, 0x143, args); /* DISP_CAPTURE_COMMIT2 */
        if (rc >= 0) capture_wait_rows();
        args[1] = 0;
        int stopped = ioctl(display_fd, 0x141, args); /* Finish DMA before reading. */
        if (rc < 0 || stopped < 0) break;
        complete = capture_rows_complete();
        if (complete) break;
    }
    flock(capture_lock, LOCK_UN);
    if (!complete) return -1;
    /* One aligned 32-bit read per pixel instead of three uncached byte reads. */
    const uint32_t *pixels = (const uint32_t *)dma_pixels;
    for (int i = 0; i < capture_width * capture_height; ++i) {
        uint32_t pixel = pixels[i];
        rgb_out[i * 3] = (unsigned char)(pixel >> 16);
        rgb_out[i * 3 + 1] = (unsigned char)(pixel >> 8);
        rgb_out[i * 3 + 2] = (unsigned char)pixel;
    }
    return 0;
}
