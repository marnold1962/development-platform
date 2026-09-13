"""CFG-4, CFG-5, REG-1: schemas exist, registries validate, bad files name the field."""
import yaml
import pytest

from devcli import config
from devcli.errors import DevError


def test_every_registry_has_a_schema_and_validates(platform_root):
    assert config.validate_all_registries() == config.REGISTRY_FILES
    for name in config.REGISTRY_FILES:
        assert (platform_root / "registries" / "schema" / f"{name}.schema.json").exists()
    for name in ("profile", "target"):
        assert (platform_root / "registries" / "schema" / f"{name}.schema.json").exists()


def test_invalid_profile_names_the_field(tmp_path):
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "profile.yaml").write_text(yaml.safe_dump({
        "name": "ok-name", "purpose": "x", "type": "flask-web", "stack": ["python"], "data_sources": []
        # platform_version missing
    }))
    with pytest.raises(DevError) as e:
        config.load_profile(tmp_path)
    assert "platform_version" in str(e.value)
    assert e.value.code == 2


def test_service_target_requires_host_and_environments(tmp_path):
    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy" / "target.yml").write_text(yaml.safe_dump({"kind": "service", "identity": "as2"}))
    with pytest.raises(DevError) as e:
        config.load_target(tmp_path)
    assert "host" in str(e.value) or "environments" in str(e.value)


def test_target_rejects_credential_like_keys(tmp_path):
    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy" / "target.yml").write_text(yaml.safe_dump({
        "kind": "desktop", "identity": "as2", "password": "x"}))
    with pytest.raises(DevError) as e:
        config.load_target(tmp_path)
    assert "password" in str(e.value)
