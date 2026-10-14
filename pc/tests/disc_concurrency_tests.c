#define _POSIX_C_SOURCE 200809L
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "pc_disc.h"

int g_pc_verbose = 0;
struct reader { u32 offset; unsigned char expected; };
static int read_repeatedly(void *opaque) {
    const struct reader *reader = opaque;
    unsigned char bytes[128];
    for (int i = 0; i < 20000; ++i) {
        if (!pc_disc_read(reader->offset, bytes, sizeof(bytes))) return 1;
        for (size_t j = 0; j < sizeof(bytes); ++j)
            if (bytes[j] != reader->expected) return 1;
    }
    return 0;
}
int main(void) {
    char directory[] = "/tmp/ac-disc-test-XXXXXX";
    if (!mkdtemp(directory) || chdir(directory)) return 1;
    unsigned char image[0xc000] = {0};
    image[0x1c] = 0xc2; image[0x1d] = 0x33;
    image[0x1e] = 0x9f; image[0x1f] = 0x3d;
    image[0x421] = 0; image[0x422] = 0x20; /* DOL at 0x2000. */
    image[0x426] = 0x10; /* FST at 0x1000. */
    image[0x1000] = 1; image[0x100b] = 1; /* Empty root directory. */
    memset(image + 0x8000, 0xaa, 128);
    memset(image + 0xa000, 0x55, 128);
    FILE *file = fopen("fixture.iso", "wb");
    if (!file || fwrite(image, 1, sizeof(image), file) != sizeof(image) || fclose(file)) return 1;
    SDL_SetMainReady();
    if (SDL_Init(0) || !pc_disc_init()) return 1;
    struct reader a = {0x8000, 0xaa}, b = {0xa000, 0x55};
    SDL_Thread *first = SDL_CreateThread(read_repeatedly, "reader-a", &a);
    SDL_Thread *second = SDL_CreateThread(read_repeatedly, "reader-b", &b);
    if (!first || !second) return 1;
    int result_a = 1, result_b = 1;
    SDL_WaitThread(first, &result_a); SDL_WaitThread(second, &result_b);
    pc_disc_shutdown(); SDL_Quit();
    unlink("fixture.iso"); chdir("/tmp"); rmdir(directory);
    return result_a || result_b;
}
