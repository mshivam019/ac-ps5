#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* Frame intervals after the swap and pacing work, including the previous
 * frame's post-VI game work. Console measurements remain gameplay evidence
 * only for the scene and duration actually tested. */
static double intervals[600];
static uint64_t previous;
static unsigned warmup;
static unsigned count;

static int compare_interval(const void *left, const void *right) {
    const double a = *(const double *)left;
    const double b = *(const double *)right;
    return (a > b) - (a < b);
}

void ac_ps5_record_frame(uint64_t ticks, uint64_t frequency) {
    if (!frequency)
        return;
    if (previous && warmup >= 600) {
        intervals[count++] = (double)(ticks - previous) * 1000.0 / (double)frequency;
        if (count == 600) {
            double total = 0.0;
            unsigned late = 0;
            for (unsigned i = 0; i < count; ++i) {
                total += intervals[i];
                if (intervals[i] > 18.0)
                    ++late;
            }
            qsort(intervals, count, sizeof(intervals[0]), compare_interval);
            printf("[AC-FRAMES] samples=600 fps=%.3f p95_ms=%.3f p99_ms=%.3f max_ms=%.3f over18ms=%u\n",
                   600000.0 / total, intervals[569], intervals[593], intervals[599], late);
            count = 0;
        }
    } else if (warmup < 600) {
        ++warmup;
    }
    previous = ticks;
}
