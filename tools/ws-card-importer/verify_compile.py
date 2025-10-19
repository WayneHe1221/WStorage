#!/usr/bin/env python3
"""Compile the importer toolchain to ensure Python environments are configured."""

from __future__ import annotations

import compileall
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    # quiet=1 prints errors only; return value indicates success
    succeeded = compileall.compile_dir(str(root), quiet=1)
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())

