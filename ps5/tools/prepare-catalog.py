#!/usr/bin/env python3
"""Prepare the owner's catalog record locally; no GitHub mutations."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TITLE = 'PPSA99660'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[a-z0-9.]+)?', args.version):
        parser.error('Invalid version')
    asset = ROOT / 'dist/releases' / args.version / (TITLE + '.zip')
    with zipfile.ZipFile(asset) as archive:
        names = archive.namelist()
        if any(not n.startswith(TITLE + '/') for n in names):
            raise ValueError('Catalog ZIP must have one title folder at its root')
        param = json.loads(archive.read(TITLE + '/sce_sys/param.json'))
        if param['titleId'] != TITLE or TITLE + '/eboot.bin' not in names:
            raise ValueError('Native title is missing or mismatched')
    repo = 'https://github.com/mshivam019/ac-ps5'
    record = dict(titleid=TITLE, name='Animal Crossing for PS5', kind='game',
        description='Unofficial native port of Animal Crossing for GameCube; requires your own USA revision 0 game data.',
        license='GPL-3.0-or-later', author='mshivam019', version=args.version,
        source_repo=repo, artifact_url=f'{repo}/releases/download/{args.version}/{TITLE}.zip',
        sha256=hashlib.file_digest(asset.open('rb'), 'sha256').hexdigest(),
        icon_url=f'https://raw.githubusercontent.com/mshivam019/ac-ps5/{args.version}/ps5/sce_sys/icon0.png')
    target = ROOT / 'dist/catalog/apps' / (TITLE + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2) + '\n')
    print(target)
    print('Offline record prepared. Public-repository/release verification remains pending.')


if __name__ == '__main__':
    main()
