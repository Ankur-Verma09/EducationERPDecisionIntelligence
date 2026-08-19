import hashlib
from pathlib import Path

BASELINE = {
    "0001_foundation_baseline.py": (
        "29D75FA384C2B53820B00C125FD9748C6CA125CD451043038EABD0CC7ECF6F9E"
    ),
    "0002_identity_and_tenancy.py": (
        "4EEDCCFD9895C496E1CB4AD16AD40B7D93BBE82E87C5BDCFDA7C36A61AEF6455"
    ),
    "0003_phase2_control_completion.py": (
        "303BAF29A9C98F82B09C5E2C615E3E354E1DE7AA17DB5CB951C9191615B1684D"
    ),
    "0004_role_assignment_concurrency.py": (
        "BC6BC3BB86651D223681F7AEA366108A03FDB59D93F0434910EB665AFF5BC8C5"
    ),
    "0005_canonical_education_model.py": (
        "D27EE80670181F73870116F25D66B89C63A1CFF6F0F9CADC125E92379989AD39"
    ),
    "0006_event_foundation.py": (
        "DFD2DF3CC7E0B53B7DFB068D6C79F5EDE78D808B191E3B85A2FDAFB53464FC00"
    ),
    "0007_generated_mock_connector.py": (
        "FD9EF6DC3D06FF2D969298BABD8039DBCF17A1FD26EF0FBDBDDFCD5A05B79388"
    ),
    "0008_synthetic_reference_demo_connector.py": (
        "8C1ADE9A34DC61F05B99787CE25FB91BD042E8CFACCF4094EA8AD0777A49A6C0"
    ),
}


def test_accepted_migrations_match_forward_immutability_baseline() -> None:
    root = Path(__file__).resolve().parents[2] / "migrations" / "versions"
    assert {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest().upper() for name in BASELINE
    } == BASELINE
