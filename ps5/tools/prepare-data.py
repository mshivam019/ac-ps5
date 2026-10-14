#!/usr/bin/env python3
"""Prepare private M.2 data from a user's USA rev-0 disc and optional HD ZIP."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_disc(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.read(0x460)
        if len(header) != 0x460 or header[:6] != b'GAFE01' or header[7] != 0:
            raise ValueError('Expected Animal Crossing USA GAFE01 revision 0')
        if header[0x1c:0x20] != bytes.fromhex('c2339f3d'):
            raise ValueError('Expected an uncompressed GameCube ISO/GCM')
        dol, fst, fst_size = struct.unpack_from('>III', header, 0x420)
        if dol + 0x100 > size or fst + fst_size > size or fst_size < 12:
            raise ValueError('Disc executable or file table is out of bounds')
        stream.seek(dol)
        dol_header = stream.read(0x100)
        offsets = struct.unpack_from('>18I', dol_header, 0)
        lengths = struct.unpack_from('>18I', dol_header, 0x90)
        for offset, length in zip(offsets, lengths):
            if length and (offset < 0x100 or dol + offset + length > size):
                raise ValueError('Disc executable section is out of bounds')
        stream.seek(fst)
        table = stream.read(fst_size)
        count = struct.unpack_from('>I', table, 8)[0]
        if count < 1 or count * 12 > fst_size:
            raise ValueError('Invalid disc file table size')
        strings = table[count * 12:]
        files = 0
        for index in range(1, count):
            name, offset, length = struct.unpack_from('>III', table, index * 12)
            name_offset = name & 0xffffff
            if name_offset >= len(strings) or b'\0' not in strings[name_offset:]:
                raise ValueError('Invalid disc file name')
            if name >> 24:
                if length <= index or length > count:
                    raise ValueError('Invalid disc directory range')
            else:
                if offset + length > size:
                    raise ValueError('Disc file is out of bounds')
                files += 1
    return {'disc_id': 'GAFE01', 'revision': 0, 'bytes': size,
            'files': files, 'sha256': digest(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', required=True, type=Path)
    parser.add_argument('--hd-zip', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    receipt = {'disc': validate_disc(args.iso), 'console_data_path': '/mnt/ext1/app-ac'}
    if args.output.exists():
        raise ValueError('Choose a new output directory to preserve existing data and saves')
    texture_members = []
    if args.hd_zip:
        with zipfile.ZipFile(args.hd_zip) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f'HD ZIP CRC failed: {bad}')
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or '..' in path.parts or '\\' in member.filename:
                    raise ValueError('Unsafe HD archive path')
                if path.parts and path.parts[0] == 'GAF' and path.suffix.lower() == '.dds':
                    texture_members.append(member)
            if not texture_members:
                raise ValueError('No GAF DDS textures in the HD archive')
            receipt['hd_pack'] = {'sha256': digest(args.hd_zip),
                'files': len(texture_members), 'bytes': sum(m.file_size for m in texture_members),
                'readme': archive.read('Readme.txt').decode('utf-8', errors='replace')}
    (args.output / 'rom').mkdir(parents=True)
    (args.output / 'save').mkdir()
    (args.output / 'texture_pack').mkdir()
    shutil.copy2(args.iso, args.output / 'rom/game.iso')
    if digest(args.output / 'rom/game.iso') != receipt['disc']['sha256']:
        raise ValueError('Staged disc hash mismatch')
    if args.hd_zip:
        with zipfile.ZipFile(args.hd_zip) as archive:
            for member in texture_members:
                relative = PurePosixPath(member.filename).relative_to('GAF')
                target = args.output / 'texture_pack' / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open('xb') as destination:
                    shutil.copyfileobj(source, destination)
    defaults = ROOT / 'ps5/default-settings.ini'
    if not defaults.is_file():
        defaults = Path(__file__).resolve().parent / 'default-settings.ini'
    shutil.copy2(defaults, args.output / 'settings.ini')
    (args.output / 'data-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Private M.2 data prepared: {args.output}')


if __name__ == '__main__':
    main()
