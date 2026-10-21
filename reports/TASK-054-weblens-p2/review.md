# weblens 第二轮审查（P2）

结论：修前全量 pytest 为 `25 passed, 1 warning in 2.63s`，没有新的 P0。本轮只收口上一轮 `E:\muse-bridge\out\TASK-020-weblens\review.md` 的 8 条 P2。6 条已按原顺序改完，收尾仍是 `25 passed, 1 warning in 2.02s`。第 4 条会拆掉现有访客区分，第 8 条是已锁定的依赖版本，这两条不改。改法与每条测试结果在 `fix-report.md`。

本副本的 `app.py` 仍是上一轮审查时的原状，没有带上 `TASK-020` 工作区里的 P1 补丁（默认仍监听 `0.0.0.0`，`app.py:757`；全局 CORS 仍是 `*`，`app.py:298-304`）。任务限定本轮不重开 P1。

行号都是修改前的。命令原文在 `run.md`。

## 基线

Python `3.11.9`。虚拟环境复用 `E:\muse-bridge\work\TASK-020-weblens\venv`，与本仓库 `requirements-dev.txt` 钉死的 fastapi / uvicorn / httpx / pytest 相同。工作目录 `E:\muse-bridge\in\TASK-054-weblens-p2`。

```
25 passed, 1 warning in 2.63s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 出处 `E:\muse-bridge\work\TASK-020-weblens\venv\Lib\site-packages\fastapi\testclient.py:1`。修前 `git status --porcelain` 无输出。

探针 `E:\muse-bridge\work\TASK-054-weblens-p2\probe_p2.py` 对本地 TestClient 发了 11 个不同路径。`GET /` 为 200。

## P2 核对

1. 活跃页面数仍被 Top 10 截断。`static/index.html:507` 用 `stats.top_pages.length`。`app.py:567-571` 对热门页面 `LIMIT 10`。探针：`TOP_PAGES_LEN 10`，响应键只有 `period`、`site`、`top_pages`、`top_referrers`、`totals`、`trend`，没有独立的页面数字段。
2. 文档接口仍开着。`app.py:297` 是 `FastAPI(title="weblens", lifespan=lifespan)`，没有关掉文档。探针：`DOCS 200 REDOC 200 OPENAPI 200`。
3. 登录框仍预填口令。`static/index.html:198` 为 `value="admin"`，`static/index.html:200` 为 `value="admin123"`。同页 `static/index.html:203` 的文字提示还在。探针：`HAS_VALUE_ADMIN True`，`HAS_VALUE_ADMIN123 True`，`HAS_HINT True`。
4. `app.py:174-181` 的 `client_ip` 仍无条件采用 `X-Forwarded-For` 的第一段。探针里两个不同的转发地址得到两个不同的 `visitor_hash`（`XFF_DISTINCT 2`）。`tests/test_app.py:72` 和 `tests/live_selftest.py:41` 用这个头区分访客。不改，理由见清单。
5. JSON 里的 `user_agent` 仍覆盖请求头。`app.py:662-667` 先取 `user_agent` / `userAgent`。探针请求头是 Chrome，正文是 Googlebot，入库为 `{'browser': '机器人', 'os': '其他', 'device': '机器人'}`。`README.md:80` 写的是从请求头读取。
6. `README.md:13` 的「今天」没有时区。`app.py:45-46` 与 `app.py:549` 用 `utcnow().date()` 切日。`NOTES.md:25` 写了 UTC 日期。
7. 第一次写入 UV 盐仍可能撞主键。`app.py:204-207` 先 SELECT 再 INSERT，不捕获完整性错误。`probe_salt.py`：`GAP_INSERT IntegrityError UNIQUE constraint failed: settings.key`。同一条连接随后 SELECT 能读到对方已提交的盐（`GAP_REREAD_SAME_TXN from-other`）。两边同时握着读事务时，探针得到的是 `OperationalError: database is locked`（`probe_p2.py` 的 `SALT_RACE`，以及 `probe_salt_wal.py`），不是主键冲突。
8. 测试依赖仍打出 Starlette 弃用警告。`requirements-dev.txt:2` 锁定 `httpx==0.28.1`。25 项通过。不改，理由见清单。

## 分级修复清单

### P0

无。修前 25 项 pytest 通过。探针里 `GET /` 为 200。

### P1

本轮不新开，也不重做上一轮 P1。上一轮 P1 的补丁不在本副本里，任务限定只收口 P2。

### P2（按此顺序，最多 8 条）

1. `app.py:567-611`、`static/index.html:507`。修法：统计接口增加区间内 `COUNT(DISTINCT page_path)`，字段放在响应顶层 `active_pages`，不放进 `totals`（`tests/test_app.py:251` 和 `tests/test_app.py:297` 对 `totals` 做了整对象相等）。前端改读 `stats.active_pages`。
2. `app.py:297`。修法：`docs_url`、`redoc_url`、`openapi_url` 设为 `None`。
3. `static/index.html:198-200`。修法：去掉两个 `value`，保留 `static/index.html:203` 的文字提示。
4. `app.py:174-181`。不改。现有测试靠 `X-Forwarded-For` 区分访客；TestClient 的直连方不是回环地址时若不再采信该头，UV 会并成一个，`tests/test_app.py:297` 的 `uv == 2` 会失败。不许改测试。
5. `app.py:662-667`。修法：只读 `User-Agent` 请求头。埋点脚本 `app.py:712-716` 本来就不传 `user_agent`。
6. `README.md:13`。修法：补一句「今天」和按天切分使用 UTC。不改 `app.py` 的切日。
7. `app.py:204-207`。修法：`INSERT` 捕获 `sqlite3.IntegrityError` 后 `rollback` 再读已提交的盐。不另加 `database is locked` 的重试。那是读事务还开着时的另一条失败，报告点名的是主键冲突。
8. `requirements-dev.txt:2`。不改。任务禁止改已有依赖的版本号，这里不是依赖冲突，测试是通过的。

## 收口结果

已改 P2-1、P2-2、P2-3、P2-5、P2-6、P2-7。P2-4、P2-8 未改，理由见上面两条。收尾全量 pytest：`25 passed, 1 warning in 2.02s`。工作区改动是 `README.md`、`app.py`、`static/index.html`。没有改 `tests/`、`requirements-dev.txt`、`LICENSE`、`UPSTREAM.md`。没有浏览器工具，页面与接口用 TestClient 核对，见 `run.md`。
