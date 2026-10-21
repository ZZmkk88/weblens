# TASK-020-weblens 执行记录

开工时间：2026-10-21。工作目录：`E:\muse-bridge\in\TASK-020-weblens`。先审查再按清单修 P0/P1。

## 步骤 1：确认解释器

`py -3 --version` 第一次输出 `Python 3.11.9`。随后裸 `python --version` 失败，原文：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

`where.exe python` 看到可用解释器：

- `C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe`
- 已有虚拟环境 `E:\muse-bridge\env\TASK-020-weblens\Scripts\python.exe`（pyvenv.cfg：home = Python 3.11.9，已装 fastapi 0.156.4、uvicorn 0.54.0）

按 README 在工作目录另建虚拟环境，避免把 `.venv` 写进待审仓库。

## 步骤 1b：本轮复核解释器（2026-10-21 续跑）

`py -3 --version` 失败，原文：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

`where.exe python` 输出：

```
E:\muse-bridge\env\TASK-020-weblens\Scripts\python.exe
C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe
C:\Users\xzm\AppData\Local\Microsoft\WindowsApps\python.exe
```

`C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe --version` 输出 `Python 3.11.9`。

`py` 启动器坏了，属于本机环境限制。README 的 Windows 安装命令 `py -m venv .venv` 在这台机器上会同样失败。后续改用 Python 3.11.9 全路径，在 `E:\muse-bridge\work\TASK-020-weblens\venv` 建虚拟环境，不把 `.venv` 写进待审仓库。

## 步骤 2：安装依赖

命令：

```
C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe -m venv E:\muse-bridge\work\TASK-020-weblens\venv
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-020-weblens\requirements-dev.txt
```

`python -m venv` 退出码 0。`pip install` 退出码 0，末尾：

```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 certifi-2026.10.19 click-8.5.0 colorama-0.4.6 fastapi-0.156.4 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.1 packaging-26.3 pluggy-1.7.0 pydantic-2.14.1 pydantic-core-2.50.1 pygments-2.21.0 pytest-9.1.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

钉死版本 fastapi==0.156.4、uvicorn==0.54.0、httpx==0.28.1、pytest==9.1.1 均安装成功。未改 requirements 版本号。

## 步骤 3：全量 pytest

工作目录 `E:\muse-bridge\in\TASK-020-weblens`。命令：

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

退出码 0。输出：

```
.........................                                                [100%]
============================== warnings summary ===============================
..\..\work\TASK-020-weblens\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-020-weblens\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 1.90s
```

与 README 写的「自动化测试 25 项」一致。警告来自 Starlette 对 httpx TestClient 的弃用提示，测试本身通过。未重试。

## 步骤 4：live_selftest

命令：

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe tests\live_selftest.py
```

退出码 0。15 个检查点全部 PASS，末行：

```
LIVE SELFTEST: ALL PASS (15 checks)
```

脚本自己在 127.0.0.1:8142 拉起 uvicorn，跑完后 `proc.terminate()` 关掉。登录响应里 `must_change_password` 为 true。建站域名被规范成 `demo.example.com`。今日统计 `{'pv': 4, 'uv': 2}`。删除后统计接口 404。

## 步骤 5：按 README 起默认端口并做探针

数据库改到工作目录，避免在仓库里生成 `data/weblens.db`。命令：

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-020-weblens\smoke_probe.py
```

退出码 0。服务起来过，探针结束时进程已停（`SERVER_STOPPED 1`，`terminate` 的退出码）。要点：

```
GET / 200 text/html; charset=utf-8
HOME_HAS_WEBLENS True
HOME_HAS_PASSWORD_VALUE True
GET /health 404 ACAO None
GET /docs 200 ACAO None
GET /openapi.json 200 ACAO None
GET /api/me 401 ACAO None
OPTIONS /api/login 200 ACAO * ALLOW_HEADERS content-type
POST /api/login bad 401 ACAO *
LOGIN_A 200 LOGIN_B 200
COLLECT_11 ok
TOP_PAGES_LEN 10 PV 11
HUGE_REFERRER 201
STORED_REFERRER_LEN 30000
CHANGE_PASSWORD 200 {"ok":true}
ME_AFTER_CHANGE tokenA 200 tokenB 200
LISTEN_LINES
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       28188
```

没有 `/health`（404）。README 也没声明这个路径，不记为缺陷。首页 200。

第二次确认跨源响应头（请求带 `Origin: https://evil.example`）：

```
GET / origin 200 ACAO *
BODY_PASSWORD True HINT True
OPENAPI 200 ACAO *
LISTEN TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       14884
```

第三次看监听进程是不是自己拉起来的：

```
LISTEN TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       27196
POPEN 28296 ALIVE None
ProcessId ParentProcessId Name
    27196           28296 python.exe
```

监听进程是本次 `python app.py` 的子进程，地址是 `0.0.0.0:8000`。三次探针结束都执行了 `terminate`，下一次都能重新绑定 8000，端口已释放。

## 步骤 6：P1-1 改默认监听后再测

`app.py` 默认 host 改为 `127.0.0.1`。pytest：`25 passed, 1 warning in 1.60s`。绑定探针：`GET / 200`，`LISTEN TCP 127.0.0.1:8000`，`STOPPED 1`。

## 步骤 7：P1-2 收紧 CORS 后再测

pytest：`25 passed, 1 warning in 1.59s`。探针：`GET /` 与 `POST /api/login` 的 ACAO 为 None；`OPTIONS /api/login` 为 405；`OPTIONS /api/collect` 为 204 且 ACAO `*`；`POST /api/collect` 为 201 且 ACAO `*`；`/tracker.js` 为 200 且含 `/api/collect`。`STOPPED 1`。

## 步骤 8：P1-3 不改代码

改密撤销其他会话会让 `tests/test_app.py` 的模块级 `auth` fixture 失效。未改 `app.py` 的 `change_password`。

## 步骤 9：P1-4 限制采集请求体

pytest：`25 passed, 1 warning in 1.61s`。探针：正常来源存 `google.com`；`Bing.com` 存 `bing.com`；30000 字符来源入库长度为 0；70089 字节请求体 `FAT 400 {"detail":"请求体过大"}`。`STOPPED 1`。

## 步骤 10：全部改完后的全量测试

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=line
```

`25 passed, 1 warning in 1.60s`

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe tests\live_selftest.py
```

`LIVE SELFTEST: ALL PASS (15 checks)`，退出码 0。

## 步骤 11：git status

```
git status --porcelain
```

```
 M app.py
```

`git diff --stat`：`app.py | 61 +++++++++++++++++++++++++++++++++++++++++++------------------`，1 file changed, 43 insertions, 18 deletions。

