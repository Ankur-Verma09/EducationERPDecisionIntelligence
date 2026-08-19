# ruff: noqa: E501, I001

from pathlib import Path


TRACE = {
    "C4-T01": "tests/integration/test_connector_postgresql.py::test_connector_runtime_rls_hides_other_tenant_and_mock_constraint_fails_closed",
    "C4-T02": "tests/api/test_generated_mock_connector_api.py::test_generated_connector_sync_quarantine_reconciliation_and_safe_events",
    "C4-T03": "tests/unit/test_generated_mock_connector.py::test_only_generated_mock_adapter_is_enabled",
    "C4-T04": "tests/api/test_generated_mock_connector_api.py::test_connector_contract_security_idempotency_etag_and_tenant_hiding",
    "C4-T05": "tests/api/test_generated_mock_connector_api.py::test_connector_contract_security_idempotency_etag_and_tenant_hiding",
    "C4-T06": "tests/api/test_generated_mock_connector_api.py::test_generated_connector_sync_quarantine_reconciliation_and_safe_events",
    "C4-T07": "tests/e2e/test_generated_connector_resume.py::test_durable_batches_replay_and_expiry_cleanup",
    "C4-T08": "tests/e2e/test_generated_connector_resume.py::test_durable_batches_replay_and_expiry_cleanup",
    "C4-T09": "tests/e2e/test_generated_connector_resume.py::test_durable_batches_replay_and_expiry_cleanup",
    "C4-T10": "tests/api/test_generated_mock_connector_api.py::test_generated_connector_sync_quarantine_reconciliation_and_safe_events",
    "C4-T11": "tests/api/test_generated_mock_connector_api.py::test_late_connector_cannot_overwrite_current_projection",
    "C4-T12": "tests/unit/test_phase3_reconciliation.py::test_observation_service_persists_replay_precedence_and_conflict",
    "C4-T13": "tests/unit/test_generated_mock_connector.py::test_generated_adapter_is_deterministic_bounded_and_timezone_aware",
    "C4-T14": "tests/api/test_generated_mock_connector_api.py::test_generated_connector_sync_quarantine_reconciliation_and_safe_events",
    "C4-T15": "tests/api/test_generated_mock_connector_api.py::test_worker_creates_and_replays_immutable_dead_letter",
    "C4-T16": "tests/api/test_generated_mock_connector_api.py::test_connector_update_job_history_and_reconciliation_reads",
    "C4-T17": "tests/api/test_generated_mock_connector_api.py::test_generated_connector_sync_quarantine_reconciliation_and_safe_events",
    "C4-T18": "tests/e2e/test_generated_connector_resume.py::test_durable_batches_replay_and_expiry_cleanup",
    "C4-T19": "tests/integration/test_connector_postgresql.py::test_connector_runtime_rls_hides_other_tenant_and_mock_constraint_fails_closed",
    "C4-T20": "tests/unit/test_phase3_migration_immutability.py::test_revision_0007_is_additive_self_contained_and_mock_only",
    "C4-T21": "tests/api/test_phase2_contract_completion.py::test_scoped_delegation_cannot_escape_department_or_tenant",
    "C4-T22": "tests/api/test_generated_mock_connector_api.py::test_connector_lists_use_bound_cursor_and_cross_route_reuse_fails",
    "C4-T23": "tests/api/test_generated_mock_connector_api.py::test_connector_contract_security_idempotency_etag_and_tenant_hiding",
    "C4-T24": "tests/api/test_generated_mock_connector_api.py::test_worker_creates_and_replays_immutable_dead_letter",
}


def test_every_connector_threat_has_an_executable_test_node() -> None:
    assert set(TRACE) == {f"C4-T{number:02d}" for number in range(1, 25)}
    root = Path(__file__).parents[2]
    for node in TRACE.values():
        file_name, test_name = node.split("::", maxsplit=1)
        contents = (root / file_name).read_text(encoding="utf-8")
        assert f"def {test_name}" in contents or f"def {test_name}[" in contents
