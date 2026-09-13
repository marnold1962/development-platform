"""scripts/inventory/collect.py parsers: cron masking, env name/len only, roots from argv.

The collector is stdlib-only and is not a package; it is loaded by path.
"""
import importlib.util
import sys

import pytest


@pytest.fixture
def collect(platform_root):
    path = platform_root / "scripts" / "inventory" / "collect.py"
    spec = importlib.util.spec_from_file_location("inventory_collect", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- cron masking


def test_cron_assignment_is_masked_with_value_length(collect):
    assert collect.mask_cron_line("API_TOKEN=abcd1234") == "API_TOKEN=<masked, len 8>"
    assert "abcd1234" not in collect.mask_cron_line("API_TOKEN=abcd1234")


def test_cron_command_line_is_verbatim(collect):
    cmd = "0 5 * * * /usr/local/bin/backup.sh --full"
    assert collect.mask_cron_line(cmd) == cmd
    at = "@reboot /home/matt/start.sh"
    assert collect.mask_cron_line(at) == at


def test_cron_quoted_value_length_excludes_quotes(collect):
    assert collect.mask_cron_line('API_TOKEN="abcd1234"') == "API_TOKEN=<masked, len 8>"
    assert collect.mask_cron_line("API_TOKEN='abcd1234'") == "API_TOKEN=<masked, len 8>"
    assert collect.mask_cron_line("  PATH = '/usr/bin:/bin'  ") == "PATH=<masked, len 13>"


def test_cron_lines_masks_assignments_keeps_commands_drops_comments(collect):
    text = "\n".join([
        "# comment",
        "SHELL=/bin/sh",
        "MAILTO=\"matt@example.com\"",
        "",
        "*/5 * * * * /usr/bin/x FOO=bar",
        "0 5 * * * root /usr/bin/y",
    ])
    assert collect.cron_lines(text) == [
        "SHELL=<masked, len 7>",
        "MAILTO=<masked, len 16>",
        "*/5 * * * * /usr/bin/x FOO=bar",
        "0 5 * * * root /usr/bin/y",
    ]
    assert "matt@example.com" not in "".join(collect.cron_lines(text))


# ---------------------------------------------------------------- env name/len


def test_env_name_len_reports_only_name_and_len(collect):
    out = collect.env_name_len(["DATABASE_URL=postgresql://user:pass@x/y", "EMPTY=", "NOEQ", 42])
    assert out == [{"name": "DATABASE_URL", "len": 26}, {"name": "EMPTY", "len": 0}, {"name": "NOEQ", "len": 0}]
    for v in out:
        assert set(v) == {"name", "len"}
    assert "user:pass" not in repr(out)


def test_parse_env_file_reports_only_name_and_len(collect):
    text = "\n".join([
        "# a comment",
        "export SECRET_KEY='s3cr3t'",
        'DATABASE_URL="postgresql://user:pass@x/y"',
        "PLAIN=abc",
        "not a var",
    ])
    out = collect.parse_env_file(text)
    assert out == [{"name": "SECRET_KEY", "len": 6}, {"name": "DATABASE_URL", "len": 26}, {"name": "PLAIN", "len": 3}]
    for v in out:
        assert set(v) == {"name", "len"}
    assert "s3cr3t" not in repr(out) and "user:pass" not in repr(out)


# ---------------------------------------------------------------- roots from argv


def test_resolve_roots_takes_argv(collect):
    assert collect.resolve_roots(["/tmp/x"]) == ["/tmp/x"]
    assert collect.resolve_roots(["/tmp/x", "/tmp/y"]) == ["/tmp/x", "/tmp/y"]


def test_resolve_roots_falls_back_to_home(collect, monkeypatch):
    monkeypatch.setenv("HOME", "/home/someone")
    assert collect.resolve_roots([]) == ["/home/someone"]
    assert collect.resolve_roots(None) == ["/home/someone"]


def test_env_file_globs_are_bounded_and_per_root(collect):
    pats = collect.env_file_globs(["/tmp/x"])
    assert "/tmp/x/*/*.env*" in pats
    assert "/tmp/x/*/.env*" in pats
    assert "/tmp/x/*/*/*/.env*" in pats
    assert "/tmp/x/*/*/*/*/.env*" not in pats
    assert not any("**" in p for p in pats)
    assert all(p.startswith("/tmp/x/") for p in pats)


def test_collect_env_files_skips_examples_and_backups(collect, tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / ".env").write_text("TOKEN=abcdef\n")
    (app / ".env.example").write_text("TOKEN=\n")
    (app / ".env.orig").write_text("TOKEN=zzz\n")
    (app / ".env.bak").write_text("TOKEN=zzz\n")
    out = collect.collect_env_files(collect.env_file_globs([str(tmp_path)]))
    assert [f["path"] for f in out] == [str(app / ".env")]
    assert out[0]["vars"] == [{"name": "TOKEN", "len": 6}]
    assert "abcdef" not in repr(out)
