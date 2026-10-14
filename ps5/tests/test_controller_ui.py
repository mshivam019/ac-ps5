#!/usr/bin/env python3
"""Run isolated host validation, without touching the parent's build tree."""
import json
from pathlib import Path
import shlex
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'ps5/assets/controller-ui'


def main():
    manifest = json.loads((ASSETS / 'manifest.json').read_text())
    files = set()
    for entry in manifest['textures']:
        name = f"tex1_{entry['width']}x{entry['height']}_{entry['hash']}_{entry['format']}.dds"
        files.add(name)
        data = (ASSETS / name).read_bytes()
        assert data[:4] == b'DDS '
        height, width = struct.unpack_from('<II', data, 12)
        assert (width, height) == (entry['width'] * 4, entry['height'] * 4)
        assert len(data) == 128 + width * height * 4
        assert struct.unpack_from('<4I', data, 92) == (0xff, 0xff00, 0xff0000, 0xff000000)
        svg = ET.parse(ASSETS / entry['svg']).getroot()
        # No embedded bitmap, external asset, or machine-dependent font.
        assert all(node.tag.split('}')[-1] in {'svg', 'g', 'rect', 'circle', 'path'} for node in svg.iter())
    assert files == {p.name for p in ASSETS.glob('tex1_*.dds')}
    with tempfile.TemporaryDirectory(prefix='ac-controller-ui-') as work:
        work = Path(work)
        subprocess.run(['python', str(ROOT / 'ps5/tools/generate-controller-ui.py'), '--output', str(work / 'assets')], check=True)
        for path in (work / 'assets').iterdir():
            assert path.read_bytes() == (ASSETS / path.name).read_bytes(), path.name
        flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'sdl2'], text=True))
        includes = ['-I' + str(ROOT / p) for p in ('pc/include', 'pc/lib/glad/include', 'include')]
        subprocess.run(['cc', '-std=c11', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                        f'-DPC_CONTROLLER_UI_TEST="{ASSETS}/"', *includes,
                        str(ROOT / 'ps5/tests/controller_ui_tests.c'), str(ROOT / 'pc/lib/glad/src/gl.c'),
                        *flags, '-ldl', '-o', str(work / 'test')], check=True)
        subprocess.run([str(work / 'test')], cwd=work, check=True)
        # The desktop build keeps its original behavior and needs no native UI.
        subprocess.run(['cc', '-std=c11', '-fsyntax-only', *includes, *flags,
                        str(ROOT / 'pc/src/pc_texture_pack.c')], check=True)
    print('Manifest, SVG provenance rules, reproducible DDS, desktop compile: PASS')


if __name__ == '__main__':
    main()
