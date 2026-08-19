"""FastAPI authentication and authorization dependencies."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from education_erp.access.policy import (
    CurrentUser,
    TenantContext,
    resolve_tenant_context,
    resolve_user,
)
from education_erp.errors import ApiError
from education_erp.identity.oidc import AuthenticationError, TokenVerifier
from education_erp.identity.principal import TokenPrincipal


def database_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.database_engine) as session, session.begin():
        yield session


def token_principal(request: Request) -> TokenPrincipal:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ApiError(401, "authentication_required", "A bearer access token is required")
    verifier: TokenVerifier | None = getattr(request.app.state, "token_verifier", None)
    if verifier is None:
        raise ApiError(503, "identity_unavailable", "Identity validation is unavailable")
    try:
        return verifier.verify(token)
    except AuthenticationError as exc:
        raise ApiError(401, "invalid_token", "The access token is invalid") from exc


def current_user(session: Session, principal: TokenPrincipal) -> CurrentUser:
    user = resolve_user(session, principal)
    if user is None:
        raise ApiError(401, "invalid_token", "The access token is not linked to an active user")
    return user


def tenant_context(
    session: Session,
    principal: TokenPrincipal,
    tenant_id: str,
) -> TenantContext:
    context = resolve_tenant_context(session, principal, tenant_id)
    if context is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return context


def require_permission(context: TenantContext, permission: str) -> None:
    if not context.permits(permission):
        raise ApiError(403, "permission_denied", "The operation is not permitted")
