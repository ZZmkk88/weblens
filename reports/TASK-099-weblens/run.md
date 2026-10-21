# TASK-099-weblens 执行记录

开工：2026-10-22。工作目录 `E:\muse-bridge\in\TASK-099-weblens`。先审查再修 P0/P1。

## 0. 环境探测

命令：`python --version`

```
Python 3.11.9
```

命令：`py --version`

```
exit: 1
Unable to create process using 'E:\python.exe --version': ???????????
```

说明：本机 `py` 启动器指向不存在的 `E:\python.exe`，README Windows 节的 `py -m venv .venv` 在这台机器上无法执行。改用 `python -m venv .venv`（Python 3.11.9，满足 README 要求的 3.10+）。此为环境限制，不计入项目缺陷。

命令：`git status --porcelain`

```
（空，工作区干净）
```

`.gitignore` 已忽略 `.venv/`、`data/`、`__pycache__/`、`*.db`。

## 1. 安装依赖

命令：`python -m venv .venv`（在仓库根目录）

```
exit: 0
```

命令：`.venv\Scripts\python.exe -m pip install -r requirements.txt`

```
Successfully installed ... fastapi-0.156.4 ... starlette-1.9.0 ... uvicorn-0.54.0
exit: 0
```

命令：`.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`

```
Successfully installed ... httpx-0.28.1 ... pytest-9.1.1
exit: 0
```

未改任何依赖版本号。临时目录 `E:\muse-bridge\work\TASK-099-weblens` 已建。

## 2. 自动化测试

命令：`.venv\Scripts\python.exe -m pytest tests/ -q --tb=short`

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-099-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.30s
```

exit: 0。README 写的是 30 项，实际收集到 33 项（见审查报告）。警告来自 Starlette/FastAPI 自带 TestClient，DECISIONS.md D-6 已决定不改。

## 3. 真实流程自测（临时库，端口 8142）

命令：`.venv\Scripts\python.exe tests/live_selftest.py`

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"<已截断>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | {... "domain":"demo.example.com" ...}
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="..."></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 7 天，合计 pv 4；UTC 日期落在 2026-10-15 至 2026-10-21
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

exit: 0。脚本自己 `proc.terminate()` 关掉了 8142 上的进程。登录令牌属于已销毁的临时库，报告里截断。

## 4. 按 README 启动服务（127.0.0.1:8000）并关掉

脚本：`E:\muse-bridge\work\TASK-099-weblens\probe_server.py`（数据库放在该工作目录，不写进仓库 `data/`）。

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-099-weblens\probe_server.py`

```
came_up=True pid=19096
GET /            status=200  content-type=text/html  X-Frame-Options=DENY  X-Content-Type-Options=nosniff
                 body 以 <!doctype html> 开头，title 为 weblens · 网站访问统计
GET /health      status=404  {"detail":"Not Found"}
GET /healthz     status=404  {"detail":"Not Found"}
GET /api/health  status=404  {"detail":"Not Found"}
GET /docs        status=404
GET /redoc       status=404
GET /openapi.json status=404
GET /tracker.js  status=200  application/javascript  Access-Control-Allow-Origin=*
GET /api/me      status=401  {"detail":"未登录"}
db before collect settings_rows=0 user=('admin', 1)
POST /api/login  status=200  must_change_password=true（令牌已截断）
POST /api/sites  status=200  domain=probe.example.com（www 与路径已去掉）
POST /api/collect status=201 page_path=/pricing
db after collect uv_salt_rows=1 referrer_domain=google.com browser=Chrome visitor_hash 长度 64
POST /api/login 140KiB status=413 body=Content Too Large
                 响应头只有 content-type=text/plain，没有 X-Frame-Options
Uvicorn running on http://127.0.0.1:8000
stopped returncode=1
```

随后 `.venv\Scripts\python.exe E:\muse-bridge\work\TASK-099-weblens\check_ports.py`：8000 与 8142 均为 ConnectTimeout，不再返回首页。`Get-CimInstance Win32_Process` 里没有 `app.py`。返回码 1 是 `terminate()` 结束子进程的结果，日志无 traceback。

无 `/health`。README 未承诺健康检查路由，首页 200 作为存活信号。不记为缺陷。

## 5. 上报正文大小（解释 README「超过 64KB 返回 400」）

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-099-weblens\probe_413.py`

```
70KiB len 71743 status 400 ctype application/json xfo DENY body {"detail":"请求体过大"}
140KiB len 143423 status 413 ctype text/plain; charset=utf-8 xfo None body Content Too Large
```

exit: 0。

## 6. 审查后重跑全量测试与 git status

没有改仓库源码（P0/P1 为空）。

命令：`.venv\Scripts\python.exe -m pytest tests/ -q --tb=line`

```
33 passed, 1 warning in 5.65s
```

exit: 0。警告仍是 fastapi/testclient.py 的 StarletteDeprecationWarning。

命令：`git status --porcelain`

```
（stdout 为空，exit 0）
```

