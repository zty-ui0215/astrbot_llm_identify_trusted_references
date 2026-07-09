from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "trusted-reference-candidate/v1"
FORBIDDEN_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}", re.I),
    re.compile(r"authorization", re.I),
    re.compile(r"api[_-]?key", re.I),
    re.compile(r"raw completion", re.I),
    re.compile(r"raw prompt", re.I),
]
REQUIRED = {"schema_version", "sample_type", "verification_status", "privacy_notice", "task_ref", "endpoint", "model", "versions", "time", "scores", "probe_ids", "capability_scores", "fingerprint_vector"}


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: top-level value must be object"]
    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append(f"{path}: missing keys: {', '.join(missing)}")
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{path}: schema_version must be {SCHEMA_VERSION}")
    endpoint = data.get("endpoint") if isinstance(data.get("endpoint"), dict) else {}
    if not endpoint.get("provider") or not endpoint.get("official_host"):
        errors.append(f"{path}: endpoint.provider and endpoint.official_host are required")
    text = json.dumps(data, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path}: forbidden sensitive pattern matched: {pattern.pattern}")
    return errors


def iter_json_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths or ["data/candidates"]:
        path = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
        if path.is_file() and path.suffix == ".json":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
    return files


def main(argv: list[str]) -> int:
    errors: list[str] = []
    files = iter_json_files(argv)
    for path in files:
        errors.extend(validate_file(path))
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"validated {len(files)} candidate file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
