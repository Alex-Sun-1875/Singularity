"""Validate active links and local Lua entry points, including planned retirement."""
from pathlib import Path
import json
import re
import sys

root = Path(__file__).resolve().parents[1]
plan = json.loads((root / "tools/latest-version-cleanup.json").read_text(encoding="utf-8"))

def retired(path):
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return False
    return relative in plan["files"] or any(relative == d or relative.startswith(d + "/") for d in plan["directories"])

problems = []
pages = [root / "README.md", *(root / "docs").rglob("*.md"), *(root / "source-art").rglob("*.md"), *(root / "assets").rglob("README.md")]
count = 0
for page in pages:
    if retired(page):
        continue
    count += 1
    text = page.read_text(encoding="utf-8")
    for _, url in re.findall(r"\[([^\]]*)\]\(([^)]+)\)", text):
        target = url.split("#")[0].strip("<>")
        if not target or "://" in target or target.startswith(("mailto:", "data:")):
            continue
        path = (page.parent / target).resolve()
        if not path.exists() or retired(path):
            problems.append(f"{page.relative_to(root)}: unavailable link {target}")

for relative in ["src/scripts/main.lua", "src/Run-Local.ps1", "src/scripts/Game/Chapter.lua", "src/scripts/Game/Save.lua"]:
    if not (root / relative).is_file() or retired(root / relative):
        problems.append(f"Missing current entry: {relative}")

print(f"Checked {count} current pages and Lua project entries; physical deletion is not performed.")
for problem in problems:
    print(problem)
sys.exit(bool(problems))
