# TASK-061-weblens 执行记录

开工时间：2026-10-21。工作目录：E:\muse-bridge\in\TASK-061-weblens。先审查再按清单修 P0/P1。

## 环境

命令：`python --version`

输出：
```
Python 3.11.9
```

README 要求 Python 3.10+。本机 3.11.9 满足。虚拟环境放到 `E:\muse-bridge\work\TASK-061-weblens\.venv`，避免在待审仓库里生成 `.venv` 和 `data/`。

## 安装依赖

工作目录：`E:\muse-bridge\in\TASK-061-weblens`。

命令：
```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` 第一行是 `-r requirements.txt`，所以运行时依赖一并安装。退出码 0。关键行：

```
Collecting fastapi==0.156.4 (from -r requirements.txt (line 1))
Collecting uvicorn==0.54.0 (from -r requirements.txt (line 2))
Collecting httpx==0.28.1 (from -r requirements-dev.txt (line 2))
Collecting pytest==9.1.1 (from -r requirements-dev.txt (line 3))
Successfully installed ... fastapi-0.156.4 ... httpx-0.28.1 ... pytest-9.1.1 ... uvicorn-0.54.0
```

钉死版本均可安装，无依赖冲突。

## 自动化测试

命令：
```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe -m pytest tests/ -q
```

输出（退出码 0）：
```
..............................                                           [100%]
============================== warnings summary ===============================
..\..\work\TASK-061-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-061-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
30 passed, 1 warning in 5.51s
```

README 写「25 项」，pytest 实际收集 30 条（见审查报告）。警告与 DECISIONS.md D-6 记录的 httpx/TestClient 弃用警告一致，不是失败。

## 真实流程自测

命令：
```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe tests\live_selftest.py
```

退出码 0。脚本自己监听 `127.0.0.1:8142`，结束时 `proc.terminate()`。登录行里的临时令牌已省略，其余为原文：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"[临时令牌已省略]","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | {"id":1,"site_id":"b79682e7-c3dd-4685-bbd3-29eb8a9cc7df","name":"演示站","domain":"demo.example.com",...}
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="b79682e7-c3dd-4685-bbd3-29eb8a9cc7df"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | {"ok":true,"site_id":"b79682e7-c3dd-4685-bbd3-29eb8a9cc7df","pageview_id":4,"page_path":"/pricing"}
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首 | [{'path': '/pricing', 'count': 3}, {'path': '/docs', 'count': 1}]
PASS 来源排行正确：google.com 3 次居首 | [{'domain': 'google.com', 'count': 3}, {'domain': 'bing.com', 'count': 1}]
PASS 近 7 天趋势长度与合计正确 | [7 天，仅 2026-10-21 有 pv=4 uv=2]
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

## 按 README 启动服务并探测

数据库改到工作目录，避免在仓库里生成 `data/weblens.db`。脚本：`E:\muse-bridge\work\TASK-061-weblens\probe_server.py`。

等价命令：在仓库目录执行 `python app.py`，并设置：

```
WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-061-weblens\weblens-manual.db
WEBLENS_HOST=127.0.0.1
WEBLENS_PORT=8000
```

启动约 1.62 秒。日志原文：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:60088 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:60088 - "GET /health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60088 - "GET /api/health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60088 - "GET /docs HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60088 - "GET /openapi.json HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60088 - "GET /tracker.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:60088 - "GET /api/sites HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:60088 - "POST /api/login HTTP/1.1" 200 OK
INFO:     127.0.0.1:60088 - "GET /api/me HTTP/1.1" 200 OK
INFO:     127.0.0.1:49249 - "POST /api/collect HTTP/1.1" 400 Bad Request
INFO:     127.0.0.1:60088 - "POST /api/login HTTP/1.1" 401 Unauthorized
```

探测摘要：

- `GET /` → 200，`text/html; charset=utf-8`，正文含 `<title>weblens · 网站访问统计</title>`，`X-Frame-Options: DENY`，`X-Content-Type-Options: nosniff`
- `GET /health`、`GET /api/health` → 404 `{"detail":"Not Found"}`。代码里没有健康检查路由，README 也没承诺。首页 200 作为存活信号。
- `GET /docs`、`GET /openapi.json` → 404
- `GET /tracker.js` → 200 `application/javascript`
- 未登录 `GET /api/sites` → 401 `{"detail":"未登录"}`
- `POST /api/login` admin/admin123 → 200，`must_change_password=true`，`token_len=43`
- `GET /api/me` → 200 `{"username":"admin","must_change_password":true}`
- 无 Content-Length 的分块 `POST /api/collect`（正文约 70KB）→ `HTTP/1.1 400 Bad Request`，正文 `{"detail":"请求体过大"}`。说明超限是读完才拒绝。
- 5000 字符密码登录 → 401，耗时 0.071 秒。长密码没有打出可观察的 CPU 卡住，不单列缺陷。

关闭：脚本对父进程 `terminate()`，打印 `stopped returncode=1 port_open=True`（Windows 上子进程 35420 比 Popen pid 35224 晚退出，探测瞬间端口仍可连）。随后复查：

```
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

无监听（cmdlet 报找不到匹配连接）。`Get-Process -Id 35420,35224` 退出码 1，两个进程都不在。服务已停。

## 库内令牌形态

命令：`E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-061-weblens\inspect_db.py`

```
user (1, 'admin', 64, 32, 1)
session_len_prefix_userid (43, 'QjB0', 1)
session_count 1
```

密码哈希长度 64，盐长度 32。会话 token 长度 43，与接口返回的 `token_len=43` 一致，是明文。

`inspect_settings.py`：服务启动并登录后 `settings []`，UV 盐并未在启动时写入。

## P1-1 验证

改 `app.py` 的会话存储后：

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
30 passed, 1 warning in 5.11s
```

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-061-weblens\probe_token.py
```

```
login_status=200 raw_len=43 stored_len=64
stored_equals_raw=False
stored_equals_sha256=True
me_status=200 me={"username":"admin","must_change_password":true}
logout_status=200 sessions_left=0
me_after_logout=401
```

## P1-2 验证

加上 128KiB 请求体上限后：

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
30 passed, 1 warning in 4.85s
```

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-061-weblens\probe_body.py
```

```
collect_70kib status=400 bytes=71708 detail={"detail":"请求体过大"}
login_140kib status=413 bytes=143375 body=Content Too Large
```

## 全量重跑

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe -m pytest tests/ -q
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe tests\live_selftest.py
```

pytest：`30 passed, 1 warning in 4.86s`（退出码 0）。

live_selftest：`LIVE SELFTEST: ALL PASS (15 checks)`（退出码 0）。登录响应里的临时令牌已省略。

`git diff --stat`：`app.py | 20 ++++++++++++++++----`，只有这一个文件。
