from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from education_erp.access.permissions import seed_builtin_access
from education_erp.config import Settings
from education_erp.identity.oidc import AuthenticationError
from education_erp.identity.principal import TokenPrincipal
from education_erp.main import create_app
from education_erp.persistence.base import Base
from education_erp.persistence.models import ExternalIdentity, PlatformRoleAssignment, User

ISSUER = "https://identity.test"
AUDIENCE = "education-api"


class FakeVerifier:
    def __init__(self, principals: dict[str, TokenPrincipal]) -> None:
        self.principals = principals

    def verify(self, token: str) -> TokenPrincipal:
        try:
            return self.principals[token]
        except KeyError as exc:
            raise AuthenticationError("invalid") from exc


def principal(subject: str, *, mfa: bool = False) -> TokenPrincipal:
    now = datetime.now(UTC)
    return TokenPrincipal(
        issuer=ISSUER,
        subject=subject,
        audience=AUDIENCE,
        issued_at=now,
        expires_at=now + timedelta(minutes=15),
        token_id=f"token-{subject}",
        assurance_methods=frozenset({"mfa"} if mfa else {"pwd"}),
    )


def phase2_app() -> FastAPI:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+pysqlite:///:memory:",
            allowed_hosts=("testserver",),
            oidc_issuer_url=ISSUER,
            oidc_audience=AUDIENCE,
        )
    )
    Base.metadata.create_all(app.state.database_engine)
    with Session(app.state.database_engine) as session, session.begin():
        session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0008')"))
        seed_builtin_access(session)
        admin = User(
            display_name="Platform Admin",
            work_email="admin@example.test",
            status="active",
        )
        session.add(admin)
        session.flush()
        session.add(ExternalIdentity(user_id=admin.id, issuer=ISSUER, subject="platform-admin"))
        session.add(PlatformRoleAssignment(user_id=admin.id, role_name="platform_admin"))
    app.state.token_verifier = FakeVerifier(
        {
            "admin": principal("platform-admin", mfa=True),
            "admin-without-mfa": principal("platform-admin"),
            "owner-a": principal("owner-a", mfa=True),
            "owner-a-without-mfa": principal("owner-a"),
            "owner-b": principal("owner-b", mfa=True),
            "viewer": principal("viewer"),
            "department-admin": principal("department-admin", mfa=True),
        }
    )
    return app


def auth(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(uuid4()),
    }


def create_tenant(
    client: TestClient,
    *,
    slug: str,
    owner_subject: str,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/platform/institutions",
        headers=auth("admin"),
        json={
            "slug": slug,
            "legal_name": f"{slug} Legal",
            "display_name": slug,
            "data_region": "test-region",
            "initial_owner": {
                "issuer": ISSUER,
                "subject": owner_subject,
                "work_email": f"{owner_subject}@example.test",
                "display_name": owner_subject,
            },
        },
    )
    assert response.status_code == 201, response.text
    tenant = response.json()
    activation = client.post(
        f"/api/v1/platform/institutions/{tenant['id']}/activate",
        headers=auth("admin"),
    )
    assert activation.status_code == 200, activation.text
    tenant["status"] = "active"
    tenant["version"] = activation.json()["version"]
    return tenant
