#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
export PS5_PAYLOAD_SDK="${PS5_PAYLOAD_SDK:-${PS5SDK_ROOT:-$HOME/ps5sdk}/native-app-boilerplate/.deps/native/ps5-payload-sdk}"
cmake -S "$root/pc" -B "$root/build/ps5" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$root/ps5/cmake/native.cmake" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_DISABLE_FIND_PACKAGE_PkgConfig=ON "$@"
cmake --build "$root/build/ps5" --parallel "${AC_BUILD_JOBS:-6}"
