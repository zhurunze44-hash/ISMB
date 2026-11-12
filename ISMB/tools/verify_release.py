#!/usr/bin/env python3
"""Fail-closed SHA256 verification of the bounded public Paper3 code release.

Run from anywhere: python ISMB/tools/verify_release.py or cd ISMB && python tools/verify_release.py
This manifest intentionally excludes itself to avoid recursive hashing.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "CODE_AND_EXPECTED_SHA256.json"


def verify():
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("EMPTY_OR_INVALID_MANIFEST")
    seen = set()
    for entry in entries:
        rel = entry["path"]
        p = Path(rel)
        if not rel or p.is_absolute() or '..' in p.parts or rel in seen or rel == MANIFEST.name:
            raise RuntimeError(f"INVALID_MANIFEST_PATH: {rel!r}")
        seen.add(rel)
        f = ROOT / rel
        if not f.is_file():
            raise RuntimeError(f"MISSING_RELEASE_FILE: {rel}")
        data = f.read_bytes()
        value = hashlib.sha256(data).hexdigest()
        if len(data) != entry["bytes"] or value != entry["sha256"]:
            raise RuntimeError(f"RELEASE_INTEGRITY_MISMATCH: {rel} actual_size={len(data)} sha256={value}")
    print(f"PUBLIC_RELEASE_INTEGRITY_PASS {len(entries)}/{len(entries)} files (scope: ISMB/ only)")
    return len(entries)


if __name__ == '__main__':
    try:
        verify()
    except Exception as exc:
        print(f"PUBLIC_RELEASE_INTEGRITY_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
