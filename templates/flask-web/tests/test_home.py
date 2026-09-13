from app.services.greeting import greeting


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_index_full_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"<html" in r.data


def test_index_htmx_fragment(client):
    r = client.get("/", headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert b"<html" not in r.data
    assert b"is running" in r.data


def test_greeting_is_pure():
    assert greeting("x") == "x is running."


def test_forwarded_prefix_sets_script_name(client):
    r = client.get("/platform/dev/demo/healthz", headers={"X-Forwarded-Prefix": "/platform/dev/demo"})
    assert r.status_code == 200
