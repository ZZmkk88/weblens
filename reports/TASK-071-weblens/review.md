# weblens 验收审查

结论：依赖能装上，自动化测试 33 项通过，真实流程自测 15 项通过，服务能起来并返回首页。没有 P0。有 1 个 P1：JSON 里的孤立 Unicode 代理字符会让登录和公开上报抛出未捕获的 `UnicodeEncodeError`，真实 HTTP 状态是 500。许可证与署名在仓库内部自洽。下面按证据写，行号均指审查时的文件。

## 本地跑通记录

解释器：本机 `py -3` 指向已损坏的 `E:\python.exe`（`py -0p` 显示 `-V:3.14 * E:\python.exe`，`-V:3.11` 为 `C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe`）。复测 `py -3 --version` 退出码 1：`Unable to create process using 'E:\python.exe --version'`。实际使用 Python 3.11.9，满足 README「Python 3.10 或更高」。虚拟环境和数据库放在 `E:\muse-bridge\work\TASK-071-weblens`，没有写进仓库。

安装（退出码 0）：

`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt`

钉死版本装上了：`fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1`，传递依赖 `starlette==1.9.0`。

全量测试（工作目录为仓库根，退出码 0，pytest 自报 6.29s）：

`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short`

```
33 passed, 1 warning in 6.29s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 来自已安装的 `fastapi/testclient.py`，不是断言失败。

真实流程自测（退出码 0）：

`E:\muse-bridge\work\TASK-071-weblens\.venv\Scripts\python.exe tests\live_selftest.py`

```
PASS 首页能打开且是 weblens 页面
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 近 7 天趋势长度与合计正确 | 末项 {'date': '2026-10-21', 'pv': 4, 'uv': 2}
LIVE SELFTEST: ALL PASS (15 checks)
```

脚本自己用 `WEBLENS_PORT=8142` 拉起 uvicorn，结束时 `proc.terminate()`。登录令牌出现在原始输出里，此处截断。

按 README 起服务：`python app.py`，`WEBLENS_DB_PATH` 指到工作目录。

`GET http://127.0.0.1:8000/` 在启动前已经是 200，标题是 `freshfeeds · 清泉阅读`，不是本仓库。weblens 再绑 8000 失败，日志原文：

```
ERROR:    [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

这是本机端口占用，不是代码拒绝监听。改 `WEBLENS_PORT=18765` 后日志有 `Uvicorn running on http://127.0.0.1:18765`。同一进程上的结果：

| 请求 | 状态 | 证据 |
|---|---|---|
| `GET /` | 200 | `text/html; charset=utf-8`，正文含 weblens；标题 `<title>weblens · 网站访问统计</title>` |
| `GET /tracker.js` | 200 | `application/javascript`，正文以 `(function ()` 开头 |
| `GET /api/me` | 401 | `{"detail":"未登录"}` |
| `GET /docs` | 404 | `{"detail":"Not Found"}` |
| `GET /health`、`GET /api/health` | 404 | `{"detail":"Not Found"}` |

首页、`/tracker.js`、`/health` 的响应都带 `x-frame-options: DENY` 和 `x-content-type-options: nosniff`。代码没有健康检查路由，README 也没写；未登录的 `/api/me` 返回 401，说明进程在正常处理请求。检查后已 `terminate()`。没有结束 8000 上原来的进程。

修复前另有一次真实 uvicorn（端口 18766）确认崩溃请求：

```
surrogate-login 500 Internal Server Error
login-after 200
```

请求体是 `{"username":"ad\ud800min","password":"x"}`。500 的正文就是 `Internal Server Error`，没有把 traceback 回给客户端。随后正常登录仍是 200，进程没有退出。

## README 与实际不符处

1. README.md:106 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。本次 `pytest tests/ -q` 的结果是 `33 passed`。UA 参数化确实是 6 条（tests/test_app.py:470）。多出来的 3 条是 tests/test_app.py:178、tests/test_app.py:197、tests/test_app.py:337，DECISIONS.md 的 D-9、D-10 已记录加过这些测试，README 的总数没改。
2. README.md:84 写「请求体超过 64KB 时返回 400」。app.py:35 的上报上限是 64KB，但 app.py:38 与 app.py:362 另有 128KB 的框架上限；超过 128KB 时中间件直接回 413，到不了这段 400。tests/test_app.py:197 把「登录正文约 140KB → 413、上报约 70KB → 400」写成了回归断言。
3. README.md:49 把默认库写成 `data/weblens.db`。app.py:27 实际是 `BASE_DIR / "data" / "weblens.db"`，也就是 app.py 所在目录，不是进程的当前工作目录。
4. README.md:57 只说「填写名称与域名」。新建站点会去掉协议、路径、端口和开头的 `www.`（app.py:71，app.py:82）。页面上有这句话（static/index.html:336），README 没有。
5. README.md:24 和 README.md:34 要求 `cd weblens`。仓库根目录就是项目根，app.py 在根上，没有下一层 `weblens` 目录。
6. tests/test_app.py:1 和 tests/live_selftest.py:6 写的运行命令是 `.venv/bin/python`。README.md:102 的 Windows 命令是 `python -m pytest tests/ -q` 和 `python tests/live_selftest.py`。在 Windows 上按测试文件头的路径找不到解释器。

