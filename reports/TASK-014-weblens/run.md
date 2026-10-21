# TASK-014-weblens 执行记录

开工时间：2026-10-21。工作目录：`E:\muse-bridge\in\TASK-014-weblens`。以下按步骤追加真实命令与输出。

## 步骤 0：确认工作区内容

命令：

```
Get-ChildItem -Force -Name
git status
git rev-parse HEAD
git remote -v
git count-objects -v
```

输出摘要：

- 工作区只有 `.git`，没有源码文件。
- `On branch main` / `No commits yet` / `nothing to commit`。
- `git rev-parse HEAD` 失败：`fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.`
- remote：`origin https://github.com/ZZmkk88/weblens.git`（fetch/push）。
- `git count-objects -v`：`count: 0`，`in-pack: 0`，`packs: 0`。
- `.git/refs/heads` 为空，`.git/FETCH_HEAD` 为空，`.git/objects/pack` 为空。

结论：调度克隆留下了空仓库，源码不在工作区。下一步 `git fetch` 取回 `origin/main`。远端地址来自 `.git/config` 与 `E:\muse-bridge\queue\TASK-014-weblens.json` 的 `repo` 字段。

## 步骤 1：本轮开工（源码已在工作区）

开工记录第一行延续本文件标题。当前工作目录 `E:\muse-bridge\in\TASK-014-weblens` 已能看到源码。先核对 Python、git 与目录，再按 README 装环境。

命令：

```
python --version
py -3 --version
git status --porcelain
git rev-parse --abbrev-ref HEAD
git log -1 --oneline
git rev-parse HEAD
```

输出：

- `python --version` → `Python 3.11.9`（满足 README「Python 3.10 或更高」）。
- `py -3 --version` 失败：`Unable to create process using 'E:\python.exe --version': ???????????`
- `git status --porcelain` 无输出（工作区干净）。
- 分支 `main`，HEAD `4af0b00e1545fb04b584874dd187b5d8c9b4cae1`，提交说明 `docs(weblens): README、调研笔记、上游溯源与许可证`。

## 步骤 2：按 README 创建虚拟环境

README Windows 步骤是 `py -m venv .venv`。

命令：

```
py -m venv .venv
```

输出（exit 1）：

```
Unable to create process using 'E:\python.exe -m venv .venv': ???????????
```

`py` 启动器指向不存在的 `E:\python.exe`。改用已验证可用的 `python`（3.11.9）创建虚拟环境。

命令：

```
python -m venv .venv
```

输出：exit 0，无报错。虚拟环境路径 `.venv`。

## 步骤 3：安装运行依赖

命令：

```
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

输出（exit 0，节选）：

```
Collecting fastapi==0.156.4
Collecting uvicorn==0.54.0
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 click-8.5.0 fastapi-0.156.4 h11-0.16.0 idna-3.20 opentelemetry-api-1.45.1 pydantic-2.14.1 pydantic-core-2.50.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

钉死版本 fastapi==0.156.4、uvicorn==0.54.0 可以装上。

## 步骤 4：安装开发依赖

命令：

```
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

输出（exit 0，节选）：

```
Collecting httpx==0.28.1
Collecting pytest==9.1.1
Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1
```

## 步骤 5：跑自动化测试

命令（README：`python -m pytest tests/ -q`）：

```
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

输出（exit 0）：

```
.........................                                                [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-014-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 2.02s
```

25 项全部通过。警告来自已安装的 Starlette/FastAPI，不是测试失败。

## 步骤 6：真实流程自测

命令（README：`python tests/live_selftest.py`）：

```
.\.venv\Scripts\python.exe tests\live_selftest.py
```

输出（exit 0）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"ywa240n575cgW9QeF3ai4CZ2KJrOxgtNGTi2dySH9J8","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | {"id":1,"site_id":"ecb7ac6c-162f-448f-a453-a876fcea50e3",...}
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="ecb7ac6c-162f-448f-a453-a876fcea50e3"></script>
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

脚本自己在 127.0.0.1:8142 拉起 Uvicorn，结束时 `proc.terminate()`。15 个检查点全部通过。

## 步骤 7：本轮复核开工（2026-10-21）

