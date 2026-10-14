#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cmake -S "$root/pc" -B "$root/build/host" -G Ninja -DPC_BUILD_PORTABILITY_TESTS=ON "$@"
cmake --build "$root/build/host" --parallel "${AC_BUILD_JOBS:-6}"
ctest --test-dir "$root/build/host" --output-on-failure
