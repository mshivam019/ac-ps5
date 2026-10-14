/* Host-only GL upload boundary capture; no window, SDK, disc, or console. */
#include <assert.h>
#include "../../pc/src/pc_texture_pack.c"

PCSettings g_pc_settings;
SDL_Window* g_pc_window;
int g_pc_profile_enabled;
void pc_profiler_add_count_texture_bind_slow(void) {}

static GLuint next_texture = 1;
static int uploads, deleted;
static unsigned char expected_pixels[256 * 256 * 4];
static size_t expected_size;
static int separate_alpha_mask;
static void GLAD_API_PTR gen(GLsizei n, GLuint* ids) { while (n--) *ids++ = next_texture++; }
static void GLAD_API_PTR bind_texture(GLenum target, GLuint id) { (void)target; (void)id; }
static void GLAD_API_PTR parameter(GLenum target, GLenum name, GLint value) {
    (void)target; (void)name; (void)value;
}
static void GLAD_API_PTR delete_textures(GLsizei n, const GLuint* ids) { (void)ids; deleted += n; }
static GLenum GLAD_API_PTR error(void) { return GL_NO_ERROR; }
static void GLAD_API_PTR integers(GLenum name, GLint* value) { (void)name; *value = 0; }
static void GLAD_API_PTR upload(GLenum target, GLint level, GLint internal, GLsizei w, GLsizei h,
                           GLint border, GLenum format, GLenum type, const void* pixels) {
    (void)target; (void)level; (void)internal; (void)border;
    assert(w > 0 && h > 0 && format == GL_RGBA && type == GL_UNSIGNED_BYTE);
    const unsigned char* rgba = pixels;
    assert(expected_size == (size_t)w * h * 4);
    assert(memcmp(expected_pixels, pixels, expected_size) == 0); /* no row flip or alpha loss */
    int visible = 0, transparent = 0;
    for (int i = 0; i < w * h; i++) {
        assert(rgba[i*4] == rgba[i*4+1] && rgba[i*4] == rgba[i*4+2]);
        visible |= rgba[i*4+3] != 0;
        transparent |= rgba[i*4+3] == 0;
    }
    assert(visible);
    /* Notice-board RGB5A3 faces use TEXEL1 for silhouette alpha. */
    assert(separate_alpha_mask ? !transparent : transparent);
    uploads++;
}

int main(void) {
    glad_glGenTextures = gen;
    glad_glBindTexture = bind_texture;
    glad_glTexParameteri = parameter;
    glad_glDeleteTextures = delete_textures;
    glad_glGetError = error;
    glad_glGetIntegerv = integers;
    glad_glTexImage2D = upload;
    pc_texture_pack_init(); /* runner uses an empty temporary working directory */
    assert(pc_texture_pack_active() && !g_texpack_active);
    assert(xxhash64("", 0) == 0xef46db3751d8e999ULL);
    for (unsigned i = 0; i < sizeof(g_controller_ui)/sizeof(g_controller_ui[0]); i++) {
        ControllerUIEntry* entry = &g_controller_ui[i];
        int w = 0, h = 0;
        char path[512];
        snprintf(path, sizeof(path), "%s%s", CONTROLLER_UI_DIR, entry->filename);
        FILE* file = fopen(path, "rb");
        assert(file && fseek(file, 128, SEEK_SET) == 0);
        expected_size = fread(expected_pixels, 1, sizeof(expected_pixels), file);
        fclose(file);
        separate_alpha_mask = entry->fmt == 5;
        assert(controller_ui_load(entry, &w, &h));
        assert(w == entry->w * 4 && h == entry->h * 4);
    }
    /* Exercise public lookup with synthetic GC data, never copyrighted pixels. */
    ControllerUIEntry* entry = &g_controller_ui[0];
    unsigned char data[2048] = { 42 };
    entry->hash = xxhash64(data, sizeof(data));
    GLuint expected = entry->texture;
    int w, h;
    assert(pc_texture_pack_lookup(data, sizeof(data), 32, 64, 2, NULL, 0, 0, &w, &h) == expected);
    assert(pc_texture_pack_lookup(data, sizeof(data), 64, 32, 2, NULL, 0, 0, &w, &h) == 0);
    assert(pc_texture_pack_lookup(data, sizeof(data), 32, 64, 1, NULL, 0, 0, &w, &h) == 0);
    int before = uploads;
    /* Private HD exact/wildcard tables and stale positive/negative caches lose. */
    texpack_insert(entry->hash, 0, 2, 32, 64, "must-not-open.dds");
    texpack_insert_wildcard(entry->hash, 2, 32, 64, "must-not-open-either.dds");
    g_texpack_active = 1;
    xxh_u64 key = loaded_cache_key(entry->hash, 0, 2, 32, 64);
    loaded_cache_insert(key, 9999, 1, 1);
    neg_cache_insert(key);
    assert(pc_texture_pack_lookup(data, sizeof(data), 32, 64, 2, NULL, 0, 0, &w, &h) == expected);
    assert(uploads == before);
    /* Missing bundled file must fall back to original, not the HD pack. */
    glDeleteTextures(1, &entry->texture);
    entry->texture = 0;
    entry->attempted = 0;
    entry->filename = "deliberately-missing.dds";
    assert(pc_texture_pack_lookup(data, sizeof(data), 32, 64, 2, NULL, 0, 0, &w, &h) == 0);
    assert(entry->attempted);
    assert(!pc_texture_pack_lookup(NULL, sizeof(data), 32, 64, 2, NULL, 0, 0, &w, &h));
    pc_texture_pack_shutdown();
    assert(deleted == uploads + 1); /* includes synthetic stale HD GL name */
    for (unsigned i = 0; i < sizeof(g_controller_ui)/sizeof(g_controller_ui[0]); i++)
        assert(!g_controller_ui[i].texture && !g_controller_ui[i].attempted);
    puts("Controller UI precedence, DDS upload, independent activation and cleanup: PASS");
    return 0;
}
