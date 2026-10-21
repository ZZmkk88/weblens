# weblens 验收审查

结论：仓库能在本机跑通。pytest 25 项通过，真实流程自测 15 项通过，`python app.py` 监听 8000，首页与 `/tracker.js` 返回 200。没有 P0。P1 有 5 条：4 条改代码，1 条（改密后作废其他会话）会打断现有测试，不改。

下面的文件行号是修复前的源码位置。改过之后的行号见 `fix-report.md`。

## 本地跑通记录

环境：前序记录里 `python --version` 为 Python 3.11.9。本轮使用已装好的 `.venv`（`fastapi==0.156.4`、`uvicorn==0.54.0`、`pytest==9.1.1`），没有重装依赖。本机 `py` 启动器在前序步骤指向不存在的 `E:\python.exe`（`Unable to create process using 'E:\python.exe -m venv .venv'`），所以 venv 是用 `python -m venv .venv` 建的。这是本机启动器问题，不是仓库缺陷。

自动化测试（工作目录 `E:\muse-bridge\in\TASK-014-weblens`，exit 0）：

```
.\.venv\Scripts\python.exe -m pytest tests/ -q
25 passed, 1 warning in 1.58s
```

警告原文是 Starlette 弃用提示：`Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 不是失败。

真实流程自测（exit 0，服务由脚本拉起到 `127.0.0.1:8142`，结束时 `terminate`）：

```
.\.venv\Scripts\python.exe tests\live_selftest.py
LIVE SELFTEST: ALL PASS (15 checks)
```

其中包括首页、埋点脚本、`admin/admin123` 登录且 `must_change_password=true`、建站域名规范成 `demo.example.com`、PV 4 / UV 2、热门页与来源、7 日趋势、改名、删除后统计 404。

按 README 起服务（`python app.py`，数据库改到 `E:\muse-bridge\work\TASK-014-weblens\smoke.db`）：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
GET / 200  标题为 weblens · 网站访问统计
GET /tracker.js 200
GET /health 404 {"detail":"Not Found"}
GET /api/health 404 {"detail":"Not Found"}
```

子进程 `terminate` 后 `poll()` 为 1，进程已退出。README 没有健康检查路径，404 不记为缺陷。

## README 与实际不符处

1. `README.md:41` 写打开 `http://127.0.0.1:8000`。`app.py:757` 是 `uvicorn.run(app, host="0.0.0.0", port=port)`。启动日志为 `Uvicorn running on http://0.0.0.0:8000`，进程监听全部网卡，不是只监听本机。
2. `README.md:80` 至 `README.md:81` 写 User-Agent 从请求头读取，只存浏览器、系统、设备三类。`app.py:662` 至 `app.py:667` 优先使用 JSON 里的 `user_agent` / `userAgent`。探针里请求头是 Chrome/Windows/桌面，正文换成 FakeBot 后，入库为 browser=机器人、os=其他、device=机器人。
3. `README.md:15` 与 `README.md:79` 写不保存完整来源 URL，referrer 只留站外域名。`app.py:651` 至 `app.py:652` 对字段 `referrer_domain` 只调用 `normalize_host`，不解析 URL。探针传入 `https://www.google.com/search?q=secret-token`，该整串（含查询参数）写入 `pageviews.referrer_domain`。同一 URL 走 `referrer` 字段时，`app.py:654` 至 `app.py:661` 正确存成 `google.com`。
4. `README.md:13` 写看板包含活跃页面数。`static/index.html:294` 至 `static/index.html:296` 的说明是「所选时间内有访问的页面数」，但 `static/index.html:507` 用 `stats.top_pages.length`。`app.py:570` 对热门页面 `LIMIT 10`，统计响应没有独立计数字段（探针 `STATS_KEYS` 为 period/site/top_pages/top_referrers/totals/trend，`TOP_PAGES_LEN` 为 10）。同一次探针写入了 15 个不同路径，页面上的活跃页面最多显示 10。
5. `README.md:47` 只把端口默认值归于 `WEBLENS_PORT=8000`。`app.py:756` 在未设置该变量时还会读取 `PORT`。未另起进程做 `PORT` 对照，以该行代码为准。
6. `README.md:48` 把默认数据库写成相对路径 `data/weblens.db`。`app.py:27` 实际是 `BASE_DIR / "data" / "weblens.db"`（`BASE_DIR` 为 `app.py` 所在目录）。在项目目录里按 README 启动时两者相同；从其他工作目录执行 `python path\to\app.py` 时，库文件不在当前目录。
7. `README.md:102` 写自动化测试 25 项、真实流程 15 个检查点。本轮输出与这句话一致，不是不符。`README.md:13` 的「人均浏览」由 `static/index.html:505` 用 PV/UV 计算，与看板描述一致，API `app.py:602` 的 `totals` 只有 pv/uv，不单列不符。

## 许可证与署名核查

