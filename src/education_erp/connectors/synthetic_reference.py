"""Checksum-bound generated demo adapter with no network, credential, or caller path."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from education_erp.connectors.contracts import AdapterBatch, AdapterRecord
from education_erp.errors import ApiError

PACKAGE_ID = "synthetic-reference-erp-v1"
PACKAGE_VERSION = "1.0.0"
MANIFEST_SHA256 = "AE2E58E6549F6E378995FBE3A69DBACF075110C52940953AB31EBAFB98D239BC"
KIND = "synthetic_reference_erp_v1"
SCENARIOS = frozenset(
    {
        "valid",
        "schema-drift-extra-field",
        "prohibited-child-attribute",
        "duplicate-version",
        "ambiguous-identity",
        "late-correction",
        "transport-timeout",
        "transport-throttled",
        "credential-rejected",
        "oversized-record",
    }
)
MAX_RECORD_BYTES = 65_536
MAX_BATCH_BYTES = 5_242_880
PAGE_SIZE = 100


def package_root() -> Path:
    """Resolve only build-owned locations; configuration cannot redirect this path."""
    candidates = (
        Path(__file__).resolve().parents[3] / "docs/pilot/mock/synthetic_reference_erp_v1",
        Path("/app/demo-package"),
    )
    for candidate in candidates:
        if (candidate / "manifest.json").is_file():
            return candidate
    raise ApiError(503, "package_unavailable", "The approved demo package is unavailable")


def _json(root: Path, relative: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((root / relative).read_text(encoding="utf-8")))


def verify_package() -> dict[str, Any]:
    root = package_root()
    if hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest().upper() != MANIFEST_SHA256:
        raise ApiError(409, "package_checksum_mismatch", "Demo package verification failed")
    manifest = _json(root, "manifest.json")
    if (
        manifest.get("package_id") != PACKAGE_ID
        or manifest.get("package_version") != PACKAGE_VERSION
        or manifest.get("approved_for_demo") is not True
        or manifest.get("authoritative_for_real_connector") is not False
        or manifest.get("approval_scope") != "demo-only-non-production"
    ):
        raise ApiError(409, "package_checksum_mismatch", "Demo package verification failed")
    approvals = cast(dict[str, str], manifest.get("approvals", {}))
    if approvals.get("demo_sponsor") != "USER-APPROVED-2026-08-05" or any(
        value != "NOT-APPROVED" for key, value in approvals.items() if key.startswith("production_")
    ):
        raise ApiError(409, "package_checksum_mismatch", "Demo package verification failed")
    for relative, expected in cast(dict[str, str], manifest["sha256"]).items():
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest().upper()
        if actual != expected:
            raise ApiError(409, "package_checksum_mismatch", "Demo package verification failed")
    schema = _json(root, "schemas/source_bundle.schema.json")
    records = _json(root, "data/valid_records.json")
    dispositions = _json(root, "policies/field_dispositions.json")
    transport = _json(root, "policies/transport_policy.json")
    identity = _json(root, "policies/identity_policy.json")
    thresholds = _json(root, "policies/thresholds.json")
    if (
        transport.get("network_egress") != "disabled"
        or transport.get("credential_reference") is not None
        or identity.get("automatic_merge") is not False
        or thresholds.get("promotion_on_breach") != "blocked"
    ):
        raise ApiError(409, "package_checksum_mismatch", "Demo package verification failed")
    refs = {
        "academic_periods": "academic_period",
        "programmes": "programme",
        "courses": "course",
        "offerings": "offering",
        "learners": "learner",
        "enrolments": "enrolment",
    }
    for source_object, definition in refs.items():
        required = set(schema["$defs"][definition]["required"])
        if set(dispositions["objects"][source_object]) != required:
            raise ApiError(409, "mapping_invalid", "Demo mapping verification failed")
        for record in cast(list[dict[str, Any]], records[source_object]):
            if set(record) != required:
                raise ApiError(409, "source_schema_unsupported", "Source schema is unsupported")
    return manifest


def schema_checksum() -> str:
    manifest = verify_package()
    return cast(str, manifest["sha256"]["schemas/source_bundle.schema.json"])


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _record(
    entity_type: str,
    source_key: str,
    observed_at: str,
    effective_at: str,
    document: dict[str, Any],
) -> AdapterRecord:
    return AdapterRecord(
        entity_type=cast(Any, entity_type),
        source_record_key=source_key,
        source_record_version=observed_at,
        observed_at=_at(observed_at),
        effective_at=_at(effective_at),
        document=document,
    )


def _canonical_records() -> tuple[AdapterRecord, ...]:
    root = package_root()
    source = _json(root, "data/valid_records.json")
    period = source["academic_periods"][0]
    programme = source["programmes"][0]
    course = source["courses"][0]
    offering = source["offerings"][0]
    records: list[AdapterRecord] = [
        _record(
            "academic-period",
            period["period_id"],
            period["updated_at"],
            f"{period['starts_on']}T00:00:00Z",
            {key: period[key] for key in ("code", "name", "period_type", "starts_on", "ends_on")},
        ),
        _record(
            "programme",
            programme["programme_id"],
            programme["updated_at"],
            f"{programme['effective_from']}T00:00:00Z",
            {"code": programme["code"]},
        ),
        _record(
            "programme-version",
            programme["programme_id"],
            programme["updated_at"],
            f"{programme['effective_from']}T00:00:00Z",
            {key: programme[key] for key in ("version_code", "name", "effective_from")}
            | {"programme_code": programme["code"]},
        ),
        _record(
            "course",
            course["course_id"],
            course["updated_at"],
            f"{course['effective_from']}T00:00:00Z",
            {"code": course["code"]},
        ),
        _record(
            "course-version",
            course["course_id"],
            course["updated_at"],
            f"{course['effective_from']}T00:00:00Z",
            {
                key: course[key]
                for key in ("version_code", "title", "credit_value", "effective_from")
            }
            | {"course_code": course["code"]},
        ),
        _record(
            "offering",
            offering["offering_id"],
            offering["updated_at"],
            offering["updated_at"],
            {
                "code": offering["code"],
                "academic_period_code": period["code"],
                "course_code": course["code"],
                "course_version_code": course["version_code"],
            },
        ),
    ]
    learners = {item["learner_id"]: item for item in source["learners"]}
    for learner in learners.values():
        records.append(
            _record(
                "learner",
                learner["learner_id"],
                learner["updated_at"],
                learner["updated_at"],
                {"institution_reference": learner["institution_reference"]},
            )
        )
    for enrolment in source["enrolments"]:
        learner = learners[enrolment["learner_id"]]
        effective = f"{enrolment['effective_from']}T00:00:00Z"
        records.extend(
            (
                _record(
                    "programme-enrolment",
                    f"{enrolment['enrolment_id']}:programme",
                    enrolment["updated_at"],
                    effective,
                    {
                        "learner_reference": learner["institution_reference"],
                        "programme_code": programme["code"],
                        "programme_version_code": programme["version_code"],
                        "effective_from": enrolment["effective_from"],
                        "status": enrolment["status"],
                    },
                ),
                _record(
                    "offering-enrolment",
                    f"{enrolment['enrolment_id']}:offering",
                    enrolment["updated_at"],
                    effective,
                    {
                        "learner_reference": learner["institution_reference"],
                        "offering_code": offering["code"],
                        "effective_from": enrolment["effective_from"],
                        "status": enrolment["status"],
                    },
                ),
            )
        )
    return tuple(records)


class SyntheticReferenceAdapter:
    """Read-only in-process adapter; intentionally has no write or network methods."""

    def __init__(self, scenario: str) -> None:
        if scenario not in SCENARIOS:
            raise ApiError(422, "invalid_connector_config", "The demo scenario is invalid")
        self.scenario = scenario
        verify_package()

    def read_batch(self, checkpoint: str, limit: int) -> AdapterBatch:
        if self.scenario == "schema-drift-extra-field":
            raise ApiError(409, "source_schema_unsupported", "Source schema is unsupported")
        if self.scenario in {"transport-timeout", "transport-throttled"}:
            raise ApiError(503, "transport_unavailable", "The demo transport is unavailable")
        if self.scenario == "credential-rejected":
            raise ApiError(422, "invalid_connector_config", "Credentials are forbidden")
        try:
            offset = int(checkpoint)
        except ValueError as exc:
            raise ApiError(409, "checkpoint_conflict", "The checkpoint is invalid") from exc
        records = list(_canonical_records())
        if self.scenario == "duplicate-version":
            records.append(records[0].model_copy(deep=True))
        elif self.scenario == "prohibited-child-attribute":
            records.append(
                records[6].model_copy(
                    update={
                        "source_record_key": "L-9998",
                        "document": {
                            "institution_reference": "SYN-9998",
                            "health_note": "generated-prohibited",
                        },
                    }
                )
            )
        elif self.scenario == "ambiguous-identity":
            records.append(records[6].model_copy(update={"source_record_key": "L-9999"}))
        elif self.scenario == "late-correction":
            records.append(
                records[0].model_copy(
                    update={
                        "source_record_version": "2029-12-01T00:00:00Z",
                        "effective_at": datetime(2030, 1, 1, tzinfo=UTC),
                        "document": {**records[0].document, "name": "Generated stale name"},
                    }
                )
            )
        elif self.scenario == "oversized-record":
            records.append(
                records[6].model_copy(
                    update={
                        "source_record_key": "L-9997",
                        "document": {"institution_reference": "SYN-9997", "extra": "x" * 65_537},
                    }
                )
            )
        bounded = max(1, min(limit, PAGE_SIZE))
        selected = records[offset : offset + bounded]
        for record in selected:
            if len(json.dumps(record.document).encode()) > MAX_RECORD_BYTES:
                # The execution service quarantines the generated oversized record without value.
                continue
        if sum(len(json.dumps(item.document).encode()) for item in selected) > MAX_BATCH_BYTES:
            raise ApiError(422, "record_too_large", "The generated batch exceeds its limit")
        next_offset = offset + len(selected)
        return AdapterBatch(
            records=tuple(selected),
            next_checkpoint=str(next_offset),
            source_exhausted=next_offset >= len(records),
            expected_total=len(records),
            expected_rejections=1
            if self.scenario in {"prohibited-child-attribute", "oversized-record"}
            else 0,
            expected_duplicates=1 if self.scenario == "duplicate-version" else 0,
        )
