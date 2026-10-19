#!/usr/bin/env python3
"""Build Animal Crossing's BGRA scanout runtime without editing the shared SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, default=Path.home() / 'ps5sdk')
    parser.add_argument('--profile', choices=('1080p60', '2160p60'), required=True)
    args = parser.parse_args()
    sdk = args.sdk_root.resolve()
    original = sdk / 'ps5-opengl-030/ps5-opengl'
    work = ROOT / 'build/graphics-bgra'
    source = work / 'source'
    source.mkdir(parents=True, exist_ok=True)
    # Only source files are copied. Large dependencies stay read-only inputs.
    for directory in ('src', 'toolchain', 'tools', 'native-app'):
        shutil.copytree(original / directory, source / directory, dirs_exist_ok=True)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i',
                    str(ROOT / 'ps5/patches/bgra-scanout.patch')], cwd=source, check=True)
    output = (work / args.profile).resolve()
    subprocess.run(['make', '-j6', '-o', 'ps5-opengl-mesa', '-C', str(original / 'tests/ps5'),
                    '-f', 'native-app.mk', 'runtime',
                    f'PS5_OPENGL_ROOT={source.resolve()}',
                    f'PS5_OPENGL_BUILD={output}',
                    f'PS5_OPENGL_MESA_SRC={original / "third_party/mesa-26.2.0"}',
                    f'PS5_OPENGL_MESA_BUILD={original / "build/mesa-ps5-probe"}',
                    f'PS5_OPENGL_PSBC={original / "third_party/opengnm-psbc"}',
                    f'PS5_PAYLOAD_SDK={sdk / "native-app-boilerplate/.deps/native/ps5-payload-sdk"}',
                    f'PS5_SCANOUT_HEIGHT={args.profile[:4]}', 'PS5_SCANOUT_FPS=60',
                    'PS5_GPU_PRESENT_BATCH=1', 'PS5_DEFERRED_DRAW_BATCH=1'], check=True)
    archive = output / 'libps5_opengl_core33.a'
    receipt = {'profile': args.profile, 'bytes': archive.stat().st_size,
               'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
               'patch_sha256': hashlib.sha256(
                   (ROOT / 'ps5/patches/bgra-scanout.patch').read_bytes()).hexdigest()}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
