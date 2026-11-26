"""Conservative change monitor for explicitly configured golf sources.

This detects page changes for human review; it does not extract or invent tournament facts.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, UnicodeDammit
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = Path(os.getenv("GOLF_CIS_SOURCES", str(ROOT / "data" / "sources.json")))
DB_PATH = Path(os.getenv("GOLF_CIS_MONITOR_DB", str(ROOT / "data" / "monitor.sqlite3")))
USER_AGENT = os.getenv("GOLF_CIS_USER_AGENT", "GolfCISBot/1.0 (+configure-contact)")
TIMEOUT = float(os.getenv("GOLF_CIS_TIMEOUT", "15"))
MAX_BYTES = int(os.getenv("GOLF_CIS_MAX_BYTES", str(2 * 1024 * 1024)))
REQUEST_DELAY = float(os.getenv("GOLF_CIS_REQUEST_DELAY", "1"))
MAX_REDIRECTS = 5


def normalized_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public http(s) source URLs are allowed")
    return parsed._replace(fragment="").geturl()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS source_checks (
      id INTEGER PRIMARY KEY, source_id TEXT NOT NULL, checked_at TEXT NOT NULL,
      http_status INTEGER, content_hash TEXT, page_title TEXT, page_text TEXT,
      discovered_links TEXT, changed INTEGER NOT NULL DEFAULT 0, error TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_source_checks_source_id_id ON source_checks(source_id, id DESC);
    CREATE TABLE IF NOT EXISTS review_queue (
      id INTEGER PRIMARY KEY, source_id TEXT NOT NULL, detected_at TEXT NOT NULL,
      page_title TEXT, url TEXT NOT NULL, reason TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending'
    );
    CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
    """)
    return con


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, connect=3, read=2, status=3, backoff_factor=0.7,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]), respect_retry_after_header=True)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def allowed_by_robots(session: requests.Session, url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = session.get(robots_url, timeout=TIMEOUT, allow_redirects=True)
        final_host = urlparse(response.url).netloc
        if final_host != parsed.netloc:
            # A robots redirect to another host is not authority for this host.
            return False
        if response.status_code in (404, 410):
            return True
        response.raise_for_status()
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)
    except requests.RequestException:
        return False


def fetch_html(session: requests.Session, url: str) -> tuple[requests.Response, str]:
    current = normalized_url(url)
    for _ in range(MAX_REDIRECTS + 1):
        if not allowed_by_robots(session, current):
            raise RuntimeError("robots.txt запрещает сбор или не удалось проверить правила")
        response = session.get(current, timeout=TIMEOUT, stream=True, allow_redirects=False)
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise RuntimeError("Redirect without Location")
            current = normalized_url(urljoin(current, location))
            continue
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if "html" not in content_type and "text/" not in content_type:
            response.close()
            raise RuntimeError(f"Unsupported Content-Type: {content_type or 'missing'}")
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            if not chunk:
                continue
            size += len(chunk)
            if size > MAX_BYTES:
                response.close()
                raise RuntimeError(f"Response exceeds {MAX_BYTES} byte limit")
            chunks.append(chunk)
        body = b"".join(chunks)
        if "charset=" not in content_type:
            # Без charset в заголовке requests подставляет ISO-8859-1 и портит кириллицу:
            # пробуем UTF-8, затем кодировку, объявленную в самой странице.
            text = UnicodeDammit(body, ["utf-8"], is_html=True).unicode_markup
            if text is not None:
                return response, text
        encoding = response.encoding or "utf-8"
        return response, body.decode(encoding, errors="replace")
    raise RuntimeError("Too many redirects")


def load_sources() -> list[dict]:
    data = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Source registry must be a JSON array")
    return data


def run_all() -> dict:
    sources = [s for s in load_sources() if s.get("enabled", True)]
    grouped: dict[str, list[dict]] = {}
    invalid: list[tuple[dict, str]] = []
    for source in sources:
        try:
            url = normalized_url(source["url"])
        except (KeyError, ValueError) as exc:
            # Ошибка в одной записи реестра не должна останавливать весь запуск.
            invalid.append((source, f"Некорректный URL источника: {exc}"))
            continue
        grouped.setdefault(url, []).append(source)

    results = []
    con = connect()
    session = make_session()
    try:
        for source, error in invalid:
            con.execute("""INSERT INTO source_checks
              (source_id,checked_at,changed,error) VALUES (?,?,0,?)""",
              (source["id"], datetime.now(timezone.utc).isoformat(), error))
            results.append({"source_id": source["id"], "status": "error", "error": error})
        for index, (url, aliases) in enumerate(grouped.items()):
            if index:
                time.sleep(max(0, REQUEST_DELAY))
            checked_at = datetime.now(timezone.utc).isoformat()
            try:
                response, html = fetch_html(session, url)
                soup = BeautifulSoup(html, "html.parser")
                for node in soup(["script", "style", "noscript", "svg"]):
                    node.decompose()
                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                page_text = " ".join(soup.get_text(" ", strip=True).split())[:200000]
                links = []
                for anchor in soup.find_all("a", href=True):
                    label = " ".join(anchor.get_text(" ", strip=True).split())
                    href = urljoin(response.url, anchor["href"])
                    if label and urlparse(href).scheme in ("http", "https"):
                        links.append({"title": label[:300], "url": href})
                links_json = json.dumps(links[:500], ensure_ascii=False)
                digest = hashlib.sha256((title + "\n" + page_text + "\n" + links_json).encode()).hexdigest()
                for source in aliases:
                    previous = con.execute(
                        "SELECT content_hash FROM source_checks WHERE source_id=? ORDER BY id DESC LIMIT 1",
                        (source["id"],)).fetchone()
                    changed = int(previous is not None and previous[0] != digest)
                    con.execute("""INSERT INTO source_checks
                      (source_id,checked_at,http_status,content_hash,page_title,page_text,discovered_links,changed,error)
                      VALUES (?,?,?,?,?,?,?,?,NULL)""",
                      (source["id"], checked_at, response.status_code, digest, title, page_text, links_json, changed))
                    if changed:
                        con.execute("""INSERT INTO review_queue
                          (source_id,detected_at,page_title,url,reason) VALUES (?,?,?,?,?)""",
                          (source["id"], checked_at, title, response.url,
                           "Содержимое источника изменилось; требуется ручная проверка турниров и результатов."))
                    results.append({"source_id": source["id"], "status": "ok",
                                    "http_status": response.status_code, "changed": bool(changed),
                                    "page_title": title, "links_found": len(links)})
            except Exception as exc:
                for source in aliases:
                    con.execute("""INSERT INTO source_checks
                      (source_id,checked_at,changed,error) VALUES (?,?,0,?)""",
                      (source["id"], checked_at, str(exc)[:1000]))
                    results.append({"source_id": source["id"], "status": "error", "error": str(exc)[:300]})
        con.commit()
    finally:
        session.close()
        con.close()
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "total": len(results),
            "ok": sum(x["status"] == "ok" for x in results),
            "changed": sum(bool(x.get("changed")) for x in results),
            "errors": sum(x["status"] == "error" for x in results), "results": results}


if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))
