#!/usr/bin/env python3
"""Cross-compile and package Animal Crossing as a native PS5 title."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('1080p60', '2160p60'), default='2160p60')
    args, cmake_args = parser.parse_known_args()
    height = args.profile.split('p')[0]
    subprocess.run(['bash', str(ROOT / 'ps5/tools/build.sh'),
                    '-DAC_PS5_HEIGHT:STRING=' + height, *cmake_args], check=True)
    graphics = [sys.executable, str(ROOT / 'ps5/tools/build-graphics.py'),
                '--profile', args.profile]
    if os.environ.get('PS5SDK_ROOT'):
        graphics += ['--sdk-root', os.environ['PS5SDK_ROOT']]
    subprocess.run(graphics, check=True)
    args = [sys.executable, str(ROOT / 'ps5/tools/link-title.py'), '--profile', args.profile]
    if os.environ.get('PS5SDK_ROOT'):
        args += ['--sdk-root', os.environ['PS5SDK_ROOT']]
    subprocess.run(args, check=True)
