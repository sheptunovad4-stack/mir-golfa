import json

import pytest

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


class FakeResponse:
    status_code = 200
    url = "https://example.org/"
    is_redirect = False
    is_permanent_redirect = False
    encoding = "ISO-8859-1"
    headers = {"Content-Type": "text/html"}

    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def close(self):
        pass

    def iter_content(self, size):
        yield self.body


class FakeSession:
    def __init__(self, body=b"<title>ok</title>"):
        self.body = body

    def get(self, *args, **kwargs):
        return FakeResponse(self.body)

    def close(self):
        pass


@pytest.mark.parametrize("encoding", ["utf-8", "windows-1251"])
def test_cyrillic_without_header_charset(encoding, monkeypatch):
    html = f'<meta charset="{encoding}"><title>Турнир по гольфу</title>'
    monkeypatch.setattr(monitor, "allowed_by_robots", lambda *args: True)
    _, text = monitor.fetch_html(FakeSession(html.encode(encoding)), "https://example.org/")
    assert text == html


def test_invalid_url_does_not_stop_run(tmp_path, monkeypatch):
    path = tmp_path / "sources.json"
    path.write_text(json.dumps([{"id": "good", "url": "https://example.org/"},
                                {"id": "bad", "url": "example.org"}]), encoding="utf-8")
    monkeypatch.setattr(monitor, "SOURCE_FILE", path)
    monkeypatch.setattr(monitor, "DB_PATH", tmp_path / "monitor.sqlite3")
    monkeypatch.setattr(monitor, "allowed_by_robots", lambda *args: True)
    monkeypatch.setattr(monitor, "make_session", FakeSession)
    report = monitor.run_all()
    assert (report["ok"], report["errors"]) == (1, 1)
