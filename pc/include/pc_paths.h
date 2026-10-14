#ifndef PC_PATHS_H
#define PC_PATHS_H
/* Native titles cannot rely on changing the sandbox working directory. */
#ifdef __PROSPERO__
#define PC_DATA_PATH(path) "/app0/data/" path
#define PC_USER_PATH(path) "/download0/" path
#define PC_SHADER_PATH(path) "/app0/assets/shaders/" path
#else
#define PC_DATA_PATH(path) path
#define PC_USER_PATH(path) path
#define PC_SHADER_PATH(path) "shaders/" path
#endif
#endif
