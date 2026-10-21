# TASK-080-weblens 执行记录

开工时间：2026-10-22
工作目录：E:\muse-bridge\in\TASK-080-weblens
角色：本地验收（Grok Build），审查云端 Muse 交付的 weblens 仓库。

## 步骤 0：建立执行记录

本文件在任何安装、测试、起服务之前创建。后续每完成一步立即追加命令与输出。

## 步骤 1：确认本机 Python

命令：

```
python --version
```

输出：

```
Python 3.11.9
```

退出码 0。README 要求 Python 3.10+，本机 3.11.9 满足。

仓库已有 `.gitignore`（`.venv/`、`data/`、`*.db` 等）。虚拟环境按 README 放在仓库 `.venv`（已被忽略）。测试产生的临时数据库通过 `TEMP`/`TMP` 指到 `E:\muse-bridge\work\TASK-080-weblens\tmp`，服务数据库用 `WEBLENS_DB_PATH` 指到工作目录，避免写进仓库。

## 步骤 2：按 README 创建虚拟环境

README（Windows）写的是 `py -m venv .venv`。本机 `py` 启动器失败。

命令：

```
py -3 -m venv E:\muse-bridge\in\TASK-080-weblens\.venv
```

输出（退出码 1）：

```
Unable to create process using 'E:\python.exe -m venv E:\muse-bridge\in\TASK-080-weblens\.venv': ???????????
```

`py` 指向不存在或无法启动的 `E:\python.exe`。改用 `where.exe python` 找到的 Python 3.11 本体创建虚拟环境。

命令：

```
where.exe python
```

输出：

```
E:\muse-bridge\env\TASK-080-weblens\Scripts\python.exe
C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe
C:\Users\xzm\AppData\Local\Microsoft\WindowsApps\python.exe
```

PATH 上第一个 `python` 是任务预置环境，不是干净环境。虚拟环境改用系统 Python 3.11 创建。

命令：

```
C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe -m venv E:\muse-bridge\in\TASK-080-weblens\.venv
```

输出：无。退出码 0。`.venv` 已创建。

## 步骤 3：安装运行依赖

命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-080-weblens\requirements.txt
```

退出码 0。关键行：

```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 click-8.5.0 fastapi-0.156.4 h11-0.16.0 idna-3.20 opentelemetry-api-1.45.1 pydantic-2.14.1 pydantic-core-2.50.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

钉死版本 fastapi==0.156.4、uvicorn==0.54.0 可安装。传递依赖带入 starlette-1.9.0。

## 步骤 4：安装开发依赖

命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-080-weblens\requirements-dev.txt
```

退出码 0。关键行：

```
Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1
```

httpx==0.28.1、pytest==9.1.1 可安装。

## 步骤 5：全量 pytest

命令（经工作目录脚本设置 TEMP/TMP，避免测试库进系统 TEMP）：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-080-weblens\run_pytest.py
```

脚本实际执行：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short -p no:cacheprovider
```

工作目录：`E:\muse-bridge\in\TASK-080-weblens`。TEMP：`E:\muse-bridge\work\TASK-080-weblens\tmp`。

输出（退出码 0）：

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-080-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.83s
```

## 步骤 6：真实流程自测 live_selftest.py

命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-080-weblens\run_live.py
```

脚本在仓库根目录执行 `tests\live_selftest.py`（其内部在临时库上启动 `app.py`，端口 8142）。退出码 0。输出末尾：

```
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

15 个检查点全部 PASS。自测进程在脚本 finally 里 terminate，未常驻。

补充：同一时段用 TestClient 对畸形 URL、域名、鉴权、`/health` 做了探测，`UNEXPECTED_COUNT 0`（无 5xx）。`/health` 与 `/api/health` 均为 404。该探测不是 README 规定步骤，记在这里供报告引用。

## 步骤 7：按 README 默认地址起服务并关掉

数据库放到工作目录，避免在仓库里生成 `data/weblens.db`（本任务禁止用 del/rm 清理）。

命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-080-weblens\run_server.py
```

环境：`WEBLENS_HOST=127.0.0.1`，`WEBLENS_PORT=8000`，`WEBLENS_DB_PATH=E:\muse-bridge\work\TASK-080-weblens\server-data\weblens.db`。

启动前探测：`PORT_8000_FREE`。进程退出码 0（脚本自身）。服务日志 `E:\muse-bridge\work\TASK-080-weblens\server-8000.log`：

```
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:60895 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:60895 - "GET /health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60895 - "GET /api/health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60895 - "GET /docs HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60895 - "GET /tracker.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:60895 - "POST /api/login HTTP/1.1" 200 OK
INFO:     127.0.0.1:60895 - "GET /api/me HTTP/1.1" 200 OK
```

响应片段：

```
RESP GET / status=200 ... x-frame-options=DENY x-content-type-options=nosniff
  body 含 <title>weblens · 网站访问统计</title>
RESP GET /health status=404 body={"detail":"Not Found"}
RESP GET /api/health status=404 body={"detail":"Not Found"}
RESP GET /docs status=404 body={"detail":"Not Found"}
RESP GET /tracker.js status=200 content-type=application/javascript
  access-control-allow-origin=*
RESP POST /api/login status=200 body 含 "username":"admin","must_change_password":true
RESP GET /api/me status=200 body={"username":"admin","must_change_password":true}
```

脚本在 finally 里 `terminate()` 服务进程。`SERVER_STOPPED returncode 1`（Windows 上被终止的进程常见退出码，日志停在上述请求，没有继续监听的证据）。仓库没有 `/health` 路由，健康检查以首页 200 为准。

## 步骤 8：埋点脚本是否跟随 Host

命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-080-weblens\run_host_snippet.py
```

同一端口再次启动后探测，然后 terminate。退出码 0。片段：

```
CREATE 200 ... "script_url":"http://127.0.0.1:8000/tracker.js"
NORMAL_HAS_127 True
EVIL_HAS_EVIL True
  snippet: <script defer src="http://evil.example/tracker.js" data-weblens-id="..."></script>
QUOTED_HAS_BREAKOUT False
  Host 含引号时响应仍是 http://127.0.0.1:8000/tracker.js
SERVER_STOPPED 1
```

`Host: evil.example` 会被写进埋点脚本（app.py 的 `request.base_url`）。带引号的 Host 这次没有突破属性。服务已停止。

## 步骤 9：确认端口已释放，并重跑全量测试

命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-080-weblens\check_port.py
```

输出（退出码 0）：

```
PORT_8000_FREE
PORT_8142_FREE
```

收尾重跑（与步骤 5 同一脚本）：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-080-weblens\run_pytest.py
```

输出（退出码 0）：

```
.................................                                        [100%]
33 passed, 1 warning in 5.29s
```

警告仍是 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 没有失败项。

## 步骤 10：git status

命令：

```
git -C E:\muse-bridge\in\TASK-080-weblens status --porcelain
```

标准输出为空，退出码 0。本轮没有修改仓库源码。`.venv/` 在 `.gitignore` 第 1 行，不出现在 porcelain 里。
