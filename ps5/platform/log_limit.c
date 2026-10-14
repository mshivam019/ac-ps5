#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

/* Driver diagnostics share the save-data quota. Both streams use O_APPEND,
 * so truncating the open file does not leave a stale write offset. */
void ac_ps5_limit_log(void) {
    struct stat info;
    int fd = fileno(stdout);
    if (fd < 0 || fstat(fd, &info) != 0 || info.st_size < 4 * 1024 * 1024)
        return;
    fflush(stdout);
    fflush(stderr);
    if (ftruncate(fd, 0) == 0) {
        clearerr(stdout);
        clearerr(stderr);
        fprintf(stderr, "[AC PS5] diagnostic log rotated to preserve save space\n");
    }
}
