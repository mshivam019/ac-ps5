#!/usr/bin/env python3
"""Check native SELF integrity, forbidden imports, title identity and release hygiene."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TITLE = 'PPSA99660'
FORBIDDEN_SUFFIXES = {'.iso', '.gcm', '.ciso', '.rvz', '.gci', '.log', '.key', '.pem', '.mp4', '.mkv'}


def title_files(title):
    for relative in ('eboot.bin', 'sce_sys/param.json', 'sce_sys/icon0.png', 'sce_module/libc.prx'):
        if not (title / relative).is_file():
            raise ValueError(f'Missing native title file: {relative}')
    if json.loads((title / 'sce_sys/param.json').read_text())['titleId'] != TITLE:
        raise ValueError('Unexpected title ID')
    files = []
    for path in sorted(title.rglob('*')):
        relative = path.relative_to(title)
        if path.is_symlink() or path.suffix.lower() in FORBIDDEN_SUFFIXES or any(
                p in {'rom', 'save', 'texture_pack', '.git', '.deps'} for p in relative.parts):
            raise ValueError(f'Private/game content in title: {relative}')
        if path.is_file():
            files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--title', type=Path, default=ROOT / 'dist' / TITLE)
    parser.add_argument('--tool', type=Path, default=Path.home() / 'ps5sdk/ps5-native-tool')
    parser.add_argument('--elf', type=Path, default=ROOT / 'build/native-title/build/llvm-pie.elf')
    args = parser.parse_args()
    files = title_files(args.title)
    receipt = json.loads((args.title / 'build-receipt.json').read_text())
    if hashlib.sha256((args.title / 'eboot.bin').read_bytes()).hexdigest() != receipt['eboot_sha256']:
        raise ValueError('Executable differs from the native build receipt')
    for relative in ('eboot.bin', 'sce_module/libc.prx'):
        subprocess.run([str(args.tool), 'self', '--inspect', '--file', str(args.title / relative)], check=True)
    if args.elf.exists():
        dynamic = subprocess.check_output(['llvm-readelf', '-d', str(args.elf)], text=True)
        if 'PosixForWebKit' in dynamic:
            raise ValueError('Unavailable WebKit POSIX import')
    print(json.dumps({'platform': 'PS5', 'title': TITLE, 'files': len(files),
        'eboot_sha256': hashlib.sha256((args.title / 'eboot.bin').read_bytes()).hexdigest(),
        'console_tested': False}, indent=2))


if __name__ == '__main__':
    main()
