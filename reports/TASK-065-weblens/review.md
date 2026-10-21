# weblens 验收报告

结论：仓库能在本机按 README 装起来并跑通。`pytest` 30 项通过，`live_selftest.py` 15 个检查点通过，`http://127.0.0.1:8000/` 返回 200 且页面含 weblens。没有健康检查路由。无 P0。有 1 个 P1：公开上报接口遇到深度嵌套 JSON 时返回 500。P2 为文档落差和已决不改项，本轮不改。

## 本地跑通记录

环境：`python --version` 为 Python 3.11.9（满足 README 的 3.10+）。本机 `py -3 --version` 失败，原文 `Unable to create process using 'E:\python.exe --version'`。这是本机启动器损坏，README 的 `py -m venv` 写法本身不是仓库缺陷。虚拟环境建在 `E:\muse-bridge\work\TASK-065-weblens\.venv`，没有写进仓库。

运行时依赖（exit 0）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-065-weblens\requirements.txt
```

装上 `fastapi-0.156.4`、`uvicorn-0.54.0`，连带 `starlette-1.9.0`。开发依赖（exit 0）再装上 `httpx-0.28.1`、`pytest-9.1.1`。

自动化测试（exit 0，5.58s）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pytest tests -q -o cache_dir=E:\muse-bridge\work\TASK-065-weblens\pytest_cache
```

```
30 passed, 1 warning in 5.58s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 与 `DECISIONS.md:47` 的 D-6 一致，未导致失败。README.md:106 写的「30 项，其中 6 项为 UA 参数化」与这次计数一致（`tests/test_app.py:424-436` 有 6 组 UA）。

真实流程自测（exit 0，临时库目录设为任务工作目录）：

```
cmd /c "set TMP=E:\muse-bridge\work\TASK-065-weblens&& set TEMP=E:\muse-bridge\work\TASK-065-weblens&& E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe tests\live_selftest.py"
```

```
LIVE SELFTEST: ALL PASS (15 checks)
```

15 条均为 PASS，包括首页、埋点脚本、登录、建站域名规范成 `demo.example.com`、PV 4 / UV 2、`/pricing` 3 次、`google.com` 3 次、近 7 天趋势、改名、删除、删除后统计 404。自测端口是 `tests/live_selftest.py:14` 的 8142，脚本在 `finally` 里关掉了子进程。

README 端口上的手工启动（数据库在临时目录 `smoke.db`，显式设置 `WEBLENS_HOST=127.0.0.1`、`WEBLENS_PORT=8000`）：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
HOME status=200 len=28345 has_weblens=True xfo=DENY nosniff=nosniff
```

`/health`、`/api/health`、`/healthz` 都是 404 `{"detail":"Not Found"}`。README 没有承诺健康检查，首页 200 作为存活证据。`/docs`、`/redoc`、`/openapi.json` 为 404。未登录的 `/api/me`、`/api/sites` 为 401 `未登录`。`/tracker.js` 为 200。`/app.py` 为 404，源码没有被静态目录暴露。默认账号登录返回 200，`must_change_password` 为 true；未改密也能建站，与 D-1 一致。

边界探测（同一进程，探测后 `terminate`，退出码 1；随后 `netstat` 看不到 8000/8142 的 LISTENING）：

```
big70_len 71708 -> 400 {"detail":"请求体过大"}
huge_len 204828 -> 413 Content Too Large   （响应无 X-Frame-Options / X-Content-Type-Options）
nested_len 8000 -> 500 Internal Server Error
```

500 的 stderr 原文：

```
File "E:\muse-bridge\in\TASK-065-weblens\app.py", line 717, in collect
    data = json.loads(raw_body.decode("utf-8"))
RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string
```

对照：同样的嵌套体打到 `/api/login` 和 `/api/change-password` 是 400 `There was an error parsing the body`。10 万字符的错误口令登录约 0.072 秒返回 401，没有变成阻断，不单列缺陷。

## README 与实际不符处

