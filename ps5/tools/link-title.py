#!/usr/bin/env python3
"""Link the cross-compiled game into a PS5 native title using our existing SDK."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"Native tool contract changed: {path}: {old!r}")
    path.write_text(text.replace(old, new))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('1080p60', '2160p60'), default='2160p60')
    parser.add_argument('--sdk-root', type=Path, default=Path.home() / 'ps5sdk')
    parser.add_argument('--hold-on-return', action='store_true', help='Diagnostic build keeps the sandbox/log mounted after main returns')
    args = parser.parse_args()
    sdk_root = args.sdk_root.resolve()
    pins = json.loads((ROOT / 'ps5/dependencies.json').read_text())
    profile = pins['graphics_profiles'][args.profile]
    cache = (ROOT / 'build/ps5/CMakeCache.txt').read_text()
    if f'AC_PS5_HEIGHT:STRING={profile["height"]}' not in cache:
        raise RuntimeError('Game and graphics profiles differ; run build.py --profile ' + args.profile)
    for item in pins['prepared_native_inputs'] + profile['prepared_native_inputs']:
        relative = item['sdk_relative_path'].replace('ac-gl-1080p60/sdk/', profile['sdk_relative_path'] + '/')
        path = sdk_root / relative
        if not path.is_file():
            raise RuntimeError(f'Missing prepared dependency: {path}')
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if path.stat().st_size != item['bytes'] or digest != item['sha256']:
            raise RuntimeError(f'Prepared dependency changed: {path}; review and update the lock')
    template = sdk_root / 'native-app-boilerplate'
    gl = sdk_root / 'ps5-opengl-030/ps5-opengl'
    prefix = sdk_root / profile['sdk_relative_path']
    sdl = sdk_root / profile['sdl_relative_path']
    archive = ROOT / 'build/ps5/libAnimalCrossing.a'
    if not archive.is_file():
        raise RuntimeError('Cross-build the game first with ps5/tools/build.sh')
    out = ROOT / 'build/native-title'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for directory in ('runtime', 'tooling', 'tools', '.deps/native'):
        shutil.copytree(template / directory, out / directory)
    shutil.copytree(ROOT / 'ps5/sce_sys', out / 'sce_sys')
    shutil.copytree(ROOT / 'ps5/platform', out / 'src')
    (out / 'vendor').mkdir()
    (out / 'assets').mkdir()
    shutil.copytree(ROOT / 'ps5/assets', out / 'assets', dirs_exist_ok=True)
    shutil.copy2(ROOT / 'ps5/default-settings.ini', out / 'assets/default-settings.ini')
    settings = out / 'assets/default-settings.ini'
    settings.write_text(settings.read_text().replace('window_width = 1920',
        f'window_width = {profile["width"]}').replace('window_height = 1080',
        f'window_height = {profile["height"]}'))
    shutil.copytree(ROOT / 'pc/shaders', out / 'assets/shaders')
    shutil.copytree(ROOT / 'ps5/licenses', out / 'licenses')
    shutil.copy2(ROOT / 'LICENSE', out / 'LICENSE')
    shutil.copy2(gl / 'native-app/runtime_shims.c', out / 'src/runtime_shims.c')
    if not args.hold_on_return:
        replace_once(out / 'src/runtime_shims.c',
                 '  for (;;)\n    sceKernelUsleep(100000);',
                 '  extern int sceSystemServiceLoadExec(const char *, const char **);\n'
                 '  int result = sceSystemServiceLoadExec("exit", NULL);\n'
                 '  fprintf(stderr, "PS5 exit request returned: 0x%x\\n", result);\n'
                 '  for (;;)\n    sceKernelUsleep(100000);')
    heap = out / 'src/app_heap.c'
    shutil.copy2(gl / 'native-app/app_heap.c', heap)
    replace_once(heap, '#define PS5_OPENGL_HEAP_SIZE (128u * 1024u * 1024u)',
                 '#define PS5_OPENGL_HEAP_SIZE ((size_t)2048u * 1024u * 1024u)')
    replace_once(heap, 'mspace state=%d base=%p size=%u\\n',
                 'mspace state=%d base=%p size=%zu\\n')
    replace_once(heap,
                 '  void *base = mmap(NULL, PS5_OPENGL_HEAP_SIZE, PROT_READ | PROT_WRITE,\n'
                 '                    MAP_PRIVATE | MAP_ANON, -1, 0);\n'
                 '  if (base == MAP_FAILED) {\n',
                 '  void *base = ps5_heap_map_direct(PS5_OPENGL_HEAP_SIZE);\n'
                 '  if (base == NULL) {\n')
    replace_once(heap, 'static int ps5_heap_ready(void) {\n',
                 'int64_t sceKernelGetDirectMemorySize(void);\n'
                 'int32_t sceKernelAllocateDirectMemory(int64_t, int64_t, size_t, size_t, int, int64_t *);\n'
                 'int32_t sceKernelMapDirectMemory(void **, size_t, int, int, int64_t, size_t);\n'
                 'static void *ps5_heap_map_direct(size_t size) {\n'
                 '  int64_t offset = 0;\n  void *base = NULL;\n'
                 '  if (sceKernelAllocateDirectMemory(0, sceKernelGetDirectMemorySize(), size,\n'
                 '                                    0x200000, 12, &offset) != 0) return NULL;\n'
                 '  if (sceKernelMapDirectMemory(&base, size, 0x33, 0, offset, 0x200000) != 0) return NULL;\n'
                 '  return base;\n}\n\nstatic int ps5_heap_ready(void) {\n')
    shutil.copy2(out / 'tooling/native/ps5-pie.ld', out / 'tooling/native/ps5-pie-base.ld')
    for name in ('ps5-pie.ld', 'app-symbols.map'):
        shutil.copy2(gl / 'native-app' / name, out / 'tooling/native' / name)
    sdk = out / '.deps/native/ps5-payload-sdk'
    for name in ('libSceAgc.so', 'libSceAgcDriver.so'):
        shutil.copy2(prefix / 'lib' / name, sdk / 'target/lib' / name)
    (sdk / 'target/lib/libScePosixForWebKit.so').unlink(missing_ok=True)
    script = out / 'tools/build.sh'
    replace_once(script, 'bash "$root/tools/setup-native-dependencies.sh" >/dev/null',
                 'test -x "$root/.deps/native/ps5-payload-sdk/bin/prospero-lld"')
    replace_once(script, '--eh-frame-hdr \\',
                 '--eh-frame-hdr --error-limit=0 --wrap=malloc --wrap=calloc '
                 '--wrap=realloc --wrap=free --wrap=posix_memalign --wrap=malloc_usable_size '
                 '--wrap=exit --wrap=_Exit --wrap=_exit '
                 '\\')
    # JSystem already defines the C++ allocation operators.
    replace_once(script,
                 'link_inputs=("$build/obj/app_crt.o" "$build/obj/app_cpp_runtime.o" "${objects[@]}")',
                 'link_inputs=("$build/obj/app_crt.o" "${objects[@]}")')
    replace_once(out / 'tooling/native/sce_module_writer.cpp',
                 'write_u64(result.data, result.heap_size, std::numeric_limits<std::uint64_t>::max());',
                 'write_u64(result.data, result.heap_size, 0x10000000ULL);')
    resource = Path(subprocess.check_output(['clang', '--print-resource-dir'], text=True).strip())
    # Keep JSystem's global allocation operators intact. Only the renderer's
    # references use the native heap; upstream SDK archives remain untouched.
    renderer = out / 'vendor/renderer'
    renderer.mkdir()
    allocation_symbols = {
        '_Znwm': 'ac_ps5_renderer_new', '_Znam': 'ac_ps5_renderer_new',
        '_ZnwmRKSt9nothrow_t': 'ac_ps5_renderer_new_nothrow',
        '_ZdlPv': 'ac_ps5_renderer_delete', '_ZdaPv': 'ac_ps5_renderer_delete',
        '_ZdlPvm': 'ac_ps5_renderer_delete_sized',
    }
    import re
    renderer_inputs = re.findall(r'\b(lib[\w.]+\.a)\b',
        (prefix / 'lib/libPS5OpenGLCore33.a').read_text())
    for name in renderer_inputs:
        command = ['llvm-objcopy']
        command += [f'--redefine-sym={old}={new}' for old, new in allocation_symbols.items()]
        subprocess.run(command + [str(prefix / 'lib' / name), str(renderer / name)], check=True)
        symbols = subprocess.check_output(['llvm-nm', '--undefined-only', str(renderer / name)], text=True)
        if any(line.split()[-1:] == [symbol] for line in symbols.splitlines()
               for symbol in allocation_symbols):
            raise RuntimeError(f'Renderer still references game allocator: {name}')
    libraries = [archive, ROOT / 'build/ps5/libglad.a', sdl / 'lib/libSDL2.a']
    libraries += [renderer / name for name in renderer_inputs]
    libraries += [sdk / 'target/lib' / name for name in
                  ('libunwind.a', 'libc++abi.a', 'libc++.a')]
    libraries += [resource / 'lib/linux/libclang_rt.builtins-x86_64.a']
    for path in libraries:
        if not path.is_file():
            raise RuntimeError(f'Missing native link input: {path}')
    group = f'SEARCH_DIR("{prefix / "lib"}")\nSEARCH_DIR("{sdk / "target/lib"}")\n'
    group += 'EXTERN(ps5_agc_gate2_run)\nGROUP (\n'
    group += ''.join(f'  "{p}"\n' for p in libraries) + ')\n'
    (out / 'vendor/libanimalcrossing.a').write_text(group)
    env = os.environ.copy()
    for name in ('APP_DEFINITIONS', 'APP_INCLUDE_PATHS', 'APP_RUNTIME_MODULES',
                 'PACBREW_PACKAGES', 'PACBREW_INCLUDE_PATHS', 'PACBREW_STATIC_ARCHIVES'):
        env[name] = ''
    env['APP_STATIC_ARCHIVES'] = 'vendor/libanimalcrossing.a'
    env['PS5_PAYLOAD_SDK'] = str(sdk)
    subprocess.run(['bash', str(script), 'Folder'], cwd=out, env=env, check=True)
    dynamic = subprocess.check_output(['llvm-readelf', '-d', str(out / 'build/llvm-pie.elf')], text=True)
    if 'PosixForWebKit' in dynamic:
        raise RuntimeError('Native executable imports unavailable WebKit POSIX module')
    title_id = json.loads((ROOT / 'ps5/sce_sys/param.json').read_text())['titleId']
    target = ROOT / 'dist' / title_id
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(out / 'dist' / title_id, target)
    shutil.copytree(ROOT / 'ps5/licenses', target / 'licenses')
    shutil.copy2(ROOT / 'LICENSE', target / 'LICENSE')
    receipt = {'title_id': title_id, 'platform': 'PS5', 'renderer': 'OpenGL 3.3',
               'target_fps': 60, 'profile': args.profile,
               'width': profile['width'], 'height': profile['height'], 'console_tested': False,
               'eboot_sha256': hashlib.sha256((target / 'eboot.bin').read_bytes()).hexdigest()}
    (target / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(target)


if __name__ == '__main__':
    main()
