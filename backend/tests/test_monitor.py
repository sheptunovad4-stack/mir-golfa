import json

from app.collectors import monitor


def test_normalized_url_rejects_non_http():
    try:
        monitor.normalized_url("file:///etc/passwd")
    except ValueError:
        pass
    else:
        raise AssertionError("non-http URL must be rejected")


def test_normalized_url_removes_fragment():
    assert monitor.normalized_url("https://example.com/a#section") == "https://example.com/a"


def test_load_sources_uses_backend_data(tmp_path, monkeypatch):
    path = tmp_path / "sources.json"
    path.write_text(json.dumps([{"id": "x"}]), encoding="utf-8")
    monkeypatch.setattr(monitor, "SOURCE_FILE", path)
    assert monitor.load_sources() == [{"id": "x"}]
