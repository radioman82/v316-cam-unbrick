// Use Zig's standard PBKDF2/HMAC implementation; never put a passphrase in
// a shell command or a quoted wpa_supplicant configuration string.
const std = @import("std");
export fn wlan_psk(password: [*]const u8, password_len: usize,
    ssid: [*]const u8, ssid_len: usize, output: [*]u8) c_int {
    std.crypto.pwhash.pbkdf2(output[0..32], password[0..password_len],
        ssid[0..ssid_len], 4096, std.crypto.auth.hmac.HmacSha1) catch return -1;
    return 0;
}
