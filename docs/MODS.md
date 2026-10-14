# HD textures and controller prompts

HD textures are optional and separate from the release. Prepare a compatible
Animal Crossing GameCube DDS pack with your owned disc:

```sh
python3 tools/prepare-data.py --iso "Animal Crossing (USA).iso" --hd-zip ACHD.zip --output prepared-data
```

Upload that directory with the install helper's data option (see INSTALL.txt).
The game reads `data/texture_pack` inside the installed title and loads matching
textures on demand. Full-pack preloading is disabled to limit memory use. A
community pack may leave some original textures unchanged.

Original DualSense glyph replacements are bundled in `assets/controller-ui`.
They take priority over matching HD-pack textures and assume default bindings.
Text-only button names, the controller diagram, and some other prompt paths
remain unchanged. This is not a general-purpose mod loader.
