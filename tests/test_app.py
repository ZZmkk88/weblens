"""Automated tests for weblens. Run: .venv/bin/python -m pytest tests/ -q"""
import json
import os
import sqlite3
import tempfile
import uuid

import pytest

_tmp = tempfile.mkdtemp(prefix="weblens-test-")
os.environ["WEBLENS_DB_PATH"] = os.path.join(_tmp, "test.db")
os.environ["WL_INITIAL_USERNAME"] = "admin"
os.environ["WL_INITIAL_PASSWORD"] = "admin123"
os.environ["WEBLENS_UV_SALT"] = "weblens-test-only-salt"

import app as appmod  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

CHROME_WIN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
EDGE_WIN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
)
FIREFOX_LINUX = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)
CHROME_ANDROID = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


@pytest.fixture(scope="module")
def client():
    with TestClient(appmod.app) as c:
        yield c


def do_login(client, password="admin123"):
    res = client.post("/api/login", json={"username": "admin", "password": password})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.fixture(scope="module")
def auth(client):
    data = do_login(client)
    return {"Authorization": f"Bearer {data['token']}"}


def mk_site(client, auth, name, domain):
    res = client.post("/api/sites", json={"name": name, "domain": domain}, headers=auth)
    assert res.status_code == 200, res.text
    return res.json()


def collect(client, public_id, path="/", referrer="", ip="203.0.113.1",
            ua=CHROME_WIN, as_text=False):
    payload = {
        "site_id": public_id,
        "url": f"https://example.com{path}",
        "referrer": referrer,
    }
    headers = {"User-Agent": ua, "X-Forwarded-For": ip}
    if as_text:
        headers["Content-Type"] = "text/plain;charset=UTF-8"
        return client.post("/api/collect", content=json.dumps(payload), headers=headers)
    return client.post("/api/collect", json=payload, headers=headers)


def get_stats(client, auth, site_id, range_value="today"):
    res = client.get(
        f"/api/sites/{site_id}/stats", params={"range": range_value}, headers=auth
    )
    assert res.status_code == 200, res.text
    return res.json()


