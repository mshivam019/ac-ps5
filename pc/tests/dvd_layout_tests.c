#define _POSIX_C_SOURCE 200809L
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "pc_disc.h"
#include "dolphin/dvd.h"
int g_pc_verbose;
static int callback_ok;
static void complete(s32 count, DVDFileInfo *info) {
    callback_ok = count == 32 && info->length == 128;
}
int main(void) {
    char directory[] = "/tmp/ac-dvd-test-XXXXXX";
    if (!mkdtemp(directory) || chdir(directory)) return 1;
    unsigned char image[0xc000] = {0};
    image[0x1c]=0xc2; image[0x1d]=0x33; image[0x1e]=0x9f; image[0x1f]=0x3d;
    image[0x422]=0x20; image[0x426]=0x10;
    image[0x1000]=1; image[0x100b]=2;
    image[0x100f]=1; image[0x1012]=0x80; image[0x1017]=128;
    memcpy(image+0x1019,"sample.bin",11);
    memset(image+0x8000,0xa5,128);
    FILE *file=fopen("fixture.iso","wb");
    if (!file || fwrite(image,1,sizeof(image),file)!=sizeof(image) || fclose(file)) return 1;
    SDL_SetMainReady();
    if (SDL_Init(0) || !pc_disc_init()) return 1;
    struct { DVDFileInfo info; unsigned char guard[16]; } state;
    memset(&state,0xcc,sizeof(state));
    unsigned char bytes[32];
    int ok=DVDOpen("sample.bin",&state.info) && state.info.length==128 && state.info.startAddr==0x8000;
    if(ok) ok=DVDReadAsyncPrio(&state.info,bytes,32,32,complete,2) && callback_ok;
    for(unsigned i=0;i<sizeof(bytes) && ok;++i) ok=bytes[i]==0xa5;
    for(unsigned i=0;i<sizeof(state.guard) && ok;++i) ok=state.guard[i]==0xcc;
    if(ok) ok=DVDClose(&state.info);
    pc_disc_shutdown(); SDL_Quit(); unlink("fixture.iso"); chdir("/tmp"); rmdir(directory);
    return !ok;
}
