from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from education_erp.config import Settings
from education_erp.identity.oidc import AuthenticationError, OidcJwtVerifier
from education_erp.persistence.models import AuditEvent
from tests.phase2_helpers import phase2_app, principal

SIGNED_VALUE = "signed"


def test_deployed_environment_requires_oidc() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            database_url=(
                "postgresql+psycopg://service:external@database/education?sslmode=require"
            ),
            allowed_hosts=("api.example.test",),
            docs_enabled=False,
        )


def test_symmetric_oidc_algorithm_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            database_url=(
                "postgresql+psycopg://service:external@database/education?sslmode=require"
            ),
            allowed_hosts=("api.example.test",),
            docs_enabled=False,
            oidc_issuer_url="https://identity.example",
            oidc_audience="api",
            oidc_algorithms=("HS256",),
        )


def test_principal_mfa_policy() -> None:
    assert principal("a", mfa=True).has_mfa(("mfa", "webauthn"))
    assert not principal("b").has_mfa(("mfa", "webauthn"))


def test_audit_events_are_immutable() -> None:
    app = phase2_app()
    with Session(app.state.database_engine) as session, session.begin():
        event = AuditEvent(
            action="test",
            target_type="test",
            outcome="success",
            request_id="c7ea2964-554f-4eed-98cc-49c1fdc41926",
        )
        session.add(event)
        session.flush()
        event_id = event.id
    with Session(app.state.database_engine) as session:
        event = session.get(AuditEvent, event_id)
        assert event is not None
        event.action = "changed"
        with pytest.raises(ValueError, match="immutable"):
            session.commit()


def test_expired_concept_is_representable_for_verifier_tests() -> None:
    expired = principal("expired")
    assert expired.expires_at > datetime.now(UTC) - timedelta(hours=1)


def test_oidc_verifier_builds_trusted_principal(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        oidc_issuer_url="https://identity.test/",
        oidc_audience="education-api",
    )
    now = datetime.now(UTC)

    class FakeJwks:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
            assert token == SIGNED_VALUE
            return SimpleNamespace(key="public-key")

    monkeypatch.setattr("education_erp.identity.oidc.PyJWKClient", FakeJwks)
    monkeypatch.setattr(
        jwt,
        "decode",
        lambda *args, **kwargs: {
            "iss": "https://identity.test",
            "sub": "subject",
            "aud": "education-api",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
            "jti": "token-id",
            "amr": ["pwd", "mfa"],
        },
    )
    verifier = OidcJwtVerifier(settings)
    result = verifier.verify(SIGNED_VALUE)
    assert result.subject == "subject"
    assert result.has_mfa(("mfa",))


def test_oidc_verifier_rejects_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        oidc_issuer_url="https://identity.test",
        oidc_audience="education-api",
    )

    class RejectingJwks:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        def get_signing_key_from_jwt(self, token: str) -> None:
            raise jwt.InvalidTokenError(token)

    monkeypatch.setattr("education_erp.identity.oidc.PyJWKClient", RejectingJwks)
    with pytest.raises(AuthenticationError):
        OidcJwtVerifier(settings).verify("invalid")