前序步骤已装好 `.venv` 并跑过一轮测试。本轮从复核测试、按 README 启动服务、对照源码开始，不重复安装依赖（除非复核失败）。虚拟环境解释器：`E:\muse-bridge\in\TASK-014-weblens\.venv\Scripts\python.exe`。

## 步骤 8：复核自动化测试

命令（工作目录 `E:\muse-bridge\in\TASK-014-weblens`）：

```
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

输出（exit 0）：

```
.........................                                                [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-014-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 1.58s
```

25 项通过。警告是 Starlette 对 `httpx` 的弃用提示，不是失败。

## 步骤 9：真实流程自测

命令：

```
.\.venv\Scripts\python.exe tests\live_selftest.py
```

输出（exit 0）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"ZwHVZ3bNmpMGziS6eBNeZpiXjBRiw8hHhqz764FoDwY","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | {"id":1,"site_id":"b8762348-9a4c-4da2-8116-c2e9db8b8cb9",...,"domain":"demo.example.com",...}
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="b8762348-9a4c-4da2-8116-c2e9db8b8cb9"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | {"ok":true,...,"page_path":"/pricing"}
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 7 天，合计 pv 4
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

脚本在 127.0.0.1:8142 起 Uvicorn，结束时 `proc.terminate()`。15 个检查点全部通过。

## 步骤 10：按 README 启动服务并检查首页 / 健康检查

数据库放到任务工作目录，避免在仓库里留下库文件。启动命令仍是 venv 里的 `python app.py`（端口默认 8000）。

命令：

```
.\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-014-weblens\smoke_server.py
```

脚本内容要点：子进程执行 `app.py`，`WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-014-weblens\smoke.db`，用 httpx 请求本机后 `proc.terminate()`。

输出（exit 0）：

```
UP True PID 25076
GET / 200 <!doctype html> ... <title>weblens · 网站访问统计</title> ...
GET /health 404 {"detail":"Not Found"}
GET /api/health 404 {"detail":"Not Found"}
GET /tracker.js 200 (function () { ... data-weblens-id ...
GET /docs 200 <!DOCTYPE html> ...
STOPPED 1
```

Uvicorn 日志（`E:\muse-bridge\work\TASK-014-weblens\smoke_server.log`）：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:50766 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:50766 - "GET /health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:50766 - "GET /api/health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:50766 - "GET /tracker.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:50766 - "GET /docs HTTP/1.1" 200 OK
```

子进程 `poll()` 为 1，进程已退出（Windows 上 `terminate()` 常见非 0 退出码）。首页与 `/tracker.js` 返回 200。没有 `/health` 或 `/api/health` 路由，返回 404。README 未承诺健康检查路径，这条 404 不记为功能缺陷。

## 步骤 11：缺陷探针（只打本地 TestClient）

命令：

```
.\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-014-weblens\probe_defects.py
```

输出要点（exit 0）：

```
COLLECT_OVERRIDE 201
ROW_OVERRIDE {"page_path": "/pricing", "referrer_domain": "https://www.google.com/search?q=secret-token", "browser": "机器人", "os": "其他", "device": "机器人", ...}
ROW_REFERRER_FIELD {"page_path": "/ok", "referrer_domain": "google.com", "browser": "Chrome", "os": "Windows", "device": "桌面", ...}
XFF_HASH_DIFFER True
TOP_PAGES_LEN 10
STATS_KEYS ['period', 'site', 'top_pages', 'top_referrers', 'totals', 'trend']
HAS_ACTIVE_PAGES False
CHANGE_PW 200
OTHER_SESSION_AFTER_PW 200 {"username":"admin","must_change_password":false}
CURRENT_SESSION_AFTER_PW 200
SESSION_COUNT 2
```

探针含义：

- 请求头是 Chrome，正文 `user_agent` 写成机器人后，入库分类变成「机器人」。
- `referrer_domain` 传入完整 URL（含 `q=secret-token`）时，整串落库；同一 URL 走 `referrer` 字段则只存 `google.com`。
- 同一 UA、不同 `X-Forwarded-For`，`visitor_hash` 不同。
- 写入 15 个不同路径后，`top_pages` 仍只有 10 条，响应里没有 `active_pages`。
- 改密后另一个登录会话仍然 200，库里还剩 2 条 session。






