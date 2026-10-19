#!/usr/bin/env python3
"""Run the patched color encoder and Mesa pixel conversions on a Linux host.

Uses actual driver/Mesa functions and generated format descriptions, not a
second implementation of the encoder. This does not emulate the PS5 GPU.
"""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]


def body(text, start):
    opening = text.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def function(text, name, result):
    match = re.search(r'\b' + name + r'\s*\(', text)
    if not match:
        raise ValueError(name)
    return result + ' ' + body(text, match.start()) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, default=Path.home() / 'ps5sdk')
    parser.add_argument('--driver-source', type=Path, default=ROOT / 'build/graphics-bgra/source')
    args = parser.parse_args()
    original = args.sdk_root / 'ps5-opengl-030/ps5-opengl'
    mesa = original / 'third_party/mesa-26.2.0'
    generated = original / 'build/mesa-ps5-probe/src'
    table = (generated / 'util/format/u_format_table.c').read_text()
    amd = (mesa / 'src/amd/common/ac_formats.c').read_text()
    driver = (args.driver_source / 'src/gallium/ps5/ps5_screen.c').read_text()
    egl = (args.driver_source / 'src/egl/ps5_egl.c').read_text()
    code = '''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "util/format/u_format.h"
#include "amd/common/amd_family.h"
#include "amdgfxregs.h"
#define PS5_ENABLE_CORE_RENDER_FORMATS_CANDIDATE CORE_FORMATS
static const struct util_format_description descriptions[PIPE_FORMAT_COUNT] = {
'''
    for name in ('B8G8R8A8_UNORM', 'R8G8B8A8_UNORM'):
        code += body(table, table.index('[PIPE_FORMAT_' + name + '] = {')) + ',\n'
    code += '''};
const struct util_format_description *util_format_description(enum pipe_format f) {
    assert(f == PIPE_FORMAT_B8G8R8A8_UNORM || f == PIPE_FORMAT_R8G8B8A8_UNORM);
    return &descriptions[f];
}
'''
    for name in ('ac_get_cb_format', 'ac_get_cb_number_type', 'ac_translate_colorswap'):
        code += function(amd, name, 'unsigned')
    code += function(driver, 'ps5_core_render_target_format', 'static bool')
    code += function(driver, 'ps5_color_target_info', 'static uint32_t')
    for fmt in ('b8g8r8a8', 'r8g8b8a8'):
        for operation in ('pack', 'unpack'):
            code += function(table, f'util_format_{fmt}_unorm_{operation}_rgba_8unorm', 'void')
    code += '''
int main(void) {
    assert(ps5_core_render_target_format(PIPE_FORMAT_B8G8R8A8_UNORM));
    assert(ps5_color_target_info(PIPE_FORMAT_B8G8R8A8_UNORM) == 0x8828);
    assert(ps5_color_target_info(PIPE_FORMAT_R8G8B8A8_UNORM) == 0x8028);
    const uint8_t colors[][4] = {{255,0,0,255}, {0,255,0,255}, {0,0,255,255},
        {255,255,255,255}, {147,89,34,127}, {20,180,70,0}};
    for (unsigned i=0; i<sizeof(colors)/sizeof(colors[0]); ++i) {
        uint8_t bgra[4], rgba[4], restored[4];
        util_format_b8g8r8a8_unorm_pack_rgba_8unorm(bgra,4,colors[i],4,1,1);
        assert(bgra[0]==colors[i][2] && bgra[1]==colors[i][1] &&
               bgra[2]==colors[i][0] && bgra[3]==colors[i][3]);
        util_format_b8g8r8a8_unorm_unpack_rgba_8unorm(restored,bgra,1);
        assert(!memcmp(restored,colors[i],4));
        util_format_r8g8b8a8_unorm_pack_rgba_8unorm(rgba,4,colors[i],4,1,1);
        assert(!memcmp(rgba,colors[i],4));
    }
    puts("PASS: BGRA render encoding, clear packing, RGBA readback and offscreen colors");
}
'''
    with tempfile.TemporaryDirectory() as directory:
        executable = Path(directory) / 'scanout-test'
        includes = [mesa / 'include', mesa / 'src', mesa / 'src/gallium/include',
                    generated, original / 'third_party/opengnm-psbc/src/amd/common']
        for enabled in (0, 1):
            command = ['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                       '-DHAVE_ENDIAN_H=1', '-D_POSIX_C_SOURCE=200809L',
                       '-fsanitize=address,undefined', f'-DCORE_FORMATS={enabled}']
            for include in includes:
                command += ['-I', str(include)]
            subprocess.run(command + ['-x', 'c', '-', '-o', str(executable)],
                           input=code, text=True, check=True)
            subprocess.run([str(executable)], check=True)
    # EGL must advertise the same format it allocates. Pbuffers stay RGBA.
    formats = re.findall(r'resource.format = (PIPE_FORMAT_\w+);', egl)
    assert formats == ['PIPE_FORMAT_Z32_FLOAT_S8X24_UINT',
                       'PIPE_FORMAT_B8G8R8A8_UNORM', 'PIPE_FORMAT_R8G8B8A8_UNORM'], formats
    assert 'ps5_config.visual.color_format = PIPE_FORMAT_B8G8R8A8_UNORM;' in egl
    print('PASS: display format agrees with VideoOut; pbuffer format unchanged')


if __name__ == '__main__':
    main()
