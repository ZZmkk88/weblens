# TASK-086-weblens 执行记录

开工：2026-10-22。工作目录 `E:\muse-bridge\in\TASK-086-weblens`。临时文件目录 `E:\muse-bridge\work\TASK-086-weblens`。

## 环境

仓库内没有 `.venv`。本机 `python` / `py -3` 指向失效的 `E:\python.exe`（报错原文：`Unable to create process using 'E:\python.exe --version'`）。可用解释器：

- `C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe` → `Python 3.11.9`（满足 README「Python 3.10+」）
- 任务预置虚拟环境 `E:\muse-bridge\env\TASK-086-weblens`（`pyvenv.cfg`：`version = 3.11.9`，由上述解释器创建）。未在仓库内建 `.venv`，避免把虚拟环境写进待审仓库。

`pip list`（安装开发依赖前）已有 `fastapi 0.156.4`、`uvicorn 0.54.0`、`starlette 1.9.0`，与 `requirements.txt` 钉死版本一致；当时没有 `httpx` / `pytest`。

### 安装开发依赖

命令：

```
E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-086-weblens\requirements-dev.txt
```

输出摘要：`fastapi==0.156.4`、`uvicorn==0.54.0` 已满足；新装 `httpx-0.28.1`、`pytest-9.1.1` 及传递依赖 `httpcore`、`certifi`、`pluggy` 等。末行：`Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1`。退出码 0。

## 测试（修复前）

环境变量：`PYTHONDONTWRITEBYTECODE=1`，`TEMP`/`TMP`=`E:\muse-bridge\work\TASK-086-weblens`（让测试自己的临时库离开系统 TEMP）。工作目录为仓库根。额外加了 `-p no:cacheprovider`，避免在仓库里写出 `.pytest_cache`。

命令：

```
cmd /c "set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& cd /d E:\muse-bridge\in\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pytest tests/ -q -p no:cacheprovider"
```

输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\env\TASK-086-weblens\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\env\TASK-086-weblens\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.89s
```

退出码 0。警告与 `DECISIONS.md` D-6 已决事项一致，测试仍通过。

### 真实流程自测

命令：

```
cmd /c "set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& cd /d E:\muse-bridge\in\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe tests\live_selftest.py"
```

输出（令牌已截断）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"aL6E…（截断）","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | …"domain":"demo.example.com"…
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="b2fc1b02-8749-4c39-b010-c7031dceaa4f"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

退出码 0。脚本在 `finally` 里 `terminate()` 了自己拉起的 8142 端口进程。趋势日期落在 `2026-10-21`（UTC），与 README「今天按 UTC」一致；本机本地日期是 2026-10-22。

## 按 README 起服务（127.0.0.1:8000）

`py` 启动器不可用，改用已装好依赖的解释器直接跑 `app.py`。数据库放到工作目录，不在仓库里生成 `data/weblens.db`。

命令：`E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe E:\muse-bridge\work\TASK-086-weblens\probe_server.py`

Uvicorn 标准输出（`E:\muse-bridge\work\TASK-086-weblens\uvicorn_stdout.txt`）首段：

```
INFO:     Started server process [34488]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:53550 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:53550 - "GET /health HTTP/1.1" 404 Not Found
```

探测输出片段：

```
SERVER_UP=True
GET / -> 200 ctype=text/html; charset=utf-8 xfo=DENY nosniff=nosniff body='<!doctype html> …'
GET /health -> 404 … body='{"detail":"Not Found"}'
GET /healthz -> 404
GET /api/health -> 404
GET /docs -> 404
GET /api/me -> 401 {"detail":"未登录"}
GET /api/sites -> 401
GET /tracker.js -> 200
GET /data/weblens.db -> 404
GET /app.py -> 404
HOME_HAS_WEBLENS=True
HOME_HAS_DEFAULT_HINT=True
HOME_PREFILL_VALUE=False
LOGIN_NO_SUCH_USER status=401 seconds=0.005
LOGIN_BAD_PASSWORD status=401 seconds=0.069
LOGIN_LONG_PW status=401 seconds=0.067
LOGIN_OK status=200 must_change=True token_len=43
NOAUTH /api/sites/1/stats -> 401
HOST_EVIL status=200 snippet=<script defer src="http://evil.example/tracker.js" …>
SQLI_NAME status=200 name="a' OR 1=1 --"
BEARER_LOWER status=401
SERVER_EXIT=1
```

访问日志里有一行 `203.0.113.9:0 - "POST /api/collect"`，该请求的 `X-Forwarded-For` 是 `203.0.113.9`，TCP 对端实际是 `127.0.0.1`。

关掉之后：`netstat -ano -p tcp | findstr :8000` 无匹配（退出码 1），8000 上没有监听。

### 补充核查

`check_more.py`（TestClient，库在工作目录）：

```
PORT_8000=closed TimeoutError: timed out
BIG_LOGIN 413 None None Content Too Large
HOME_HDR 200 DENY None
SESSION_TTL_REMAINING_SEC=86243
USER ('admin', 1, 64, 32)
TOKEN_STORED_LEN 64 PREFIX 2f48615c
```

会话剩余约 86243 秒，接近 24×3600=86400。口令哈希长度 64、盐长度 32、库内令牌长度 64（SHA-256 十六进制，不是明文）。140KB 登录正文返回 413，且没有 `X-Frame-Options`。

`C:\Windows\py.exe --version` 再次失败，原文：`Unable to create process using 'E:\python.exe --version'`。这是本机启动器问题，不是仓库缺陷。

修复前 `git status --porcelain` 无输出，工作区干净。

## 修复后验证

P1-1 改的是 `app.py` 的登录与改密口令比较。对应用例：

```
cmd /c 'set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& cd /d E:\muse-bridge\in\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pytest tests/test_app.py -q -p no:cacheprovider -k "login or password"'
```

```
4 passed, 29 deselected, 1 warning in 2.38s
```

退出码 0。

耗时对比（`time_login.py`）：

```
MISSING 401/0.080 401/0.076 401/0.076
WRONGPW 401/0.075 401/0.070 401/0.071
```

全量测试：

```
cmd /c "set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& cd /d E:\muse-bridge\in\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pytest tests/ -q -p no:cacheprovider"
```

```
33 passed, 1 warning in 5.61s
```

退出码 0。

`python tests/live_selftest.py`（同一环境变量）末行 `LIVE SELFTEST: ALL PASS (15 checks)`，退出码 0。

收尾：

```
git -C E:\muse-bridge\in\TASK-086-weblens status --porcelain
```

```
 M app.py
```

