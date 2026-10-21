# weblens 验收报告

结论：本机可以装好并跑通。pytest 为 `33 passed, 1 warning`，`live_selftest` 为 15/15，`http://127.0.0.1:8000/` 返回 200，标题含 weblens。仓库没有 `/health`，该路径返回 404。P0 与 P1 都没有，源码未改。P2 是文档偏差，以及 `DECISIONS.md` 里已经决定维持的风险。

## 本地跑通记录

环境：`python --version` 为 `Python 3.11.9`，满足 README 的 3.10+。README Windows 步骤里的 `py -3 --version` 在本机失败，原文：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

这是本机 py 启动器损坏，虚拟环境改用 `python -m venv`，建在 `E:\muse-bridge\work\TASK-076-weblens\venv`。

运行依赖与测试依赖都安装成功（exit 0）：fastapi==0.156.4、uvicorn==0.54.0、httpx==0.28.1、pytest==9.1.1，传递依赖含 starlette==1.9.0。

### 自动化测试

工作目录为仓库根。命令：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe -m pytest tests/ -q -o cache_dir=E:\muse-bridge\work\TASK-076-weblens\pytest-cache
```

输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.71s
```

警告来自虚拟环境里的 `fastapi/testclient.py:1`，不导致失败。`DECISIONS.md:47` 已决定不处理。

审查结束、确认源码未改之后又跑了同一命令：`33 passed, 1 warning in 5.00s`。

`tests/test_app.py` 在导入时自己调用 `tempfile.mkdtemp`，第一次 pytest 的临时库因此落在系统临时目录。测试文件按任务不能改。

### 真实流程自测

`tests/live_selftest.py` 在临时库上启动 Uvicorn（端口 8142），走完登录、建站、上报、统计、改名、删除。命令 exit 0，最后一行：

```
LIVE SELFTEST: ALL PASS (15 checks)
```

其中有：`PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}`，以及埋点片段 `http://127.0.0.1:8142/tracker.js`。

### 首页与端口

按 README 监听 `127.0.0.1:8000`。数据库设为 `E:\muse-bridge\work\TASK-076-weblens\tmp\smoke.db`，避免在仓库里生成 `data/weblens.db`。访问用 httpx，未使用 curl/wget。进程在探测后已 `terminate`。

服务日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:53044 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:53044 - "GET /health HTTP/1.1" 404 Not Found
```

探测片段：

```
GET / status=200 ctype=text/html; charset=utf-8
  x-frame-options=DENY
  body=<!doctype html> ... <title>weblens · 网站访问统计</title> ...
GET /health status=404
  body={"detail":"Not Found"}
GET /tracker.js status=200
  access-control-allow-origin=*
GET /api/me status=401
  body={"detail":"未登录"}
POST /api/login status=200
  must_change_password=true
GET /docs status=404
GET /openapi.json status=404
POST /api/login 140kb status=413
  x-frame-options=None
  body=Content Too Large
POST /api/collect missing status=400
  body={"detail":"缺少 site_id"}
  access-control-allow-origin=None
```

README 没有健康检查路径，`/health` 的 404 与代码一致。首页 200 作为存活检查。`SERVER_EXIT=1` 是进程被结束后的退出码，日志里没有启动失败。

事后 `netstat -ano | findstr ":8000 :8142"` 没有 `127.0.0.1:8000` 或 `:8142` 的 LISTENING。唯一命中是一条无关 IPv6 连接，远程地址文本里含有字符 `8000`，对端端口是 443。

## README 与实际不符处

1. `README.md:106` 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。pytest 结果是 33 passed。`tests/test_app.py` 有 28 个 `def test_`，其中 `test_ua_classification_cases`（`tests/test_app.py:470`）展开为 6 条，合计 33。6 这个数字与参数表一致；总数少计了 3，对应后补的 `tests/test_app.py:178`、`tests/test_app.py:197`、`tests/test_app.py:337`。同一行的「真实流程自测 15 个检查点」与本次 `ALL PASS (15 checks)` 一致。

2. `README.md:84` 写「请求体超过 64KB 时返回 400」。`/api/collect` 在 64KB 以上、128KB 以内返回 400（`app.py:35`、`app.py:710`）。任意请求超过 128KB 时由 `RequestBodyLimitMiddleware` 返回 413（`app.py:38`、`app.py:362`）。实测约 140KB 的登录正文为 `status=413`，正文 `Content Too Large`。

3. `README.md:51` 写 `WEBLENS_UV_SALT`「不设置时首次启动在本机数据库中生成」。`get_uv_salt`（`app.py:220`）只被 `visitor_hash`（`app.py:249`）调用，哈希只在上报时计算（`app.py:777`）。`init_db`（`app.py:256`）不插入这行盐。进程启动后、第一次上报之前，库里没有 `uv_salt`。

4. `README.md:49` 把默认库路径写成 `data/weblens.db`。代码是 `BASE_DIR / "data" / "weblens.db"`（`app.py:27`），锚定 `app.py` 所在目录。按 README 先进入项目目录再启动时，两条路径重合。从其他工作目录启动时，文件仍在 `app.py` 旁边。

5. `README.md:9` 写「Token 24 小时有效」。过期时间是 `TOKEN_TTL_SECONDS = 24 * 60 * 60`（`app.py:28`）。同一功能清单没有写改密会删除该用户的其他会话、保留本次会话（`app.py:455`）。24 小时仍是过期时间，吊销是额外行为。

以下条目核对过，与代码一致：默认账号 `admin` / `admin123`、默认监听 `127.0.0.1:8000`、今天按 UTC 切日、删除站点级联删除访问记录、`/docs` 与 `/redoc` 与 `/openapi.json` 关闭、上报只留路径和站外来源域名、User-Agent 只读请求头、直接依赖版本钉死、项目结构列出的文件都在。

## 许可证与署名核查

仓内许可证类型都是 MIT，署名分工清楚：

- `LICENSE:1` 起为 MIT 正文，`LICENSE:3` 为 `Copyright (c) 2026 weblens contributors`
- `README.md:5` 指向 `UPSTREAM.md`，`README.md:122` 写 MIT
- `UPSTREAM.md:7` 写上游 license 为 MIT，`UPSTREAM.md:8` 署名为 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`
- `NOTES.md:5` 至 `NOTES.md:7` 与 UPSTREAM 的项目名、commit、版权行相同
- `app.py` 没有第二份许可证头

