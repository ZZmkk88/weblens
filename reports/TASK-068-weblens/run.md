# TASK-068-weblens 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-068-weblens`。先审查再按清单修 P0/P1。

## 环境

命令：`python --version` 与 `python -c "import sys; print(sys.executable); print(sys.version)"`

```
Python 3.11.9
E:\muse-bridge\env\TASK-068-weblens\Scripts\python.exe
3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
```

README Windows 步骤写的是 `py -m venv .venv`。本机 `py -3 -c "import sys; print(sys.version)"` 失败原文：

```
Unable to create process using 'E:\python.exe -c "import sys; print(sys.version)"': ???????????
```

判定为环境限制（py 启动器指向不存在的 E:\python.exe），不记为项目缺陷。后续命令使用已有任务虚拟环境里的 `python`（3.11.9，满足 README「Python 3.10+」）。

`git status --porcelain` 开工时无输出（工作区干净）。`.gitignore` 已忽略 `.venv/`、`data/`、`*.db`。

## 安装依赖

命令（cwd = `E:\muse-bridge\in\TASK-068-weblens`）：`python -m pip install -r requirements-dev.txt`

结果摘要（exit 0）：

```
Requirement already satisfied: fastapi==0.156.4
Requirement already satisfied: uvicorn==0.54.0
Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1
```

传递依赖实查：starlette 1.9.0，pydantic 2.14.1。运行依赖在本环境里事先已装好，开发依赖本次装上。

## 自动化测试

命令（cwd = `E:\muse-bridge\in\TASK-068-weblens`）：`python -m pytest tests/ -q --tb=short`

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\env\TASK-068-weblens\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\env\TASK-068-weblens\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 4.82s
```

exit 0。32 项全部通过。警告与 DECISIONS.md D-6 记录的 httpx/TestClient 弃用警告一致。

## 真实流程自测

命令：`python tests/live_selftest.py`

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"<临时库令牌已打码>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | ... "domain":"demo.example.com" ...
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="f93fe9eb-9a2f-41c7-a9f8-7147b78a44ec"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | {"ok":true,...,"pageview_id":4,"page_path":"/pricing"}
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首 | [{'path': '/pricing', 'count': 3}, {'path': '/docs', 'count': 1}]
PASS 来源排行正确：google.com 3 次居首 | [{'domain': 'google.com', 'count': 3}, {'domain': 'bing.com', 'count': 1}]
PASS 近 7 天趋势长度与合计正确 | 7 天，合计 pv 4；末日 2026-10-21 pv 4 uv 2
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

exit 0。脚本在 127.0.0.1:8142 拉起 uvicorn 后自行 terminate。令牌打码是因为该行含一次性会话令牌；其余为真实输出。

## 按 README 起服务（127.0.0.1:8000）

数据库改到工作目录，避免在仓库里落下 `data/weblens.db`。启动脚本：`E:\muse-bridge\work\TASK-068-weblens\serve.py`（设置 `WEBLENS_DB_PATH`、`WEBLENS_HOST=127.0.0.1`、`WEBLENS_PORT=8000` 后执行 `app.py`）。

启动输出：

```
INFO:     Started server process [12644]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

探测命令：`python E:\muse-bridge\work\TASK-068-weblens\probe_http.py`

```
GET / status=200 xfo=DENY nosniff=nosniff ctype=text/html; charset=utf-8 body=<!doctype html> ... <title>weblens · 网站访问统计</title>
GET /health status=404 xfo=DENY nosniff=nosniff ctype=application/json body={"detail":"Not Found"}
GET /docs status=404 ... {"detail":"Not Found"}
GET /redoc status=404 ... {"detail":"Not Found"}
GET /openapi.json status=404 ... {"detail":"Not Found"}
GET /tracker.js status=200 ctype=application/javascript body=(function () { ... data-weblens-id ...
GET /api/sites status=401 body={"detail":"未登录"}
POST /api/login status 200 must_change True user admin
GET /api/me 200 {"username":"admin","must_change_password":true}
POST /api/collect unknown 404 cors None {"detail":"站点不存在"}
```

README 没有定义 `/health`。首页 200，未登录接口 401，默认账号可登录。`/docs`、`/redoc`、`/openapi.json` 均为 404。

同轮逻辑探针 `probe_logic.py`（TestClient，库在工作目录）补充：

```
POST collect 70KB status=400 body={"detail":"请求体过大"} xfo=DENY
POST collect 140KB status=413 xfo=None nosniff=None body=Content Too Large
POST sql name status=200 name 原样入库，未执行 SQL
POST bad domain status=400 body={"detail":"域名格式不正确"}
users count=1 names=['admin'] hash_len=64 salt_len=32 hash_is_plaintext=False
```

第二次 `init_db` 换了初始用户名，用户数仍为 1。

关闭服务后再次执行 `probe_http.py`，连接失败原文：

```
httpx.ConnectError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。
```

8000 已不再监听。

## 审查结论后的全量重跑（未改源码）

命令（cwd = 仓库根）：`python -m pytest tests/ -q --tb=short; python tests/live_selftest.py`

```
32 passed, 1 warning in 3.41s
LIVE SELFTEST: ALL PASS (15 checks)
```

pytest 警告仍是 StarletteDeprecationWarning（httpx / TestClient）。live_selftest 15 条均为 PASS。登录行里的一次性 token 不写入本记录。

## 收尾 git status

命令：`git -C E:\muse-bridge\in\TASK-068-weblens status --porcelain`

无输出（exit 0）。仓库工作区与开工时一样干净。审查报告在 `E:\muse-bridge\out\TASK-068-weblens\`，没有改仓库源码。
