/* In-process menu commands, executed by the existing MiniGUI dispatch thread.
 * ABI: byte-verified sdvcam_menu_v22 + MiniGUI 3.0 Threads, ARM32 soft-float. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>
#include "control_protocol.h"

#define CT_MESSAGE 0x7e90
typedef uint32_t object;
typedef int (*dispatch_fn)(void *);
typedef int (*post_fn)(uint32_t, int, uint32_t, uint32_t);
static dispatch_fn real_dispatch;
static post_fn post_message;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t condition = PTHREAD_COND_INITIALIZER;
static uint32_t sequence, pending, wake_handle;
static int completed, outcome;
static int started;

static uint32_t get(object p, unsigned offset) { return *(uint32_t *)(uintptr_t)(p + offset); }
static unsigned char flag(object p, unsigned offset) { return *(unsigned char *)(uintptr_t)(p + offset); }
static void set(object p, unsigned offset, uint32_t value) { *(uint32_t *)(uintptr_t)(p + offset) = value; }
static void set_flag(object p, unsigned offset, unsigned char value) { *(unsigned char *)(uintptr_t)(p + offset) = value; }
static void call1(uint32_t address, object self) { ((void (*)(object))(uintptr_t)(address | 1))(self); }
static void virtual_call(object self, unsigned offset) {
    if (self) ((void (*)(object))(uintptr_t)get(get(self, 0), offset))(self);
}
static object manager(void) { return *(uint32_t *)0x35f9e0; }
static object window(int id) {
    object m = manager(), node = m ? get(m, 0x30) : 0;
    for (int i = 0; node && i < 32; ++i) {
        unsigned key = get(node, 16);
        if (key == (unsigned)id) return get(node, 20);
        node = get(node, id < (int)key ? 8 : 12);
    }
    return 0;
}
static int visible(object self) { return self && flag(self, 12); }
static void post_app(object preview, unsigned message, unsigned value) {
    ((void (*)(object, object, unsigned, unsigned))(uintptr_t)0x5aa09)(preview, preview, message, value);
}

struct memory_range { uintptr_t start, end; };
static struct memory_range ranges[160];
static int range_count;
static void refresh_ranges(void) {
    range_count = 0;
    FILE *f = fopen("/proc/self/maps", "r");
    if (!f) return;
    char line[320], permissions[5]; unsigned long start, end;
    while (range_count < 160 && fgets(line, sizeof(line), f)) {
        if (sscanf(line, "%lx-%lx %4s", &start, &end, permissions) == 3 && permissions[0] == 'r')
            ranges[range_count++] = (struct memory_range){start, end};
    }
    fclose(f);
}
static int readable(uintptr_t p, size_t n) {
    for (int i = 0; i < range_count; ++i)
        if (p >= ranges[i].start && p < ranges[i].end && n <= ranges[i].end - p) return 1;
    return 0;
}
static int is_window(object self) {
    if (!readable(self, 0xac)) return 0;
    object table = get(self, 0);
    return table >= 0x1f0000 && table < 0x27b600 && readable(table, 0x20) &&
           get(table, 12) == 0x52acf; /* Shared Window::GetHandle implementation. */
}
static void close_setting_children(object setting) {
    if (!setting) return;
    refresh_ranges();
    for (unsigned offset = 0xdc; offset < 0x1b8; offset += 4) {
        object child = get(setting, offset);
        if (child != setting && is_window(child) && get(child, 0xa8) == setting && visible(child))
            virtual_call(child, 0x1c);
    }
}
static void dismiss(object preview, object setting) {
    object prompt = get(preview, 0xe8);
    if (visible(prompt)) virtual_call(prompt, 0x1c);
    /* Settings owns its own instance of the same nonmodal prompt class. */
    if (!setting) return;
    refresh_ranges();
    for (unsigned offset = 0xdc; offset < 0x1b8; offset += 4) {
        object child = get(setting, offset);
        if (is_window(child) && get(child, 0) == get(prompt, 0) && visible(child))
            virtual_call(child, 0x1c);
    }
}
static void preview_screen(object preview, object setting) {
    const unsigned offsets[] = {0xec, 0xf0, 0x114, 0x118};
    const uint32_t close_methods[] = {0x66de0, 0x59514, 0x697ac, 0x58c1c};
    for (unsigned i = 0; i < 4; ++i) {
        object child = get(preview, offsets[i]);
        if (visible(child)) call1(close_methods[i], child);
    }
    close_setting_children(setting);
    if (!visible(preview)) {
        int previous = 0;
        for (int id = 1; id <= 7; ++id) if (id != 2 && visible(window(id))) { previous = id; break; }
        ((void (*)(object, int, int, int))(uintptr_t)0x6264d)(manager(), previous, 2, 1);
    }
    int (*enable)(uint32_t, int) = dlsym(RTLD_NEXT, "EnableWindow");
    uint32_t (*activate)(uint32_t) = dlsym(RTLD_NEXT, "SetActiveWindow");
    uint32_t handle = get(preview, 0x2c);
    if (enable) enable(handle, 1);
    if (activate) activate(handle);
}
static void show_family(object preview, int family) {
    object model = get(preview, 0xec);
    set_flag(model, 0x11d, (unsigned char)family);
    set(model, 0x118, 0);
    call1(0x67746, model);
    call1(0x5a6f4, preview);
}
static int execute(unsigned command) {
    if (*(uint32_t *)0x5b83c != 0xbadcf1ef) return -2;
    object preview = window(2), setting = window(1);
    if (!preview || get(preview, 0) != 0x203b04 || !setting) return -2;
    fprintf(stderr, "CT_DIRECT command=%u gui_thread=%lu\n", command, (unsigned long)pthread_self());
    if (command == CT_DISMISS) { dismiss(preview, setting); return 0; }
    if (command != CT_MENU && command != CT_PHOTO && command != CT_VIDEO &&
        command != CT_STREAMING && command != CT_SETUP && command != CT_MODES &&
        command != CT_BACK && command != CT_SHUTTER &&
        !(command >= CT_MODE_FIRST && command < CT_MODE_FIRST + 8)) return -3;
    dismiss(preview, setting);
    preview_screen(preview, setting);
    if (command >= CT_MODE_FIRST) {
        int mode = command - CT_MODE_FIRST;
        object model = get(preview, 0xec);
        set_flag(model, 0x11d, mode < 4 ? 0 : 4);
        set(model, 0x118, (unsigned)(mode % 4));
        ((void (*)(object, object, int))(uintptr_t)0x5ab55)(preview, 0, mode);
    } else if (command == CT_MENU) {
        virtual_call(get(preview, 0x114), 0x6c);
    } else if (command == CT_SETUP) {
        post_app(preview, 74, 1);
    } else if (command == CT_SHUTTER) {
        unsigned mode = get(setting, 0xec);
        post_app(preview, mode < 4 ? 59 : 81, 1);
    } else if (command == CT_PHOTO || command == CT_VIDEO || command == CT_STREAMING || command == CT_MODES) {
        int family = command == CT_PHOTO ? 4 : 0;
        if (command == CT_MODES) family = get(setting, 0xec) >= 4 ? 4 : 0;
        show_family(preview, family);
        if (command == CT_STREAMING) system("/mnt/extsd/start_streaming.sh &");
    }
    return 0;
}

