#!/usr/bin/env python3
"""Upload a closed native PS5 title, preserving M.2 saves and prior executables."""
import argparse
from datetime import datetime, timezone
import ftplib
import json
import console_control
from pathlib import Path

TITLE = 'PPSA99660'
DIRECTORIES = set()


def exists(ftp, path):
    try:
        size = ftp.size(path)
        # ftpsrv v0.20 returns unsigned -1 instead of FTP 550 for a missing file.
        return size is not None and 0 <= size < (1 << 63)
    except ftplib.error_perm as error:
        if not str(error).startswith('550'):
            raise
        return False


def directory(ftp, path):
    current = ''
    for part in path.split('/'):
        if not part:
            continue
        current += '/' + part
        if current in DIRECTORIES:
            continue
        try:
            ftp.mkd(current)
        except ftplib.error_perm:
            ftp.cwd(current)
        DIRECTORIES.add(current)


def upload(ftp, source, target, preserve, stamp):
    directory(ftp, target.rsplit('/', 1)[0])
    present = exists(ftp, target)
    if preserve and present:
        print('Preserved', target)
        return
    with source.open('rb') as stream:
        ftp.storbinary('STOR ' + target + '.next', stream, 262144)
    stored = ftp.size(target + '.next')
    if stored != source.stat().st_size:
        parent, name = (target + '.next').rsplit('/', 1)
        entries = json.loads(console_control.call(36, {'path': parent}))['entries']
        stored = next((entry['size'] for entry in entries if entry['name'] == name), None)
    if stored != source.stat().st_size:
        raise RuntimeError(f'Transfer size mismatch: {target}')
    backup = target + '.before-' + stamp
    if present:
        ftp.rename(target, backup)
    try:
        ftp.rename(target + '.next', target)
    except Exception:
        if present:
            ftp.rename(backup, target)
        raise
    print('Uploaded', target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--src', required=True, type=Path)
    parser.add_argument('--console', required=True)
    parser.add_argument('--ftp-port', default=2121, type=int)
    parser.add_argument('--control-port', default=9114, type=int)
    parser.add_argument('--install-root', default='/mnt/ext1/etaHEN/games')
    parser.add_argument('--data', type=Path, help='Optional prepare-data.py output; saves never uploaded')
    args = parser.parse_args()
    if not (args.src / 'eboot.bin').is_file():
        parser.error('--src must be the extracted PPSA99660 title folder')
    meta = json.loads((args.src / 'sce_sys/param.json').read_text())
    if meta['titleId'] != TITLE:
        raise ValueError('Title ID mismatch')
    console_control.HOST = args.console
    console_control.PORT = args.control_port
    processes = json.loads(console_control.call(162, {}))['procs']
    if any(process.get('title_id') == TITLE for process in processes):
        raise RuntimeError('Save and close Animal Crossing before updating its live files')
    title_files = []
    for source in args.src.rglob('*'):
        relative = source.relative_to(args.src)
        if source.is_symlink() or any(p in {'save', 'rom', 'texture_pack'} for p in relative.parts):
            raise ValueError(f'Unexpected game/user content in title: {relative}')
        if source.is_file():
            title_files.append(source)
    data_files = []
    if args.data:
        for source in args.data.rglob('*'):
            relative = source.relative_to(args.data)
            if source.is_symlink():
                raise ValueError('Data must not contain symbolic links')
            if source.is_file() and (relative.parts[0] in {'rom', 'texture_pack'} or relative.as_posix() == 'settings.ini'):
                data_files.append(source)
    print('Close Animal Crossing before uploading. This helper does not close, register or launch titles.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    base = args.install_root.rstrip('/') + '/' + TITLE
    with ftplib.FTP() as ftp:
        ftp.connect(args.console, args.ftp_port, timeout=60)
        ftp.login()
        ftp.voidcmd('TYPE I')
        for source in sorted(data_files):
            relative = source.relative_to(args.data).as_posix()
            upload(ftp, source, base + '/data/' + relative, True, stamp)
        for source in sorted(title_files, key=lambda p: (p.name == 'eboot.bin', str(p))):
            relative = source.relative_to(args.src).as_posix()
            upload(ftp, source, base + '/' + relative, False, stamp)
    print('Register/mount', base, 'with PS5 Upload or your existing native-title launcher.')


if __name__ == '__main__':
    main()
