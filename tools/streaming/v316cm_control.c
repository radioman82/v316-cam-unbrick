#define _POSIX_C_SOURCE 200809L
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>
#include "control_protocol.h"

/* Fixed ABI for the byte-verified menu_v22 build, not arbitrary memory writes. */
static int memfd = -1;
static uint32_t preview, setting, model, tiles;
static int pid;
static const char *error = "camera unavailable";
static int readmem(uint32_t at, void *out, size_t count) {
    return at >= 0x10000 && at < 0xc0000000 &&
           pread(memfd, out, count, at) == (ssize_t)count ? 0 : -1;
}
static uint32_t word(uint32_t at) { uint32_t value = 0; readmem(at, &value, 4); return value; }
static int byte(uint32_t at) { unsigned char value = 0; readmem(at, &value, 1); return value; }
static int visible(uint32_t window) { return window && byte(window + 12) != 0; }
static int is_recording(void) {
    char directory[64]; snprintf(directory, sizeof(directory), "/proc/%d/fd", pid);
    DIR *dir = opendir(directory);
    if (!dir) return 0;
    struct dirent *entry;
    int active = 0;
    while ((entry = readdir(dir))) {
        char path[128], target[256];
        snprintf(path, sizeof(path), "%s/%.20s", directory, entry->d_name);
        ssize_t n = readlink(path, target, sizeof(target) - 1);
        if (n <= 0) continue;
        target[n] = 0;
        const char *ext = strrchr(target, '.');
        if (!strstr(target, "/mnt/extsd/DCIM/") || !ext ||
            (strcmp(ext, ".mp4") && strcmp(ext, ".sec"))) continue;
        snprintf(path, sizeof(path), "/proc/%d/fdinfo/%.20s", pid, entry->d_name);
        FILE *f = fopen(path, "r");
        if (!f) continue;
        char line[160];
        while (fgets(line, sizeof(line), f)) {
            if (!strncmp(line, "flags:", 6) &&
                (strtoul(line + 6, NULL, 8) & O_ACCMODE) != O_RDONLY) active = 1;
        }
        fclose(f);
        if (active) break;
    }
    closedir(dir);
    return active;
}
static uint32_t window(int id) {
    uint32_t manager = word(0x35f9e0), node = word(manager + 0x30);
    for (int i = 0; node && i < 32; ++i) {
        uint32_t key = word(node + 16);
        if (key == (uint32_t)id) return word(node + 20);
        node = word(node + (id < (int)key ? 8 : 12));
    }
    return 0;
}
static int open_camera(void) {
    DIR *dir = opendir("/proc");
    if (!dir) return -1;
    struct dirent *entry;
    while ((entry = readdir(dir))) {
        if (entry->d_name[0] < '0' || entry->d_name[0] > '9') continue;
        char path[96], name[32];
        snprintf(path, sizeof(path), "/proc/%.20s/comm", entry->d_name);
        FILE *f = fopen(path, "r");
        if (!f) continue;
        int match = fgets(name, sizeof(name), f) && strcmp(name, "sdvcam\n") == 0;
        fclose(f);
        if (!match) continue;
        pid = atoi(entry->d_name);
        snprintf(path, sizeof(path), "/proc/%d/mem", pid);
        memfd = open(path, O_RDONLY | O_CLOEXEC);
        break;
    }
    closedir(dir);
    if (memfd < 0) return -1;
    /* Exact v22 key hook: B.W 0x24adf8 at 0x5b83c. */
    if (word(0x5b83c) != 0xbadcf1ef) {
        error = "menu_v22 required";
        return -1;
    }
    preview = window(2); setting = window(1);
    model = word(preview + 0xec); tiles = word(preview + 0x114);
    if (word(preview) != 0x203b04 || word(model) != 0x205fd0 || word(tiles) != 0x20679c) {
        error = "camera UI layout mismatch";
        return -1;
    }
    return 0;
}
static void pause_ms(long ms) {
    struct timespec t = {ms / 1000, ms % 1000 * 1000000};
    while (nanosleep(&t, &t) < 0 && errno == EINTR) {}
}
struct input32 { uint32_t sec, usec; uint16_t type, code; int32_t value; };
_Static_assert(sizeof(struct input32) == 16, "ARM input_event ABI");
static int event(int fd, unsigned code, int value) {
    struct input32 events[2] = {{0, 0, 1, (uint16_t)code, value}, {0}};
    return write(fd, events, sizeof(events)) == sizeof(events) ? 0 : -1;
}
static int tap(int device, unsigned code) {
    char path[32]; snprintf(path, sizeof(path), "/dev/input/event%d", device);
    int fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    int rc = event(fd, code, 1);
    pause_ms(20);
    int released = event(fd, code, 0);
    close(fd);
    pause_ms(140);
    if (rc < 0 || released < 0) { error = "key injection failed"; return -1; }
    return 0;
}
static int direct_command(unsigned command) {
    if ((command == CT_PHOTO || command == CT_VIDEO || command == CT_STREAMING ||
         command == CT_SETUP || command == CT_MODES || command >= CT_MODE_FIRST) && is_recording()) {
        error = "stop recording before changing mode"; return -1;
    }
    int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd < 0) return -1;
    struct timeval timeout = {6, 0};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    strcpy(address.sun_path, CT_SOCKET);
    struct ct_request request = {CT_MAGIC, command};
    struct ct_reply reply = {-1};
    int ok = connect(fd, (void *)&address, sizeof(address)) == 0 &&
             send(fd, &request, sizeof(request), MSG_NOSIGNAL) == sizeof(request) &&
             recv(fd, &reply, sizeof(reply), MSG_WAITALL) == sizeof(reply);
    close(fd);
    if (!ok) { error = "direct camera connection unavailable"; return -1; }
    if (reply.result != 0) {
        error = reply.result == -4 ? "camera GUI did not acknowledge command" : "direct camera command rejected";
        return -1;
    }
    return 0;
}
static int action(const char *name) {
    static const char *modes[] = {"video-normal", "video-slow", "video-loop", "video-timelapse",
                                  "photo-normal", "photo-auto", "photo-burst", "photo-timer"};
    for (int mode = 0; mode < 8; ++mode)
        if (!strcmp(name, modes[mode])) return direct_command(CT_MODE_FIRST + mode);
    if (!strcmp(name, "up")) return tap(0, 115);
    if (!strcmp(name, "down")) return tap(0, 114);
    if (!strcmp(name, "ok")) return tap(0, 139);
    if (!strcmp(name, "shutter")) {
        int rc = direct_command(CT_SHUTTER);
        pause_ms(500);
        return rc;
    }
    if (!strcmp(name, "back")) return direct_command(CT_BACK);
    if (!strcmp(name, "dismiss")) return direct_command(CT_DISMISS);
    if (!strcmp(name, "menu")) return direct_command(CT_MENU);
    if (!strcmp(name, "modes")) return direct_command(CT_MODES);
    if (!strcmp(name, "photo")) return direct_command(CT_PHOTO);
    if (!strcmp(name, "video")) return direct_command(CT_VIDEO);
    if (!strcmp(name, "streaming")) return direct_command(CT_STREAMING);
    if (!strcmp(name, "setup")) return direct_command(CT_SETUP);
    error = "unknown action"; return -1;
}
static void result(int ok, int cgi) {
    if (cgi) printf("%sContent-Type: application/json\r\nCache-Control: no-store\r\n\r\n",
                    ok ? "" : "Status: 409 Conflict\r\n");
    printf("{\"ok\":%s,\"message\":\"%s\",\"transport\":\"direct-ipc\",\"pid\":%d,\"preview\":%s,"
           "\"settings\":%s,\"tiles\":%s,\"modes\":%s,\"family\":\"%s\","
           "\"selected\":%u,\"recording\":%s,\"prompt\":%s}\n",
           ok ? "true" : "false", ok ? "ready" : error, pid,
           visible(preview) ? "true" : "false", visible(setting) ? "true" : "false",
           visible(tiles) ? "true" : "false", visible(model) ? "true" : "false",
           byte(model + 0x11d) == 4 ? "photo" : "video", word(model + 0x118),
           is_recording() ? "true" : "false",
           visible(word(preview + 0xe8)) ? "true" : "false");
}
int main(int argc, char **argv) {
    const char *method = argc > 1 ? NULL : getenv("REQUEST_METHOD");
    int cgi = method != NULL;
    const char *name = argc > 1 ? argv[1] : "status";
    char body[48];
    if (cgi && strcmp(method, "GET") && strcmp(method, "POST")) {
        fputs("Status: 405 Method Not Allowed\r\nAllow: GET, POST\r\n\r\n", stdout); return 1;
    }
    if (cgi && !strcmp(method, "POST")) {
        const char *origin = getenv("HTTP_ORIGIN"), *host = getenv("HTTP_HOST");
        char expected[256]; snprintf(expected, sizeof(expected), "http://%s", host ? host : "");
        if (origin && strcmp(origin, expected)) {
            fputs("Status: 403 Forbidden\r\n\r\n", stdout); return 1;
        }
        const char *length = getenv("CONTENT_LENGTH");
        int n = length ? atoi(length) : 0;
        if (n < 1 || n >= (int)sizeof(body) || fread(body, 1, n, stdin) != (size_t)n) {
            fputs("Status: 400 Bad Request\r\n\r\n", stdout); return 1;
        }
        body[n] = 0;
        if (strchr(body, '\n') || strchr(body, '\r') || strlen(body) != (size_t)n) {
            fputs("Status: 400 Bad Request\r\n\r\n", stdout); return 1;
        }
        name = body;
    }
    alarm(8);
    int lock = open("/tmp/v316cm-control.lock", O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    int ok = lock >= 0 && flock(lock, LOCK_EX) == 0 && open_camera() == 0;
    if (ok && strcmp(name, "status")) ok = action(name) == 0;
    result(ok, cgi);
    if (memfd >= 0) close(memfd);
    if (lock >= 0) close(lock);
    return ok ? 0 : 1;
}
