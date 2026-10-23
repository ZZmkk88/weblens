"""weblens: a lightweight self-hosted website analytics tool.

Create a site, copy one small tracking script into its pages, and read
pageview / unique-visitor totals, daily trends, popular pages and
referrer domains from a single dashboard. Single-file FastAPI backend +
SQLite + one static page. Design notes live in NOTES.md.
"""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.middleware.body_limit import RequestBodyLimitMiddleware

BASE_DIR = Path(__file__).resolve().parent
def resolve_db_path(raw_value: str | None) -> str:
    # 相对路径按 app.py 所在目录解析，不跟进程的当前工作目录走；
    # 否则换目录启动会另建一套带默认口令的新库。
    # （与 README「相对 app.py 所在目录」的声明一致。）
    value = (raw_value or "").strip()
    if not value:
        return str(BASE_DIR / "data" / "weblens.db")
    if os.path.isabs(value):
        return value
    return str(BASE_DIR / value)


DB_PATH = resolve_db_path(os.environ.get("WEBLENS_DB_PATH"))
TOKEN_TTL_SECONDS = 24 * 60 * 60
INITIAL_USERNAME = os.environ.get("WL_INITIAL_USERNAME", "admin")
INITIAL_PASSWORD = os.environ.get("WL_INITIAL_PASSWORD", "admin123")
MAX_SITE_NAME = 80
MAX_DOMAIN_LENGTH = 253
MAX_PAGE_PATH = 1000
MAX_URL_LENGTH = 2048
MAX_COLLECT_BODY = 64 * 1024
# 128KiB 高于上报接口自带的 64KB 检查：超 64KB 的上报仍由路由返回 400，
# 框架层的 413 只拦更大的正文（如登录接口）。
MAX_REQUEST_BODY = 128 * 1024
HOST_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*$"
)


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def is_utf8_text(value: str) -> bool:
    # JSON 允许孤立代理字符进 Python str，但 SQLite / PBKDF2 的 UTF-8 编码会抛
    # UnicodeEncodeError，公开接口上就会变成未捕获的 HTTP 500。
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def hash_password(password: str, salt_hex: str) -> str:
    if not is_utf8_text(password):
        raise HTTPException(status_code=400, detail="密码包含无法编码的字符")
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 200_000
    ).hex()


# 用户不存在时仍走一遍 PBKDF2，避免用响应时间判断用户名是否存在。
# 这组值不对应任何真实账号，只为凑足同样的计算量。
_UNKNOWN_USER_SALT = "00" * 16
_UNKNOWN_USER_HASH = "0" * 64


def password_matches(password: str, salt_hex: str, expected_hex: str) -> bool:
    # 口径#8：敏感比对用 secrets.compare_digest，避免时序侧信道。
    # （hash_password 内的代理字符检查先抛 400，与调用方行为一致。）
    actual = hash_password(password, salt_hex)
    return secrets.compare_digest(actual, expected_hex)


def session_key(token: str) -> str:
    # 会话令牌熵足够（token_urlsafe 32 字节），库里只存 SHA-256，不必再加盐。
    # 接口返回给客户端的仍是原始令牌。
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_host(host: str) -> str:
    host = (host or "").strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_domain_input(value: str) -> str:
    raw = (value or "").strip()
    if not raw or len(raw) > MAX_URL_LENGTH or any(ch.isspace() for ch in raw):
        raise HTTPException(status_code=400, detail="域名为空、过长或包含空白")
    try:
        # urlparse 对畸形 IPv6（如 http://[）抛 ValueError，这里要变成 400。
        if "://" in raw:
            parsed = urllib.parse.urlparse(raw)
            if parsed.scheme not in ("http", "https"):
                raise HTTPException(status_code=400, detail="域名只支持 http/https 地址")
            host = parsed.hostname or ""
        else:
            host = urllib.parse.urlparse("//" + raw).hostname or ""
    except (ValueError, UnicodeError):
        raise HTTPException(status_code=400, detail="域名格式不正确")
    host = normalize_host(host)
    if not host or len(host) > MAX_DOMAIN_LENGTH or not HOST_RE.match(host):
        raise HTTPException(status_code=400, detail="域名格式不正确")
    return host


