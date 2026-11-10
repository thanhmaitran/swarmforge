"""Refresh the generated tables inside docs/experiments/*.md.

Pages contain ``<!-- BEGIN table:NAME -->`` ... ``<!-- END table:NAME -->`` blocks; this script replaces their content with
``reports/tables/NAME.md`` so documentation never holds hand-copied numbers.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "reports" / "tables"
PATTERN = re.compile(r"(<!-- BEGIN table:(\w+) -->)(.*?)(<!-- END table:\2 -->)", re.S)


def refresh(md: Path) -> bool:
    text = md.read_text()

    def sub(m: re.Match[str]) -> str:
        src = TABLES / f"{m.group(2)}.md"
        body = src.read_text().strip() if src.exists() else "_not generated yet_"
        return f"{m.group(1)}\n\n{body}\n\n{m.group(4)}"

    new = PATTERN.sub(sub, text)
    if new != text:
        md.write_text(new)
    return new != text


if __name__ == "__main__":
    for page in sorted((ROOT / "docs" / "experiments").glob("*.md")):
        print(page.name, "updated" if refresh(page) else "unchanged")
