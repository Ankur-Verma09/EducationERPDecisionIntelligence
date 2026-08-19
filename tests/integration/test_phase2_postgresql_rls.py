import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_postgresql_rls_isolates_tenants_and_pool_reuse() -> None:
    database_url = os.getenv("EDUERP_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("EDUERP_TEST_DATABASE_URL is required for PostgreSQL RLS integration")
    engine = create_engine(database_url, pool_size=1, max_overflow=0)
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    campus_a = str(uuid4())
    try:
        with engine.begin() as connection:
            role = connection.execute(
                text(
                    """
                    SELECT rolsuper, rolbypassrls
                    FROM pg_roles
                    WHERE rolname = current_user
                    """
                )
            ).one()
            assert role == (False, False), (
                "RLS integration tests must use the non-privileged runtime role"
            )
            connection.execute(
                text(
                    """
                    INSERT INTO institutions
                        (id, slug, legal_name, display_name, status, data_region,
                         security_epoch, version, created_at, updated_at)
                    VALUES
                        (:id, :slug, 'Tenant A', 'Tenant A', 'active', 'test',
                         0, 1, now(), now()),
                        (:other_id, :other_slug, 'Tenant B', 'Tenant B', 'active',
                         'test', 0, 1, now(), now())
                    """
                ),
                {
                    "id": tenant_a,
                    "slug": f"tenant-a-{tenant_a}",
                    "other_id": tenant_b,
                    "other_slug": f"tenant-b-{tenant_b}",
                },
            )
            connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_a},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO campuses (id, tenant_id, code, name, status, version)
                    VALUES (:id, :tenant_id, 'MAIN', 'Main', 'active', 1)
                    """
                ),
                {"id": campus_a, "tenant_id": tenant_a},
            )
            assert connection.execute(text("SELECT count(*) FROM campuses")).scalar_one() == 1
            connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_b},
            )
            assert connection.execute(text("SELECT count(*) FROM campuses")).scalar_one() == 0

        # SET LOCAL must not survive commit or pooled-connection reuse.
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM campuses")).scalar_one() == 0
    finally:
        engine.dispose()
