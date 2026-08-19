"""Validate structural completeness and checksums of an authority package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TEXT = (
    "package_id",
    "package_version",
    "vendor",
    "product",
    "product_version",
    "source_release",
    "classification",
    "transport",
)
OWNERS = ("product_owner", "source_owner", "privacy_owner", "security_owner")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / "manifest.json"
    if not path.is_file():
        return ["manifest.json is missing"]
    try:
        manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"manifest.json is invalid: {type(exc).__name__}"]
    for key in TEXT:
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip() or "REQUIRED" in value.upper():
            errors.append(f"{key} is missing or unresolved")
    if manifest.get("authoritative_for_real_connector") is not True:
        errors.append("authoritative_for_real_connector must be true")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        errors.append("files map is missing")
    else:
        for role, relative in files.items():
            if not isinstance(relative, str) or not (root / relative).exists():
                errors.append(f"files.{role} does not resolve")
    approvals = manifest.get("approvals")
    if not isinstance(approvals, dict):
        errors.append("approvals map is missing")
    else:
        for owner in OWNERS:
            approval = approvals.get(owner)
            if not isinstance(approval, dict):
                errors.append(f"approvals.{owner} is missing")
                continue
            for key in ("name", "approval_id", "date"):
                value = approval.get(key)
                if not isinstance(value, str) or not value.strip() or "REQUIRED" in value.upper():
                    errors.append(f"approvals.{owner}.{key} is unresolved")
    checksums = manifest.get("sha256")
    if not isinstance(checksums, dict) or not checksums:
        errors.append("sha256 map is missing")
    else:
        for relative, expected in checksums.items():
            file_path = root / relative
            if not file_path.is_file():
                errors.append(f"checksum target is missing: {relative}")
                continue
            actual = hashlib.sha256(file_path.read_bytes()).hexdigest().upper()
            if not isinstance(expected, str) or actual != expected.upper():
                errors.append(f"checksum mismatch: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    errors = validate(args.package.resolve())
    status = "blocked" if errors else "structurally-valid"
    print(json.dumps({"status": status, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
