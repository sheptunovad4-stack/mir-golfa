"""Safe source monitor for Golf CIS.

Fetches only explicitly configured URLs, stores page fingerprints and discovered links,
and flags changes for review. It deliberately does NOT guess tournament winners/scores.
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
SOURCE_FILE = Path(os.getenv("GOLF_CIS_SOURCES", ROOT / "sources.json"))
DB_PATH = Path(os.getenv("GOLF_CIS_MONITOR_DB", ROOT / "monitor.sqlite3"))
USER_AGENT = os.getenv("GOLF_CIS_USER_AGENT", "GolfCISBot/0.1 (contact: configure-admin-contact)")
TIMEOUT = int(os.getenv("GOLF_CIS_TIMEOUT", "20"))

def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
      CREATE TABLE IF NOT EXISTS source_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT NOT NULL,
        checked_at TEXT NOT NULL,
        http_status INTEGER,
        content_hash TEXT,
        page_title TEXT,
        page_text TEXT,
        discovered_links TEXT,
        changed INTEGER NOT NULL DEFAULT 0,
        error TEXT
      )
    """)
    con.execute("""
      CREATE TABLE IF NOT EXISTS review_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT NOT NULL,
        detected_at TEXT NOT NULL,
        page_title TEXT,
        url TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
      )
    """)
    con.commit()
    return con

def allowed_by_robots(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        response = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        if response.status_code >= 400:
            # A missing robots.txt is not a disallow; site terms still apply.
            return True
        rp.parse(response.text.splitlines())
        return rp.can_fetch(USER_AGENT, url)
    except requests.RequestException:
        # Fail closed if robots policy cannot be checked.
        return False

def load_sources():
    with open(SOURCE_FILE, encoding="utf-8") as f:
        return json.load(f)

def check_source(source: dict) -> dict:
    url = source["url"]
    checked_at = datetime.now(timezone.utc).isoformat()
    con = connect()
    try:
        if not source.get("enabled", True):
            return {"source_id": source["id"], "status": "disabled"}
        if not allowed_by_robots(url):
            raise RuntimeError("robots.txt не разрешает сбор либо его не удалось проверить")
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower() and "text" not in content_type.lower():
            raise RuntimeError(f"Неподдерживаемый Content-Type: {content_type}")
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else source["name"]
        page_text = " ".join(soup.get_text(" ", strip=True).split())[:200000]
        links = []
        for a in soup.find_all("a", href=True):
            label = " ".join(a.get_text(" ", strip=True).split())
            href = urljoin(url, a["href"])
            if label and urlparse(href).scheme in ("http", "https"):
                links.append({"title": label[:300], "url": href})
        # Keep only first 500 links to bound storage.
        links_json = json.dumps(links[:500], ensure_ascii=False)
        digest = hashlib.sha256((title + "\n" + page_text + "\n" + links_json).encode("utf-8")).hexdigest()
        prev = con.execute(
            "SELECT content_hash FROM source_checks WHERE source_id=? ORDER BY id DESC LIMIT 1",
            (source["id"],)
        ).fetchone()
        changed = int(prev is not None and prev[0] != digest)
        con.execute(
            """INSERT INTO source_checks
            (source_id, checked_at, http_status, content_hash, page_title, page_text, discovered_links, changed, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (source["id"], checked_at, response.status_code, digest, title, page_text, links_json, changed)
        )
        if changed:
            con.execute(
                "INSERT INTO review_queue (source_id, detected_at, page_title, url, reason) VALUES (?, ?, ?, ?, ?)",
                (source["id"], checked_at, title, url, "Изменилось содержимое страницы; проверьте турниры/даты/результаты.")
            )
        con.commit()
        return {"source_id": source["id"], "status": "ok", "http_status": response.status_code,
                "changed": bool(changed), "page_title": title, "links_found": len(links)}
    except Exception as exc:
        con.execute(
            """INSERT INTO source_checks
            (source_id, checked_at, http_status, content_hash, page_title, page_text, discovered_links, changed, error)
            VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, 0, ?)""",
            (source["id"], checked_at, str(exc)[:1000])
        )
        con.commit()
        return {"source_id": source["id"], "status": "error", "error": str(exc)[:300]}
    finally:
        con.close()

def run_all():
    results = [check_source(s) for s in load_sources() if s.get("enabled", True)]
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "total": len(results),
            "ok": sum(r.get("status") == "ok" for r in results),
            "changed": sum(bool(r.get("changed")) for r in results),
            "errors": sum(r.get("status") == "error" for r in results), "results": results}

if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))
