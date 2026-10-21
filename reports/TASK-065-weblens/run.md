# TASK-065-weblens 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-065-weblens`。临时文件目录 `E:\muse-bridge\work\TASK-065-weblens`。

## 1. 环境探测

命令：

```
py -3 --version
```

输出（exit 1）：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

本机 `py` 启动器指向不存在的 `E:\python.exe`。README Windows 节写的是 `py -m venv`。这是本机启动器损坏，不是仓库代码错误。后续改用 `python` 执行同等步骤。

命令：

```
python --version
```

输出（exit 0）：

```
Python 3.11.9
```

满足 README「Python 3.10 或更高版本」。

命令：

```
git -C E:\muse-bridge\in\TASK-065-weblens status --porcelain
git -C E:\muse-bridge\in\TASK-065-weblens log -1 --oneline
```

输出：

```
(status 空，工作区干净)
00c1a38 fix(TASK-061): 会话令牌改 SHA-256 哈希入库；未认证接口请求体 128KiB 硬上限
```

`Get-ChildItem -Force` 见到 `.gitignore`（list_dir 默认不显示点文件）。端口探测 `netstat -ano | findstr ":8000 :8142"` 只命中一条远端 IPv6 地址里的 `:8000:` 字样，本机 8000 / 8142 没有 LISTENING。

环境变量 `PORT`、`WEBLENS_PORT`、`WEBLENS_HOST` 本次未另打印；后续起服务时显式设置 `WEBLENS_DB_PATH`，避免把数据库写进仓库。

## 2. 安装依赖

虚拟环境放在临时目录，不写进仓库：`E:\muse-bridge\work\TASK-065-weblens\.venv`。

命令（exit 0）：

```
python -m venv E:\muse-bridge\work\TASK-065-weblens\.venv
```

命令（exit 0）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-065-weblens\requirements.txt
```

输出片段：

```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 click-8.5.0 fastapi-0.156.4 h11-0.16.0 idna-3.20 opentelemetry-api-1.45.1 pydantic-2.14.1 pydantic-core-2.50.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

命令（exit 0）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-065-weblens\requirements-dev.txt
```

输出片段：

```
Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1
```

`RequestBodyLimitMiddleware` 在已安装的 `starlette/middleware/body_limit.py:30` 存在，构造参数是 `max_body_size`。

## 3. 自动化测试

工作目录 `E:\muse-bridge\in\TASK-065-weblens`。命令（exit 0，约 5.58s）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pytest tests -q -o cache_dir=E:\muse-bridge\work\TASK-065-weblens\pytest_cache
```

输出：

```
..............................                                           [100%]
============================== warnings summary ===============================
..\..\work\TASK-065-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-065-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
30 passed, 1 warning in 5.58s
```

30 项全部通过。警告与 DECISIONS.md D-6 记录的 httpx/TestClient 弃用警告一致，未导致失败。

## 4. 真实流程自测

命令（exit 0）。为让脚本自建的临时库落在任务临时目录，用 `cmd /c set TMP=...&& set TEMP=...` 包了一层：

```
cmd /c "set TMP=E:\muse-bridge\work\TASK-065-weblens&& set TEMP=E:\muse-bridge\work\TASK-065-weblens&& E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe tests\live_selftest.py"
```

输出（登录令牌为临时库签发，服务已退出，此处截断令牌）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"7Nma…IA4","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="9e149cbe-1c47-4a46-ab5b-12840426eda9"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | end date 2026-10-21 pv 4 uv 2，前 6 天为 0
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

自测监听 `127.0.0.1:8142`（`tests/live_selftest.py:14`），不是 README 的 8000。脚本在 `finally` 里 `terminate` 了子进程。

## 5. 按 README 端口起服务并探测

数据库放到临时目录。命令：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-065-weblens\smoke.py
```

脚本内设置 `WEBLENS_HOST=127.0.0.1`、`WEBLENS_PORT=8000`、`WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-065-weblens\smoke.db`，然后 `python app.py`，探测完 `terminate`。

stderr 启动行：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

首页与路由（摘录）：

```
HOME status=200 len=28345 has_weblens=True xfo=DENY nosniff=nosniff
HTTP /health status=404 body={"detail":"Not Found"}
HTTP /api/health status=404
HTTP /healthz status=404
HTTP /docs status=404
HTTP /redoc status=404
HTTP /openapi.json status=404
OK /tracker.js status=200
HTTP /api/me status=401 body={"detail":"未登录"}
HTTP /api/sites status=401
HTTP /app.py status=404
OK /api/login status=200 must_change_password=true
OK /api/sites status=200  （未改密也能建站）
big70_len 71708 -> HTTP 400 {"detail":"请求体过大"}  xfo=DENY
huge_len 204828 -> HTTP 413 body=Content Too Large  xfo=None nosniff=None
nested_len 8000 -> HTTP 500 body=Internal Server Error
longpw_len 100037 -> HTTP 401 elapsed=0.072s
```

500 的原文在 `server-stderr.log`：

```
File "E:\muse-bridge\in\TASK-065-weblens\app.py", line 717, in collect
    data = json.loads(raw_body.decode("utf-8"))
RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string
```

进程结束后退出码 1（Windows 上 `terminate` 的常见结果）。复查监听：

```
netstat -ano | findstr "LISTENING" | findstr ":8000 :8142"
```

无匹配（findstr 退出码 1），8000 与 8142 都没有留下 LISTENING。

另一次嵌套 JSON 对照（`probe_nested.py`，同样起在 8000 后关掉）：

```
/api/login 8000 400 {"detail":"There was an error parsing the body"}
/api/login 12001 400 {"detail":"There was an error parsing the body"}
/api/collect 8000 500 Internal Server Error
/api/change-password 8000 400 {"detail":"There was an error parsing the body"}
```

只有手写 `json.loads` 的 `/api/collect` 返回 500。FastAPI 代解析的登录和改密接口返回 400。

## 6. 修复 P1-1 后的验证

改动只在 `app.py`：`json.loads` 增加捕获 `RecursionError`。

命令（exit 0）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-065-weblens\probe_nested.py
```

```
/api/collect 8000 400 {"detail":"请求体不是合法 JSON"}
EXIT 1
```

退出码 1 仍是关掉子进程的结果。`/api/collect` 已从 500 变为 400。

单条回归（exit 0，4.80s）：

```
30 passed, 1 warning in 4.80s
```

全量重跑（exit 0，4.68s）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pytest tests -q -o cache_dir=E:\muse-bridge\work\TASK-065-weblens\pytest_cache
```

```
30 passed, 1 warning in 4.68s
```

全量自测（exit 0）：

```
cmd /c "set TMP=E:\muse-bridge\work\TASK-065-weblens&& set TEMP=E:\muse-bridge\work\TASK-065-weblens&& E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe tests\live_selftest.py"
```

```
LIVE SELFTEST: ALL PASS (15 checks)
```

收尾：

```
git -C E:\muse-bridge\in\TASK-065-weblens status --porcelain
```

```
 M app.py
```

