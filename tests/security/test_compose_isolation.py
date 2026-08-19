from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]


def test_compose_profiles_networks_resources_and_credentials_are_isolated() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]
    api = services["api"]
    ai = services["ai-contract-test-double"]

    assert api["profiles"] == ["core"]
    assert ai["profiles"] == ["ai"]
    assert "core_data" in api["networks"]
    assert "core_data" not in ai["networks"]
    assert "EDUERP_DATABASE_URL" not in ai.get("environment", {})
    assert "ports" not in ai
    assert ai["environment"]["AI_EXTERNAL_PROVIDER_ACCESS"] == "disabled"
    assert ai["mem_limit"] and ai["cpus"]
    assert api["mem_limit"] and api["cpus"]
    assert compose["networks"]["core_data"]["internal"] is True
    assert compose["networks"]["ai_internal"]["internal"] is True


def test_model_weights_and_private_datasets_are_ignored() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("*.gguf", "*.safetensors", "evaluation/datasets/private/"):
        assert pattern in ignored
