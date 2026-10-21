# TASK-073-weblens 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-073-weblens`。顺序：先审查并跑通，结论写入 review.md，再按清单修 P0/P1（最多 5 项）。

## 步骤 0：环境探测

命令：

```
python --version
py --version
git -C "E:\muse-bridge\in\TASK-073-weblens" status --porcelain
git -C "E:\muse-bridge\in\TASK-073-weblens" rev-parse --is-inside-work-tree
```

输出：

```
Python 3.11.9
Unable to create process using 'E:\python.exe --version': ???????????
true
```

`git status --porcelain` 无输出（工作区干净）。`py` 启动器在本机不可用（指向不存在的 `E:\python.exe`）。README Windows 段写的是 `py -m venv`，本机改用 `python -m venv`。仓库内有 `.gitignore`，忽略 `.venv/`、`data/`、`*.db`。

## 步骤 1：按 README 建虚拟环境

命令（README 写法，失败）：

```
py -3 -m venv "E:\muse-bridge\in\TASK-073-weblens\.venv"
```

输出（exit 1）：

```
Unable to create process using 'E:\python.exe -m venv E:\muse-bridge\in\TASK-073-weblens\.venv': ???????????
```

命令（改用 python，成功，exit 0，无输出）：

```
python -m venv "E:\muse-bridge\in\TASK-073-weblens\.venv"
```

## 步骤 2：安装运行依赖

命令（在仓库根目录执行，exit 0）：

```
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

关键输出：

```
Collecting fastapi==0.156.4
Collecting uvicorn==0.54.0
Collecting starlette>=0.46.0
  Using cached starlette-1.9.0-py3-none-any.whl
Successfully installed ... fastapi-0.156.4 ... starlette-1.9.0 ... uvicorn-0.54.0
```

钉死版本可安装。传递依赖含 starlette 1.9.0、pydantic 2.14.1。未升级 pip（任务禁止改无关依赖）。

## 步骤 3：安装测试依赖

命令（exit 0）：

```
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

关键输出：

```
Successfully installed ... httpx-0.28.1 ... pytest-9.1.1
```

httpx 0.28.1 与 pytest 9.1.1 安装成功。

## 步骤 4：自动化测试

为避免测试使用系统 TEMP，设置 `TEMP`/`TMP` 到 `E:\muse-bridge\work\TASK-073-weblens`。pytest 缓存也改到该目录。命令在仓库根目录执行：

```
$env:TEMP = "E:\muse-bridge\work\TASK-073-weblens"
$env:TMP = "E:\muse-bridge\work\TASK-073-weblens"
$env:PYTHONIOENCODING = "utf-8"
.venv\Scripts\python.exe -m pytest tests/ -q -o cache_dir=E:\muse-bridge\work\TASK-073-weblens\pytest-cache
```

实际通过工作目录脚本 `E:\muse-bridge\work\TASK-073-weblens\run_pytest.py` 设置 TEMP/TMP 后调用 pytest（命令行内联设置环境变量被执行策略拦住）。

命令：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_pytest.py
```

输出（exit 0，耗时 5.93s）：

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-073-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.93s
```

README 写「自动化测试 30 项」，实际收集并通过 33 项。警告为 Starlette 对 httpx TestClient 的弃用提示，测试未失败。

## 步骤 5：真实流程自测 live_selftest

命令（脚本把 TEMP/TMP 指到工作目录后执行 `tests/live_selftest.py`）：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_live.py
```

输出（exit 0；登录令牌来自临时库，进程结束后库即弃用，下面截断令牌）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"A0Dn…（截断）","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | {"id":1,"site_id":"b8f4e334-297a-45e3-a6a8-5170338d7d47","name":"演示站","domain":"demo.example.com", ...}
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="b8f4e334-297a-45e3-a6a8-5170338d7d47"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | {"ok":true,"site_id":"b8f4e334-297a-45e3-a6a8-5170338d7d47","pageview_id":4,"page_path":"/pricing"}
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | ... {'date': '2026-10-21', 'pv': 4, 'uv': 2}
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

趋势日期落在 UTC 的 2026-10-21，与 README「按天切分使用 UTC」一致。created_at 样例为 `2026-10-21T16:03:55+00:00`。

## 步骤 6：按 README 起服务（127.0.0.1:8000），检查首页后关闭

数据库改到工作目录，避免在仓库留下 `data/weblens.db`（禁止 del/rm，不能事后删）。脚本：`E:\muse-bridge\work\TASK-073-weblens\run_smoke.py`。

命令：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_smoke.py
```

关键输出（exit 0）：

```
ENV_PORT None
ENV_WEBLENS_PORT None
ENV_WEBLENS_HOST None
UP True pid 32224
GET / status=200 xfo=DENY nosniff=nosniff ctype=text/html; charset=utf-8 body=<!doctype html> ... <title>weblens · 网站访问统计</
GET /health status=404 ... body={"detail":"Not Found"}
GET /docs status=404
GET /redoc status=404
GET /openapi.json status=404
GET /tracker.js status=200 ctype=application/javascript
GET /api/me status=401 body={"detail":"未登录"}
SETTINGS_BEFORE_COLLECT []
USERS [('admin', 1)]
POST /api/collect 140KiB 413 Content Too Large
POST /api/collect 70KiB 400 {"detail":"请求体过大"}
STOPPED 1
```

stderr：

```
INFO:     Started server process [12968]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

无 traceback。`STOPPED 1` 是 `proc.terminate()` 在 Windows 上的退出码，不是启动失败。

随后 bind 检查（`check_bind.py`）：

```
BIND 8000 OK free
BIND 8142 OK free
```

`tasklist /FI "PID eq 12968"` 与 `tasklist /FI "PID eq 32224"` 均无匹配进程。服务已关。

补充：对已关闭端口做 TCP connect 得到 `TimeoutError`（本机对未监听端口不立刻拒绝）。以 bind 成功为准，端口无人占用。

## 步骤 7：Host 头探测（不计入测试失败）

命令：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\probe_host.py
```

`Host: evil.example` 时 snippet 为 `http://evil.example/tracker.js`（合法 Host，与 `request.base_url` 一致）。含引号或 CRLF 的 Host 被 Starlette 丢弃，snippet 仍是 `http://testserver/tracker.js`，没有属性逃逸。不列为缺陷。

## 步骤 8：确认清单后重跑全量测试

未改仓库源码。重跑 pytest（exit 0）：

```
33 passed, 1 warning in 5.86s
```

重跑 live_selftest（exit 0）：

```
LIVE SELFTEST: ALL PASS (15 checks)
```

## 步骤 9：git status --porcelain

命令（仓库根目录，exit 0）：

```
git status --porcelain
```

输出为空。本轮未改仓库文件。

