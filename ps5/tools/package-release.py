#!/usr/bin/env python3
"""Create Windows/Linux installers for the same native PS5 title; no desktop game."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile
from validate import ROOT, TITLE, title_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='v0.1.0-dev.1')
    parser.add_argument('--console-tested', action='store_true', help='Record completed console validation for this exact title build')
    parser.add_argument('--title', type=Path, default=ROOT / 'dist' / TITLE)
    args = parser.parse_args()
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[a-z0-9.]+)?', args.version):
        parser.error('Invalid version')
    files = title_files(args.title)
    build = json.loads((args.title / 'build-receipt.json').read_text())
    manifest = {'version': args.version, 'platform': 'PS5', 'title': TITLE,
        'profile': build['profile'], 'width': build['width'], 'height': build['height'],
        'target_fps': build['target_fps'],
        'console_tested': args.console_tested, 'files': [{'path': p.relative_to(args.title).as_posix(),
            'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    output = ROOT / 'dist/releases' / args.version
    output.mkdir(parents=True, exist_ok=True)
    for platform in ('catalog', 'linux', 'windows'):
        name = f'{TITLE}.zip' if platform == 'catalog' else f'animal-crossing-ps5-{build["profile"]}-{args.version}-{platform}.zip'
        target = output / name
        if target.exists():
            raise ValueError(f'Preserve existing release artifact: {target}')
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            prefix = TITLE if platform == 'catalog' else 'output/' + TITLE
            for path in files:
                archive.write(path, prefix + '/' + path.relative_to(args.title).as_posix())
            if platform != 'catalog':
                wrapper = 'install.sh' if platform == 'linux' else 'install.ps1'
                for name in ('install.py', 'console_control.py', wrapper, 'prepare-data.py', 'ps5_install_lib.py', 'prepare-files.py', 'transfer-files.py', 'Prepare-Files-Windows.cmd', 'prepare-files.sh', 'validate-files.py', 'Validate-Files-Windows.cmd', 'validate-files.sh', 'ps5_store_setup.py', 'store-setup.py', 'Store-Setup-Windows.cmd', 'store-setup.sh', 'INSTALL-HELPER-LICENSE'):
                    archive.write(ROOT / 'ps5/tools' / name, 'tools/' + name)
                archive.write(args.title / 'assets/default-settings.ini', 'tools/default-settings.ini')
                archive.write(ROOT / 'README.md', 'README.md')
                archive.write(ROOT / 'ps5/INSTALL.txt', 'INSTALL.txt')
                archive.write(ROOT / 'INSTALL.md', 'INSTALL.md')
                for guide in ('CONSOLE-SETUP.md', 'MODS.md', 'SETTINGS.md'):
                    archive.write(ROOT / 'docs' / guide, guide)
                archive.writestr('MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
        with zipfile.ZipFile(target) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP CRC validation failed')
            for item in manifest['files']:
                data = archive.read(prefix + '/' + item['path'])
                if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                    raise ValueError('ZIP differs from the staged native title')
        target.with_suffix(target.suffix + '.sha256').write_text(hashlib.file_digest(target.open('rb'), 'sha256').hexdigest() + '  ' + target.name + '\n')
        print(target)
    (output / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
