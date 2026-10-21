# TASK-092-weblens 执行记录

开工：2026-10-22。工作目录 E:\muse-bridge\in\TASK-092-weblens。先审查再修 P0/P1。

临时文件与虚拟环境、数据库都在 `E:\muse-bridge\work\TASK-092-weblens`。未使用 curl / wget。未抓取外部网页。pip 只用于按 requirements 安装。

## 1. 装依赖

```text
python --version
```

输出：`Python 3.11.9`。

README Windows 步骤里的启动器：

```text
py -3 --version
```

退出码 1，原文：

```text
Unable to create process using 'E:\python.exe --version': ???????????
```

环境限制：本机 `py` 指向不存在的 `E:\python.exe`。后续改用 `python`。

```text
python -m venv E:\muse-bridge\work\TASK-092-weblens\.venv
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-092-weblens\requirements-dev.txt
```

pip 退出码 0。节选：

```text
Collecting fastapi==0.156.4
Collecting uvicorn==0.54.0
Collecting httpx==0.28.1
Collecting pytest==9.1.1
Successfully installed ... fastapi-0.156.4 ... httpx-0.28.1 ... pytest-9.1.1 ... starlette-1.9.0 ... uvicorn-0.54.0
```

未执行 `Activate.ps1`。

## 2. 全量测试（审查时）

工作目录：`E:\muse-bridge\in\TASK-092-weblens`。

```text
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=line
```

退出码 0：

```text
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-092-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-092-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.39s
```

## 3. 真实流程自测

```text
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe tests\live_selftest.py
```

退出码 0。节选（登录令牌已截断）：

```text
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"…","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名
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

趋势日期落在 `2026-10-21`，`created_at` 示例 `2026-10-21T17:07:51+00:00`。

## 4. 起服务并做首页 / 健康检查

启动脚本：`E:\muse-bridge\work\TASK-092-weblens\run_server.py`（设置 `WEBLENS_DB_PATH` 到工作目录，`WEBLENS_HOST=127.0.0.1`，`WEBLENS_PORT=8000`，再以 `__main__` 运行仓库 `app.py`）。

日志：

```text
INFO:     Started server process [35756]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

`E:\muse-bridge\work\TASK-092-weblens\http_check.py` 结果节选：

```text
GET / -> 200 text/html; charset=utf-8 xfo=DENY nosniff=nosniff
<!doctype html> ... <title>weblens · 网站访问统计</title>
GET /health -> 404 application/json xfo=DENY
{"detail":"Not Found"}
GET /api/health -> 404 application/json xfo=DENY
{"detail":"Not Found"}
GET /tracker.js -> 200 application/javascript xfo=DENY nosniff=nosniff
GET /docs -> 404 application/json
{"detail":"Not Found"}
POST /api/login -> 200 ... "username":"admin","must_change_password":true
GET /api/me -> 200 {"username":"admin","must_change_password":true}
GET /api/sites/9223372036854775808 -> 500 text/plain; charset=utf-8 xfo=None
Internal Server Error
GET /api/sites/1 -> 404 {"detail":"站点不存在"}
GET / -> 200
```

服务日志中的异常落点：

```text
File "E:\muse-bridge\in\TASK-092-weblens\app.py", line 562, in get_site
    row = get_site_row(site_pk, user["id"])
File "E:\muse-bridge\in\TASK-092-weblens\app.py", line 485, in get_site_row
    row = conn.execute(
OverflowError: Python int too large to convert to SQLite INTEGER
```

同一路径不带令牌（`db_check.py`）：`unauth huge 401 {"detail":"未登录"}`。

启动并登录、尚未上报时查工作库：

```text
settings []
users [(1, 'admin', 1)]
sessions [(64, 1)]
```

`sessions` 里令牌长度 64，是 SHA-256 十六进制，不是原始令牌。

## 5. 关掉服务

已结束启动该服务的后台任务。之后：

```text
netstat -ano | findstr :8000
```

只有 `127.0.0.1:8000` 的 `TIME_WAIT`（PID 0），没有 LISTENING。`findstr` 还命中一条 IPv6 地址里含 `:8000:` 的无关连接，对端端口是 443。

再次连接：

```text
ConnectionRefusedError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。
```

此前用 `urllib` 对 `http://127.0.0.1:8000/` 超时一次（`TimeoutError`），与上面的拒绝结果不一致；以 `netstat` 无 LISTENING 和 WinError 10061 为准，服务已停。

## 6. 收尾重跑测试

```text
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=line
```

退出码 0：

```text
33 passed, 1 warning in 5.60s
```

警告与第 2 节相同（`StarletteDeprecationWarning` / `httpx2`）。

## 7. git status

```text
git -C E:\muse-bridge\in\TASK-092-weblens status --porcelain
```

退出码 0，输出为空。本轮未改仓库源码，空输出是预期。
