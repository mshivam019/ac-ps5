/* Static Mesa must not allocate through the guest game's JKR heap. */
#include <stddef.h>
#include <stdlib.h>

void *ac_ps5_renderer_new(size_t size) { return malloc(size ? size : 1); }
void *ac_ps5_renderer_new_nothrow(size_t size, const void *tag) {
    (void)tag;
    return ac_ps5_renderer_new(size);
}
void ac_ps5_renderer_delete(void *memory) { free(memory); }
void ac_ps5_renderer_delete_sized(void *memory, size_t size) {
    (void)size;
    free(memory);
}
