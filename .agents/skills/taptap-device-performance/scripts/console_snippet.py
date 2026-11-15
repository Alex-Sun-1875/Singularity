#!/usr/bin/env python3
"""Generate a DevTools console expression; no device connection or execution."""
import argparse
import json
from pathlib import Path
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('operation', choices=['snapshot', 'start', 'take', 'cleanup'])
p.add_argument('--key', default='__taptapPerfManual')
p.add_argument('--seconds', type=float, default=20)
p.add_argument('--label', default='android-standing-baseline')
p.add_argument('--copy', action='store_true', help='Use Chrome DevTools copy() for exporting JSON')
p.add_argument('--out', type=Path, help='Write UTF-8 directly to a file instead of stdout')
a = p.parse_args()
if not 1 <= a.seconds <= 60:
    p.error('Use 1–60 seconds')
source = Path(__file__).with_name('collect.js').read_text(encoding='utf-8')
options = {key: value for key, value in vars(a).items() if key != 'out'}
expression = '(' + source + ')(' + json.dumps(options) + ')'
result = 'copy(' + expression + ')' if a.copy else expression
if a.out:
    a.out.write_text(result + '\n', encoding='utf-8')
else:
    sys.stdout.reconfigure(encoding='utf-8')
    print(result)
