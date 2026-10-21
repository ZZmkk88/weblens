# weblens 验收审查

结论：仓库能在本机跑通。pytest **33 passed**（5.93s），`live_selftest.py` **15 项全过**，默认地址 `http://127.0.0.1:8000` 首页 **200**，服务已关闭。没有 P0，没有需要改代码的 P1。README 有 3 处与代码不符。许可证与署名在仓库内自洽。本轮不改源码。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。README 要求 3.10+。本机 `py` 启动器不可用。

`py --version` 与 `py -3 -m venv` 的原文：

```
Unable to create process using 'E:\python.exe --version': ???????????
Unable to create process using 'E:\python.exe -m venv E:\muse-bridge\in\TASK-073-weblens\.venv': ???????????
```

这是本机启动器指向无效的 `E:\python.exe`，不是项目代码错误。随后用 `python -m venv .venv` 成功（exit 0）。

运行依赖（exit 0）：`fastapi==0.156.4`、`uvicorn==0.54.0`，并装上 starlette 1.9.0、pydantic 2.14.1。测试依赖（exit 0）：`httpx==0.28.1`、`pytest==9.1.1`。

自动化测试命令：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_pytest.py
```

该脚本把 `TEMP`/`TMP` 和 pytest 缓存指到 `E:\muse-bridge\work\TASK-073-weblens`，再执行 `pytest tests/ -q`。输出：

```
33 passed, 1 warning in 5.93s
```

警告原文：

```
.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

测试未失败。`DECISIONS.md:47` 已把该警告标为暂不处理。

真实流程自测命令：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_live.py
```

输出末行：`LIVE SELFTEST: ALL PASS (15 checks)`。15 条均为 `PASS`，包括首页、埋点脚本、登录、建站、4 次上报、今日 PV 4 / UV 2、近 7 天趋势、改名、删除、删除后 404。服务由脚本在临时库上监听 `127.0.0.1:8142`，结束时 `terminate`。

按 README 起默认服务（数据库改到工作目录 `smoke.db`，避免在仓库留下无法删除的 `data/weblens.db`）：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_smoke.py
```

stderr：`Uvicorn running on http://127.0.0.1:8000`。当时环境变量 `PORT`、`WEBLENS_PORT`、`WEBLENS_HOST` 均为空，因此走代码默认值。

| 请求 | 状态 |
|---|---|
| `GET /` | 200，`text/html`，正文含 `weblens · 网站访问统计`，`X-Frame-Options: DENY`，`X-Content-Type-Options: nosniff` |
| `GET /health` | 404 `{"detail":"Not Found"}` |
| `GET /docs`、`/redoc`、`/openapi.json` | 404 |
| `GET /tracker.js` | 200 `application/javascript` |
| `GET /api/me` | 401 `{"detail":"未登录"}` |
| `POST /api/collect` 约 140KiB | 413 `Content Too Large` |
| `POST /api/collect` 约 70KiB | 400 `{"detail":"请求体过大"}` |

README 没有 `/health`。404 表示没有这条路由，首页 200 即本服务的存活信号。

启动后、任何上报之前：`USERS [('admin', 1)]`，`SETTINGS_BEFORE_COLLECT []`。

关闭：`proc.terminate()` 后退出码 1（Windows 上结束进程的常见码），stderr 无 traceback。随后 `check_bind.py` 对 `127.0.0.1:8000` 与 `8142` bind 均成功。`tasklist` 查不到启动时的 PID 32224 与日志中的 12968。服务已停。

对已关闭端口做 TCP connect 得到 `TimeoutError`。本机对「无人监听」的端口不立刻拒绝。bind 成功说明端口空闲。

## README 与实际不符处

1. `README.md:106` 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。实际 pytest 收集并跑过 **33** 项。`tests/test_app.py` 有 28 个 `def test_`，其中 `test_ua_classification_cases`（`tests/test_app.py:470`）参数化为 6 条，其余 27 条，合计 33。括号里「6 项 UA」仍然对。15 个真实流程检查点与本次输出一致。`DECISIONS.md:82` 把 README 从 25 改到 30；其后 `tests/test_app.py:178`、`:197`、`:337` 三条回归没有把 README 的数字改成 33（见 `DECISIONS.md:101`、`DECISIONS.md:120`）。

2. `README.md:84` 写「请求体超过 64KB 时返回 400」。`app.py:35` 的上报上限是 64KiB 并返回 400（`app.py:709-714`），但 `app.py:38` 与 `app.py:362` 还有一层 128KiB 框架上限。本次实机：约 70KiB 的 `POST /api/collect` 返回 **400**，约 140KiB 返回 **413** `Content Too Large`，不是 400。