def domain_from_value(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw or raw.startswith("/"):
        return ""
    try:
        # 公开上报的来源不合法时记空串，避免 urlparse 的 ValueError 变成 500 并丢掉这次访问。
        if "://" in raw or raw.startswith("//"):
            host = urllib.parse.urlparse(raw).hostname or ""
        else:
            host = urllib.parse.urlparse("//" + raw).hostname or ""
    except (ValueError, UnicodeError):
        return ""
    host = normalize_host(host)
    if not is_utf8_text(host):
        return ""
    return host


def parse_page_path(value: str) -> str:
    raw = (value or "").strip() or "/"
    if len(raw) > MAX_URL_LENGTH:
        raise HTTPException(status_code=400, detail="页面地址过长")
    try:
        parsed = urllib.parse.urlparse(raw)
        parsed_host = parsed.hostname
    except (ValueError, UnicodeError):
        raise HTTPException(status_code=400, detail="页面地址格式不正确")
    if parsed.scheme:
        if parsed.scheme not in ("http", "https") or not parsed_host:
            raise HTTPException(status_code=400, detail="页面地址格式不正确")
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    if (
        len(path) > MAX_PAGE_PATH
        or any(ord(ch) < 32 for ch in path)
        or not is_utf8_text(path)
    ):
        raise HTTPException(status_code=400, detail="页面路径不合法")
    return path


def page_hostname(value: str, site_domain: str) -> str:
    try:
        parsed = urllib.parse.urlparse(value or "")
        if parsed.hostname:
            return normalize_host(parsed.hostname)
    except (ValueError, UnicodeError):
        return site_domain
    return site_domain


def classify_user_agent(user_agent: str | None) -> dict:
    ua = user_agent or ""
    low = ua.lower()
    bot_tokens = (
        "bot", "spider", "crawler", "curl/", "wget/", "python-requests",
        "postmanruntime", "headlesschrome",
    )
    is_bot = any(token in low for token in bot_tokens)

    if is_bot:
        browser = "机器人"
    elif "edg/" in low or "edga/" in low or "edgios/" in low:
        browser = "Edge"
    elif "opr/" in low or "opera" in low:
        browser = "Opera"
    elif "samsungbrowser/" in low:
        browser = "Samsung Internet"
    elif "firefox/" in low:
        browser = "Firefox"
    elif "crios/" in low or "chrome/" in low or "chromium/" in low:
        browser = "Chrome"
    elif "safari/" in low:
        browser = "Safari"
    elif "trident/" in low or "msie" in low:
        browser = "Internet Explorer"
    else:
        browser = "其他"

    if "windows" in low:
        os_name = "Windows"
    elif "android" in low:
        os_name = "Android"
    elif "iphone" in low or "ipad" in low or "ipod" in low:
        os_name = "iOS"
    elif "cros" in low:
        os_name = "ChromeOS"
    elif "mac os x" in low or "macintosh" in low:
        os_name = "macOS"
    elif "linux" in low:
        os_name = "Linux"
    else:
        os_name = "其他"

    if is_bot:
        device = "机器人"
    elif "ipad" in low or "tablet" in low:
        device = "平板"
    elif (
        "mobile" in low or "iphone" in low or "ipod" in low
        or "windows phone" in low
    ):
        device = "移动设备"
    else:
        device = "桌面"
    return {"browser": browser, "os": os_name, "device": device}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or "unknown"
    real_ip = request.headers.get("x-real-ip", "")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# database
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_uv_salt(conn: sqlite3.Connection) -> str:
    env_salt = os.environ.get("WEBLENS_UV_SALT", "").strip()
    if env_salt:
        return env_salt
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'uv_salt'"
    ).fetchone()
    if row is not None:
        return row["value"]
    salt = secrets.token_hex(32)
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('uv_salt', ?)", (salt,)
        )
    except sqlite3.IntegrityError:
        # 并发首次写入撞主键：回滚掉失败的 INSERT，读对方已提交的盐。
        conn.rollback()
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'uv_salt'"
        ).fetchone()
        if row is None:
            raise
        return row["value"]
    return salt


