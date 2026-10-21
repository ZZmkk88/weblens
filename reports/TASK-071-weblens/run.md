# TASK-071-weblens 执行记录

开工时间：2026-10-21（本地执行方 Grok Build）。工作目录：E:\muse-bridge\in\TASK-071-weblens。本文件随步骤追加，不攒到最后。

## 步骤 0 环境探测

命令：`py -3 --version`；`python --version`；`git status --porcelain`；`git rev-parse --is-inside-work-tree`；`git log -1 --oneline`

输出摘要：

- `py -3 --version` → `Python 3.11.9`
- `python --version` → `Unable to create process using 'E:\python.exe --version'`（系统 python 指向失效路径）
- `git status --porcelain` → 无输出（工作区干净）
- `git rev-parse --is-inside-work-tree` → `true`
- `git log -1 --oneline` → `91e08ef docs(TASK-065): DECISIONS.md 记 D-10（深度嵌套 JSON 收口决定）`

说明：虚拟环境与运行期数据库放在 `E:\muse-bridge\work\TASK-071-weblens`，不写进仓库（任务禁止 del/rm，避免留下无法删除的 `.venv` 与 `data\weblens.db`）。

## 步骤 1 选择解释器并创建虚拟环境

命令：`py -0p`

输出：
```
 -V:3.14 *        E:\python.exe
 -V:3.11          C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe
```

命令：`py -3 -m venv E:\muse-bridge\work\TASK-071-weblens\.venv`

输出：`Unable to create process using 'E:\python.exe -m venv ...'（退出码 1）`。`py -3` 选中已损坏的 3.14。

命令：`C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe --version`

输出：`Python 3.11.9`（满足 README「Python 3.10 或更高」）。

命令：`C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe -m venv E:\muse-bridge\work\TASK-071-weblens\.venv`

输出：退出码 0，无报错。

## 步骤 2 安装依赖

命令：`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-071-weblens\requirements.txt -r E:\muse-bridge\in\TASK-071-weblens\requirements-dev.txt`

输出摘要（退出码 0）：
```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 certifi-2026.10.19 click-8.5.0 colorama-0.4.6 fastapi-0.156.4 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.1 packaging-26.3 pluggy-1.7.0 pydantic-2.14.1 pydantic-core-2.50.1 pygments-2.21.0 pytest-9.1.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```
钉死版本均安装成功：fastapi==0.156.4、uvicorn==0.54.0、httpx==0.28.1、pytest==9.1.1。传递依赖含 starlette==1.9.0（与 DECISIONS.md D-9 所称 starlette 1.9.0 一致）。

## 步骤 3 全量 pytest

命令（工作目录 `E:\muse-bridge\in\TASK-071-weblens`）：

`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short`

输出（退出码 0）：
```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-071-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-071-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.29s
```

## 步骤 4 真实流程自测 live_selftest

命令（工作目录 `E:\muse-bridge\in\TASK-071-weblens`）：

`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe tests\live_selftest.py`

输出（退出码 0，临时库由脚本自己建在系统临时目录并随进程结束；登录令牌已截断）：
```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"yL8x…（已截断）","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain 为 demo.example.com
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="…"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | page_path=/pricing
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 末项 {'date': '2026-10-21', 'pv': 4, 'uv': 2}，前 6 天为 0
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```
服务由脚本 `proc.terminate()` 关掉，监听端口 8142。

更正：步骤 0 把 `py -3 --version` 记成 `Python 3.11.9` 不准确。复测命令 `py -3 --version` 退出码 1，输出 `Unable to create process using 'E:\python.exe --version'`。可用解释器以步骤 1 的 `py -0p` 与 Python 3.11.9 全路径为准。

## 步骤 5 按 README 端口起服务

命令：`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-071-weblens\smoke.py`

环境变量：`WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-071-weblens\smoke.db`，`WEBLENS_HOST=127.0.0.1`。先按 README 试 8000，被占用后再用 18765。

8000 上已有别的程序（不是本次启动的 weblens）。预检 `GET http://127.0.0.1:8000/` → 200，正文标题为 `freshfeeds · 清泉阅读`。

weblens 绑定 8000 的日志（退出码 3）：
```
ERROR:    [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

改 `WEBLENS_PORT=18765` 后：
```
INFO:     Uvicorn running on http://127.0.0.1:18765 (Press CTRL+C to quit)
GET / -> 200 content-type=text/html; charset=utf-8 x-frame-options=DENY x-content-type-options=nosniff
GET /health -> 404 {"detail":"Not Found"}
GET /api/health -> 404 {"detail":"Not Found"}
GET /api/me -> 401 {"detail":"未登录"}
GET /docs -> 404 {"detail":"Not Found"}
GET /tracker.js -> 200 content-type=application/javascript
```
首页正文含 `weblens`（脚本判断 `b"weblens" in body` 为真；随后单独请求确认标题为 `<title>weblens · 网站访问统计</title>`）。进程 `terminate()` 后返回码 1，日志在 shutdown 前已写完访问记录，服务已停。未动 8000 上的既有进程。

## 步骤 6 畸形 Unicode 探针（修复前）

命令：`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-071-weblens\probe2.py`

数据库：`E:\muse-bridge\work\TASK-071-weblens\probe2.db`。JSON 里的 `\ud800` / `\u0000` 以原始 UTF-8 字节送入。

输出摘要：
```
EXC sur-user UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' ... position 2
EXC sur-pass UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' ... position 1
401 admin-nul （用户名 admin\u0000hack + 正确密码，没有登录成功）
200 nul-name （站点名 a\u0000b 被接受并入库）
EXC sur-name UnicodeEncodeError
400 sur-domain {"detail":"域名格式不正确"}
EXC sur-url UnicodeEncodeError
400 nul-url {"detail":"页面路径不合法"}
EXC sur-ref UnicodeEncodeError
201 sur-refdom （显式 referrer_domain 含代理字符时被丢弃，上报仍成功）
201 ok-after （前面的异常没有打挂进程内的后续请求）
host-snippet src="http://evil.example/tracker.js" （Host 被写进埋点地址）
xfh-snippet src="http://testserver/tracker.js" （X-Forwarded-Host 未改写）
sqli 名称原样入库，sites 表仍在（sites-left 3）
404 docs
cors-acao None
```

真实 uvicorn（`http_surrogate.py`，端口 18766，库 `surrogate.db`）：
```
title <title>weblens · 网站访问统计</title>
surrogate-login 500 Internal Server Error
login-after 200 （服务还在，正常登录成功）
stopped 1
```
登录请求正文为 ASCII：`{"username":"ad\ud800min","password":"x"}`。





