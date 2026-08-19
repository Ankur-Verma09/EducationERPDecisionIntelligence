# ruff: noqa: E501

import re
from pathlib import Path

# Every threat is bound to an executable test that exercises its primary control.
# Several integration journeys intentionally cover more than one related threat.
THREAT_EVIDENCE = {
    "P3-T01": "tests/security/test_phase3_security.py::test_phase3_hides_cross_tenant_learner_and_never_lists_identifier",
    "P3-T02": "tests/integration/test_phase3_postgresql_rls.py::test_phase3_postgresql_tables_force_rls_and_runtime_cannot_bypass",
    "P3-T03": "tests/security/test_phase3_security.py::test_platform_admin_has_no_implicit_learner_access_and_reveal_requires_mfa",
    "P3-T04": "tests/api/test_phase2_contract_completion.py::test_scoped_delegation_cannot_escape_department_or_tenant",
    "P3-T05": "tests/security/test_phase3_security.py::test_phase3_hides_cross_tenant_learner_and_never_lists_identifier",
    "P3-T06": "tests/api/test_phase3_api.py::test_phase3_rejects_prohibited_overposting_and_requires_preconditions",
    "P3-T07": "tests/security/test_phase3_security.py::test_learner_identifier_never_enters_request_telemetry",
    "P3-T08": "tests/security/test_phase3_security.py::test_platform_admin_has_no_implicit_learner_access_and_reveal_requires_mfa",
    "P3-T09": "tests/unit/test_phase3_reconciliation.py::test_adversarial_source_key_is_treated_as_opaque_data",
    "P3-T10": "tests/unit/test_phase3_reconciliation.py::test_observation_service_rejects_unapproved_entity_and_source",
    "P3-T11": "tests/unit/test_phase3_reconciliation.py::test_observation_service_persists_replay_precedence_and_conflict",
    "P3-T12": "tests/unit/test_phase3_reconciliation.py::test_observation_service_persists_replay_precedence_and_conflict",
    "P3-T13": "tests/unit/test_phase3_domain.py::test_source_authority_precedence_equivalence_and_late_arrival",
    "P3-T14": "tests/unit/test_phase3_reconciliation.py::test_observation_service_persists_replay_precedence_and_conflict",
    "P3-T15": "tests/integration/test_phase3_postgresql_rls.py::test_phase3_postgresql_tables_force_rls_and_runtime_cannot_bypass",
    "P3-T16": "tests/security/test_phase3_security.py::test_phase3_hides_cross_tenant_learner_and_never_lists_identifier",
    "P3-T17": "tests/unit/test_phase3_domain.py::test_protected_phase3_operations_require_mfa_and_unrestricted_processing",
    "P3-T18": "tests/security/test_phase3_security.py::test_phase3_processing_restriction_blocks_new_enrolment",
    "P3-T19": "tests/security/test_phase3_security.py::test_subject_export_requires_mfa_reason_and_single_request_scope",
    "P3-T20": "tests/security/test_phase3_security.py::test_phase3_exposes_no_physical_delete_operation",
    "P3-T21": "tests/integration/test_phase3_postgresql_rls.py::test_phase3_postgresql_rejects_overlapping_temporal_versions",
    "P3-T22": "tests/security/test_phase3_bound_cursor.py::test_phase3_cursor_is_signed_and_bound_to_tenant_and_collection",
    "P3-T23": "tests/security/test_phase3_security.py::test_phase3_idempotency_replay_is_actor_scoped",
    "P3-T24": "tests/security/test_phase3_security.py::test_audit_outage_fails_sensitive_operation_closed",
    "P3-T25": "tests/api/test_phase3_api.py::test_phase3_rejects_prohibited_overposting_and_requires_preconditions",
    "P3-T26": "tests/security/test_phase3_security.py::test_export_retention_operational_verification_is_present",
}


def test_every_phase3_threat_has_executable_evidence() -> None:
    root = Path(__file__).parents[2]
    threat_model = (root / "docs/security/PHASE_3_THREAT_MODEL.md").read_text(encoding="utf-8")
    approved = set(re.findall(r"\| (P3-T\d{2}) \|", threat_model))

    assert approved == {f"P3-T{number:02d}" for number in range(1, 27)}
    assert set(THREAT_EVIDENCE) == approved
    for node_id in THREAT_EVIDENCE.values():
        relative_file, function_name = node_id.split("::", maxsplit=1)
        source = (root / relative_file).read_text(encoding="utf-8")
        assert f"def {function_name}(" in source
