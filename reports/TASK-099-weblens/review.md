# weblens 验收审查

结论：仓库能在本机跑通。pytest **33 passed**（1 条依赖库警告），`live_selftest.py` **15/15 通过**，`127.0.0.1:8000` 首页 **200**。没有 P0，没有需要改代码的 P1。README 有 3 处与代码不符，另有 2 条低优先级代码问题。许可证与署名在仓库内部自洽；上游 commit 与版权行原文本次未联网复核。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。README 要求 3.10+。本机 `py --version` 失败：`Unable to create process using 'E:\python.exe --version'`，所以没有用 README Windows 节的 `py -m venv`，改用 `python -m venv .venv`。这是本机启动器损坏，不是仓库缺陷。

依赖（未改版本号）：

- `.venv\Scripts\python.exe -m pip install -r requirements.txt` → fastapi 0.156.4、uvicorn 0.54.0、starlette 1.9.0，exit 0
- `.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` → httpx 0.28.1、pytest 9.1.1，exit 0

自动化测试：

```
.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
33 passed, 1 warning in 6.30s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 出处是 `.venv\Lib\site-packages\fastapi\testclient.py:1`，不是本仓库。DECISIONS.md:47 已决定不改。

真实流程（临时库，端口 8142）：

```
.venv\Scripts\python.exe tests/live_selftest.py
LIVE SELFTEST: ALL PASS (15 checks)
```

15 个检查点全部 PASS，包括首页、埋点脚本、登录、建站域名规范化、PV 4 / UV 2、热门页、来源、7 日趋势、改名、删除、删除后 404。脚本在 `finally` 里 `proc.terminate()`。近 7 日趋势的日期是 UTC `2026-10-15` 至 `2026-10-21`，与 README「今天按 UTC」一致（当时 UTC 日期为 10-21）。

README 默认服务（工作目录里的数据库，避免在仓库里落下 `data/weblens.db`）：

```
Uvicorn running on http://127.0.0.1:8000
GET / → 200，text/html，正文含 weblens
GET /api/me 无令牌 → 401 {"detail":"未登录"}
POST /api/login admin/admin123 → 200，must_change_password=true
GET /docs /redoc /openapi.json → 404
```

没有健康检查路由。`GET /health`、`/healthz`、`/api/health` 都是 404 `{"detail":"Not Found"}`。README 没有承诺这些路径，不记缺陷。首页 200 当作存活信号。

服务已停：`terminate()` 后返回码 1（Windows 上结束子进程的常见结果，日志无 traceback）。再次请求 8000 与 8142 均超时，进程列表里没有 `app.py`。

未使用浏览器。埋点脚本是否在真实页面里发出 `sendBeacon`，只核对了 `app.py:807-830` 的脚本正文和 live 测试对脚本文本的断言，没有在浏览器里执行。

命令与更长输出见 `run.md`。

## README 与实际不符处

1. **测试数量写错。** README.md:106 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。本次 `pytest tests/ -q` 结果是 **33 passed**。6 项参数化仍然成立（`tests/test_app.py:470-478` 共 6 条 UA）。多出来的 3 项是后来补上的回归，README 仍停在 DECISIONS.md:82 把数字改成 30 的时候：`tests/test_app.py:178` 会话哈希、`:197` 正文 413、`:337` 深度嵌套 JSON。15 个 live 检查点与 README.md:106 后半句一致（`tests/live_selftest.py:164`）。

2. **「超过 64KB 返回 400」不完整。** README.md:84 写「请求体超过 64KB 时返回 400」。上报接口自身的上限是 `app.py:35` 的 64KiB，`app.py:710-714` 确实返回 400。但 `app.py:38` 与 `app.py:362` 还有一层 128KiB 的框架限制，更大的正文在进路由之前就变成 413。实测（`probe_413.py`）：70KiB 上报 → `400 {"detail":"请求体过大"}`；140KiB 上报 → `413`，正文 `Content Too Large`。

3. **UV 盐不是启动时生成的。** README.md:51 写「不设置时首次启动在本机数据库中生成」。`init_db`（`app.py:256-320`）不写 `settings`。盐在 `get_uv_salt`（`app.py:220-243`）里、第一次算访客哈希时插入，调用点是上报（`app.py:777`）。实测：服务起来并登录建站之后、上报之前，`settings` 行数是 0；一次 `POST /api/collect` 之后 `uv_salt` 行数是 1。NOTES.md:26 的「首次初始化」同样比代码更早。

已核对、与代码一致（不记缺陷）：24 小时令牌 README.md:9 / `app.py:28`；默认账号 README.md:9 / `app.py:29-30`；默认只听 `127.0.0.1:8000` README.md:47-48 / `app.py:861-862`（日志原文 `Uvicorn running on http://127.0.0.1:8000`）；数据库默认路径 README.md:49 / `app.py:27`；删除站点级联访问记录 README.md:10 / `app.py:289`（测试 `test_delete_site_cascades_pageviews` 通过）；Top 10 README.md:14 / `app.py:646` 与 `app.py:654`；今天用 UTC README.md:13 / `app.py:49` 与 `app.py:625`；User-Agent 只读请求头 README.md:83 / `app.py:763-764`。人均浏览不在接口里单列，由 `static/index.html:505-506` 用 PV/UV 算出，看板功能在，不算 README 说错。

