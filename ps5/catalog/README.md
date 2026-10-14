# Catalog submission preparation

The catalog requires a public GitHub repository, a published release asset and
matching metadata. Private release URLs cannot pass its public download check.
The dedicated catalog ZIP contains PPSA99660/ at its root; installer ZIPs use a
different layout and must not be used for the catalog record.

After the final release is built, run:

```sh
python3 ps5/tools/prepare-catalog.py --version v1.0.0
python3 -m catalog check --apps-dir /path/to/ac-ps5/dist/catalog/apps
```

The second command runs in a checkout of blackbearreloaded/ps5-homebrew-catalog.
Copy only dist/catalog/apps/PPSA99660.json into your later catalog PR. Do not
submit until the repository/release are public and the online verify command
passes. The preparer pins the icon to the release tag and hashes the actual ZIP.
It never changes repository visibility, publishes a release, or opens a PR.

