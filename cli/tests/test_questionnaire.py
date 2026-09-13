"""CFG-8: at most eleven items; defaults from registry; validation."""
import pytest

from devcli import questionnaire
from devcli.errors import DevError


def test_at_most_eleven_items():
    assert len(questionnaire.items()) <= 11


def test_non_interactive_defaults_everything_it_can():
    a = questionnaire.run("flask", "as2", {"name": "demo-app", "purpose": "demo"}, interactive=False)
    assert a["host"] == "as2"
    assert a["branches"] == ["dev", "cert", "main"]
    assert a["type"] == "flask-web"
    assert a["data_sources"] == []


def test_unknown_target_is_rejected():
    with pytest.raises(DevError) as e:
        questionnaire.run("flask", "nowhere", {"name": "demo-app", "purpose": "demo"}, interactive=False)
    assert "unknown hosting target" in str(e.value)


def test_bad_name_is_rejected():
    with pytest.raises(DevError):
        questionnaire.run("flask", "as2", {"name": "Bad Name", "purpose": "demo"}, interactive=False)


def test_data_source_strings_become_objects():
    a = questionnaire.run("flask", "as2", {"name": "demo-app", "purpose": "d", "data_sources": ["qa-ops:read-only"]}, interactive=False)
    assert a["data_sources"] == [{"name": "qa-ops", "access": "read-only"}]