1. `README.md:84` 写「请求体超过 64KB 时返回 400」。`app.py:35` 的上报上限是 64KiB，`app.py:708-714` 超限返回 400，这只覆盖大约 64KiB 到 128KiB。`app.py:38` 与 `app.py:362` 把全局正文上限设为 128KiB，更大的正文由 Starlette 直接回 413 纯文本 `Content Too Large`。实测 71708 字节为 400，204828 字节为 413。
2. `README.md:9` 只写「Token 24 小时有效，首次登录提示改密」。`app.py:455-459` 在改密成功后会删掉该用户除本次以外的全部会话。README 没有写这个行为。`static/index.html:352` 写「修改后当前登录保持有效」，也没有写其他会话会被吊销。
3. `README.md:72-78` 的上报示例只有 `site_id`、`url`、`referrer`。`app.py:812-816` 的埋点脚本还会发送 `title`。`app.py:287-298` 的表结构没有标题列，标题被丢掉。README 的隐私说明没有提到这个字段。
4. `README.md:80` 只要求 `site_id`。`app.py:728-733` 还接受 `siteId`、`website_id`，`app.py:725-726` 会把嵌套的 `payload` 对象并进顶层。README 没有写这些别名。
5. `README.md:110-118` 的项目结构没有列出 `.gitignore`。该文件在仓库根目录，忽略 `.venv/`、`data/`、`*.db` 等。

以下 README 说法与代码一致，不记为不符：默认账号与 24 小时令牌（`app.py:28-30`）、删除站点级联删除访问（`app.py:289`，测试已通过）、UTC 切日（`app.py:49`、`app.py:625`）、环境变量默认值（`app.py:27`、`app.py:860-861`）、只存路径 / 来源域名 / UA 粗分类（`tests/test_app.py` 对应用例已通过）、测试数量 30 与自测 15（本次实测）。

## 许可证与署名核查

本地文件彼此一致，未改 LICENSE 与 UPSTREAM。

- `LICENSE:1-3` 是标准 MIT 正文，版权行为 `Copyright (c) 2026 weblens contributors`。
- `README.md:122` 写 MIT，并指向 LICENSE。`README.md:5` 写代码为独立实现，署名见 UPSTREAM.md。
- `UPSTREAM.md:5-8` 记录上游 `umami-software/umami`、提交 `e92fdab99508a8ed05249f6c5f07e140deab79e1`、MIT，以及版权行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。`NOTES.md:6-7` 与这三行相同。
- `UPSTREAM.md:14` 写明未复制上游源码。仓库里是 Python / FastAPI / SQLite，没有上游的 Node 或 TypeScript 树，与这句话在本地能核对的范围内一致。MIT 的独立实现不需要把上游版权写进自己的 LICENSE；上游署名放在 UPSTREAM.md 是自洽的。
- 该提交是否就是 2026-10-21 上游默认分支 HEAD、版权行是否与上游 LICENSE 逐字相同，本次按任务没有访问外部页面，未联网核实。没有本地证据证明这两句是错的，所以不改 LICENSE 与 UPSTREAM。

## 分级修复清单

### P0

无。依赖能装上，测试通过，8000 端口首页返回 200。

### P1

1. `app.py:717-719`：`/api/collect` 自己 `json.loads`，只捕获了 `UnicodeDecodeError` 和 `json.JSONDecodeError`。8000 字节的深度嵌套数组触发 `RecursionError`，公开接口返回 500 `Internal Server Error`（stderr 见上）。修法：把 `RecursionError` 并入同一处捕获，返回 400，详情仍为「请求体不是合法 JSON」。

### P2

1. `README.md:84` 与 `app.py:38`、`app.py:362`：超过 128KiB 的正文返回 413 纯文本，不是 README 写的 400。修法：在 README 补一句「超过 128KiB 由框架返回 413」。本轮不改代码，413 是 `00c1a38` 的有意上限。
2. `README.md:9`、`static/index.html:352` 与 `app.py:455-459`：改密吊销其他会话没有写进说明。修法：README 功能清单补一句。本轮不改文案。
3. `app.py:812-816` 埋点多发送 `title`，服务端不存。修法：从脚本里去掉 `title`，或在 README 注明该字段会被丢弃。本轮不改。
4. `app.py:725-733` 的字段别名 README 未写。修法：README 补一句，或删掉别名。本轮不改。
5. `README.md:110-118` 未列 `.gitignore`。修法：项目结构补一行。本轮不改。
6. `app.py:352-362`：安全响应头中间件在请求体限制中间件内侧，413 响应没有 `X-Frame-Options` 和 `X-Content-Type-Options`（实测 `xfo=None`）。修法：把安全头中间件挂到最外层。严重性低，本轮不改。
7. `app.py:199-206` 无条件采信 `X-Forwarded-For`。`DECISIONS.md:45-46` D-6 已决定不改，因为现有测试靠这个头区分访客。维持不修。
8. `app.py:246-253` 的访客哈希是加盐 SHA-256，盐与哈希在同一库里，持库者可以穷举 IPv4。`DECISIONS.md:87` 已决定不改算法。维持不修。
9. `pytest` 的 `StarletteDeprecationWarning`（httpx / TestClient）。`DECISIONS.md:47` D-6 已决定不动依赖版本。维持不修。
