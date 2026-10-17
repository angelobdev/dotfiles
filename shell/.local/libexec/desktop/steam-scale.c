/* Apply Steam desktop UI scaling after its CEF renderer initializes. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int cef_initialize(const void *args, const void *settings, void *app, void *sandbox) {
    int (*initialize)(const void *, const void *, void *, void *) = dlsym(RTLD_NEXT, "cef_initialize");
    if (!initialize) return 0;
    int result = initialize(args, settings, app, sandbox);
    char executable[4096];
    ssize_t n = readlink("/proc/self/exe", executable, sizeof(executable) - 1);
    if (n < 0) return result;
    executable[n] = 0;
    const char *name = strrchr(executable, '/');
    if (!name || strcmp(name + 1, "steamwebhelper")) return result;
    const char *value = getenv("DESKTOP_STEAM_CEF_SCALE");
    if (!value || !result) return result;
    char *end;
    errno = 0;
    double scale = strtod(value, &end);
    if (errno || *end || !isfinite(scale) || scale < 1 || scale > 4) return result;
    void (*set_scale)(double) = dlsym(RTLD_NEXT, "cef_set_force_device_scale_factor");
    if (set_scale) {
        set_scale(scale);
        fprintf(stderr, "desktop-steam: CEF initialized at UI scale %.3f\n", scale);
    }
    return result;
}
