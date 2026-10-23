# TASK-102-weblens 执行记录

开工：2026-10-23 本地验收 weblens 仓库。先读仓库结构与 README，再装环境、跑测试、起服务。

## 1. 环境与依赖

工作目录：`E:\muse-bridge\in\TASK-102-weblens`。虚拟环境建在仓库 `.venv`（`.gitignore` 已忽略）。

### 1.1 解释器

命令：`python --version`

```
Python 3.11.9
```

exit 0。满足 README「Python 3.10 或更高版本」。

命令：`py -3 --version`（README Windows 步骤写的是 `py -m venv`）

```
Unable to create process using 'E:\python.exe --version': ???????????
```

exit 1。本机 `py` 启动器指向不存在的 `E:\python.exe`，属本机环境，不是仓库代码错误。后续改用 `python`。

### 1.2 建虚拟环境

命令：`python -m venv .venv`

exit 0，无输出。

### 1.3 安装运行依赖

命令：`.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt`

exit 0。摘要：

```
Collecting fastapi==0.156.4
Collecting uvicorn==0.54.0
Collecting starlette>=0.46.0 -> starlette-1.9.0
Successfully installed ... fastapi-0.156.4 ... starlette-1.9.0 ... uvicorn-0.54.0
```

钉死版本可安装。传递依赖 starlette 1.9.0 与 DECISIONS.md 所写一致。耗时未单独计时，命令一次成功。

### 1.4 安装测试依赖

命令：`.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements-dev.txt`

exit 0。摘要：

```
Requirement already satisfied: fastapi==0.156.4
Requirement already satisfied: uvicorn==0.54.0
Collecting httpx==0.28.1
Collecting pytest==9.1.1
Successfully installed ... httpx-0.28.1 ... pytest-9.1.1
```

耗时未单独计时，命令一次成功。

## 2. 自动化测试

临时目录通过工作区脚本把 `TEMP`/`TMP` 指到 `E:\muse-bridge\work\TASK-102-weblens`，避免测试库落到系统 TEMP。脚本：`E:\muse-bridge\work\TASK-102-weblens\run_pytest.py`。

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_pytest.py`

（脚本内等价于在仓库根执行 `python -m pytest tests/ -q --tb=short`）

```
.....................................                                    [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.

37 passed, 1 warning in 14.20s
```

exit 0。37 项全部通过，与 README 写的「37 项」一致。警告与 DECISIONS.md D-6 已记录的 TestClient/httpx 弃用警告相同，未当缺陷。

## 3. 真实流程自测 live_selftest

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_live.py`

脚本把 `TEMP`/`TMP` 指到工作目录后，以 `__main__` 执行 `tests/live_selftest.py`（等价于 README 的 `python tests/live_selftest.py`）。该脚本自行在 127.0.0.1:8142 拉起 Uvicorn，结束时 `proc.terminate()` 关掉。

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"<临时库令牌已省略>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="..."></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | page_path=/pricing
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 7 天，最后一天 pv=4 uv=2
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

exit 0。15 个检查点全部通过。令牌出自已销毁的临时库，记录里不保留原文。

## 4. 按 README 启动服务并检查首页

数据库放到工作目录，避免在仓库里生成 `data/weblens.db`。

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_server.py`

脚本设置 `WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-102-weblens\server.db`、`WEBLENS_HOST=127.0.0.1`、`WEBLENS_PORT=8000` 后，以 `__main__` 执行 `app.py`（等价于 README 的 `python app.py`）。

```
INFO:     Started server process [19588]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

探针命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\probe_http.py`

```
GET / -> 200 headers={'server': 'uvicorn', 'cache-control': 'no-store', 'content-type': 'text/html; charset=utf-8', 'x-frame-options': 'DENY', 'x-content-type-options': 'nosniff'}
  body=<!doctype html> ... <title>weblens · 网站访问统计</title> ...
GET /health -> 404 {"detail":"Not Found"}
GET /healthz -> 404 {"detail":"Not Found"}
GET /api/health -> 404 {"detail":"Not Found"}
GET /docs -> 404 {"detail":"Not Found"}
GET /redoc -> 404 {"detail":"Not Found"}
GET /openapi.json -> 404 {"detail":"Not Found"}
GET /tracker.js -> 200 content-type=application/javascript
GET /api/sites -> 401 {"detail":"未登录"}
GET /api/me -> 401 {"detail":"未登录"}
POST /api/login -> 200 cache-control=no-store must_change_password=True username=admin token_len=43
GET /api/me -> 200 {"username":"admin","must_change_password":true}
POST /api/logout -> 200 {"ok":true}
GET /api/me after logout -> 401 {"detail":"登录已过期，请重新登录"}
```

README 没有健康检查路由。`/health`、`/healthz`、`/api/health` 都是 404。首页 200 作为存活检查。

补充探针 `probe_host.py`：带 `Host: evil.example` 建站，返回 `script_url http://evil.example/tracker.js`。带尖括号的 Host 没有打断属性（仍是 `http://127.0.0.1:8000/tracker.js`）。

补充探针 `probe_edges.py`：40 个并发 `POST /api/collect` 全部 201，没有复现 database is locked。非字符串 `url` 被存成路径 `/{'a': 1}`。

相对路径库：工作目录为当前目录，`WEBLENS_DB_PATH=relative-from-cwd.db` 时打印 `DB_PATH relative-from-cwd.db`，`exists_in_work True`，`exists_beside_app False`。

## 5. 关闭服务

后台任务 `01a16977-be52-7821-83bf-28048c093c9a` 已终止（工具返回 killed）。

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\probe_netstat.py`

```
DONE
```

输出里没有 `:8000` 或 `:8142`，端口已不在监听。

## 6. 修复 P1-1 后的验证

只改了 `app.py` 的数据库路径解析（`app.py:27` 至 `app.py:34`）。

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\check_db_path.py`

```
--- relative
stdout E:\muse-bridge\in\TASK-102-weblens\..\..\work\TASK-102-weblens\only-resolved.db
resolved E:\muse-bridge\work\TASK-102-weblens\only-resolved.db
anchored_to_app_dir True
file_exists True
resolved_under_work True
user_row ('admin', 1)
--- absolute
stdout E:\muse-bridge\work\TASK-102-weblens\abs-check.db
absolute_unchanged True
absolute_exists True
```

exit 0。

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_pytest.py`

```
37 passed, 1 warning in 7.48s
```

exit 0。

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_live.py`

```
LIVE SELFTEST: ALL PASS (15 checks)
```

exit 0。

命令：`git status --porcelain`

```
 M app.py
```
