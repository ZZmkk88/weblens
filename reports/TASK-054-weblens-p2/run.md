# TASK-054 weblens P2 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-054-weblens-p2`。本轮只处理上一轮 `E:\muse-bridge\out\TASK-020-weblens\review.md` 中的 P2，按报告顺序，最多 8 条。P0/P1 上一轮已修，本轮不重开。

## 基线：解释器与全量 pytest

复用已有虚拟环境 `E:\muse-bridge\work\TASK-020-weblens\venv`（与本仓库 `requirements-dev.txt` 钉死的 fastapi/uvicorn/httpx/pytest 相同）。工作目录为仓库根。

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
$py = "E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe"
& $py --version
$sw = [Diagnostics.Stopwatch]::StartNew()
& $py -m pytest tests/ -q --tb=short
Write-Output "EXIT $LASTEXITCODE"
$sw.Stop()
Write-Output "ELAPSED_MS $($sw.ElapsedMilliseconds)"
git status --porcelain
```

输出：

```
Python 3.11.9
.........................                                                [100%]
============================== warnings summary ===============================
..\..\work\TASK-020-weblens\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-020-weblens\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 2.63s
```

退出码 0。耗时 2.63s（pytest 自报）。警告来自 venv 里的 Starlette，不是本仓库断言失败。

## P2 现状探针

脚本：`E:\muse-bridge\work\TASK-054-weblens-p2\probe_p2.py`。数据库写在同一工作目录，不进仓库。

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-054-weblens-p2\probe_p2.py
```

退出码 1。盐竞争段在对方 `commit` 时得到 `sqlite3.OperationalError: database is locked`，前面的检查已经打出：

```
DOCS 200 REDOC 200 OPENAPI 200
HOME 200
HAS_VALUE_ADMIN True
HAS_VALUE_ADMIN123 True
HAS_HINT True
TOP_PAGES_LEN 10
STATS_KEYS ['period', 'site', 'top_pages', 'top_referrers', 'totals', 'trend']
HAS_ACTIVE_PAGES False
UA_OVERRIDE_STATUS 201
UA_OVERRIDE_STORED {'browser': '机器人', 'os': '其他', 'device': '机器人'}
XFF_STATUS /xff-a 201
XFF_STATUS /xff-b 201
XFF_DISTINCT 2
SALT_RACE {"0": "OperationalError:database is locked", "1": "inserted"}
```

请求头是 Chrome，JSON `user_agent` 是 Googlebot，入库浏览器类是「机器人」。11 个不同路径时 `top_pages` 长度为 10，响应里没有 `active_pages`。两个不同的 `X-Forwarded-For` 得到两个不同的 `visitor_hash`。

补跑主键冲突（先提交读事务，再让另一连接写入，然后本连接 INSERT）：

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-054-weblens-p2\probe_salt.py
```

退出码 0。

```
GAP_SELECT None
GAP_INSERT IntegrityError UNIQUE constraint failed: settings.key
GAP_REREAD_SAME_TXN from-other
GAP_REREAD_AFTER_ROLLBACK from-other
```

同一条连接在完整性错误之后重新 SELECT，能读到对方已提交的 `from-other`。

WAL 下读事务还开着时，另一连接可以提交，本连接随后的 INSERT 是 `OperationalError: database is locked`，不是主键冲突（`probe_salt_wal.py`，退出码 1）。

## P2-1 之后的全量 pytest

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.15s
```

退出码 0。

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-054-weblens-p2\verify_p2_1.py
```

```
ACTIVE 11
TOP_LEN 10
TOTALS {'pv': 11, 'uv': 1}
```

退出码 0。

## P2-2 之后的全量 pytest

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.08s
```

退出码 0。

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-054-weblens-p2\verify_p2_2.py
```

```
/docs 404
/redoc 404
/openapi.json 404
/ 200
```

退出码 0。

## P2-3 之后的全量 pytest

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.01s
```

退出码 0。

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-054-weblens-p2\verify_p2_3.py
```

```
HAS_VALUE_ADMIN False
HAS_VALUE_ADMIN123 False
HAS_HINT True
```

退出码 0。

## P2-5 之后的全量 pytest

P2-4 未改代码，没有单独的 pytest。

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.07s
```

退出码 0。

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-054-weblens-p2\verify_p2_5.py
```

```
JSON_OVERRIDE_STATUS 201
HEADER_BOT_STATUS 201
/from-json Chrome Windows 桌面
/from-header 机器人 其他 机器人
```

退出码 0。

## P2-6 之后的全量 pytest

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 1.97s
```

退出码 0。README 只加了一句 UTC，没有改切日代码。

## P2-7 之后的全量 pytest

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 1.99s
```

退出码 0。

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe E:\muse-bridge\work\TASK-054-weblens-p2\verify_p2_7.py
```

```
HAPPY_SAME True 64
COLLECT 201
PAGEVIEWS 1
STORED_SALT_LEN 64
RECOVERED True 2 1
```

退出码 0。

## 收尾全量 pytest

P2-8 未改依赖。全部代码改动结束后再跑一次：

```
Set-Location E:\muse-bridge\in\TASK-054-weblens-p2
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 2.02s
```

退出码 0。

```
git -C E:\muse-bridge\in\TASK-054-weblens-p2 status --porcelain
```

```
 M README.md
 M app.py
 M static/index.html
```

```
git -C E:\muse-bridge\in\TASK-054-weblens-p2 diff --stat
```

```
 README.md         |  2 +-
 app.py            | 36 ++++++++++++++++++++++++++----------
 static/index.html |  6 +++---
 3 files changed, 30 insertions(+), 14 deletions(-)
```

