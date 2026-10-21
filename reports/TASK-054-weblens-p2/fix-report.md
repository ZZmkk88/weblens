# TASK-054 修复记录

对照 `review.md` 的 P2。每条改完跑一次全量 pytest。不修的条目写在后面。行号是改完后的位置。

## P2-1 活跃页面数不被 Top 10 截断

- 文件：`app.py:596-600` 增加 `COUNT(DISTINCT page_path)`；`app.py:623` 把结果放在响应顶层 `active_pages`，没有放进 `totals`。`static/index.html:507` 改为 `stats.active_pages`。行号是全部改完后的位置。
- 改法：热门页面列表仍是 `LIMIT 10`。看板上的活跃页面数改读区间内的不同路径数。
- 验证：

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.15s
```

退出码 0。另外 `verify_p2_1.py`：11 个路径时 `ACTIVE 11`，`TOP_LEN 10`，`TOTALS {'pv': 11, 'uv': 1}`。

## P2-2 关闭 FastAPI 文档

- 文件：`app.py:306-312`
- 改法：创建应用时把 `docs_url`、`redoc_url`、`openapi_url` 设为 `None`。
- 验证：

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.08s
```

退出码 0。`verify_p2_2.py`：`/docs 404`，`/redoc 404`，`/openapi.json 404`，`/ 200`。

## P2-3 登录框不再预填口令

- 文件：`static/index.html:198`、`static/index.html:200`
- 改法：去掉 `value="admin"` 和 `value="admin123"`。`static/index.html:203` 的「默认账号 admin / admin123，首次登录后请修改密码。」保留。
- 验证：

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.01s
```

退出码 0。`verify_p2_3.py`：`HAS_VALUE_ADMIN False`，`HAS_VALUE_ADMIN123 False`，`HAS_HINT True`。

## P2-4 无条件信任 X-Forwarded-For

- 文件：未改。问题仍在 `app.py:174-181`。
- 改法：没有改。`tests/test_app.py:72` 和 `tests/live_selftest.py:41` 用 `X-Forwarded-For` 区分访客。TestClient 的直连主机是 `testclient`，不是回环地址。若只在直连方为本机时采信该头，两名访客会并成同一个 UV，`tests/test_app.py:297` 的 `{"pv": 4, "uv": 2}` 会失败。不许改测试，所以这条留着。修前探针 `XFF_DISTINCT 2`。

## P2-5 只从请求头读取 User-Agent

- 文件：`app.py:683`
- 改法：删除对 JSON `user_agent` / `userAgent` 的读取，只留 `request.headers.get("user-agent")`。
- 验证：

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.07s
```

退出码 0。`verify_p2_5.py`：请求头 Chrome、正文 Googlebot 时入库 `Chrome Windows 桌面`；请求头 Googlebot 时入库 `机器人 其他 机器人`。

## P2-6 README 写明按 UTC 切日

- 文件：`README.md:13`
- 改法：在统计看板这一条末尾补上「这里的「今天」以及按天切分使用 UTC」。没有改 `app.py:45-46` 和 `app.py:564` 的切日逻辑。
- 验证：

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 1.97s
```

退出码 0。

## P2-7 第一次写入 UV 盐时捕获主键冲突

- 文件：`app.py:205-216`
- 改法：`INSERT` 放进 `try`。`sqlite3.IntegrityError` 时 `rollback`，再 `SELECT` 已提交的盐；读不到则把原错误抛出去。没有处理 `database is locked`。修前 `probe_salt_wal.py` 在读事务还开着时得到的是 `OperationalError: database is locked`，那条路径本轮不另加重试。
- 验证：

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 1.99s
```

退出码 0。`verify_p2_7.py`（未设置 `WEBLENS_UV_SALT`）：`HAPPY_SAME True 64`，`COLLECT 201`，`PAGEVIEWS 1`，`STORED_SALT_LEN 64`。把第一次 SELECT 做成空、让 INSERT 抛出 `IntegrityError` 后，函数返回已有盐：`RECOVERED True 2 1`。

## P2-8 httpx TestClient 弃用警告

- 文件：未改。`requirements-dev.txt:2` 仍是 `httpx==0.28.1`。
- 改法：没有改。任务禁止改已有依赖的版本号，这里不是依赖冲突。全量测试是通过的，警告来自 venv 里的 Starlette，不是断言失败。

## 改动后全量测试

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.02s
```

退出码 0。没有失败用例。警告仍是 Starlette 的 httpx TestClient 弃用提示。没有改 `tests/`，没有 skip / xfail。

## git status

```
git status --porcelain
```

```
 M README.md
 M app.py
 M static/index.html
```
