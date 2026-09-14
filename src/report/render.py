"""Render the Markdown report to a self-contained HTML file (figures embedded, MathML equations, table of contents).

Requires pandoc (tested with pandoc 3.5). Usage: python -m src.report.render
Output: docs/report_20260914_ev_model.html
"""
from __future__ import annotations

import shutil
import subprocess

from src.utils.paths import ROOT

REPORT = ROOT / "docs" / "report_20260914_ev_model.md"
CSS = ROOT / "docs" / "report.css"


def main() -> None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc not found on PATH")
    out = REPORT.with_suffix(".html")
    cmd = [pandoc, str(REPORT), "-f", "markdown+tex_math_single_backslash", "-o", str(out), "--standalone", "--embed-resources", "--mathml", "--toc", "--toc-depth=2",
           f"--resource-path={REPORT.parent}", f"--css={CSS}", "--metadata", "lang=en"]
    subprocess.run(cmd, check=True, cwd=REPORT.parent)
    print("wrote", out, round(out.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
