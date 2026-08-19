from datetime import date

import pytest

from education_erp.access.policy import CurrentUser, TenantContext
from education_erp.canonical.service import (
    fingerprint,
    mask_reference,
    normalized_code,
    reconcile_observation,
    require_mfa,
    require_unrestricted,
    transition_enrolment,
    validate_interval,
)
from education_erp.errors import ApiError


def test_canonical_values_are_normalized_masked_and_tenant_bound() -> None:
    assert normalized_code(" gen-cs_101 ") == "GEN-CS_101"
    assert mask_reference("GEN-LRN-1007").endswith("1007")
    assert "GEN-LRN" not in mask_reference("GEN-LRN-1007")
    assert fingerprint("tenant-a", "GEN-1") != fingerprint("tenant-b", "GEN-1")


def test_invalid_code_and_temporal_interval_fail_closed() -> None:
    with pytest.raises(ApiError):
        normalized_code("../unsafe")
    with pytest.raises(ApiError) as error:
        validate_interval(date(2026, 2, 1), date(2026, 2, 1))
    assert error.value.code == "temporal_conflict"


def test_enrolment_transitions_are_explicit() -> None:
    assert transition_enrolment("pending", "activate") == "active"
    assert transition_enrolment("active", "complete") == "completed"
    with pytest.raises(ApiError) as error:
        transition_enrolment("completed", "activate")
    assert error.value.code == "state_conflict"


def test_protected_phase3_operations_require_mfa_and_unrestricted_processing() -> None:
    context = TenantContext(
        tenant_id="tenant",
        membership_id="membership",
        user=CurrentUser(id="user", display_name="Generated", work_email="generated@example.test"),
        permissions=frozenset({"learner:read"}),
        assurance_methods=frozenset({"pwd"}),
        permission_scopes=(("learner:read", None, None),),
    )
    assert context.permits_scope("learner:read")
    assert not context.permits_scope("learner:manage")
    with pytest.raises(ApiError) as mfa_error:
        require_mfa(context)
    assert mfa_error.value.code == "mfa_required"
    with pytest.raises(ApiError) as restriction_error:
        require_unrestricted(True)
    assert restriction_error.value.code == "processing_restricted"


def test_source_authority_precedence_equivalence_and_late_arrival() -> None:
    assert (
        reconcile_observation(
            current_hash=None,
            current_authority=None,
            incoming_hash="a",
            incoming_authority="primary",
            is_late=False,
        )
        == "create"
    )
    assert (
        reconcile_observation(
            current_hash="a",
            current_authority="primary",
            incoming_hash="a",
            incoming_authority="secondary",
            is_late=False,
        )
        == "confirm"
    )
    assert (
        reconcile_observation(
            current_hash="a",
            current_authority="secondary",
            incoming_hash="b",
            incoming_authority="primary",
            is_late=False,
        )
        == "supersede"
    )
    assert (
        reconcile_observation(
            current_hash="a",
            current_authority="primary",
            incoming_hash="b",
            incoming_authority="primary",
            is_late=True,
        )
        == "reconcile"
    )
