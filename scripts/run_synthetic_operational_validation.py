"""Run a generated production-like connector validation profile."""

from __future__ import annotations

import argparse
import json

from education_erp.connectors.operational_validation import PROFILES, run_profile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=tuple(PROFILES), default="baseline", nargs="?")
    args = parser.parse_args()
    report = run_profile(args.profile)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
