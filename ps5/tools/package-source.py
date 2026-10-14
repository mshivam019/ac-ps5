#!/usr/bin/env python3
"""Archive tracked game/port source and the prepared native dependency source trees."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {'.git', 'build', 'dist', '__pycache__', '.cache', '.deps', '.local', 'conformance'}
SKIP_SUFFIXES = {'.iso', '.gcm', '.rvz', '.ciso', '.gci', '.key', '.pem', '.log', '.o', '.a', '.so', '.elf', '.bin', '.exe', '.prx'}


def source_files(root):
    for base, directories, files in os.walk(root):
        directories[:] = sorted(d for d in directories if d not in SKIP_DIRS and not (Path(base) / d).is_symlink())
        for name in sorted(files):
            path = Path(base) / name
            if not name.startswith('.env') and not path.is_symlink() and path.suffix.lower() not in SKIP_SUFFIXES:
                yield path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--sdk-root', type=Path, default=Path.home() / 'ps5sdk')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Choose a new source artifact path')
    if subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Commit the port before packaging corresponding source')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    gl = args.sdk_root / 'ps5-opengl-030/ps5-opengl'
    dependencies = {'native-app': args.sdk_root / 'native-app-boilerplate',
                    'ps5-opengl': gl,
                    'sdl2': gl / 'build/sdl2-native/SDL',
                    'sdl2-integration': gl / 'build/sdl2-native/integration',
                    'sdl2-2160': gl / 'build/soh-sdl-2160p120/SDL',
                    'sdl2-2160-integration': gl / 'build/soh-sdl-2160p120/integration'}
    entries = []
    with tarfile.open(args.output, 'w:gz') as archive:
        names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
        for name in sorted(n for n in names if n):
            path = ROOT / name
            archive_name = 'animal-crossing-ps5/' + name
            if path.is_symlink() or path.suffix.lower() in {'.iso', '.gcm', '.rvz', '.gci', '.key', '.pem'}:
                raise ValueError(f'Private file tracked in port source: {name}')
            archive.add(path, arcname=archive_name, recursive=False)
            entries.append({'path': archive_name, 'bytes': path.stat().st_size,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        for name, directory in dependencies.items():
            if not directory.is_dir():
                raise ValueError(f'Missing prepared dependency source: {directory}')
            for path in source_files(directory):
                archive_name = 'dependencies/' + name + '/' + path.relative_to(directory).as_posix()
                archive.add(path, arcname=archive_name, recursive=False)
                entries.append({'path': archive_name, 'bytes': path.stat().st_size,
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    with tarfile.open(args.output, 'r:gz') as archive:
        members = archive.getmembers()
        if len(members) != len(entries):
            raise ValueError('Source archive entry count mismatch')
        for member, item in zip(members, entries):
            stream = archive.extractfile(member)
            if member.name != item['path'] or member.size != item['bytes'] or stream is None:
                raise ValueError('Source archive metadata mismatch')
            if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
                raise ValueError('Source archive content hash mismatch')
    receipt = {'entries': len(entries), 'bytes': args.output.stat().st_size,
               'sha256': hashlib.file_digest(args.output.open('rb'), 'sha256').hexdigest(),
               'revision': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()}
    manifest_path = args.output.with_name(args.output.name.removesuffix('.tar.gz') + '-manifest.json')
    manifest_path.write_text(json.dumps({'revision': receipt['revision'], 'files': entries}, indent=2) + '\n')
    args.output.with_suffix(args.output.suffix + '.receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
