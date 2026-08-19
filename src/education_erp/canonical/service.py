"""Phase 3 canonical domain rules shared by API and future connector ports."""

import hashlib
import re
from datetime import date

from education_erp.access.policy import TenantContext
from education_erp.errors import ApiError

CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,63}$")
ENROLMENT_TRANSITIONS = {
    "pending": {"active", "cancelled"},
    "active": {"suspended", "withdrawn", "completed", "cancelled"},
    "suspended": {"active", "withdrawn", "cancelled"},
    "withdrawn": set(),
    "completed": set(),
    "cancelled": set(),
}


def normalized_code(value: str) -> str:
    code = value.strip().upper()
    if not CODE_PATTERN.fullmatch(code):
        raise ApiError(422, "validation_error", "The code format is invalid")
    return code


def validate_interval(start: date, end: date | None) -> None:
    if end is not None and end <= start:
        raise ApiError(409, "temporal_conflict", "The effective interval is invalid")


def fingerprint(tenant_id: str, value: str) -> str:
    return hashlib.sha256(f"{tenant_id}:{value.strip().upper()}".encode()).hexdigest()


def mask_reference(value: str) -> str:
    suffix = value[-4:] if len(value) >= 4 else value
    return "*" * max(4, len(value) - len(suffix)) + suffix


def require_scope(
    context: TenantContext,
    permission: str,
    campus_id: str | None = None,
    department_id: str | None = None,
) -> None:
    if not context.permits_scope(permission, campus_id, department_id):
        raise ApiError(404, "resource_not_found", "The requested resource was not found")


def require_mfa(context: TenantContext) -> None:
    if not context.assurance_methods.intersection({"mfa", "otp", "webauthn"}):
        raise ApiError(403, "mfa_required", "Multi-factor authentication is required")


def require_unrestricted(restricted: bool) -> None:
    if restricted:
        raise ApiError(423, "processing_restricted", "Processing is restricted")


def transition_enrolment(current: str, action: str) -> str:
    target = {
        "activate": "active",
        "suspend": "suspended",
        "withdraw": "withdrawn",
        "complete": "completed",
        "cancel": "cancelled",
    }.get(action)
    if target is None or target not in ENROLMENT_TRANSITIONS.get(current, set()):
        raise ApiError(409, "state_conflict", "The enrolment transition is invalid")
    return target


def reconcile_observation(
    *,
    current_hash: str | None,
    current_authority: str | None,
    incoming_hash: str,
    incoming_authority: str,
    is_late: bool,
) -> str:
    """Return the deterministic projection disposition for an observation."""

    if current_hash is None:
        return "create"
    if current_hash == incoming_hash:
        return "confirm"
    rank = {"reference": 0, "secondary": 1, "primary": 2}
    if incoming_authority not in rank or current_authority not in rank:
        raise ApiError(403, "source_not_authorized", "The source authority is invalid")
    if is_late:
        return "reconcile"
    if rank[incoming_authority] > rank[current_authority]:
        return "supersede"
    return "reconcile"
