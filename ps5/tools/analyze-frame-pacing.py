#!/usr/bin/env python3
"""Evaluate recorded native frame windows; never infer performance from a build."""
import argparse
import json
from pathlib import Path
import re

PATTERN = re.compile(
    r'\[AC-FRAMES\] samples=(\d+) fps=([\d.]+) p95_ms=([\d.]+) '
    r'p99_ms=([\d.]+) max_ms=([\d.]+) over18ms=(\d+)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--minimum-windows', type=int, default=6)
    args = parser.parse_args()
    windows = []
    for match in PATTERN.finditer(args.log.read_text(errors='replace')):
        samples, fps, p95, p99, peak, late = match.groups()
        windows.append({'samples': int(samples), 'fps': float(fps), 'p95_ms': float(p95),
                        'p99_ms': float(p99), 'max_ms': float(peak), 'over18ms': int(late)})
    # Budgets accommodate the console's 59.94 Hz mode. Loading transitions should
    # be measured separately; passing one scene never establishes whole-game FPS.
    failures = []
    if len(windows) < max(args.minimum_windows, 1):
        failures.append('Insufficient recorded windows for a one-minute scene sample')
    for index, window in enumerate(windows):
        if window['samples'] != 600 or window['fps'] < 59.4 or window['p99_ms'] > 18.0 or window['over18ms'] > 6:
            failures.append(f'Window {index + 1} misses the scene frame-pacing budget')
    print(json.dumps({'scene_budget_passed': not failures, 'windows': windows,
                      'failures': failures, 'scope': 'Recorded scene only; confirm gameplay and multiple scenes separately'}, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
