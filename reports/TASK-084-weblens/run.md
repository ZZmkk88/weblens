# TASK-084-weblens 执行记录

- 开工时间：2026-10-22
- 工作目录：E:\muse-bridge\in\TASK-084-weblens
- 角色：本地验收（先审查，再修 P0/P1，最多 5 项）

## 步骤记录

### 0. 开工

已创建本文件。下一步：读 README 与仓库结构，再按说明装环境、跑测试、起服务。

### 1. 环境探查（未装依赖）

命令：

```
python --version
```

输出：

```
Python 3.11.9
```

命令：

```
py --version
```

输出（exit 1）：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

说明：README Windows 步骤写的是 `py -m venv .venv`。本机 `py` 启动器指向不存在的 `E:\python.exe`，无法按字面执行。改用已可用的 `python -m venv`。此为环境限制，不记为项目缺陷。

命令：

```
git -C E:\muse-bridge\in\TASK-084-weblens status --porcelain
```

输出：空（工作区干净）。

仓库含 `.gitignore`（list_dir 默认不显示点文件），忽略 `.venv/`、`data/`、`__pycache__/`、`*.db` 等。

### 2. 创建虚拟环境

README 指定在项目内建 `.venv`。`py` 不可用，改用：

```
python -m venv E:\muse-bridge\in\TASK-084-weblens\.venv
```

结果：exit 0，虚拟环境已创建。

### 3. 安装 requirements.txt

命令：

```
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

结果：exit 0。装上 fastapi==0.156.4、uvicorn==0.54.0，以及传递依赖 starlette==1.9.0、pydantic==2.14.1。pip 提示可升级（24.0 -> 26.2.2），未升级。

### 4. 安装 requirements-dev.txt

命令：

```
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

结果：exit 0。装上 httpx==0.28.1、pytest==9.1.1（fastapi/uvicorn 已满足）。

### 5. 全量 pytest

工作目录：E:\muse-bridge\in\TASK-084-weblens
打算把临时目录改到 E:\muse-bridge\work\TASK-084-weblens\tmp。
第一次跑的时候这个目录还不存在（创建命令早前未执行成功）。
Python 的 tempfile 在目录不存在时会回退到系统 TEMP。
下面第 5b / 6b 节是补建目录后的重跑，临时库落在工作目录。
PYTHONDONTWRITEBYTECODE=1。

命令：

```
.venv\Scripts\python.exe -m pytest tests/ -q
```

辅助脚本（仅设置 TEMP/TMP，不改仓库）：`E:\muse-bridge\work\TASK-084-weblens\run_pytest.py`

结果：exit 0。

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-084-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.16s
```

结论：自动化测试 33 项通过（README 写的是 30 项）。1 条警告来自 FastAPI/Starlette 对 httpx TestClient 的弃用提示，不是失败。

### 6. 真实流程自测 live_selftest.py

辅助脚本：`E:\muse-bridge\work\TASK-084-weblens\run_live.py`（只改 TEMP/TMP）。

命令：

```
.venv\Scripts\python.exe tests/live_selftest.py
```

结果：exit 0。服务由脚本在 127.0.0.1:8142 拉起，结束时 `proc.terminate()` 关掉。

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"(已截断，临时库已随进程销毁)","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="..."></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | page_path=/pricing
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 末项 date=2026-10-21 pv=4 uv=2（按 UTC 切日；本机本地日期为 2026-10-22）
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

### 5b. 补建临时目录后重跑 pytest

`E:\muse-bridge\work\TASK-084-weblens\tmp` 在第 5 步时还不存在，Python tempfile 会回退到系统 TEMP。
补建目录后重跑。

结果：exit 0。

```
33 passed, 1 warning in 11.98s
```

警告原文与第 5 步相同（StarletteDeprecationWarning: install `httpx2` instead）。
临时库落在 `E:\muse-bridge\work\TASK-084-weblens\tmp\weblens-test-hfm8293v`。

### 6b. 重跑 live_selftest

目录建好后有一次重跑没有采到子进程输出，exit 1，没有 PASS/FAIL 文本。
把 stdout/stderr 接到管道后再跑，exit 0，15 项全部 PASS。
同一脚本在第 6 步也已全部 PASS。不记为产品缺陷。

临时库：`E:\muse-bridge\work\TASK-084-weblens\tmp\weblens-live-vj1m08bf`。
趋势末日是 `2026-10-21`（UTC）。本机本地时间此时已是 2026-10-22 00:51，与 README「按 UTC 切日」一致。

### 7. 按 README 起默认服务（127.0.0.1:8000）并检查首页 / 健康检查

数据库改指到工作目录，避免在仓库 `data\` 落库。端口、监听地址用代码默认值。

命令：

```
.venv\Scripts\python.exe app.py
```

环境：`WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-084-weblens\tmp\server-weblens.db`，未设置 `WEBLENS_HOST` / `WEBLENS_PORT` / `PORT`。

启动日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

探测（httpx，未使用 curl/wget）：

```
GET / status=200 ctype=text/html; charset=utf-8 xfo=DENY xcto=nosniff server=uvicorn
  body 以 <!doctype html> ... <title>weblens · 网站访问统计</title> 开头