- `LICENSE:3` 为本项目 MIT，版权行 `Copyright (c) 2026 weblens contributors`。正文是标准 MIT 许可，允许使用、修改、分发，并要求保留版权与许可声明。
- `UPSTREAM.md:4` 至 `UPSTREAM.md:8` 记录上游 `https://github.com/umami-software/umami`，commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`，许可证 MIT，署名 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。
- `UPSTREAM.md:12` 至 `UPSTREAM.md:14` 声称该 commit 于 2026-10-21 经 GitHub 实查、版权行逐字来自上游 LICENSE、本项目未复制上游源码。`README.md:5`、`NOTES.md:5` 至 `NOTES.md:7` 与这段署名互相一致。
- 在 `app.py`、`static/index.html`、`tests/` 中检索 `umami` 无匹配；匹配只出现在 `NOTES.md` 与 `UPSTREAM.md`。实现是 Python + FastAPI + SQLite，不是上游的 Node/TypeScript 源码拷贝。抽查 `TRACKER_JS`（`app.py:706` 起）是一段独立的上报脚本。
- 两份版权主体不同，在「独立实现、未复制源码」成立时是自洽的：本仓库 `LICENSE` 覆盖 weblens 自己的代码；上游 MIT 署名放在 `UPSTREAM.md`，不应当改写进 `LICENSE` 冒充本项目版权人。
- 上游 commit 是否存在、版权行是否与该提交的 `LICENSE` 逐字相同：任务禁止访问外网，未核实。没有确凿的内部事实错误，不改 `LICENSE` 与 `UPSTREAM.md`。

## 分级修复清单

### P0

无。测试与服务均能启动，首页返回 200。

### P1

1. 监听全部网卡，且默认口令是 `admin` / `admin123`（`README.md:9`，登录页 `static/index.html:200` 预填该口令）。文件 `app.py:757`。修法：默认 `host` 改为 `127.0.0.1`。
2. 公开上报可以用正文伪造 UA 分类，与 `README.md:80` 不符。文件 `app.py:662`。修法：只读取 `User-Agent` 请求头。
3. `referrer_domain` 可把带查询串的完整 URL 写入数据库，违反 `README.md:15`。文件 `app.py:651`。修法：与 `referrer` 一样只提取主机名，超长主机名丢弃。
4. 活跃页面数在超过 10 个路径时少计。文件 `app.py:570`、`static/index.html:507`。修法：统计接口增加区间内 `COUNT(DISTINCT page_path)`，前端显示该字段；`totals` 仍只含 pv/uv，避免改动现有断言。
5. 改密后其他会话仍然有效。文件 `app.py:379`；界面 `static/index.html:352` 写的是当前登录保持有效。探针：改密后另一个 token 访问 `/api/me` 仍是 200，`sessions` 仍为 2 行。修法本应删除该用户除当前 token 以外的会话。本次不改：`tests/test_app.py:53` 的 `auth` 是模块级 fixture，`tests/test_app.py:117` 的第二次改密用的是另一个新 token，若此时作废其他会话，后面的用例会拿着原 token 收到 401。不许改测试，所以这条只记录、不动代码。

### P2

1. 公开上报无条件采信 `X-Forwarded-For` / `X-Real-IP`。文件 `app.py:174`。探针：同一 UA、两个伪造地址，`visitor_hash` 不同。修法：默认只用 TCP 对端地址，仅在显式配置可信代理时读取转发头。测试助手靠这个头区分 IP，本次不改口径。
2. 登录页预填默认口令。文件 `static/index.html:198`。修法：去掉 `value="admin123"`，保留 README 已写明的默认账号说明即可。P1-1 把监听收回到本机后，风险限于本机使用者。
3. 登录没有失败次数限制。文件 `app.py:343`。修法：对同一用户名做短时锁定。单用户本地工具，本次不改。
4. `FastAPI()` 默认开放 `/docs`。文件 `app.py:297`。本轮 `GET /docs` 为 200，页面还引用外部 CDN。修法：生产默认关闭 `docs_url`。本次不改。
5. 数据库连接没有显式 `close`。文件 `app.py:188`。`with get_conn()` 只提交事务。CPython 会在函数返回时析构并关掉连接，本轮测试没有出现句柄耗尽。修法：上下文管理器里 `finally: conn.close()`。改动面大，本次不改。
6. 访客哈希不含 `site_id`。文件 `app.py:215`。同一访客在不同站点的哈希相同，库泄露后可跨站关联。修法：把站点 ID 加入哈希材料。会改变 UV 口径，本次不改。
7. 「今天」按 UTC 切日。文件 `app.py:549`。`README.md:13` 没有写时区。修法：在 README 注明 UTC，或按可配置时区切日。本次不改。
8. `README.md:104` 的项目结构没有列出 `requirements.txt`、`requirements-dev.txt`、`LICENSE`。修法：补三行。本次不改文档。