def db_rows(query, params=()):
    conn = sqlite3.connect(appmod.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


# ------------------------------------------------------------------ auth ----

def test_login_wrong_password(client):
    res = client.post("/api/login", json={"username": "admin", "password": "nope"})
    assert res.status_code == 401


def test_login_ok_and_must_change(client):
    data = do_login(client)
    assert data["token"]
    assert data["username"] == "admin"
    assert data["must_change_password"] is True


def test_unauthenticated_rejected(client):
    assert client.get("/api/sites").status_code == 401
    assert client.post("/api/sites", json={"name": "x", "domain": "x.com"}).status_code == 401
    assert client.get("/api/sites/1/stats").status_code == 401
    assert client.get("/api/sites/1/snippet").status_code == 401


def test_change_password_round_trip(client, auth):
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "newpass456"},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    assert do_login(client, "newpass456")["must_change_password"] is False
    token2 = do_login(client, "newpass456")["token"]
    res = client.post(
        "/api/change-password",
        json={"old_password": "newpass456", "new_password": "admin123"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 200


# ----------------------------------------------------------------- sites ----

def test_create_site_normalizes_domain_and_builds_snippet(client, auth):
    site = mk_site(client, auth, "官网", "https://www.example.com/landing?x=1")
    assert site["domain"] == "example.com"
    assert len(site["site_id"]) == 36
    uuid.UUID(site["site_id"])
    assert site["pageviews"] == 0
    assert "/tracker.js" in site["snippet"]
    assert f'data-weblens-id="{site["site_id"]}"' in site["snippet"]


def test_create_site_validation_errors(client, auth):
    res = client.post(
        "/api/sites", json={"name": "  ", "domain": "example.com"}, headers=auth
    )
    assert res.status_code == 400
    res = client.post(
        "/api/sites", json={"name": "坏域名", "domain": "not a domain"}, headers=auth
    )
    assert res.status_code == 400
    res = client.post(
        "/api/sites", json={"name": "坏协议", "domain": "ftp://example.com"}, headers=auth
    )
    assert res.status_code == 400
    res = client.post("/api/sites", json={"name": "缺字段"}, headers=auth)
    assert res.status_code == 422


def test_list_and_get_site(client, auth):
    site = mk_site(client, auth, "文档站", "docs.example.org")
    listed = client.get("/api/sites", headers=auth).json()
    assert any(item["id"] == site["id"] for item in listed)
    got = client.get(f"/api/sites/{site['id']}", headers=auth)
    assert got.status_code == 200
    assert got.json()["name"] == "文档站"
    snippet = client.get(f"/api/sites/{site['id']}/snippet", headers=auth)
    assert snippet.status_code == 200
    assert snippet.json()["site_id"] == site["site_id"]


def test_update_site(client, auth):
    site = mk_site(client, auth, "旧名", "old.example.net")
    res = client.put(
        f"/api/sites/{site['id']}",
        json={"name": "新名", "domain": "https://new.example.net/path"},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    assert res.json()["name"] == "新名"
    assert res.json()["domain"] == "new.example.net"


def test_missing_site_returns_404(client, auth):
    assert client.get("/api/sites/999999", headers=auth).status_code == 404
    assert client.put(
        "/api/sites/999999", json={"name": "x"}, headers=auth
    ).status_code == 404
    assert client.delete("/api/sites/999999", headers=auth).status_code == 404
    assert client.get(
        "/api/sites/999999/stats", headers=auth
    ).status_code == 404


# --------------------------------------------------------------- collect ----

def test_collect_missing_site_id_rejected(client):
    res = client.post("/api/collect", json={"url": "/pricing"})
    assert res.status_code == 400


def test_collect_unknown_site_404(client):
    res = collect(client, str(uuid.uuid4()), path="/pricing")
    assert res.status_code == 404


def test_collect_invalid_url_rejected(client, auth):
    site = mk_site(client, auth, "校验站", "validate.example.com")
    res = client.post(
        "/api/collect",
        json={"site_id": site["site_id"], "url": "javascript:alert(1)"},
        headers={"User-Agent": CHROME_WIN},
    )
    assert res.status_code == 400


def test_collect_stores_only_reduced_data(client, auth):
    site = mk_site(client, auth, "隐私站", "privacy.example.com")
    ip = "203.0.113.77"
    res = collect(
        client,
        site["site_id"],
        path="/pricing?utm_source=test",
        referrer="https://www.google.com/search?q=secret",
        ip=ip,
        ua=CHROME_WIN,
    )
    assert res.status_code == 201, res.text
    assert res.json()["page_path"] == "/pricing"
    rows = db_rows("SELECT * FROM pageviews WHERE site_id = ?", (site["id"],))
    assert len(rows) == 1
    row = rows[0]
    assert row["page_path"] == "/pricing"
    assert row["referrer_domain"] == "google.com"
    assert row["browser"] == "Chrome"
    assert row["os"] == "Windows"
    assert row["device"] == "桌面"
    assert len(row["visitor_hash"]) == 64
    assert ip not in [str(value) for value in row]
    assert "google.com/search" not in [str(value) for value in row]


def test_collect_accepts_text_plain_beacon_body(client, auth):
    site = mk_site(client, auth, "Beacon站", "beacon.example.com")
    res = collect(client, site["site_id"], path="/beacon", as_text=True)
    assert res.status_code == 201, res.text
    stats = get_stats(client, auth, site["id"], "today")
    assert stats["totals"] == {"pv": 1, "uv": 1}


def test_self_referrer_is_not_counted_as_source(client, auth):
    site = mk_site(client, auth, "自引用站", "self.example.com")
    res = collect(
        client,
        site["site_id"],
        path="/next",
        referrer="https://self.example.com/previous",
    )
    assert res.status_code == 201
    rows = db_rows("SELECT * FROM pageviews WHERE site_id = ?", (site["id"],))
    assert rows[0]["referrer_domain"] == ""
    stats = get_stats(client, auth, site["id"], "today")
    assert stats["top_referrers"] == []


# ----------------------------------------------------------------- stats ----

def test_stats_totals_trends_and_tops(client, auth):
    site = mk_site(client, auth, "统计站", "stats.example.com")
    public_id = site["site_id"]
    # Visitor A: three pageviews. PV grows, UV stays one for this visitor.
    for path in ("/pricing", "/pricing", "/features"):
        res = collect(
            client,
            public_id,
            path=path,
            referrer="https://www.google.com/search",
            ip="203.0.113.10",
            ua=CHROME_WIN,
        )
        assert res.status_code == 201, res.text
    # Visitor B: one pageview from another IP and another UA class.
    res = collect(
        client,
        public_id,
        path="/pricing",
        referrer="https://www.bing.com/search",
        ip="203.0.113.11",
        ua=SAFARI_IPHONE,
    )
    assert res.status_code == 201, res.text

    today = get_stats(client, auth, site["id"], "today")
    assert today["totals"] == {"pv": 4, "uv": 2}
    assert today["trend"] == [
        {"date": today["period"]["end_date"], "pv": 4, "uv": 2}
    ]
    assert [(x["path"], x["count"]) for x in today["top_pages"]] == [
        ("/pricing", 3),
        ("/features", 1),
    ]
    assert [(x["domain"], x["count"]) for x in today["top_referrers"]] == [
        ("google.com", 3),
        ("bing.com", 1),
    ]

    week = get_stats(client, auth, site["id"], "7d")
    assert len(week["trend"]) == 7
    assert sum(day["pv"] for day in week["trend"]) == 4
    assert sum(day["uv"] for day in week["trend"]) == 2

    month = get_stats(client, auth, site["id"], "30d")
    assert len(month["trend"]) == 30
    assert sum(day["pv"] for day in month["trend"]) == 4


def test_stats_invalid_range_rejected(client, auth):
    site = mk_site(client, auth, "范围站", "range.example.com")
    res = client.get(
        f"/api/sites/{site['id']}/stats", params={"range": "365d"}, headers=auth
    )
    assert res.status_code == 400


@pytest.mark.parametrize(
    "ua,expected",
    [
        (CHROME_WIN, {"browser": "Chrome", "os": "Windows", "device": "桌面"}),
        (EDGE_WIN, {"browser": "Edge", "os": "Windows", "device": "桌面"}),
        (FIREFOX_LINUX, {"browser": "Firefox", "os": "Linux", "device": "桌面"}),
        (SAFARI_IPHONE, {"browser": "Safari", "os": "iOS", "device": "移动设备"}),
        (CHROME_ANDROID, {"browser": "Chrome", "os": "Android", "device": "移动设备"}),
        (GOOGLEBOT, {"browser": "机器人", "os": "其他", "device": "机器人"}),
    ],
)
def test_ua_classification_cases(ua, expected):
    assert appmod.classify_user_agent(ua) == expected


def test_homepage_and_tracker_script(client):
    home = client.get("/")
    assert home.status_code == 200
    assert "weblens" in home.text
    tracker = client.get("/tracker.js")
    assert tracker.status_code == 200
    assert "data-weblens-id" in tracker.text
    assert "/api/collect" in tracker.text


def test_delete_site_cascades_pageviews(client, auth):
    site = mk_site(client, auth, "待删站", "delete.example.com")
    res = collect(client, site["site_id"], path="/gone")
    assert res.status_code == 201
    res = client.delete(f"/api/sites/{site['id']}", headers=auth)
    assert res.status_code == 200
    assert client.get(f"/api/sites/{site['id']}", headers=auth).status_code == 404
    rows = db_rows("SELECT * FROM pageviews WHERE site_id = ?", (site["id"],))
    assert rows == []