`README.md:5` 与 `UPSTREAM.md:14` 都写本仓是独立实现、未复制上游源码。抽查 `app.py`、`static/index.html`、`tests/`，没有 Umami 的前端/接口源码。上游版权记在 `UPSTREAM.md`，本仓 `LICENSE` 只署 weblens contributors，与「设计参考、代码自写」这套说法一致。

未核实项：任务禁止外网抓取，没有复验 `UPSTREAM.md:6` 与 `NOTES.md:6` 的 commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`，也没有对照 GitHub 上的上游 LICENSE 原文。`UPSTREAM.md:12` 的「2026-10-21 实查」只是仓内陈述。没有发现需要改正 `LICENSE` 或 `UPSTREAM.md` 的仓内事实错误，这两个文件未改。

## 分级修复清单

### P0

无。安装、pytest、live_selftest、8000 端口首页都跑通了。

### P1

无。会话令牌哈希入库、改密吊销其他会话、文档页默认关闭、上报 64KB 限制、畸形 IPv6、深度嵌套 JSON，都有对应实现和通过的测试。默认口令提示、无条件采信 `X-Forwarded-For`、访客哈希可穷举，见下面 P2，仓库已决定维持，默认绑定还是 `127.0.0.1`。

### P2

1. `README.md:106`。把「30 项」改成「33 项」。
2. `README.md:84`。补上超过 128KB 时返回 413，对应 `app.py:38` 与 `app.py:362`。
3. `README.md:51`。改成第一次写入访问记录时生成盐，对应 `app.py:220` 与 `app.py:249`。
4. `README.md:49`。注明默认数据库路径相对于 `app.py` 所在目录，对应 `app.py:27`。
5. `README.md:9`。补一句改密会删除该用户的其他会话并保留本次会话，对应 `app.py:455`。
6. `app.py:362`。超限 413 由外层中间件直接返回，实测没有 `X-Frame-Options` 和 `X-Content-Type-Options`。给这条响应补上与 `app.py:356` 相同的两个头。本次不改：正文只有 `Content Too Large`。
7. `app.py:718`。`/api/collect` 用 `HTTPException` 返回错误时不带 `COLLECT_CORS`；成功响应在 `app.py:802` 才带。给错误响应也加上这组头。本次不改：埋点脚本不读响应体，成功的上报仍然入库。
8. `app.py:199`。无条件采信 `X-Forwarded-For` 与 `X-Real-IP`。`DECISIONS.md:45` 已决定不改。
9. `app.py:246`。访客哈希盐与同日的浏览器、系统、设备存在同一库中，IPv4 可以被穷举。`DECISIONS.md:87` 已决定不改算法。
10. `static/index.html:29`。把不存在的字体名 `ui-sans-system` 改成 `ui-sans-serif`。
11. 虚拟环境 `fastapi/testclient.py:1` 的 `StarletteDeprecationWarning`。`DECISIONS.md:47` 已决定不改，本次也不改依赖版本。
12. `static/index.html:203`。登录页保留默认口令文字提示。`DECISIONS.md:36` 已决定保留。

本次只允许修 P0 和 P1。上面 12 条都未改。
