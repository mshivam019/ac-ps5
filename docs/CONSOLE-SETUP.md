CURRENT INSTALLATION GUIDE: https://github.com/mshivam019/ac-ps5/blob/main/INSTALL.md
Use that guide for internal/USB storage, offline copying or Wi-Fi FTP.
M.2, Ethernet and PS5 Upload are optional. Paths in older instructions below
describe the developer setup, not required hardware or transfer software.

# Console setup

Download the Windows or Linux release for your computer; both contain the same
native PS5 title in `output/PPSA99660`. No compilation is required to install it.
Use Python 3.11+ and follow INSTALL.txt to prepare your own GAFE01 revision 0
ISO/GCM, optionally with a compatible HD pack. Game data is not included.

Tested on PS5 firmware 9.00 with kstuff, ShadowMountPlus, FTP and PS5 Upload.
Use your existing jailbreak and native-folder title workflow. Set the console
address in the installer command. Default destination is M.2:
`/mnt/ext1/etaHEN/games/PPSA99660`.

Save and Quit, then close Animal Crossing before updating. The installer backs
up replaced title files and preserves game data and saves. Register the folder
with PS5 Upload after installation. Re-register after artwork updates so the
registered `sce_sys` and home-screen metadata receive the new images.

The catalog ZIP instead contains `PPSA99660/` at its root. For a fresh install,
use the Windows/Linux package helpers to prepare your game data separately.