## 许可证与署名核查

内部自洽，上游事实未核实。

- LICENSE:1-3 是 MIT，版权行 `Copyright (c) 2026 weblens contributors`。README.md:120-122 指向该文件，并写 MIT。
- README.md:5、UPSTREAM.md:14、NOTES.md:14 都写本仓库是独立实现，不是抄上游源码。代码是 Python / FastAPI / SQLite（`app.py`），与 UPSTREAM.md:1 指向的 Umami（Node 服务）不是同一份源码。仓库里没有第二份许可证，源文件头也没有别的许可证声明。
- UPSTREAM.md:7-8 与 NOTES.md:5-7 对上游的说法一致：MIT，署名行都是 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。UPSTREAM.md:13 声明这行是逐字复制。两份文档彼此一致。
- 独立实现不必把上游版权行写进自己的 LICENSE；上游署名放在 UPSTREAM.md，README 有链接。这和「借用思路、不复制代码」的说法相符。
- 未改 LICENSE / UPSTREAM。`source_commit` `e92fdab99508a8ed05249f6c5f07e140deab79e1` 以及上游 LICENSE 原文是否就是这一行，本次按任务禁止抓取外网页面，**未核实**。没有发现可以凭仓库内部证据判定的事实错误。

## 分级修复清单

### P0

无。安装、pytest、live 自测、8000 端口首页均已跑通。

### P1

无。上一轮已经收口、且代码和测试仍在的项，按 DECISIONS.md 关闭，不重复开、也不改：

- 首次登录只提示改密、不强制拦截：DECISIONS.md:5-8。`static/index.html:237-239` 只显示提示。
- `X-Forwarded-For` 无条件采信：DECISIONS.md:45-46，实现在 `app.py:199-206`。现有测试靠这个头区分访客；本任务不许改测试，所以不能改这里。
- 访客哈希可被穷举：DECISIONS.md:87，算法在 `app.py:246-253`。决定是不改算法。
- TestClient / httpx 弃用警告：DECISIONS.md:47。警告在依赖库里，不改版本号。

### P2

1. README.md:106 测试数 30 与实际 33 不符。修法：把「30 项」改成「33 项」。
2. README.md:84 未说明超过 128KiB 返回 413。修法：写明 64KiB 至 128KiB 的上报仍是 400，超过 128KiB 由框架返回 413（`app.py:35-38`、`app.py:362`）。
3. README.md:51 把 UV 盐写成启动时生成。修法：改成第一次上报计算 UV 时写入 `settings`（`app.py:220-243`）。
4. static/index.html:29 字体名 `ui-sans-system` 不是合法的 CSS generic family（应为 `ui-sans-serif`）。后面还有 `system-ui` 和系统字体，页面不会因此空白。修法：改成 `ui-sans-serif`。
5. 超过 128KiB 的 413 没有安全响应头。`app.py:362` 的正文限制中间件在 `app.py:352` 的安全头中间件外面，413 在内层跑到之前就返回了。实测 140KiB 上报：`xfo None`，正文 `Content Too Large`。正文是固定字符串，点不了劫持、也嗅探不出页面。修法：让安全头包住正文限制，或在 413 响应上补 `X-Frame-Options: DENY` 与 `X-Content-Type-Options: nosniff`。

P2 本次不改。任务只允许修 P0 和 P1。
