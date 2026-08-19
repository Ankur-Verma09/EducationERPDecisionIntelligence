# ruff: noqa: E501, I001

from pathlib import Path


TRACE = {
    "C5-T01": "tests/integration/test_synthetic_reference_postgresql.py::test_demo_database_rejects_network_credentials_mutation_and_cross_tenant_access",
    "C5-T02": "tests/api/test_synthetic_reference_connector_api.py::test_demo_api_rejects_network_credentials_paths_tls_and_wrong_version",
    "C5-T03": "tests/unit/test_synthetic_reference_connector.py::test_valid_adapter_maps_all_entities_without_write_surface",
    "C5-T04": "tests/api/test_synthetic_reference_connector_api.py::test_demo_api_rejects_network_credentials_paths_tls_and_wrong_version",
    "C5-T05": "tests/api/test_synthetic_reference_connector_api.py::test_demo_api_rejects_network_credentials_paths_tls_and_wrong_version",
    "C5-T06": "tests/security/test_synthetic_reference_security.py::test_schema_drift_transport_failures_and_core_health_are_isolated",
    "C5-T07": "tests/unit/test_synthetic_reference_connector.py::test_every_approved_scenario_is_closed_and_deterministic",
    "C5-T08": "tests/api/test_synthetic_reference_connector_api.py::test_demo_quarantine_threshold_block_and_no_sensitive_persistence",
    "C5-T09": "tests/security/test_synthetic_reference_security.py::test_identity_ambiguity_does_not_auto_merge_or_expose_source_keys",
    "C5-T10": "tests/security/test_synthetic_reference_security.py::test_late_correction_cannot_overwrite_current_projection",
    "C5-T11": "tests/e2e/test_generated_connector_resume.py::test_durable_batches_replay_and_expiry_cleanup",
    "C5-T12": "tests/security/test_synthetic_reference_security.py::test_schema_drift_transport_failures_and_core_health_are_isolated",
    "C5-T13": "tests/unit/test_synthetic_reference_connector.py::test_valid_adapter_maps_all_entities_without_write_surface",
    "C5-T14": "tests/security/test_synthetic_reference_security.py::test_stale_test_clock_blocks_freshness_and_staging_is_bounded",
    "C5-T15": "tests/api/test_generated_mock_connector_api.py::test_connector_lists_use_bound_cursor_and_cross_route_reuse_fails",
    "C5-T16": "tests/security/test_synthetic_reference_security.py::test_thresholds_are_immutable_snapshots_and_block_duplicate_promotion",
    "C5-T17": "tests/integration/test_connector_postgresql.py::test_connector_runtime_rls_hides_other_tenant_and_mock_constraint_fails_closed",
    "C5-T18": "tests/api/test_synthetic_reference_connector_api.py::test_demo_quarantine_threshold_block_and_no_sensitive_persistence",
    "C5-T19": "tests/e2e/test_generated_connector_resume.py::test_durable_batches_replay_and_expiry_cleanup",
    "C5-T20": "tests/integration/test_synthetic_reference_postgresql.py::test_demo_schema_transport_tables_force_rls_and_append_only",
    "C5-T21": "tests/security/test_synthetic_reference_security.py::test_schema_drift_transport_failures_and_core_health_are_isolated",
    "C5-T22": "tests/unit/test_synthetic_reference_connector.py::test_package_is_fixed_checksum_bound_and_demo_only",
    "C5-T23": "tests/unit/test_phase3_migration_immutability.py::test_revision_0008_is_additive_self_contained_and_demo_only",
    "C5-T24": "tests/unit/test_synthetic_reference_connector.py::test_package_is_fixed_checksum_bound_and_demo_only",
}


def test_every_sprint5_threat_has_an_executable_test_node() -> None:
    assert set(TRACE) == {f"C5-T{number:02d}" for number in range(1, 25)}
    root = Path(__file__).parents[2]
    for node in TRACE.values():
        file_name, test_name = node.split("::", maxsplit=1)
        contents = (root / file_name).read_text(encoding="utf-8")
        assert f"def {test_name}" in contents
