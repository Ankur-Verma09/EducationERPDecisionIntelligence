"""Deterministic generated mock ERP adapter with no I/O or credentials."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from education_erp.connectors.contracts import AdapterBatch, AdapterRecord, ConnectorAdapter
from education_erp.errors import ApiError

SCENARIOS = frozenset({"valid", "mixed", "duplicates", "late"})


def _records(scenario: str) -> tuple[AdapterRecord, ...]:
    base = datetime(2030, 1, 15, 9, tzinfo=UTC)
    documents = (
        (
            "academic-period",
            "PERIOD-1",
            {
                "code": "GEN-2030",
                "name": "Generated 2030",
                "period_type": "year",
                "starts_on": "2030-01-01",
                "ends_on": "2030-12-31",
            },
        ),
        ("programme", "PROGRAMME-1", {"code": "GEN-PROG"}),
        (
            "programme-version",
            "PROGRAMME-VERSION-1",
            {
                "programme_code": "GEN-PROG",
                "version_code": "2030",
                "name": "Generated Programme",
                "effective_from": "2030-01-01",
            },
        ),
        ("course", "COURSE-1", {"code": "GEN-COURSE"}),
        (
            "course-version",
            "COURSE-VERSION-1",
            {
                "course_code": "GEN-COURSE",
                "version_code": "2030",
                "title": "Generated Course",
                "credit_value": 3,
                "effective_from": "2030-01-01",
            },
        ),
        (
            "offering",
            "OFFERING-1",
            {
                "code": "GEN-OFFERING",
                "academic_period_code": "GEN-2030",
                "course_code": "GEN-COURSE",
                "course_version_code": "2030",
            },
        ),
        ("learner", "LEARNER-1", {"institution_reference": "GEN-0001"}),
        (
            "programme-enrolment",
            "PROGRAMME-ENROLMENT-1",
            {
                "learner_reference": "GEN-0001",
                "programme_code": "GEN-PROG",
                "programme_version_code": "2030",
                "effective_from": "2030-01-15",
                "status": "active",
            },
        ),
        (
            "offering-enrolment",
            "OFFERING-ENROLMENT-1",
            {
                "learner_reference": "GEN-0001",
                "offering_code": "GEN-OFFERING",
                "effective_from": "2030-01-15",
                "status": "active",
            },
        ),
    )
    valid = [
        AdapterRecord(
            entity_type=cast(Any, entity_type),
            source_record_key=f"GENERATED-{key}",
            source_record_version="1",
            observed_at=base + timedelta(minutes=index),
            effective_at=base,
            document=cast(dict[str, Any], document),
        )
        for index, (entity_type, key, document) in enumerate(documents, 1)
    ]
    if scenario == "valid":
        return tuple(valid)
    if scenario == "mixed":
        return (
            *valid,
            AdapterRecord(
                entity_type="learner",
                source_record_key="GENERATED-BAD",
                source_record_version="1",
                observed_at=base,
                effective_at=base,
                document={"institution_reference": "", "prohibited_note": "generated-invalid"},
            ),
        )
    if scenario == "duplicates":
        return (*valid, valid[0].model_copy(deep=True))
    if scenario == "late":
        return (
            *valid,
            valid[0].model_copy(
                update={
                    "source_record_version": "2",
                    "effective_at": base - timedelta(days=1),
                    "document": {
                        **valid[0].document,
                        "name": "Generated stale academic period",
                    },
                }
            ),
        )
    raise ApiError(422, "invalid_connector_config", "The generated fixture scenario is invalid")


class GeneratedMockAdapter:
    def __init__(self, scenario: str) -> None:
        if scenario not in SCENARIOS:
            raise ApiError(
                422, "invalid_connector_config", "The generated fixture scenario is invalid"
            )
        self.scenario = scenario

    def read_batch(self, checkpoint: str, limit: int) -> AdapterBatch:
        try:
            offset = int(checkpoint)
        except ValueError as exc:
            raise ApiError(409, "checkpoint_conflict", "The checkpoint is invalid") from exc
        bounded = max(1, min(limit, 100))
        records = _records(self.scenario)
        selected = records[offset : offset + bounded]
        next_offset = offset + len(selected)
        return AdapterBatch(
            records=selected,
            next_checkpoint=str(next_offset),
            source_exhausted=next_offset >= len(records),
            expected_total=len(records),
            expected_rejections=1 if self.scenario == "mixed" else 0,
            expected_duplicates=1 if self.scenario == "duplicates" else 0,
        )


def adapter_for(kind: str, scenario: str) -> ConnectorAdapter:
    if kind == "generated_mock_v1":
        return GeneratedMockAdapter(scenario)
    if kind == "synthetic_reference_erp_v1":
        from education_erp.connectors.synthetic_reference import SyntheticReferenceAdapter

        return SyntheticReferenceAdapter(scenario)
    raise ApiError(422, "connector_kind_not_enabled", "The connector kind is not enabled")
