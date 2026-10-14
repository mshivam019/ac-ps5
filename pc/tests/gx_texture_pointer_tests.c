#include <stdint.h>
#include <string.h>
#include "dolphin/gx/GXStruct.h"
#include "dolphin/gx/GXEnum.h"

extern void GXInitTexObj(void *, void *, u16, u16, u32, u32, u32, u8);
extern void GXInitTexObjData(void *, void *);
extern void *GXGetTexObjData(const void *);
extern void GXInitTlutObj(void *, void *, u32, u16);
int main(void) {
    GXTexObj original, copied;
    uintptr_t addresses[] = {0, 0x12345678, UINT64_C(0x2201937c0), UINT64_C(0x3201937c0)};
    for (unsigned i = 0; i < sizeof(addresses) / sizeof(addresses[0]); ++i) {
        GXInitTexObj(&original, (void *)addresses[i], 32, 16, GX_TF_I8, 0, 0, 0);
        memcpy(&copied, &original, sizeof(copied));
        if (GXGetTexObjData(&copied) != (void *)addresses[i]) return 1;
        GXInitTexObjData(&copied, (void *)addresses[(i + 1) % 4]);
        if (GXGetTexObjData(&copied) != (void *)addresses[(i + 1) % 4]) return 1;
    }
    return sizeof(GXTexObj) != 88 || sizeof(GXTlutObj) != 16;
}
