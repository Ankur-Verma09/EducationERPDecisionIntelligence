from datetime import UTC

import pytest

from education_erp.connectors.generated_mock import GeneratedMockAdapter, adapter_for
from education_erp.errors import ApiError


def test_generated_adapter_is_deterministic_bounded_and_timezone_aware() -> None:
    first = GeneratedMockAdapter("mixed").read_batch("0", 2)
    second = GeneratedMockAdapter("mixed").read_batch("2", 1000)
    assert len(first.records) == 2
    assert first.next_checkpoint == "2"
    assert not first.source_exhausted
    assert len(second.records) == 8
    assert second.source_exhausted
    assert second.expected_total == 10
    assert second.expected_rejections == 1
    assert all(record.observed_at.tzinfo is UTC for record in first.records)


@pytest.mark.parametrize("kind", ["api", "sftp", "database", "file", "https://example.test"])
def test_only_generated_mock_adapter_is_enabled(kind: str) -> None:
    with pytest.raises(ApiError) as exc:
        adapter_for(kind, "valid")
    assert exc.value.code == "connector_kind_not_enabled"


def test_generated_adapter_rejects_checkpoint_and_scenario_injection() -> None:
    with pytest.raises(ApiError):
        GeneratedMockAdapter("../../customer.csv")
    with pytest.raises(ApiError) as exc:
        GeneratedMockAdapter("valid").read_batch("SELECT *", 10)
    assert exc.value.code == "checkpoint_conflict"


@pytest.mark.parametrize(
    ("scenario", "expected_total", "expected_duplicates"),
    [("valid", 9, 0), ("duplicates", 10, 1), ("late", 10, 0)],
)
def test_all_generated_scenarios_have_explicit_manifests(
    scenario: str, expected_total: int, expected_duplicates: int
) -> None:
    batch = GeneratedMockAdapter(scenario).read_batch("0", 100)
    assert batch.source_exhausted
    assert batch.expected_total == expected_total
    assert batch.expected_duplicates == expected_duplicates


def test_late_fixture_is_explicitly_older_than_current_observation() -> None:
    records = GeneratedMockAdapter("late").read_batch("0", 100).records
    current, late = records[0], records[-1]
    assert late.source_record_key == current.source_record_key
    assert late.source_record_version == "2"
    assert late.effective_at < current.effective_at
    assert late.observed_at == current.observed_at
