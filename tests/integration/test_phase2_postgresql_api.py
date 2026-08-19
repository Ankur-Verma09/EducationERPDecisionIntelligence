import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, exc, func, select, text
from sqlalchemy.orm import Session

from education_erp.config import Settings
from education_erp.identity.principal import TokenPrincipal
from education_erp.main import create_app
from education_erp.persistence.connector_models import ConnectorBatch, StagingRecord
from education_erp.persistence.event_models import OutboxEvent
from education_erp.persistence.models import (
    Campus,
    ExternalIdentity,
    Membership,
    PlatformRoleAssignment,
    User,
)
from education_erp.persistence.phase3_models import (
    OfferingEnrolment,
    ProgrammeEnrolment,
    SourceObservation,
)
from tests.phase2_helpers import AUDIENCE, ISSUER, FakeVerifier, auth, principal


@pytest.mark.integration
def test_postgresql_runtime_executes_platform_tenant_lifecycle() -> None:
    runtime_url = os.getenv("EDUERP_TEST_DATABASE_URL")
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    if not runtime_url or not owner_url:
        pytest.skip("PostgreSQL runtime and migration URLs are required")

    subject = f"postgres-admin-{uuid4()}"
    slug = f"postgres-api-{uuid4()}"
    owner_subject = f"postgres-owner-{uuid4()}"
    owner_engine = create_engine(owner_url)
    with Session(owner_engine) as session, session.begin():
        admin = User(
            display_name="PostgreSQL Platform Admin",
            work_email=f"{subject}@example.test",
            status="active",
        )
        session.add(admin)
        session.flush()
        session.add(ExternalIdentity(user_id=admin.id, issuer=ISSUER, subject=subject))
        session.add(PlatformRoleAssignment(user_id=admin.id, role_name="platform_admin"))

    app = create_app(
        Settings(
            environment="test",
            database_url=runtime_url,
            allowed_hosts=("testserver",),
            oidc_issuer_url=ISSUER,
            oidc_audience=AUDIENCE,
        )
    )
    admin_principal: TokenPrincipal = principal(subject, mfa=True)
    owner_principal: TokenPrincipal = principal(owner_subject, mfa=True)
    verifier = FakeVerifier(
        {
            "postgres-admin": admin_principal,
            "postgres-owner": owner_principal,
        }
    )
    app.state.token_verifier = verifier
    replay_key = f"postgres-replay-{uuid4()}"
    campus_body = {"code": "REPLAY", "name": "Persistent Replay Campus"}
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/platform/institutions",
            headers=auth("postgres-admin"),
            json={
                "slug": slug,
                "legal_name": "PostgreSQL API Tenant",
                "display_name": "PostgreSQL API Tenant",
                "data_region": "test",
                "initial_owner": {
                    "issuer": ISSUER,
                    "subject": owner_subject,
                    "work_email": f"{owner_subject}@example.test",
                    "display_name": "PostgreSQL Owner",
                },
            },
        )
        assert created.status_code == 201, created.text
        tenant_id = created.json()["id"]

        activated = client.post(
            f"/api/v1/platform/institutions/{tenant_id}/activate",
            headers=auth("postgres-admin"),
        )
        assert activated.status_code == 200, activated.text

        connector = client.post(
            f"/api/v1/tenants/{tenant_id}/connectors",
            headers=auth("postgres-owner"),
            json={
                "name": "Generated PostgreSQL connector",
                "kind": "generated_mock_v1",
                "scenario": "mixed",
            },
        )
        assert connector.status_code == 201, connector.text
        connector_job = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("postgres-owner"),
            json={"connector_id": connector.json()["id"]},
        )
        assert connector_job.status_code == 201, connector_job.text
        assert connector_job.json()["state"] == "succeeded"
        assert connector_job.json()["accepted_count"] == 9
        assert connector_job.json()["rejected_count"] == 1
        with Session(owner_engine) as session:
            assert (
                session.scalar(
                    select(func.count(SourceObservation.id)).where(
                        SourceObservation.tenant_id == tenant_id
                    )
                )
                == 9
            )
            assert (
                session.scalar(
                    select(func.count(ConnectorBatch.id)).where(
                        ConnectorBatch.tenant_id == tenant_id,
                        ConnectorBatch.state == "completed",
                    )
                )
                == 1
            )

        synthetic = client.post(
            f"/api/v1/tenants/{tenant_id}/connectors",
            headers=auth("postgres-owner"),
            json={
                "name": "Synthetic reference PostgreSQL demo",
                "kind": "synthetic_reference_erp_v1",
                "package_version": "1.0.0",
                "scenario": "valid",
            },
        )
        assert synthetic.status_code == 201, synthetic.text
        synthetic_job = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("postgres-owner"),
            json={"connector_id": synthetic.json()["id"]},
        )
        assert synthetic_job.status_code == 201, synthetic_job.text
        assert synthetic_job.json()["state"] == "succeeded"
        with Session(owner_engine) as session:
            assert (
                session.scalar(
                    select(func.count(ProgrammeEnrolment.id)).where(
                        ProgrammeEnrolment.tenant_id == tenant_id,
                        ProgrammeEnrolment.status == "active",
                    )
                )
                >= 1
            )
            staging_id = session.scalar(
                select(StagingRecord.id).where(
                    StagingRecord.tenant_id == tenant_id,
                    StagingRecord.retention_class == "landing-24h",
                )
            )
            assert staging_id is not None
            with pytest.raises(exc.IntegrityError), session.begin_nested():
                session.execute(
                    text(
                        "UPDATE connector_staging_records "
                        "SET expires_at = created_at + INTERVAL '25 hours' WHERE id=:id"
                    ),
                    {"id": staging_id},
                )
                session.flush()
            assert (
                session.scalar(
                    select(func.count(OfferingEnrolment.id)).where(
                        OfferingEnrolment.tenant_id == tenant_id,
                        OfferingEnrolment.status == "active",
                    )
                )
                >= 1
            )
            assert (
                session.scalar(
                    select(func.count(OutboxEvent.id)).where(
                        OutboxEvent.tenant_id == tenant_id,
                        OutboxEvent.event_type == "connector.sync_completed.v1",
                        OutboxEvent.correlation_id.is_not(None),
                    )
                )
                >= 1
            )

        campus = client.post(
            f"/api/v1/tenants/{tenant_id}/campuses",
            headers={
                "Authorization": "Bearer postgres-owner",
                "Idempotency-Key": replay_key,
            },
            json=campus_body,
        )
        assert campus.status_code == 201, campus.text
        campus_response = campus.json()

        suspended = client.post(
            f"/api/v1/platform/institutions/{tenant_id}/suspend",
            headers=auth("postgres-admin"),
            json={"reason": "PostgreSQL runtime validation"},
        )
        assert suspended.status_code == 200, suspended.text

        reactivated = client.post(
            f"/api/v1/platform/institutions/{tenant_id}/activate",
            headers=auth("postgres-admin"),
        )
        assert reactivated.status_code == 200, reactivated.text

        with Session(owner_engine) as session:
            owner_membership_id = session.scalar(
                select(Membership.id)
                .join(User, User.id == Membership.user_id)
                .join(ExternalIdentity, ExternalIdentity.user_id == User.id)
                .where(
                    Membership.tenant_id == tenant_id,
                    ExternalIdentity.issuer == ISSUER,
                    ExternalIdentity.subject == owner_subject,
                )
            )
        assert owner_membership_id is not None
        deletion = client.post(
            f"/api/v1/platform/institutions/{tenant_id}/request-deletion",
            headers=auth("postgres-admin"),
            json={
                "reason": "PostgreSQL runtime owner-approved deletion",
                "tenant_owner_approval_membership_id": owner_membership_id,
            },
        )
        assert deletion.status_code == 200, deletion.text

    replay_app = create_app(
        Settings(
            environment="test",
            database_url=runtime_url,
            allowed_hosts=("testserver",),
            oidc_issuer_url=ISSUER,
            oidc_audience=AUDIENCE,
        )
    )
    replay_app.state.token_verifier = verifier
    with TestClient(replay_app) as replay_client:
        replay = replay_client.post(
            f"/api/v1/tenants/{tenant_id}/campuses",
            headers={
                "Authorization": "Bearer postgres-owner",
                "Idempotency-Key": replay_key,
            },
            json=campus_body,
        )
        assert replay.status_code == 201, replay.text
        assert replay.json() == campus_response

    with Session(owner_engine) as session:
        campus_count = session.scalar(
            select(func.count())
            .select_from(Campus)
            .where(Campus.tenant_id == tenant_id, Campus.code == "REPLAY")
        )
    assert campus_count == 1
    owner_engine.dispose()
