"""Shared Phase 2 HTTP controls: persistent replay and opaque cursors."""

from __future__ import annotations

import base64
import functools
import hashlib
import hmac
import inspect
import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, ParamSpec, TypeVar, cast
from uuid import UUID

from fastapi import Header, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from education_erp.api.dependencies import current_user
from education_erp.config import get_settings
from education_erp.errors import ApiError
from education_erp.identity.principal import TokenPrincipal
from education_erp.persistence.models import IdempotencyRecord

P = ParamSpec("P")
R = TypeVar("R")


def encode_cursor(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def decode_cursor(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode()
        UUID(decoded)
        return decoded
    except (ValueError, UnicodeDecodeError) as exc:
        raise ApiError(400, "invalid_cursor", "The pagination cursor is invalid") from exc


def page(items: Sequence[Any], limit: int) -> dict[str, object]:
    visible = list(items[:limit])
    return {
        "items": visible,
        "next_cursor": encode_cursor(str(visible[-1].id)) if len(items) > limit else None,
    }


def encode_bound_cursor(
    value: str,
    *,
    tenant_id: str,
    collection: str,
    filters: str = "",
) -> str:
    payload = {
        "position": value,
        "tenant": tenant_id,
        "collection": collection,
        "filters": filters,
        "expires": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
    }
    encoded = (
        base64.urlsafe_b64encode(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )
        .decode()
        .rstrip("=")
    )
    signature = hmac.new(
        get_settings().cursor_signing_key.encode(),
        encoded.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded}.{signature}"


def decode_bound_cursor(
    value: str | None,
    *,
    tenant_id: str,
    collection: str,
    filters: str = "",
) -> str | None:
    if value is None:
        return None
    try:
        encoded, signature = value.split(".", maxsplit=1)
        expected = hmac.new(
            get_settings().cursor_signing_key.encode(),
            encoded.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode())
        position = str(payload["position"])
        UUID(position)
        if (
            payload["tenant"] != tenant_id
            or payload["collection"] != collection
            or payload["filters"] != filters
            or int(payload["expires"]) <= int(datetime.now(UTC).timestamp())
        ):
            raise ValueError
        return position
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(400, "invalid_cursor", "The pagination cursor is invalid") from exc


def bound_page(
    items: Sequence[Any],
    limit: int,
    *,
    tenant_id: str,
    collection: str,
    filters: str = "",
) -> dict[str, object]:
    visible = list(items[:limit])
    return {
        "items": visible,
        "next_cursor": (
            encode_bound_cursor(
                str(visible[-1].id),
                tenant_id=tenant_id,
                collection=collection,
                filters=filters,
            )
            if len(items) > limit
            else None
        ),
    }


def _request_hash(arguments: dict[str, Any]) -> str:
    excluded = {"request", "response", "session", "principal", "if_match", "idempotency_key"}
    payload = {
        key: jsonable_encoder(value) for key, value in arguments.items() if key not in excluded
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def idempotent(func: Callable[P, R]) -> Callable[P, R | Response]:
    """Require a key and persist/replay the completed mutation response."""

    signature = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | Response:
        call_kwargs = dict(kwargs)
        call_kwargs.pop("idempotency_key", None)
        bound = signature.bind(*args, **call_kwargs)
        request = cast(Request, bound.arguments["request"])
        session = cast(Session, bound.arguments["session"])
        principal = cast(TokenPrincipal, bound.arguments["principal"])
        key = request.headers.get("Idempotency-Key")
        if not key or len(key) > 200:
            raise ApiError(428, "idempotency_key_required", "Idempotency-Key is required")
        actor = current_user(session, principal)
        route = request.url.path
        digest = _request_hash(dict(bound.arguments))
        record = session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.actor_user_id == actor.id,
                IdempotencyRecord.method == request.method,
                IdempotencyRecord.route == route,
                IdempotencyRecord.key == key,
                IdempotencyRecord.expires_at > datetime.now(UTC),
            )
        )
        if record is not None:
            if record.request_hash != digest:
                raise ApiError(409, "idempotency_conflict", "The idempotency key was reused")
            return JSONResponse(status_code=record.response_status, content=record.response_body)

        result = func(*args, **cast(Any, call_kwargs))
        encoded = jsonable_encoder(result)
        status = int(getattr(request.scope["route"], "status_code", None) or 200)
        tenant_id = cast(str | None, bound.arguments.get("tenant_id"))
        if tenant_id is None and isinstance(encoded, dict):
            tenant_id = cast(str | None, encoded.get("id"))
        session.add(
            IdempotencyRecord(
                tenant_id=tenant_id,
                actor_user_id=actor.id,
                method=request.method,
                route=route,
                key=key,
                request_hash=digest,
                response_status=status,
                response_body=encoded if isinstance(encoded, dict) else {"result": encoded},
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        return result

    parameters = [
        *signature.parameters.values(),
        inspect.Parameter(
            "idempotency_key",
            inspect.Parameter.KEYWORD_ONLY,
            default=None,
            annotation=Annotated[str | None, Header(alias="Idempotency-Key")],
        ),
    ]
    wrapper.__signature__ = signature.replace(parameters=parameters)  # type: ignore[attr-defined]
    return wrapper
