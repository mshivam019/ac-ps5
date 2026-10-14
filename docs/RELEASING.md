# Releasing

From the prepared SDK workspace, build with `tools/build.sh --profile 2160p60`.
After testing that exact title folder on console, commit the source, then run:

```sh
tools/release.sh --version v1.0.0 --console-tested
```

This packages the existing `dist/PPSA99660` into profile-named Windows/Linux
ZIPs, a catalog ZIP, corresponding source and manifests. Installer ZIPs use
`output/PPSA99660`, `tools/`, INSTALL.txt, CONSOLE-SETUP.md, MODS.md and SETTINGS.md,
following the oot64-ps5 layout. Each archive has a SHA-256 sidecar.

The script preserves existing artifacts and does not publish or change GitHub
visibility. It requires a clean committed tree. Bump contentVersion before
building a new release. Never bundle disc images, HD packs or saves.
