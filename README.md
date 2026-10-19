# Animal Crossing for PS5

**Installed from ProsperoStore?** [Use the game-specific setup](INSTALL.md#already-installed-from-prosperostore): choose your game files and an output location; it prepares and checks a ready-to-copy folder automatically. Download **PS5-Install-Helper-v1.2.0.zip** from this game's release. Python 3.9+ is required; game conversion/module preparation requirements are listed in the guide.

**[Start here: installation, USB/offline copying, Wi-Fi FTP and game-file locations](INSTALL.md).**
M.2, Ethernet and PS5 Upload are optional. The guide also explains recovery after
store updates; older packaged instructions may describe the developer's M.2 setup.

Native PS5 port of the USA GameCube release, based on ACreTeam's decompilation,
FlyingMeta's PC platform layer and PalindromicBreadLoaf's 64-bit adaptations.
The game is compiled for PS5; no GameCube emulator runs underneath it.

[Download v1.0.0](https://github.com/mshivam019/ac-ps5/releases/tag/v1.0.0) · [Installation and controls](ps5/INSTALL.txt) · [Build from source](docs/BUILDING.md)

## Features

- Native homebrew title **Animal Crossing** (`PPSA99660`), launched from the PS5 home screen.
- Native 3840×2160 rendering, with an optional 1920×1080 build profile.
- OpenGL renderer with a 60 Hz presentation target.
- DualSense controls and PlayStation prompts for the keyboard and notice board.
- Normal game saves and persistent settings.
- Optional community HD textures loaded on demand.

## Guides

- [Build scripts and dependency requirements](docs/BUILDING.md)
- [Release packaging](docs/RELEASING.md)
- [HD textures and prompts](docs/MODS.md)
- [Settings and controls](docs/SETTINGS.md)
- [Installation and controls](ps5/INSTALL.txt)
- [Catalog submission preparation](ps5/catalog/README.md)
- [Original upstream documentation](README.upstream.md)

The native title ID is PPSA99660. Use the installation location selected by your
loader/store (internal storage, M.2 or supported USB). Game data lives in the title's `data`
directory (`/app0/data`); saves and settings use `/download0` and survive title
updates. Save with the gyroid outside your own house before closing the game.

For normal play, copy your own USA GAFE01 revision 0 ISO/GCM directly to
`PPSA99660/data/rom/game.iso`; no preparer or compiler is required. Optional community HD textures
are prepared separately and loaded on demand; the pack does not replace every
texture. No disc image, community HD pack, keys or personal saves are included.

`PPSA99660.zip` is the catalog app-folder package. Windows/Linux ZIP names refer
to their installer scripts; both install the same native PS5 application.

The combined PS5 distribution and new PS5 integration are GPL-3.0-or-later.
Original decompilation remains CC0 and the PC layer remains MIT. Their complete
original license notices are preserved in
[the upstream license](ps5/licenses/animal-crossing-upstream-LICENSE).
Other libraries retain their notices under `ps5/licenses/`; corresponding
source is distributed separately. Animal Crossing belongs to Nintendo; this
is an unofficial port, not a Nintendo release.
