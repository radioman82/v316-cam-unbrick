#ifndef V316CM_CONTROL_PROTOCOL_H
#define V316CM_CONTROL_PROTOCOL_H
#include <stdint.h>
#define CT_SOCKET "/tmp/v316cm-control.sock"
#define CT_MAGIC 0x43543930u
enum ct_command {
    CT_MENU = 1, CT_PHOTO, CT_VIDEO, CT_STREAMING, CT_SETUP,
    CT_MODES, CT_DISMISS, CT_BACK, CT_SHUTTER, CT_MODE_FIRST = 32
};
struct ct_request { uint32_t magic, command; };
struct ct_reply { int32_t result; };
#endif
