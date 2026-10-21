# TASK-058-weblens 执行记录

开工时间：2026-10-21。工作目录：E:\muse-bridge\in\TASK-058-weblens。先审查再按清单修 P0/P1。

## 0. 环境探测

命令：

```
py -3 --version
```

输出（exit 1）：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

本机 `py` 启动器指向不存在的 `E:\python.exe`，README 的 Windows 写法 `py -m venv .venv` 在这台机器上无法执行。改用已可用的 `python`（不把这算成仓库缺陷，属本机启动器损坏）。

命令：

```
python --version
where.exe python
```

输出：

```
Python 3.11.9
```

`where.exe python` 的输出在下一步补上（本步先确认版本满足 README 要求的 3.10+）。

命令：

```
git -C E:\muse-bridge\in\TASK-058-weblens status --porcelain
```

输出：空（工作区干净，exit 0）。

虚拟环境不放进仓库，建在工作目录：

```
python -m venv E:\muse-bridge\work\TASK-058-weblens\venv
```

输出：exit 0。

`where.exe python` 输出：

```
E:\muse-bridge\env\TASK-058-weblens\Scripts\python.exe
C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe
C:\Users\xzm\AppData\Local\Microsoft\WindowsApps\python.exe
```

PATH 上第一个 python 是已有环境 `E:\muse-bridge\env\TASK-058-weblens`（已装 fastapi 0.156.4 / uvicorn 0.54.0，未见 pytest）。验收改用新建的干净虚拟环境 `E:\muse-bridge\work\TASK-058-weblens\venv`，避免混用。

## 1. 安装运行依赖

命令：

```
E:\muse-bridge\work\TASK-058-weblens\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-058-weblens\requirements.txt
```

输出（exit 0，节选）：

```
Collecting fastapi==0.156.4
Collecting uvicorn==0.54.0
Successfully installed ... fastapi-0.156.4 ... uvicorn-0.54.0
```

钉死版本可以装上。

## 2. 安装开发依赖

命令：

```
E:\muse-bridge\work\TASK-058-weblens\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-058-weblens\requirements-dev.txt
```

输出（exit 0，节选）：

```
Collecting httpx==0.28.1
Collecting pytest==9.1.1
Successfully installed ... httpx-0.28.1 ... pytest-9.1.1
```

## 3. 全量 pytest

命令（临时目录改到 E:\muse-bridge\work\TASK-058-weblens\tmp，避免写入系统 TEMP；PYTHONPYCACHEPREFIX 指向工作目录，避免仓库里生成 __pycache__）：

```
E:\muse-bridge\work\TASK-058-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

工作目录：E:\muse-bridge\in\TASK-058-weblens

输出（exit 0）：

```
............................                                             [100%]
============================== warnings summary ===============================
..\..\work\TASK-058-weblens\venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.

28 passed, 1 warning in 6.98s
```

收集到 28 项，不是 README 写的 25 项。警告与 DECISIONS.md D-6 已记录的 TestClient/httpx 弃用警告一致，测试本身通过。耗时 6.98s。

## 4. 真实流程自测 live_selftest

命令：

```
E:\muse-bridge\work\TASK-058-weblens\venv\Scripts\python.exe tests/live_selftest.py
```

工作目录：E:\muse-bridge\in\TASK-058-weblens。TEMP 指向 E:\muse-bridge\work\TASK-058-weblens\tmp。脚本自己把服务绑到 127.0.0.1:8142。

输出（exit 0，耗时 4.677s；登录响应里的 token 已截断）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"（已截断）","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="..."></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | end date 2026-10-21 pv 4 uv 2，共 7 天
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
EXIT 0
```

15 个检查点与 README 的「15」一致。脚本在 finally 里 terminate 了子进程。

## 5. 按 README 启动服务并检查首页 / 健康检查

数据库改到工作目录，避免在仓库里生成 data/weblens.db。未设置 WEBLENS_HOST / WEBLENS_PORT。继承的 PORT 为 None。

