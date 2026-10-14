#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
version=
tested=()
while (($#)); do
  case "$1" in
    --version) version=${2:?Missing version}; shift 2 ;;
    --console-tested) tested=(--console-tested); shift ;;
    *) echo "Usage: tools/release.sh --version v1.0.0 [--console-tested]" >&2; exit 2 ;;
  esac
done
[[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9.]+)?$ ]] || { echo "Invalid or missing version" >&2; exit 2; }
[[ -z "$(git status --porcelain)" ]] || { echo "Commit source before packaging" >&2; exit 2; }
python3 ps5/tools/package-release.py --version "$version" "${tested[@]}"
python3 ps5/tools/package-source.py --output "dist/releases/$version/animal-crossing-ps5-$version-source.tar.gz"
python3 ps5/tools/prepare-catalog.py --version "$version"
python3 - "$version" <<'CHECKSUMS'
import hashlib, sys
from pathlib import Path
root = Path('dist/releases') / sys.argv[1]
rows = []
for path in sorted(list(root.glob('*.zip')) + list(root.glob('*.tar.gz'))):
    row = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() + '  ' + path.name + '\n'
    path.with_suffix(path.suffix + '.sha256').write_text(row)
    rows.append(row)
(root / 'SHA256SUMS').write_text(''.join(rows))
CHECKSUMS
