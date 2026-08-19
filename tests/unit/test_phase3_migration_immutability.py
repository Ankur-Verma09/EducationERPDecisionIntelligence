from pathlib import Path


def test_revision_0005_is_self_contained_and_does_not_import_application_metadata() -> None:
    revision = (
        Path(__file__).parents[2] / "migrations" / "versions" / "0005_canonical_education_model.py"
    ).read_text(encoding="utf-8")

    assert "education_erp.persistence" not in revision
    assert "Base.metadata" not in revision
    assert "def _create_phase3_tables()" in revision
    assert revision.count("op.create_table(") == 18


def test_revision_0006_is_additive_and_self_contained() -> None:
    revision = (
        Path(__file__).parents[2] / "migrations" / "versions" / "0006_event_foundation.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "0006"' in revision
    assert 'down_revision: str | None = "0005"' in revision
    assert "education_erp.persistence" not in revision
    assert "Base.metadata" not in revision
    assert revision.count("op.create_table(") == 2


def test_revision_0007_is_additive_self_contained_and_mock_only() -> None:
    revision = (
        Path(__file__).parents[2] / "migrations" / "versions" / "0007_generated_mock_connector.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "0007"' in revision
    assert 'down_revision: str | None = "0006"' in revision
    assert "education_erp.persistence" not in revision
    assert "Base.metadata" not in revision
    assert revision.count("op.create_table(") == 11
    assert "kind = 'generated_mock_v1'" in revision
    assert "disabled_in_sprint4" in revision


def test_revision_0008_is_additive_self_contained_and_demo_only() -> None:
    revision = (
        Path(__file__).parents[2]
        / "migrations"
        / "versions"
        / "0008_synthetic_reference_demo_connector.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "0008"' in revision
    assert 'down_revision: str | None = "0007"' in revision
    assert "education_erp.persistence" not in revision
    assert "Base.metadata" not in revision
    assert revision.count("op.create_table(") == 2
    assert "synthetic_reference_erp_v1" in revision
    assert "in_process_csv_test_double" in revision
    assert "network_egress = false" in revision
    assert "credential_reference IS NULL" in revision
