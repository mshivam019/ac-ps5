#include <errno.h>
#include <stdio.h>
#include <sys/stat.h>

/* Reuse the working native titles' exit hook: libc exit triggers SIGSYS on 9.00. */
extern void catchReturnFromMain(int status) __attribute__((noreturn));
void __wrap_exit(int status) { catchReturnFromMain(status); }
void __wrap__Exit(int status) { catchReturnFromMain(status); }
void __wrap__exit(int status) { catchReturnFromMain(status); }

extern int ac_ps5_game_main(int argc, char **argv);

static int prepare_settings(void) {
    FILE *existing = fopen("/download0/settings.ini", "rb");
    if (existing) {
        fclose(existing);
        return 0;
    }
    if (errno != ENOENT)
        return -1;
    FILE *source = fopen("/app0/data/settings.ini", "rb");
    if (!source)
        source = fopen("/app0/assets/default-settings.ini", "rb");
    if (!source)
        return -1;
    FILE *target = fopen("/download0/settings.ini", "wb");
    if (!target) {
        fclose(source);
        return -1;
    }
    unsigned char buffer[4096];
    size_t count;
    int status = 0;
    while ((count = fread(buffer, 1, sizeof(buffer), source)) != 0) {
        if (fwrite(buffer, 1, count, target) != count) {
            status = -1;
            break;
        }
    }
    if (ferror(source))
        status = -1;
    fclose(source);
    if (fclose(target) != 0)
        status = -1;
    if (status != 0)
        remove("/download0/settings.ini");
    return status;
}

int main(int argc, char **argv) {
    /* /app0 is the native title on M.2; /download0 is its writable sandbox. */
    fprintf(stderr, "[AC PS5] native OpenGL, data=/app0/data, saves=/download0/save\n");
    if (mkdir("/download0/save", 0755) != 0 && errno != EEXIST) {
        fprintf(stderr, "[AC PS5] save directory unavailable: %d\n", errno);
        return 1;
    }
    if (prepare_settings() != 0) {
        fprintf(stderr, "[AC PS5] settings initialization failed: %d\n", errno);
        return 1;
    }
    char *game_argv[] = {"AnimalCrossing", "--profile", "600", "--verbose", NULL};
    FILE *diagnostic = fopen("/app0/ps5-capture.txt", "r");
    int game_argc = diagnostic ? 4 : 3;
    if (diagnostic) fclose(diagnostic);
    (void)argc;
    (void)argv;
    return ac_ps5_game_main(game_argc, game_argv);
}
