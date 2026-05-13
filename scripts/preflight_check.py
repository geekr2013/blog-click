#!/usr/bin/env python3
"""Preflight checks for Naver auto-publish pipeline."""
from __future__ import annotations
import os
import sys

REQUIRED = ["NAVER_BLOG_ID", "NAVER_ID", "NAVER_PASSWORD"]


def mask(v: str) -> str:
    if len(v) <= 4:
        return "*" * len(v)
    return v[:2] + "*" * (len(v)-4) + v[-2:]


def main() -> int:
    missing = []
    print("[Preflight] Required environment variables")
    for key in REQUIRED:
        val = os.getenv(key, "")
        if not val:
            missing.append(key)
            print(f"- {key}: MISSING")
        else:
            print(f"- {key}: OK ({mask(val)})")

    if missing:
        print("\nMissing required values. Add them in:")
        print("GitHub > Repository > Settings > Secrets and variables > Actions > New repository secret")
        print("Missing keys:", ", ".join(missing))
        return 1

    print("\nAll required values are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
