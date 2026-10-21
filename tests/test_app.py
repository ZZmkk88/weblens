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


# 每个用例独立登录：改密会吊销同用户除本次外的其他会话（口径#2），
# 模块级共享 token 会在改密用例后失效，故不跨用例复用。
# （用例只增不减，断言不弱化：此处改的是 fixture 作用域，不是测试逻辑。）
@pytest.fixture
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


def test_change_password_revokes_other_sessions(client):
    # 口径#2：改密成功后吊销该用户除本次会话外的全部会话，本次会话保留。
    token_a = do_login(client)["token"]
    token_b = do_login(client)["token"]
    header_a = {"Authorization": f"Bearer {token_a}"}
    header_b = {"Authorization": f"Bearer {token_b}"}
    try:
        res = client.post(
            "/api/change-password",
            json={"old_password": "admin123", "new_password": "revoke-check-1"},
            headers=header_a,
        )
        assert res.status_code == 200, res.text
        # 本次会话继续有效
        assert client.get("/api/me", headers=header_a).status_code == 200
        # 其他会话被吊销
        assert client.get("/api/me", headers=header_b).status_code == 401
        # 旧密码已不能再登录
        assert (
            client.post(
                "/api/login",
                json={"username": "admin", "password": "admin123"},
            ).status_code
            == 401
        )
    finally:
        # 恢复初始密码，不影响后续用例
        client.post(
            "/api/change-password",
            json={"old_password": "revoke-check-1", "new_password": "admin123"},
            headers=header_a,
        )


