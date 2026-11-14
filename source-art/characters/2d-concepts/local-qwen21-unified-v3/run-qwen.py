"""Reuse the existing native Qwen runner with this task's own record directory."""
from pathlib import Path
import importlib.util
import json
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('existing_native_qwen_runner',HERE.parent/'local-qwen21-consistency-v2/run-masked.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
runner.ROOT=HERE
for case in json.loads((HERE/'cases.json').read_text(encoding='utf-8')):
    if (HERE/'results'/case['name']/'result.json').exists():continue
    runner.run(case)