命令：

```
E:\muse-bridge\work\TASK-058-weblens\venv\Scripts\python.exe app.py
```

工作目录：E:\muse-bridge\in\TASK-058-weblens。WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-058-weblens\run-server.db。

stderr（服务起来后的原文）：

```
INFO:     Started server process [32108]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

启动到首次 GET / 返回，用时 1.49s。

探针结果：

```
GET /            status=200 ctype=text/html; charset=utf-8 len=28316  HAS_WEBLENS True
GET /health      status=404
GET /api/health  status=404
GET /healthz     status=404
GET /docs        status=404
GET /redoc       status=404
GET /openapi.json status=404
GET /tracker.js  status=200  HAS /api/collect 与 data-weblens-id
POST /api/login  admin/admin123 -> 200 must_change_password True（有 token）
POST /api/collect 超过 64KiB -> 400 {"detail":"请求体过大"}
```

首页响应头只有 `server: uvicorn` 和 `content-type`，没有 X-Frame-Options / CSP / X-Content-Type-Options。

README 没有声明健康检查路由，代码里也没有。`/health`、`/api/health`、`/healthz` 都是 404。存活依据是首页 200 和 uvicorn 监听行。

停止方式：对子进程 terminate。输出 `STOP_TERMINATE 1`（Windows 上被终止的进程退出码为 1）。随后连接 127.0.0.1:8000 得到 `PORT_8000_CLOSED TimeoutError`。服务已关掉。整段耗时 1.579s。

## 6. 边界探针（修之前）

公开上报在畸形 IPv6 referrer 上抛未捕获异常。探针命令：

```
E:\muse-bridge\work\TASK-058-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-058-weblens\probe_edges.py
```

失败原文（节选）：

```
File "E:\muse-bridge\in\TASK-058-weblens\app.py", line 710, in collect
    referrer_domain = domain_from_value(str(referrer_value))
File "E:\muse-bridge\in\TASK-058-weblens\app.py", line 88, in domain_from_value
    host = urllib.parse.urlparse(raw).hostname or ""
ValueError: Invalid IPv6 URL
```

触发体：`referrer` 为 `http://[`。同一输入在四个函数上的结果（probe_urlparse.py）：

```
EXC  domain_from_value 'http://[' -> ValueError: Invalid IPv6 URL
EXC  parse_page_path 'http://[' -> ValueError: Invalid IPv6 URL
EXC  normalize_domain_input 'http://[' -> ValueError: Invalid IPv6 URL
EXC  page_hostname 'http://[' -> ValueError: Invalid IPv6 URL
```

`http://[::1` 与 `http://[gggg::1]/` 同样是 ValueError。合法的 `http://[::1]/x` 可以解析出 hostname `::1`。

## 7. 修复 P1-1 后的验证

只改了 `app.py` 里四个 URL 解析函数。探针：

```
E:\muse-bridge\work\TASK-058-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-058-weblens\probe_p1_after.py
```

输出节选：

```
domain_from_value http://[ -> ''
collect bad referrer 201 ... page_path=/kept
collect bad url 400 {"detail":"页面地址格式不正确"}
create bad domain 400 {"detail":"域名格式不正确"}
stored [('/kept', '')]
```

紧接着回归：

```
...\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
28 passed, 1 warning in 4.93s
```

## 8. 全量重跑

```
...\venv\Scripts\python.exe -m pytest tests/ -q --tb=line
28 passed, 1 warning in 4.77s
EXIT 0

...\venv\Scripts\python.exe tests/live_selftest.py
LIVE SELFTEST: ALL PASS (15 checks)
ELAPSED_S 2.83 EXIT 0
```

## 9. git status --porcelain

```
git -C E:\muse-bridge\in\TASK-058-weblens status --porcelain
 M app.py
```

`git diff --stat`：`app.py | 47 +++++++++++++++++++++++++++++++----------------`。未 commit。




