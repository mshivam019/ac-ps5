# Native PS5 build

The game is cross-compiled to x86_64-sie-ps5 with the existing Clang 18 native
application SDK. OpenGL 3.3 and SDL2 are the same native integration used by the
earlier ports. `ps5/tools/build.py` builds a PS5 SELF and title folder, not a
Linux game executable.

```sh
python3 ps5/tools/build.py --profile 2160p60
# Optional performance fallback: --profile 1080p60
python3 ps5/tools/validate.py
```

Prepared dependencies currently live under `~/ps5sdk`: native-app-boilerplate,
the payload SDK in its `.deps/native`, ps5-opengl-030/ps5-opengl,
ac-gl-1080p60/sdk and ac-gl-2160p60/sdk (isolated 60 Hz runtime builds), native SDL2, and Clang 18. Dependency hashes
and the source baseline are recorded in `ps5/dependencies.json`. These initial
scripts use that prepared workspace; fresh-machine dependency bootstrap is
pending. The source package includes the prepared graphics/SDL/native-tooling
source trees. It does not include game data or the HD pack.

The native compilation archive is `build/ps5/libAnimalCrossing.a`. Native
linking/signing outputs `dist/PPSA99660/eboot.bin`, metadata and the clean-room
`sce_module/libc.prx`. The prepared linker rejects unknown SDK imports. The
WebKit POSIX module is excluded. JSystem supplies C++ allocation operators;
the native platform supplies a 2 GiB direct-memory heap and delayed TLS cleanup.
The matched runtime supplies SDL's refresh getter. The title ID PPSA99660 is
registered on the test console. Renderer allocation symbols are isolated from
JSystem's game heap in the local copies of the static graphics archives.

Reference checks are deliberately separate:

```sh
cmake -S pc -B build/portability -G Ninja -DPC_BUILD_GAME=OFF -DPC_BUILD_PORTABILITY_TESTS=ON
cmake --build build/portability
ctest --test-dir build/portability --output-on-failure
```

Native defaults target 3840x2160 at 60 Hz; `--profile 1080p60` builds the
1920x1080 fallback. VSync is on, MSAA is off, and HD textures load on demand.
The native log includes 600-frame timing windows after a 600-frame warm-up.
Both profiles present directly; the obsolete framebuffer-copy experiment is
not used. Current 4K windows vary around 30–60 FPS, so neither the profile name
nor the display refresh should be described as guaranteed gameplay FPS.

Use `python3 ps5/tools/analyze-frame-pacing.py --log CONSOLE_LOG` on each recorded
scene. It requires at least six 600-frame windows and checks average FPS, p99
and late frames against the initial 59.94 Hz scene budget. Check outdoor village,
indoors, menus and transitions separately; one scene cannot establish whole-game
stability.

Release scripts follow the other ports:

```sh
python3 ps5/tools/package-release.py --version v1.0.0
python3 ps5/tools/package-source.py --output dist/releases/v1.0.0/animal-crossing-ps5-v1.0.0-source.tar.gz
```

The catalog ZIP has `PPSA99660/` at its root. Both installer ZIPs contain the same native PS5 executable, a platform-specific
installer wrapper, manifests and notices. They do not contain the ISO, HD pack
or saves. ZIP contents and corresponding-source entries are fully hashed and
read back by the packaging scripts. 

### Prepared graphics profile

The native runtime uses the same patched SDK 0.3.0 source as Ocarina/Majora,
rebuilt into its own output directory. It does not replace their SDK or SDL:

```sh
make -j6 -C "$HOME/ps5sdk/ps5-opengl-030/ps5-opengl/tests/ps5" -f native-app.mk runtime \
  PS5_PAYLOAD_SDK="$HOME/ps5sdk/native-app-boilerplate/.deps/native/ps5-payload-sdk" \
  PS5_OPENGL_BUILD="$HOME/ps5sdk/ps5-opengl-030/ps5-opengl/build/ac-runtime-1080p60" \
  PS5_SCANOUT_FPS=60 PS5_SCANOUT_HEIGHT=1080 \
  PS5_GPU_PRESENT_BATCH=1 PS5_DEFERRED_DRAW_BATCH=1
```

`ac-gl-1080p60/sdk` is a separate copy of the working patched SDK's supporting
archives, with `libps5_opengl_core33.a`, `libSceAgc.so` and `libSceAgcDriver.so`
from that runtime output. The 1080p `build/sdl2-native/sdk` SDL integration is
paired with it. Exact linked archive hashes are checked by `link-title.py`.
Changing the runtime requires reviewing and updating those pins, not overwriting
an existing port's dependencies.

For the 2160p profile, set PS5_SCANOUT_HEIGHT=2160 and use the separate
ac-runtime-2160p60 output. It pairs ac-gl-2160p60/sdk with the existing
soh-sdl-2160p120/sdk integration; the runtime refresh getter reports the linked
60 Hz runtime. Link-time validation rejects mixed game/renderer heights.

Artwork can be regenerated with `ps5/tools/prepare-art.py` using rsvg-convert,
Pillow and ispc_texcomp. The source SVGs and provenance are under ps5/art.

Catalog metadata is prepared with `ps5/tools/prepare-catalog.py`; see
ps5/catalog/README.md. Do not change repository visibility as part of packaging.

Controller prompt assets are reproducible with:

```sh
python3 ps5/tools/generate-controller-ui.py
python3 ps5/tests/test_controller_ui.py
```

The generator uses rsvg-convert and original vector shapes. The optional
`--verify-iso` check validates the source-texture hash manifest against an owned
GAFE01 rev0 dump without copying original pixels into the replacement pack.
