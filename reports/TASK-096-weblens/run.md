# TASK-096-weblens 执行记录

开工：2026-10-22。工作目录 `E:\muse-bridge\in\TASK-096-weblens`。先读仓库文件，再按 README 装环境、跑测试、起服务。

## 步骤 0：环境探测

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
py -3 --version
```

输出（退出码 1）：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

说明：README Windows 节写的是 `py -m venv`。本机 `py` 启动器指向损坏的 `E:\python.exe`，属环境限制，不计入项目缺陷。后续改用已可用的 `python -m venv`。

命令：

```
git status --porcelain
git rev-parse --show-toplevel
```

输出：

```
（porcelain 为空，工作区干净）
E:/muse-bridge/in/TASK-096-weblens
```

## 步骤 1：安装依赖

虚拟环境放在 `E:\muse-bridge\work\TASK-096-weblens\.venv`（不写进仓库）。

命令：

```
python -m venv E:\muse-bridge\work\TASK-096-weblens\.venv
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

输出摘要（退出码 0）：

```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 click-8.5.0 fastapi-0.156.4 h11-0.16.0 idna-3.20 opentelemetry-api-1.45.1 pydantic-2.14.1 pydantic-core-2.50.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

输出摘要（退出码 0）：

```
Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1
```

已装关键版本：fastapi 0.156.4、uvicorn 0.54.0、starlette 1.9.0、httpx 0.28.1、pytest 9.1.1。与 requirements 钉死版本一致。

## 步骤 2：全量 pytest

临时目录与 pytest 缓存指到 `E:\muse-bridge\work\TASK-096-weblens`（通过 `run_pytest.py` 设置 TEMP/TMP）。

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short -o cache_dir=E:\muse-bridge\work\TASK-096-weblens\pytest_cache
```

输出（退出码 0）：

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-096-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-096-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.00s
```

## 步骤 3：live_selftest（真实 Uvicorn，端口 8142）

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe E:\muse-bridge\in\TASK-096-weblens\tests\live_selftest.py
```

输出（退出码 0，脚本在 finally 里 terminate 子进程）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"tK3oqnXAAhzr9P4cELozjp2MUvZgfkSTQI04NfMX1LU","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | {"id":1,"site_id":"a653c595-7a2a-42ec-884d-1ba63ad8b11b",...}
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="a653c595-7a2a-42ec-884d-1ba63ad8b11b"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 末条 date=2026-10-21 pv=4 uv=2（服务端 UTC 日）
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

服务由脚本拉起并在结束时关掉，未残留在 8142。

## 步骤 4：按 README 在 8000 端口起服务并关掉

数据库与日志放在工作目录：`E:\muse-bridge\work\TASK-096-weblens\smoke.db`、`server.log`。脚本在结束时 `proc.terminate()`，未使用 taskkill。

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-096-weblens\smoke_server.py
```

服务日志原文：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

探测输出摘要（退出码 0）：

```
server_up True pid 34800
GET / status=200 ctype=text/html; charset=utf-8
  x-frame-options=DENY
  x-content-type-options=nosniff
  body=<!doctype html> ... <title>weblens · 网站访问统计</title> ...
GET /tracker.js status=200 ctype=application/javascript
GET /health status=404 body={"detail":"Not Found"}
GET /api/health status=404 body={"detail":"Not Found"}
GET /docs status=404
GET /redoc status=404
GET /openapi.json status=404
GET /api/me status=401 body={"detail":"未登录"}
settings_before_collect []
POST /api/login status=200（must_change_password 为 true，令牌原文略）
nested /api/login status=400 body={"detail":"There was an error parsing the body"}
nested /api/collect status=400 body={"detail":"请求体不是合法 JSON"}
nested /api/change-password status=400 body={"detail":"There was an error parsing the body"}
still_up_after_nested 200
bad_utf collect 400 {"detail":"请求体不是合法 JSON"}
weird types collect 404 {"detail":"站点不存在"}
settings_after_requests_before_good_collect []
collect 201 {"ok":true,...,"page_path":"/pricing"}
settings_after_collect ['uv_salt']
process_poll_before_stop None
process_poll_after_stop 1
port_still_accepts False ReadError
```

说明：仓库没有独立健康检查路由。首页 `GET /` 返回 200，`/health` 与 `/api/health` 为 404，不算 README 承诺落空。深度嵌套 JSON 打到登录与改密接口返回 400，进程仍在。UV 盐在首次成功上报之后才出现在 `settings` 表。进程已退出，8000 不再接受连接。

访问日志里有一条 `203.0.113.9:0 - "POST /api/collect"`：请求带了 `X-Forwarded-For: 203.0.113.9`。uvicorn 默认 `proxy_headers=True`（已装包 `uvicorn/config.py:225`），会改写客户端地址。

## 步骤 5：Host 头探针（工作目录脚本，测完即关服务）

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-096-weblens\probe_host.py
```

输出摘要（退出码 0）：

```
valid_alt_host 200
..."script_url":"http://evil.example/tracker.js","snippet":"<script defer src=\"http://evil.example/tracker.js\" data-weblens-id=\"...\"></script>"
list_alt_host 200
contains_evil True
users [('admin', 1)]
sessions_are_64hex [(64, '11e50965')]
stopped 1
```

带引号的恶意 Host（`evil.example"><script>...`）在步骤 4 里没有写进 snippet，脚本地址仍是 `http://127.0.0.1:8000/tracker.js`。合法主机名 `evil.example` 会反映到当次响应的 `script_url`，不入库。

## 步骤 6：收集测试项数量

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe -m pytest tests/test_app.py --collect-only -q -o cache_dir=E:\muse-bridge\work\TASK-096-weblens\pytest_cache
```

输出末行：

```
33 tests collected in 0.87s
```

其中 `test_ua_classification_cases` 展开为 6 条（expected0–expected5），其余 27 条。与 README 写的 30 项不一致。

## 步骤 7：审查结束后重跑全量测试

未改仓库源码。命令与结果见 `fix-report.md`。pytest：`33 passed, 1 warning in 6.38s`（退出码 0）。live_selftest：`LIVE SELFTEST: ALL PASS (15 checks)`（退出码 0）。

耗时：pytest 自报 6.38s（此前一轮 6.00s，收集 0.87s）。安装、live 自测与 8000 冒烟没有另加秒表，以各命令退出码为准。

## 步骤 8：git status

命令：

```
git status --porcelain
```

输出：空（退出码 0）。仓库相对开工时没有新增或修改的文件。

