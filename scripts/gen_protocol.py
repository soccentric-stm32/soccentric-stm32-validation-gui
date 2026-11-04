#!/usr/bin/env python3
"""Regenerate the Python HWLINK bindings from protocol/hwlink.fbs (GCON-004)."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "protocol" / "hwlink.fbs"
OUT = ROOT / "src" / "hwval_studio" / "protocol" / "generated"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flatc", default=shutil.which("flatc") or "flatc")
    args = parser.parse_args()
    if not SCHEMA.is_file():
        print(f"missing schema: {SCHEMA}", file=sys.stderr)
        return 1
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "__init__.py").write_text("")
    subprocess.run([args.flatc, "--python", "-o", str(OUT), str(SCHEMA)], check=True)
    package = OUT / "hwlink"
    (package / "__init__.py").write_text("")
    # flatc emits absolute imports for nested tables (`from hwlink.X import X`);
    # make them relative so the package can be bundled normally.
    for path in package.glob("*.py"):
        text = path.read_text()
        new = text.replace("from hwlink.", "from .")
        if new != text:
            path.write_text(new)
    print(f"generated {package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
