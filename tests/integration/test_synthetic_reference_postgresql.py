import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, exc, text

pytestmark = pytest.mark.integration


def _urls() -> tuple[str, str]:
    owner = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    runtime = os.getenv("EDUERP_TEST_DATABASE_URL")
    if not owner or not runtime:
        pytest.skip("PostgreSQL runtime and migration URLs are required")
    return owner, runtime


def test_demo_schema_transport_tables_force_rls_and_append_only() -> None:
    owner_url, runtime_url = _urls()
    owner, runtime = create_engine(owner_url), create_engine(runtime_url)
    tables = ["connector_source_schemas", "connector_transport_configs"]
    with owner.connect() as connection:
        forced = connection.execute(
            text(
                "SELECT count(*) FROM pg_class WHERE relname = ANY(:tables) "
                "AND relrowsecurity AND relforcerowsecurity"
            ),
            {"tables": tables},
        ).scalar_one()
        assert forced == 2
        triggers = connection.execute(
            text(
                "SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:triggers) AND NOT tgisinternal"
            ),
            {"triggers": [f"{table}_append_only" for table in tables]},
        ).scalar_one()
        assert triggers == 2
    with runtime.connect() as connection:
        role = connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user")
        ).one()
        assert role == (False, False)
    owner.dispose()
    runtime.dispose()


def test_demo_database_rejects_network_credentials_mutation_and_cross_tenant_access() -> None:
    owner_url, runtime_url = _urls()
    owner, runtime = create_engine(owner_url), create_engine(runtime_url)
    tenant_a, tenant_b, connector_id = str(uuid4()), str(uuid4()), str(uuid4())
    schema_id, transport_id = str(uuid4()), str(uuid4())
    with owner.begin() as connection:
        for tenant_id in (tenant_a, tenant_b):
            connection.execute(
                text(
                    "INSERT INTO institutions "
                    "(id,slug,legal_name,display_name,status,data_region,security_epoch,version,"
                    "created_at,updated_at) VALUES "
                    "(:id,:slug,'Generated','Generated','active','test',0,1,now(),now())"
                ),
                {"id": tenant_id, "slug": f"synthetic-{tenant_id}"},
            )
        connection.execute(
            text(
                "INSERT INTO connectors "
                "(id,tenant_id,name,kind,status,config,version,created_at,updated_at) VALUES "
                "(:id,:tenant,'Synthetic','synthetic_reference_erp_v1','active','{}',1,now(),now())"
            ),
            {"id": connector_id, "tenant": tenant_a},
        )
        connection.execute(
            text(
                "INSERT INTO connector_source_schemas "
                "(id,tenant_id,connector_id,package_id,package_version,schema_version,"
                "schema_checksum,status,created_at) VALUES "
                "(:id,:tenant,:connector,'synthetic-reference-erp-v1','1.0.0','1',"
                "'generated','verified',now())"
            ),
            {"id": schema_id, "tenant": tenant_a, "connector": connector_id},
        )
        connection.execute(
            text(
                "INSERT INTO connector_transport_configs "
                "(id,tenant_id,connector_id,kind,network_egress,credential_reference,page_size,"
                "max_record_bytes,max_batch_bytes,read_timeout_seconds,max_attempts,"
                "backoff_seconds,created_at) VALUES "
                "(:id,:tenant,:connector,'in_process_csv_test_double',false,NULL,100,65536,"
                "5242880,15,3,'[1,2,4]',now())"
            ),
            {"id": transport_id, "tenant": tenant_a, "connector": connector_id},
        )
        with pytest.raises(exc.IntegrityError), connection.begin_nested():
            connection.execute(
                text(
                    "INSERT INTO connector_transport_configs "
                    "(id,tenant_id,connector_id,kind,network_egress,credential_reference,page_size,"
                    "max_record_bytes,max_batch_bytes,read_timeout_seconds,max_attempts,"
                    "backoff_seconds,created_at) VALUES "
                    "(:id,:tenant,:connector,'in_process_csv_test_double',true,'vault:x',100,65536,"
                    "5242880,15,3,'[1,2,4]',now())"
                ),
                {"id": str(uuid4()), "tenant": tenant_a, "connector": connector_id},
            )
    with runtime.begin() as connection:
        connection.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b})
        assert (
            connection.execute(text("SELECT count(*) FROM connector_source_schemas")).scalar_one()
            == 0
        )
        connection.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a})
        assert (
            connection.execute(text("SELECT count(*) FROM connector_source_schemas")).scalar_one()
            == 1
        )
        with pytest.raises(exc.ProgrammingError), connection.begin_nested():
            connection.execute(
                text("UPDATE connector_source_schemas SET status='rejected' WHERE id=:id"),
                {"id": schema_id},
            )
        with pytest.raises(exc.ProgrammingError), connection.begin_nested():
            connection.execute(
                text("DELETE FROM connector_transport_configs WHERE id=:id"),
                {"id": transport_id},
            )
    with owner.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE connector_source_schemas DISABLE TRIGGER "
                "connector_source_schemas_append_only"
            )
        )
        connection.execute(
            text("DELETE FROM connector_source_schemas WHERE tenant_id=:tenant"),
            {"tenant": tenant_a},
        )
        connection.execute(
            text(
                "ALTER TABLE connector_source_schemas ENABLE TRIGGER "
                "connector_source_schemas_append_only"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE connector_transport_configs DISABLE TRIGGER "
                "connector_transport_configs_append_only"
            )
        )
        connection.execute(
            text("DELETE FROM connector_transport_configs WHERE tenant_id=:tenant"),
            {"tenant": tenant_a},
        )
        connection.execute(
            text(
                "ALTER TABLE connector_transport_configs ENABLE TRIGGER "
                "connector_transport_configs_append_only"
            )
        )
        connection.execute(text("DELETE FROM connectors WHERE id=:id"), {"id": connector_id})
        connection.execute(
            text("DELETE FROM institutions WHERE id IN (:a,:b)"), {"a": tenant_a, "b": tenant_b}
        )
    owner.dispose()
    runtime.dispose()