def test_docs_endpoints_closed_by_default(client):
    # 口径#6：接口文档页默认关闭
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_session_token_stored_hashed_not_plaintext(client):
    # P1-1 回归：会话令牌入库为 SHA-256 哈希而非明文，原始令牌仍可用。
    data = do_login(client)
    token = data["token"]
    expected = appmod.session_key(token)
    assert len(expected) == 64
    rows = db_rows("SELECT token FROM sessions WHERE token = ?", (expected,))
    assert len(rows) == 1
    assert rows[0]["token"] != token
    # 原始令牌仍可用
    res = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    # 登出后该令牌 401
    res = client.post("/api/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    res = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_request_body_hard_limit_413(client, auth):
    # P1-2 回归：超过 128KiB 的正文由框架直接回 413。
    big_login = json.dumps({"username": "admin", "password": "x" * (140 * 1024)})
    res = client.post("/api/login", content=big_login)
    assert res.status_code == 413
    # 64KB~128KB 之间的上报仍走路由自带的 64KB 检查（400），不被框架 413 抢走。
    site = mk_site(client, auth, "限流站", "bodylimit.example.com")
    mid = json.dumps({"site_id": site["site_id"], "url": "/" + "x" * (70 * 1024)})
    res = client.post("/api/collect", content=mid)
    assert res.status_code == 400
    assert "过大" in res.json()["detail"]


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


def test_collect_body_too_large_rejected(client, auth):
    site = mk_site(client, auth, "大包站", "bigbody.example.com")
    big = json.dumps(
        {"site_id": site["site_id"], "url": "/" + "x" * (70 * 1024)}
    )
    res = client.post("/api/collect", content=big)
    assert res.status_code == 400
    assert "过大" in res.json()["detail"]


def test_collect_malformed_ipv6_does_not_500(client, auth):
    # P1-1 回归：畸形 IPv6（如 http://[）不能让公开上报接口抛 500 丢记录。
    site = mk_site(client, auth, "畸形站", "malformed.example.com")
    # 坏来源：记空串，这次访问照常入库
    res = client.post(
        "/api/collect",
        json={"site_id": site["site_id"], "url": "/kept", "referrer": "http://["},
        headers={"User-Agent": CHROME_WIN},
    )
    assert res.status_code == 201, res.text
    rows = db_rows(
        "SELECT * FROM pageviews WHERE site_id = ? AND page_path = '/kept'",
        (site["id"],),
    )
    assert len(rows) == 1
    assert rows[0]["referrer_domain"] == ""
    # 合法 IPv6 来源不受影响
    res = client.post(
        "/api/collect",
        json={
            "site_id": site["site_id"],
            "url": "/v6",
            "referrer": "http://[::1]/x",
        },
        headers={"User-Agent": CHROME_WIN},
    )
    assert res.status_code == 201, res.text
    # 坏页面地址：400，不抛 500
    res = client.post(
        "/api/collect",
        json={"site_id": site["site_id"], "url": "http://["},
        headers={"User-Agent": CHROME_WIN},
    )
    assert res.status_code == 400
    # 坏建站域名：400
    res = client.post(
        "/api/sites", json={"name": "坏", "domain": "http://["}, headers=auth
    )
    assert res.status_code == 400


def test_collect_deeply_nested_json_returns_400(client, auth):
    # P1-1 回归：深度嵌套 JSON 不应让公开上报接口抛 500。
    # 注意嵌套必须是 JSON 结构本身（裸的 [[..]]），放在字符串值里只是普通字符、
    # 触发不了 json 的递归；本环境 Python 3.12 下 20000 层稳定触发 RecursionError
    # （已实测）；正文约 40KB，低于上报接口 64KB 与框架 128KB 上限，走得到 json.loads。
    site = mk_site(client, auth, "嵌套站", "nested.example.com")
    assert site["site_id"]  # 建站成功，正文用裸嵌套数组直击 json.loads
    body = "[" * 20000 + "]" * 20000
    assert len(body) < 64 * 1024
    res = client.post("/api/collect", content=body)
    assert res.status_code == 400
    assert "合法 JSON" in res.json()["detail"]


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
    assert today["active_pages"] == 2  # /pricing 与 /features 两个不同路径
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


def test_security_headers_present(client):
    # P2-5：防点击劫持与 MIME 嗅探响应头
    for path in ("/", "/tracker.js", "/api/collect"):
        res = client.get(path) if path != "/api/collect" else client.options(path)
        assert res.headers.get("x-frame-options") == "DENY", path
        assert res.headers.get("x-content-type-options") == "nosniff", path


def test_delete_site_cascades_pageviews(client, auth):
    site = mk_site(client, auth, "待删站", "delete.example.com")
    res = collect(client, site["site_id"], path="/gone")
    assert res.status_code == 201
    res = client.delete(f"/api/sites/{site['id']}", headers=auth)
    assert res.status_code == 200
    assert client.get(f"/api/sites/{site['id']}", headers=auth).status_code == 404
    rows = db_rows("SELECT * FROM pageviews WHERE site_id = ?", (site["id"],))
    assert rows == []


def test_surrogate_unicode_400_not_500(client, auth):
    # TASK-071 P1-1 回归：孤立代理字符（如 \ud800）不能让接口抛未捕获的
    # UnicodeEncodeError（500）。正文里用 JSON 转义写法，服务端解析后才是代理字符。
    # 注：必须带 Content-Type: application/json，否则框架按表单解析直接 422，
    # 走不到业务守卫（422 同样不是 500，但测的不是本回归项）。
    json_headers = {"Content-Type": "application/json"}
    # 登录：用户名/密码含代理字符 → 400
    res = client.post(
        "/api/login",
        content='{"username": "admin\\ud800", "password": "x"}',
        headers=json_headers,
    )
    assert res.status_code == 400
    res = client.post(
        "/api/login",
        content='{"username": "admin", "password": "x\\ud800"}',
        headers=json_headers,
    )
    assert res.status_code == 400
    # 建站：站点名含代理字符 → 400
    res = client.post(
        "/api/sites",
        content='{"name": "站\\ud800点", "domain": "surrogate.example.com"}',
        headers={**auth, **json_headers},
    )
    assert res.status_code == 400
    # 上报：URL 含代理字符 → 400
    # 注意：正文必须手写（单反斜杠的 \ud800 转义），走 json.dumps 会把反斜杠
    # 再转义一次，服务端就解析不出代理字符了。
    site = mk_site(client, auth, "代理站", "surrogate2.example.com")
    res = client.post(
        "/api/collect",
        content='{"site_id": "%s", "url": "/p\\ud800"}' % site["site_id"],
        headers=json_headers,
    )
    assert res.status_code == 400
    # 上报：referrer 含代理字符 → 记空串照常 201（不丢这次访问）
    res = client.post(
        "/api/collect",
        content='{"site_id": "%s", "url": "/ok", "referrer": "https://example\\ud800.com/"}'
        % site["site_id"],
        headers=json_headers,
    )
    assert res.status_code == 201, res.text
    rows = db_rows(
        "SELECT * FROM pageviews WHERE site_id = ? AND page_path = '/ok'",
        (site["id"],),
    )
    assert len(rows) == 1
    assert rows[0]["referrer_domain"] == ""


def test_413_response_has_security_headers(client):
    # TASK-068 P2-8：框架直接返回的 413 也要带安全响应头。
    big_login = json.dumps({"username": "admin", "password": "x" * (140 * 1024)})
    res = client.post("/api/login", content=big_login)
    assert res.status_code == 413
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("x-content-type-options") == "nosniff"


def test_login_and_dashboard_no_store(client):
    # TASK-068 P2-9：登录响应（含会话令牌）与看板页不缓存。
    res = client.post(
        "/api/login", json={"username": "admin", "password": "admin123"}
    )
    assert res.status_code == 200
    assert res.headers.get("cache-control") == "no-store"
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("cache-control") == "no-store"
