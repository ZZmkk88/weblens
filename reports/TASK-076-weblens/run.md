# TASK-076-weblens 执行记录

开工时间：2026-10-22（本地）。工作目录：`E:\muse-bridge\in\TASK-076-weblens`。以下按步骤追加真实命令与输出，未执行的命令不记为已验证。

## 0. 环境探查

命令：

```
python --version
py -3 --version
git rev-parse --is-inside-work-tree
git status --porcelain
```

输出：

```
Python 3.11.9
py -3 --version → exit 1
Unable to create process using 'E:\python.exe --version': ???????????
git rev-parse → true
git status --porcelain → （空，工作区干净）
```

说明：本机 `python` 是 3.11.9，满足 README「Python 3.10+」。README Windows 步骤写的 `py -m venv` 在本机不可用（py 启动器指向损坏的 `E:\python.exe`），这是环境限制，不是仓库缺陷。虚拟环境改用 `python -m venv`，建在 `E:\muse-bridge\work\TASK-076-weblens\venv`（不写进待审仓库）。

## 1. 安装运行依赖

命令与结果（exit 0）：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-076-weblens\requirements.txt
```

装上的钉死版本：fastapi==0.156.4、uvicorn==0.54.0。传递依赖里 starlette==1.9.0、pydantic==2.14.1、anyio==4.15.1。末行：`Successfully installed ... fastapi-0.156.4 ... starlette-1.9.0 ... uvicorn-0.54.0`。

## 2. 安装测试依赖

命令与结果（exit 0）：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-076-weblens\requirements-dev.txt
```

新增：httpx==0.28.1、pytest==9.1.1、httpcore==1.0.9。末行含 `Successfully installed ... httpx-0.28.1 ... pytest-9.1.1`。

## 3. 自动化测试

工作目录即仓库根（shell 默认 cwd）。pytest 缓存目录指到工作区，避免在仓库里生成 `.pytest_cache`。这一次没有改 `TEMP`：`tests/test_app.py` 自己调用 `tempfile.mkdtemp`，临时库落在系统临时目录。该行为来自测试文件，未改测试。

命令（exit 0）：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe -m pytest tests/ -q -o cache_dir=E:\muse-bridge\work\TASK-076-weblens\pytest-cache
```

输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.71s
```

## 4. 真实服务自测 live_selftest

通过工作目录里的 `run_live.py` 启动，把 `TEMP`/`TMP` 指到 `E:\muse-bridge\work\TASK-076-weblens\tmp`，再执行仓库里的 `tests/live_selftest.py`。该脚本自己在临时库上拉起 Uvicorn，端口 8142，结束后 `terminate`。

命令（exit 0）：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-076-weblens\run_live.py
```

输出末段：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"...","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | ... "domain":"demo.example.com" ...
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="..."></script>
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

令牌是一次性临时库的会话，服务已退出。上面把 token 和 site_id 截短；当时终端里的登录行是完整 JSON，`must_change_password` 为 true。

## 5. 按 README 起服务（8000）并关闭

数据库放到 `E:\muse-bridge\work\TASK-076-weblens\tmp\smoke.db`，避免在仓库里生成 `data/weblens.db`。`WEBLENS_HOST=127.0.0.1`，`WEBLENS_PORT=8000`。脚本：`E:\muse-bridge\work\TASK-076-weblens\smoke.py`。用 httpx 访问，未使用 curl/wget。结束后对该进程 `terminate`。

命令（exit 0）：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-076-weblens\smoke.py
```

输出片段：

```
SERVER_UP=True PID=34160
GET / status=200 ctype=text/html; charset=utf-8
  x-frame-options=DENY
  x-content-type-options=nosniff
  body=<!doctype html> ... <title>weblens · 网站访问统计</title> ...
GET /health status=404 ctype=application/json
  body={"detail":"Not Found"}
GET /tracker.js status=200 ctype=application/javascript
  access-control-allow-origin=*
GET /api/me status=401
  body={"detail":"未登录"}
GET /docs status=404
GET /openapi.json status=404
POST /api/login status=200
  body={"token":"...","username":"admin","must_change_password":true}
GET /api/me auth status=200
  body={"username":"admin","must_change_password":true}
POST /api/login nested status=400
  body={"detail":"There was an error parsing the body"}
POST /api/collect nested status=400
  body={"detail":"请求体不是合法 JSON"}
  access-control-allow-origin=None
POST /api/login 140kb status=413 ctype=text/plain; charset=utf-8
  x-frame-options=None
  x-content-type-options=None
  body=Content Too Large
POST /api/collect missing status=400
  body={"detail":"缺少 site_id"}
  access-control-allow-origin=None
```

服务日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:53044 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:53044 - "GET /health HTTP/1.1" 404 Not Found
...
INFO:     127.0.0.1:53044 - "POST /api/login HTTP/1.1" 413 Request Entity Too Large
SERVER_EXIT=1
```

`SERVER_EXIT=1` 是进程被 `terminate` 之后的退出码，日志里没有启动失败。README 没有 `/health`。首页 200 作为存活检查。

## 6. 确认端口已放下

命令：

```
netstat -ano | findstr ":8000 :8142"
```

唯一命中是一条无关的 IPv6 远程地址（地址文本里含有 `8000` 这四个字符，对端端口是 443），没有 `127.0.0.1:8000` 或 `:8142` 的 LISTENING。两个探测端口都没有服务在听。

随后 `git status --porcelain` 与 `git status --porcelain --untracked-files=all` 都没有输出，仓库仍干净。

## 7. 审查结束后重跑全量测试

源码没有改动。命令与第 3 节相同（exit 0）：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe -m pytest tests/ -q -o cache_dir=E:\muse-bridge\work\TASK-076-weblens\pytest-cache
```

输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.00s
```

没有失败用例。

