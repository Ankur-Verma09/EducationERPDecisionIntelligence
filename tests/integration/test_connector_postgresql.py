import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, exc, text

pytestmark = pytest.mark.integration

TABLES = (
    "connectors",
    "connector_credential_refs",
    "connector_mapping_sets",
    "connector_mapping_versions",
    "connector_sync_jobs",
    "connector_watermarks",
    "connector_batches",
    "connector_staging_records",
    "connector_validation_errors",
    "connector_reconciliation_runs",
    "connector_dead_letters",
)


def test_connector_tables_force_rls_permissions_and_append_only_history() -> None:
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    runtime_url = os.getenv("EDUERP_TEST_DATABASE_URL")
    if not owner_url or not runtime_url:
        pytest.skip("PostgreSQL runtime and migration URLs are required")
    owner = create_engine(owner_url)
    runtime = create_engine(runtime_url)
    with owner.connect() as connection:
        forced = connection.execute(
            text(
                "SELECT count(*) FROM pg_class WHERE relname = ANY(:tables) "
                "AND relrowsecurity AND relforcerowsecurity"
            ),
            {"tables": list(TABLES)},
        ).scalar_one()
        assert forced == len(TABLES)
        triggers = connection.execute(
            text(
                "SELECT count(*) FROM pg_trigger WHERE tgname IN "
                "('connector_mapping_versions_append_only','connector_batches_append_only') "
                "AND NOT tgisinternal"
            )
        ).scalar_one()
        assert triggers == 2
        credential_disabled = connection.execute(
            text(
                "SELECT count(*) FROM pg_constraint "
                "WHERE conrelid = 'connector_credential_refs'::regclass "
                "AND pg_get_constraintdef(oid) = 'CHECK (false)'"
            )
        ).scalar_one()
        assert credential_disabled == 1
        owner_permissions = connection.execute(
            text(
                "SELECT count(*) FROM role_permissions rp "
                "JOIN roles r ON r.id=rp.role_id JOIN permissions p ON p.id=rp.permission_id "
                "WHERE r.name='tenant_owner' AND p.name LIKE 'connector:%'"
            )
        ).scalar_one()
        assert owner_permissions == 5
    with runtime.connect() as connection:
        role = connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user")
        ).one()
        assert role == (False, False)
        assert connection.execute(text("SELECT count(*) FROM connectors")).scalar_one() == 0
    owner.dispose()
    runtime.dispose()


def test_connector_runtime_rls_hides_other_tenant_and_mock_constraint_fails_closed() -> None:
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    runtime_url = os.getenv("EDUERP_TEST_DATABASE_URL")
    if not owner_url or not runtime_url:
        pytest.skip("PostgreSQL runtime and migration URLs are required")
    owner = create_engine(owner_url)
    runtime = create_engine(runtime_url)
    tenant_a, tenant_b, connector_id = str(uuid4()), str(uuid4()), str(uuid4())
    mapping_set_id, mapping_id = str(uuid4()), str(uuid4())
    with owner.begin() as connection:
        for tenant_id in (tenant_a, tenant_b):
            connection.execute(
                text(
                    "INSERT INTO institutions "
                    "(id,slug,legal_name,display_name,status,data_region,security_epoch,version,"
                    "created_at,updated_at) VALUES "
                    "(:id,:slug,'Generated','Generated','active','test',0,1,now(),now())"
                ),
                {"id": tenant_id, "slug": f"connector-{tenant_id}"},
            )
        connection.execute(
            text(
                "INSERT INTO connectors "
                "(id,tenant_id,name,kind,status,config,version,created_at,updated_at) VALUES "
                "(:id,:tenant,'Generated','generated_mock_v1','active','{}',1,now(),now())"
            ),
            {"id": connector_id, "tenant": tenant_a},
        )
        connection.execute(
            text(
                "INSERT INTO connector_mapping_sets (id,tenant_id,connector_id,name,created_at) "
                "VALUES (:id,:tenant,:connector,'generated',now())"
            ),
            {"id": mapping_set_id, "tenant": tenant_a, "connector": connector_id},
        )
        connection.execute(
            text(
                "INSERT INTO connector_mapping_versions "
                "(id,tenant_id,connector_id,mapping_set_id,version,schema_version,document,"
                "checksum,active,created_at) VALUES "
                "(:id,:tenant,:connector,:mapping_set,1,'1','{}','generated',true,now())"
            ),
            {
                "id": mapping_id,
                "tenant": tenant_a,
                "connector": connector_id,
                "mapping_set": mapping_set_id,
            },
        )
        with pytest.raises(exc.IntegrityError), connection.begin_nested():
            connection.execute(
                text(
                    "INSERT INTO connectors (id,tenant_id,name,kind,status,config,version,"
                    "created_at,updated_at) VALUES "
                    "(:id,:tenant,'Unsafe','sftp','active','{}',1,now(),now())"
                ),
                {"id": str(uuid4()), "tenant": tenant_a},
            )
    with runtime.begin() as connection:
        connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": tenant_b}
        )
        assert connection.execute(text("SELECT count(*) FROM connectors")).scalar_one() == 0
        connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": tenant_a}
        )
        assert connection.execute(text("SELECT count(*) FROM connectors")).scalar_one() == 1
        with pytest.raises(exc.ProgrammingError), connection.begin_nested():
            connection.execute(
                text("UPDATE connector_mapping_versions SET checksum='changed' WHERE id=:id"),
                {"id": mapping_id},
            )
        with pytest.raises(exc.ProgrammingError), connection.begin_nested():
            connection.execute(
                text("DELETE FROM connector_mapping_versions WHERE id=:id"), {"id": mapping_id}
            )
    with owner.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE connector_mapping_versions DISABLE TRIGGER "
                "connector_mapping_versions_append_only"
            )
        )
        connection.execute(
            text("DELETE FROM connector_mapping_versions WHERE id=:id"), {"id": mapping_id}
        )
        connection.execute(
            text(
                "ALTER TABLE connector_mapping_versions ENABLE TRIGGER "
                "connector_mapping_versions_append_only"
            )
        )
        connection.execute(
            text("DELETE FROM connector_mapping_sets WHERE id=:id"), {"id": mapping_set_id}
        )
        connection.execute(text("DELETE FROM connectors WHERE id=:id"), {"id": connector_id})
        connection.execute(
            text("DELETE FROM institutions WHERE id IN (:a,:b)"), {"a": tenant_a, "b": tenant_b}
        )
    owner.dispose()
    runtime.dispose()