int DispatchMessage(void *message) {
    if (!real_dispatch) real_dispatch = (dispatch_fn)dlsym(RTLD_NEXT, "DispatchMessage");
    uint32_t *fields = message; /* MiniGUI MSG starts with hwnd, message, wParam. */
    if (fields && fields[1] == CT_MESSAGE) {
        pthread_mutex_lock(&mutex);
        unsigned command = fields[2] == sequence ? pending : 0;
        pending = 0;
        pthread_mutex_unlock(&mutex);
        int result = command ? execute(command) : -4;
        pthread_mutex_lock(&mutex);
        if (fields[2] == sequence) { outcome = result; completed = 1; pthread_cond_signal(&condition); }
        pthread_mutex_unlock(&mutex);
        return 0;
    }
    int result = real_dispatch ? real_dispatch(message) : 0;
    object preview = window(2);
    if (preview && get(preview, 0) == 0x203b04) {
        pthread_mutex_lock(&mutex);
        wake_handle = get(preview, 0x2c);
        pthread_mutex_unlock(&mutex);
    }
    return result;
}
static void *serve(void *unused) {
    (void)unused;
    int server = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    strcpy(address.sun_path, CT_SOCKET);
    unlink(CT_SOCKET);
    if (server < 0 || bind(server, (void *)&address, sizeof(address)) < 0 || listen(server, 4) < 0) return NULL;
    chmod(CT_SOCKET, 0600);
    fprintf(stderr, "CT_DIRECT ready %s\n", CT_SOCKET);
    for (;;) {
        int client = accept4(server, NULL, NULL, SOCK_CLOEXEC);
        if (client < 0) continue;
        struct timeval timeout = {5, 0};
        setsockopt(client, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        struct ct_request request;
        struct ct_reply reply = {-1};
        if (recv(client, &request, sizeof(request), MSG_WAITALL) == sizeof(request) && request.magic == CT_MAGIC) {
            pthread_mutex_lock(&mutex);
            uint32_t handle = wake_handle;
            sequence++; pending = request.command; completed = 0;
            uint32_t seq = sequence;
            pthread_mutex_unlock(&mutex);
            int posted = handle && handle != UINT32_MAX && post_message &&
                         post_message(handle, CT_MESSAGE, seq, 0) == 0;
            pthread_mutex_lock(&mutex);
            struct timespec deadline; clock_gettime(CLOCK_REALTIME, &deadline); deadline.tv_sec += 5;
            while (posted && !completed) {
                if (pthread_cond_timedwait(&condition, &mutex, &deadline) == ETIMEDOUT) break;
            }
            reply.result = completed ? outcome : -4;
            if (!completed) pending = 0;
            pthread_mutex_unlock(&mutex);
        }
        send(client, &reply, sizeof(reply), MSG_NOSIGNAL);
        close(client);
    }
    return NULL;
}
__attribute__((constructor)) static void initialize(void) {
    char executable[256];
    ssize_t length = readlink("/proc/self/exe", executable, sizeof(executable) - 1);
    if (length <= 0) return;
    executable[length] = 0;
    const char *name = strrchr(executable, '/');
    if (!name || (strcmp(name + 1, "sdvcam") && strcmp(name + 1, ".sdvcam_patched"))) return;
    if (*(uint32_t *)0x5b83c != 0xbadcf1ef || started) return;
    unsetenv("LD_PRELOAD"); /* Camera child processes must not load this module. */
    started = 1;
    real_dispatch = dlsym(RTLD_NEXT, "DispatchMessage");
    post_message = dlsym(RTLD_NEXT, "PostMessage");
    pthread_t thread;
    if (pthread_create(&thread, NULL, serve, NULL) == 0) pthread_detach(thread);
}