以下与代码一致，不列入不符：Token 24 小时（app.py:28）、默认 `127.0.0.1:8000`（app.py:861）、初始账号 admin / admin123（app.py:29）、按 UTC 切日（app.py:49，app.py:625）、删除站点级联删除访问（app.py:289）、`/docs` 默认关闭（app.py:337，实测 404）、自测 15 个检查点（live_selftest 全部 PASS）。

## 许可证与署名核查

- LICENSE:1 起是标准 MIT 正文。LICENSE:3 版权行是 `Copyright (c) 2026 weblens contributors`。
- README.md:5 写「代码为独立实现」，README.md:122 指向这份 MIT。
- UPSTREAM.md:5 的 `source_url` 是 `https://github.com/umami-software/umami`。UPSTREAM.md:6 的 `source_commit` 是 `e92fdab99508a8ed05249f6c5f07e140deab79e1`。UPSTREAM.md:7 写上游许可证为 MIT。UPSTREAM.md:8 的署名是 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。UPSTREAM.md:14 声明未复制上游源码。
- NOTES.md:6 至 NOTES.md:8 与 UPSTREAM.md 的提交号、版权行相同。
- 本仓库是 Python + FastAPI + SQLite，源码里没有上游的 Node/TypeScript 文件，也没有把 Umami 版权行写进 LICENSE。在「独立实现、只借鉴思路」这个前提下，本仓库 LICENSE 只保留自己的版权、上游版权另记在 UPSTREAM.md，两边不冲突。

本轮按任务要求没有抓取 GitHub，`source_commit` 是否仍是上游默认分支 HEAD、版权行是否与上游 LICENSE 逐字相同，均未复核，标为未核实。仓库内部这几份声明彼此一致，没有发现必须改 LICENSE 或 UPSTREAM.md 的确凿错误，这两份文件未改。

## 分级修复清单

### P0

无。安装、pytest、live_selftest、换端口起服务都成功。8000 绑不上是本机已有进程，不是本仓库的缺陷。

### P1

1. P1-1 孤立 Unicode 代理字符（JSON `\ud800`）导致未捕获的 `UnicodeEncodeError`，公开接口返回 HTTP 500。登录用户名在 app.py:405 入库查询时抛出；密码在 app.py:58 的 `encode("utf-8")` 抛出；站点名在 app.py:476 之后的 INSERT 抛出；上报 URL 在 app.py:127 放行后于 INSERT 抛出；上报 referrer 在 app.py:109 把坏主机名返回后于 INSERT 抛出。真实 uvicorn 上登录复现为 `500 Internal Server Error`，进程仍存活。修法：不能 UTF-8 编码的账号、密码、站点名、页面路径直接返回 400；来源主机名记空串并继续入库（与 app.py:102 对畸形来源的既有口径一致）。

### P2

1. P2-1 README 测试总数过期。README.md:106。修法：把「30 项」改成与当前收集结果一致的 33 项，并注明含 6 项 UA 参数化。
2. P2-2 README 把上报体积错误说成一律 400。README.md:84，对照 app.py:38 与 app.py:362。修法：写明 64KB 到 128KB 为 400，超过 128KB 为 413。
3. P2-3 默认数据库路径写得像相对当前目录。README.md:49，对照 app.py:27。修法：写明相对 app.py 所在目录。
4. P2-4 README 未写域名规范化。README.md:57，对照 app.py:71 与 app.py:82。修法：补上会去掉协议、路径和开头的 www。
5. P2-5 测试文件头是 Unix 虚拟环境路径。tests/test_app.py:1，tests/live_selftest.py:6。修法：改成 README 里的 `python -m pytest` / `python tests/live_selftest.py`。本任务禁止改测试文件，不修。
6. P2-6 埋点脚本的源地址直接取自请求 Host。app.py:495。带 `Host: evil.example` 的已登录请求会得到 `src="http://evil.example/tracker.js"`。`X-Forwarded-Host` 不会改写（探针仍是 `http://testserver/tracker.js`）。片段不落库，默认只监听本机。修法：用显式配置的公开基址拼接脚本 URL，不信任请求 Host。
7. P2-7 `X-Forwarded-For` 无条件采信。app.py:200。修法：仅在配置了可信代理时采用。DECISIONS.md D-6 已决定不改，本轮不修。
8. P2-8 仓库根没有 `.gitignore`，默认库会落在 app.py:27 的 `data/weblens.db`（含密码哈希和 UV 盐）。修法：忽略 `data/*.db` 和 `.venv`。
9. P2-9 Starlette 对 httpx TestClient 的弃用警告。pytest 警告指向 site-packages 的 `fastapi/testclient.py:1`。修法：改用 httpx2 对应的客户端。DECISIONS.md D-6 已决定不改，且不能改测试，本轮不修。
10. P2-10 访客哈希把 IP 与盐拼在一起做 SHA-256。app.py:250。盐与哈希在同一个库里，小地址空间可以穷举。修法：维持现有算法。DECISIONS.md D-8 已决定不改，本轮不修。

已核对、不单开条目的决定：首次改密只提示不强制（DECISIONS.md D-1，static/index.html:237 只是通知条）；会话令牌哈希入库（app.py:63）；请求体 128KB 上限（app.py:362）；`/docs` 关闭（app.py:337）。用户名 `admin\u0000hack` 加正确密码返回 401，没有绕过登录。站点名里的 SQL 片段是参数绑定后原样入库，表还在。