3. `README.md:51` 写未设置 `WEBLENS_UV_SALT` 时「首次启动在本机数据库中生成」。`init_db`（`app.py:256-320`）和 `lifespan`（`app.py:327-329`）不写盐。盐只在 `get_uv_salt`（`app.py:220-243`，插入在 `app.py:231-233`）里生成，由首次上报经 `visitor_hash`（`app.py:249`）触发。启动后实测 `settings` 表为空，同时 `users` 已有 `admin`，说明初始化跑过、盐却还没写。

其余抽查过的 README 陈述与代码一致，不单列：Token 24 小时（`app.py:28`）、默认账号（`app.py:29-30`）、默认监听 `127.0.0.1` 与端口 `8000`（`app.py:861-862`，且本次环境没有 `PORT`）、默认库 `data/weblens.db`（`app.py:27`）、今天按 UTC 切日（`app.py:625-626`，自测趋势日期为 `2026-10-21`）、删除站点级联访问记录（测试 `test_delete_site_cascades_pageviews` 通过）、项目结构里点名的文件都在。

本机 `py` 失败只记在跑通记录里，不记为 README 与代码不符。`.gitignore` 存在（`.gitignore:1-10`），`README.md:110-118` 的结构清单没写它，属于遗漏，见 P2。

## 许可证与署名核查

仓库内声明一致，未改 `LICENSE` 与 `UPSTREAM.md`。

- `LICENSE:1-3`：MIT，版权行 `Copyright (c) 2026 weblens contributors`。
- `README.md:5-6` 与 `README.md:122`：MIT，并指向 `UPSTREAM.md`，写明代码为独立实现。
- `UPSTREAM.md:5-8`：上游 `https://github.com/umami-software/umami`，commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`，许可证 MIT，署名 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。
- `UPSTREAM.md:12-14`：该版权行自称复制自上游 LICENSE，本仓代码为独立实现，未复制上游源码。
- `NOTES.md:5-7`：同一条上游版权行，并写明「逐字复制，见 UPSTREAM.md」。`UPSTREAM.md:8` 与这句逐字相同。

本仓 `LICENSE` 使用 2026 weblens 署名，上游版权只出现在溯源文档里。这与「独立实现、另行署名」的写法一致。仓库内没有把 Umami 版权写进本仓 `LICENSE` 的说法，也没有与之相反的说法。

`source_commit` 是否为 2026-10-21 的上游默认分支 HEAD、以及上游 LICENSE 原文是否仍是这一行：本次禁止外网抓取，**未核实**。没有发现可以改 `LICENSE` / `UPSTREAM.md` 的仓库内证据，所以没有改这两个文件。

## 分级修复清单

### P0

无。依赖能装上，33 项测试通过，自测 15 项通过，8000 端口首页返回 200，进程已退出。

### P1

无。没有发现仍开放的、会阻断运行或直接破坏安全、数据、权限的缺陷。下面几条在 `DECISIONS.md` 里已经关闭，本次不改代码：

- 首次登录只提示改密、不拦截功能。`DECISIONS.md:5-8`（D-1）。实现是 `must_change_password` 只出现在登录响应和页面提示里（`app.py:418`，`static/index.html:237-239`）。测试在未改密时仍能建站。
- 登录页保留「默认账号 admin / admin123」文字。`DECISIONS.md:36-37`、`static/index.html:203`。
- `X-Forwarded-For` 无条件采信。`app.py:199-206`，`DECISIONS.md:45-46`（D-6）。`tests/test_app.py:75` 与 `:422` 用该头区分访客。改判断会让 UV 断言失败，且禁止改测试。
- TestClient 的 httpx 弃用警告。`DECISIONS.md:47`。警告来自已安装的 `fastapi/testclient.py:1`，不改钉死版本。

### P2

1. `README.md:106`。修法：把「30 项」改成「33 项」，6 项 UA 参数化与 15 个自测检查点可以保留。
2. `README.md:84`（对应 `app.py:35-38`、`app.py:362`、`app.py:709-714`）。修法：写明上报体在 64KiB 与 128KiB 之间返回 400，大于 128KiB 返回 413。
3. `README.md:51`（对应 `app.py:231-233`，`init_db` 在 `app.py:256`）。修法：把「首次启动生成」改成「首次上报计算 UV 时写入 `settings`」。
4. `README.md:110-118` 未列 `.gitignore`（`.gitignore:1`）。修法：在项目结构补一行。
5. `app.py:408` 与 `app.py:438` 用 `!=` 比较口令哈希。修法：改为 `hmac.compare_digest`。单用户且用户名公开，PBKDF2 为 200000 次（`app.py:59`），实用风险低，本轮不改。
6. `app.py:401` 的登录与 `app.py:706` 的公开上报没有频率限制。修法：加进程内限流。属新增行为，本轮不改。
7. `static/index.html:29` 字体名写成 `ui-sans-system`。修法：改为 `ui-sans-serif`。只影响字体回退，本轮不改。

本轮只允许修 P0/P1，因此以上 P2 都不改。