GET /health status=404 body={"detail":"Not Found"}
GET /api/health status=404 body={"detail":"Not Found"}
GET /docs status=404
GET /redoc status=404
GET /openapi.json status=404
GET /tracker.js status=200 ctype=application/javascript
GET /api/me status=401 body={"detail":"未登录"}
POST /api/login status=200 body 含 username=admin、must_change_password=true（token 省略）
GET /api/me（带 Bearer）status=200 body={"username":"admin","must_change_password":true}
```

关闭：对启动的子进程 `terminate()`。日志里的服务进程已不再接受连接：

```
AFTER_STOP ConnectTimeout timed out
```

`terminate()` 在 Windows 上使进程退出码为 1。请求阶段全部按上面的状态码返回，端口随后关闭。

README 没有写健康检查路径。`/health` 与 `/api/health` 都是 404。首页 200。

### 8. 安全探针（不改仓库）

`probe_security.py` / `probe_collect_413.py`，TestClient。

PBKDF2-HMAC-SHA256、200000 次，口令长度 8 与 65536 都是约 0.07 秒，长口令没有把单次校验放大。
4096 字节口令打到 `/api/login`：401，耗时 0.077 秒。

未登录：`GET /api/sites` 401，`GET /api/me` 401，`GET /api/sites/1/stats` 401，`GET /docs` 404。
用户名 `admin' OR '1'='1`：401，`{"detail":"用户名或密码不正确"}`。

Host 写入埋点片段：

```
Host evil.example:8000 → src="http://evil.example:8000/tracker.js"
Host 含引号和 <script> → 未采用该 Host，仍是 testserver
Host 127.0.0.1:8000 → src="http://127.0.0.1:8000/tracker.js"
```

上报正文大小：

```
70KB  nbytes=71740 status=400 ctype=application/json xfo=DENY body={"detail":"请求体过大"}
140KB nbytes=143420 status=413 ctype=text/plain; charset=utf-8 xfo=None body=Content Too Large
```

### 9. 系统 TEMP 泄漏

第 5/6 步因为工作临时目录当时不存在，各落了一个目录：

- `C:\Users\xzm\AppData\Local\Temp\weblens-test-rmo9h0ai`（mtime 2026-10-22 00:45:06）
- `C:\Users\xzm\AppData\Local\Temp\weblens-live-xfjwhx5u`（mtime 2026-10-22 00:48:21，与第一次 live 的 created_at 16:48:21Z 对齐）

只删除这两个。系统 TEMP 里其余 `weblens-*` 时间更早，不是这次跑出来的，未动。

清理命令：`python E:\muse-bridge\work\TASK-084-weblens\cleanup_my_temp.py`

```
removed C:\Users\xzm\AppData\Local\Temp\weblens-test-rmo9h0ai
removed C:\Users\xzm\AppData\Local\Temp\weblens-live-xfjwhx5u
```

### 10. 审查结束后的全量测试

P0/P1 为空，未改源码。仍按要求重跑一次全量 pytest。

命令：

```
.venv\Scripts\python.exe -m pytest tests/ -q
```

结果：exit 0。

```
33 passed, 1 warning in 5.59s
```

警告仍是 `fastapi/testclient.py:1` 的 StarletteDeprecationWarning。没有失败项。

### 11. git status --porcelain

在仓库根目录执行。输出为空（exit 0）。未改源码，`.venv` 被 `.gitignore` 忽略。