def visitor_hash(
    conn: sqlite3.Connection, ip: str, ua_class: dict, view_date: str
) -> str:
    salt = get_uv_salt(conn)
    material = "\x1f".join(
        [salt, ip, ua_class["browser"], ua_class["os"], ua_class["device"], view_date]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                expires_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pageviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
                page_path TEXT NOT NULL,
                referrer_domain TEXT NOT NULL DEFAULT '',
                browser TEXT NOT NULL,
                os TEXT NOT NULL,
                device TEXT NOT NULL,
                visitor_hash TEXT NOT NULL,
                view_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_pageviews_site_date
                ON pageviews(site_id, view_date);
            CREATE INDEX IF NOT EXISTS idx_pageviews_site_path
                ON pageviews(site_id, page_path);
            """
        )
        # 单用户设计：初始账号只在库里没有任何用户时创建一次。
        # 换 WL_INITIAL_USERNAME 不会再追加第二个账号（旧账号依然有效，
        # 如需停用请直接改密码或删库重建）。
        user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if user_count == 0:
            salt = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO users (username, password_hash, salt,"
                " must_change_password, created_at) VALUES (?, ?, ?, 1, ?)",
                (
                    INITIAL_USERNAME,
                    hash_password(INITIAL_PASSWORD, salt),
                    salt,
                    iso(utcnow()),
                ),
            )


# ---------------------------------------------------------------------------
# app + auth
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


# 口径#6：接口文档页默认关闭（/docs、/redoc、/openapi.json 未登录可访问视为问题）
app = FastAPI(
    title="weblens",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


# Cross-origin access is only for the public tracker. Login and the
# dashboard stay same-origin so a random page cannot read them.
COLLECT_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


# 先挂请求体上限：超限正文在到达业务逻辑前就被截断，直接回 413。
app.add_middleware(RequestBodyLimitMiddleware, max_body_size=MAX_REQUEST_BODY)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # 后挂载即在最外层：所有响应（含框架直接返回的 413）都带上安全响应头。
    # 防点击劫持与 MIME 嗅探；看板不设计被嵌套展示。
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class SiteIn(BaseModel):
    name: str
    domain: str


class SiteUpdateIn(BaseModel):
    name: str | None = None
    domain: str | None = None


def current_user(request: Request) -> sqlite3.Row:
    auth = request.headers.get("Authorization", "")
    token = auth[len("Bearer "):].strip() if auth.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token = ? AND s.expires_at > ?",
            (session_key(token), time.time()),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return row


@app.post("/api/login")
def login(body: LoginIn):
    init_db()
    username = body.username.strip()
    if not is_utf8_text(username):
        raise HTTPException(status_code=400, detail="用户名包含无法编码的字符")
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        # 用户不存在时也跑一遍 PBKDF2（哑盐），再返回 401：
        # 否则"用户名不存在"（直接返回）和"密码错误"（跑完 PBKDF2 才返回）
        # 的响应时间差几十毫秒，可被用来枚举有效用户名。
        if user is None:
            password_matches(body.password, _UNKNOWN_USER_SALT, _UNKNOWN_USER_HASH)
            raise HTTPException(status_code=401, detail="用户名或密码不正确")
        if not password_matches(body.password, user["salt"], user["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码不正确")
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (session_key(token), user["id"], time.time() + TOKEN_TTL_SECONDS),
        )
    # 登录响应不缓存：里面带着本次会话令牌。
    return JSONResponse(
        {
            "token": token,
            "username": user["username"],
            "must_change_password": bool(user["must_change_password"]),
        },
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/logout")
def logout(request: Request, user: sqlite3.Row = Depends(current_user)):
    token = request.headers.get("Authorization", "")[len("Bearer "):].strip()
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (session_key(token),))
    return {"ok": True}


@app.post("/api/change-password")
def change_password(
    body: ChangePasswordIn,
    request: Request,
    user: sqlite3.Row = Depends(current_user),
):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    # 口径#8：敏感比对走 password_matches（PBKDF2 + secrets.compare_digest）。
    if not password_matches(body.old_password, user["salt"], user["password_hash"]):
        raise HTTPException(status_code=400, detail="旧密码不正确")
    # 口径#2：本次请求携带的令牌就是当前会话，改密时保留它。
    auth_header = request.headers.get("Authorization", "")
    current_token = (
        auth_header[len("Bearer "):].strip()
        if auth_header.startswith("Bearer ")
        else ""
    )
    salt = secrets.token_hex(16)
    with get_conn() as conn:
        # 密码更新与会话吊销在同一事务里，要么一起生效要么一起回滚。
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ?,"
            " must_change_password = 0 WHERE id = ?",
            (hash_password(body.new_password, salt), salt, user["id"]),
        )
        if current_token:
            conn.execute(
                "DELETE FROM sessions WHERE user_id = ? AND token != ?",
                (user["id"], session_key(current_token)),
            )
        # 取不到当前令牌时不删任何会话，避免把自己踢下线。
    return {"ok": True}


@app.get("/api/me")
def me(user: sqlite3.Row = Depends(current_user)):
    return {
        "username": user["username"],
        "must_change_password": bool(user["must_change_password"]),
    }


# ---------------------------------------------------------------------------
# sites
# ---------------------------------------------------------------------------

def validate_site_name(name: str) -> str:
    name = (name or "").strip()
    if not name or len(name) > MAX_SITE_NAME:
        raise HTTPException(status_code=400, detail="站点名称为空或过长")
    if not is_utf8_text(name):
        raise HTTPException(status_code=400, detail="站点名称包含无法编码的字符")
    return name


def get_site_row(site_pk: int, user_id: int) -> sqlite3.Row:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sites WHERE id = ? AND user_id = ?",
            (site_pk, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="站点不存在")
    return row


def tracking_snippet(request: Request, row: sqlite3.Row) -> tuple[str, str]:
    base = str(request.base_url).rstrip("/")
    script_url = f"{base}/tracker.js"
    snippet = (
        f'<script defer src="{script_url}" '
        f'data-weblens-id="{row["site_id"]}"></script>'
    )
    return script_url, snippet


def site_json(
    row: sqlite3.Row,
    request: Request | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict:
    data = {
        "id": row["id"],
        "site_id": row["site_id"],
        "name": row["name"],
        "domain": row["domain"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if conn is not None:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM pageviews WHERE site_id = ?", (row["id"],)
        ).fetchone()
        data["pageviews"] = count["c"]
    if request is not None:
        script_url, snippet = tracking_snippet(request, row)
        data["script_url"] = script_url
        data["snippet"] = snippet
    return data


@app.get("/api/sites")
def list_sites(request: Request, user: sqlite3.Row = Depends(current_user)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sites WHERE user_id = ? ORDER BY id", (user["id"],)
        ).fetchall()
        return [site_json(r, request, conn) for r in rows]


@app.post("/api/sites")
def create_site(
    body: SiteIn, request: Request, user: sqlite3.Row = Depends(current_user)
):
    name = validate_site_name(body.name)
    domain = normalize_domain_input(body.domain)
    now = iso(utcnow())
    public_id = str(uuid.uuid4())
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sites (site_id, user_id, name, domain, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (public_id, user["id"], name, domain, now, now),
        )
        row = conn.execute(
            "SELECT * FROM sites WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return site_json(row, request, conn)


@app.get("/api/sites/{site_pk}")
def get_site(
    site_pk: int, request: Request, user: sqlite3.Row = Depends(current_user)
):
    row = get_site_row(site_pk, user["id"])
    with get_conn() as conn:
        return site_json(row, request, conn)


@app.get("/api/sites/{site_pk}/snippet")
def get_snippet(
    site_pk: int, request: Request, user: sqlite3.Row = Depends(current_user)
):
    row = get_site_row(site_pk, user["id"])
    script_url, snippet = tracking_snippet(request, row)
    return {"site_id": row["site_id"], "script_url": script_url, "snippet": snippet}


@app.put("/api/sites/{site_pk}")
def update_site(
    site_pk: int,
    body: SiteUpdateIn,
    request: Request,
    user: sqlite3.Row = Depends(current_user),
):
    get_site_row(site_pk, user["id"])
    fields: dict = {}
    if body.name is not None:
        fields["name"] = validate_site_name(body.name)
    if body.domain is not None:
        fields["domain"] = normalize_domain_input(body.domain)
    if fields:
        fields["updated_at"] = iso(utcnow())
        sets = ", ".join(f"{key} = ?" for key in fields)
        with get_conn() as conn:
            conn.execute(
                f"UPDATE sites SET {sets} WHERE id = ?",
                (*fields.values(), site_pk),
            )
    row = get_site_row(site_pk, user["id"])
    with get_conn() as conn:
        return site_json(row, request, conn)


@app.delete("/api/sites/{site_pk}")
def delete_site(site_pk: int, user: sqlite3.Row = Depends(current_user)):
    get_site_row(site_pk, user["id"])
    with get_conn() as conn:
        conn.execute("DELETE FROM sites WHERE id = ?", (site_pk,))
    return {"ok": True}


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------

@app.get("/api/sites/{site_pk}/stats")
def site_stats(
    site_pk: int,
    range_value: str = Query(default="7d", alias="range"),
    user: sqlite3.Row = Depends(current_user),
):
    site = get_site_row(site_pk, user["id"])
    ranges = {"today": 1, "7d": 7, "30d": 30}
    if range_value not in ranges:
        raise HTTPException(status_code=400, detail="时间范围只支持 today、7d、30d")
    day_count = ranges[range_value]
    end_date = utcnow().date()
    start_date = end_date - timedelta(days=day_count - 1)
    start = start_date.isoformat()
    end = end_date.isoformat()

    with get_conn() as conn:
        totals = conn.execute(
            "SELECT COUNT(*) AS pv, COUNT(DISTINCT visitor_hash) AS uv"
            " FROM pageviews WHERE site_id = ? AND view_date BETWEEN ? AND ?",
            (site_pk, start, end),
        ).fetchone()
        trend_rows = conn.execute(
            "SELECT view_date, COUNT(*) AS pv,"
            " COUNT(DISTINCT visitor_hash) AS uv FROM pageviews"
            " WHERE site_id = ? AND view_date BETWEEN ? AND ?"
            " GROUP BY view_date",
            (site_pk, start, end),
        ).fetchall()
        top_pages = conn.execute(
            "SELECT page_path, COUNT(*) AS count FROM pageviews"
            " WHERE site_id = ? AND view_date BETWEEN ? AND ?"
            " GROUP BY page_path ORDER BY count DESC, page_path ASC LIMIT 10",
            (site_pk, start, end),
        ).fetchall()
        top_referrers = conn.execute(
            "SELECT referrer_domain, COUNT(*) AS count FROM pageviews"
            " WHERE site_id = ? AND view_date BETWEEN ? AND ?"
            " AND referrer_domain <> ''"
            " GROUP BY referrer_domain"
            " ORDER BY count DESC, referrer_domain ASC LIMIT 10",
            (site_pk, start, end),
        ).fetchall()
        # 活跃页面数按全量路径去重（热门页只返回 10 条，不能拿它当总数）。
        active_pages = conn.execute(
            "SELECT COUNT(DISTINCT page_path) AS c FROM pageviews"
            " WHERE site_id = ? AND view_date BETWEEN ? AND ?",
            (site_pk, start, end),
        ).fetchone()["c"]

    by_date = {row["view_date"]: row for row in trend_rows}
    trend = []
    for offset in range(day_count):
        day = start_date + timedelta(days=offset)
        key = day.isoformat()
        row = by_date.get(key)
        trend.append(
            {
                "date": key,
                "pv": row["pv"] if row else 0,
                "uv": row["uv"] if row else 0,
            }
        )
    return {
        "site": site_json(site),
        "period": {
            "range": range_value,
            "start_date": start,
            "end_date": end,
        },
        "totals": {"pv": totals["pv"], "uv": totals["uv"]},
        "active_pages": active_pages,
        "trend": trend,
        "top_pages": [
            {"path": row["page_path"], "count": row["count"]} for row in top_pages
        ],
        "top_referrers": [
            {"domain": row["referrer_domain"], "count": row["count"]}
            for row in top_referrers
        ],
    }


# ---------------------------------------------------------------------------
# collection + tracker script
# ---------------------------------------------------------------------------

@app.options("/api/collect")
def collect_options():
    return PlainTextResponse("", status_code=204, headers=COLLECT_CORS)


@app.post("/api/collect", status_code=201)
async def collect(request: Request):
    # 请求体 64KB 上限：先看 Content-Length 快速拒绝，再按实际长度复核。
    content_length = request.headers.get("content-length", "")
    if content_length.isdigit() and int(content_length) > MAX_COLLECT_BODY:
        raise HTTPException(status_code=400, detail="请求体过大")
    raw_body = await request.body()
    if len(raw_body) > MAX_COLLECT_BODY:
        raise HTTPException(status_code=400, detail="请求体过大")
    if raw_body:
        try:
            data = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            # 深度嵌套会在解码时打满递归上限；公开上报接口应返回 400，而不是 500。
            raise HTTPException(status_code=400, detail="请求体不是合法 JSON")
    else:
        data = {}
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="请求体必须是 JSON 对象")
    payload = data
    if isinstance(data.get("payload"), dict):
        payload = {**data, **data["payload"]}

    public_id = str(
        payload.get("site_id")
        or payload.get("siteId")
        or payload.get("website_id")
        or ""
    ).strip()
    if not public_id:
        raise HTTPException(status_code=400, detail="缺少 site_id")

    raw_url = str(
        payload.get("url")
        or payload.get("page_url")
        or payload.get("path")
        or "/"
    )
    page_path = parse_page_path(raw_url)

    if payload.get("referrer_domain"):
        candidate = normalize_host(str(payload["referrer_domain"]))
        if len(candidate) > MAX_DOMAIN_LENGTH or not HOST_RE.match(candidate):
            referrer_domain = ""
        else:
            referrer_domain = candidate
    else:
        referrer_value = (
            payload.get("referrer")
            or payload.get("referer")
            or request.headers.get("referer")
            or request.headers.get("referrer")
            or ""
        )
        referrer_domain = domain_from_value(str(referrer_value))
        if len(referrer_domain) > MAX_DOMAIN_LENGTH:
            referrer_domain = ""
    # UA 分类只认请求头：正文里的 user_agent/userAgent 可被伪造，不再采信。
    user_agent = request.headers.get("user-agent") or ""
    ua_class = classify_user_agent(user_agent)
    now = utcnow()
    view_date = now.date().isoformat()

    with get_conn() as conn:
        site = conn.execute(
            "SELECT * FROM sites WHERE site_id = ?", (public_id,)
        ).fetchone()
        if site is None:
            raise HTTPException(status_code=404, detail="站点不存在")
        if referrer_domain in (site["domain"], page_hostname(raw_url, site["domain"])):
            referrer_domain = ""
        vhash = visitor_hash(conn, client_ip(request), ua_class, view_date)
        cur = conn.execute(
            "INSERT INTO pageviews (site_id, page_path, referrer_domain, browser,"
            " os, device, visitor_hash, view_date, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                site["id"],
                page_path,
                referrer_domain,
                ua_class["browser"],
                ua_class["os"],
                ua_class["device"],
                vhash,
                view_date,
                iso(now),
            ),
        )
        pageview_id = cur.lastrowid
    return JSONResponse(
        {
            "ok": True,
            "site_id": public_id,
            "pageview_id": pageview_id,
            "page_path": page_path,
        },
        status_code=201,
        headers=COLLECT_CORS,
    )


TRACKER_JS = """(function () {
  var script = document.currentScript;
  if (!script) return;
  var siteId = script.getAttribute('data-weblens-id');
  if (!siteId) return;
  var endpoint = new URL('/api/collect', script.src).href;
  var body = JSON.stringify({
    site_id: siteId,
    url: window.location.href,
    referrer: document.referrer || '',
    title: document.title || ''
  });
  if (navigator.sendBeacon) {
    var blob = new Blob([body], { type: 'text/plain;charset=UTF-8' });
    if (navigator.sendBeacon(endpoint, blob)) return;
  }
  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
    body: body,
    keepalive: true,
    mode: 'cors'
  }).catch(function () {});
})();
"""


@app.get("/tracker.js")
def tracker_js():
    return PlainTextResponse(
        TRACKER_JS,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ---------------------------------------------------------------------------
# static page
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    # 看板页不缓存：每次打开都走最新版本，避免旧前端配新接口。
    return FileResponse(
        BASE_DIR / "static" / "index.html",
        headers={"Cache-Control": "no-store"},
    )


init_db()

if __name__ == "__main__":
    import uvicorn

    # 口径#3：默认只监听本机；对外放开走 WEBLENS_HOST 环境变量。
    host = os.environ.get("WEBLENS_HOST", "127.0.0.1")
    port = int(os.environ.get("WEBLENS_PORT", os.environ.get("PORT", "8000")))
    uvicorn.run(app, host=host, port=port)
