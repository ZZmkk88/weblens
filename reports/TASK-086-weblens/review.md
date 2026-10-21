# weblens 验收审查

结论：按 README 的依赖版本可以跑通。修复前 `pytest tests/ -q` 为 **33 passed, 1 warning in 5.89s**；`tests/live_selftest.py` 为 **LIVE SELFTEST: ALL PASS (15 checks)**。默认地址 `http://127.0.0.1:8000` 已启动，首页 `GET /` 返回 200，查完已停掉，`netstat` 看不到 8000 监听。没有 P0。P1 只列 1 条：登录可以用响应时间判断用户名是否存在。P2 不改。

## 本地跑通记录

解释器：`C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe` 输出 `Python 3.11.9`。README 要求 3.10+。本机 `C:\Windows\py.exe --version` 失败，原文：`Unable to create process using 'E:\python.exe --version'`。因此没有按 README 的 `py -m venv .venv` 在仓库里建虚拟环境（也避免把 `.venv` 写进待审目录）。使用任务预置环境 `E:\muse-bridge\env\TASK-086-weblens`（`pyvenv.cfg` 写明 3.11.9）。

安装：

```
E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-086-weblens\requirements-dev.txt
```

`fastapi==0.156.4`、`uvicorn==0.54.0` 已满足；新装 `httpx-0.28.1`、`pytest-9.1.1`。末行：`Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1`。退出码 0。传递依赖实际为 `starlette 1.9.0`、`pydantic 2.14.1`（`pip list`）。

自动化测试（修复前）：

```
cmd /c "set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& cd /d E:\muse-bridge\in\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pytest tests/ -q -p no:cacheprovider"
```

```
33 passed, 1 warning in 5.89s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 来自 `fastapi/testclient.py:1`。`DECISIONS.md:47` 已决定不改。不记为本次缺陷，也没有重试。

真实流程自测：`python tests/live_selftest.py`（同一环境变量）。15 条均为 `PASS`，末行 `LIVE SELFTEST: ALL PASS (15 checks)`，退出码 0。服务由脚本自己 `terminate()`。

默认服务：`WEBLENS_HOST=127.0.0.1`、`WEBLENS_PORT=8000`、数据库在 `E:\muse-bridge\work\TASK-086-weblens\manual.db`。Uvicorn 日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:53550 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:53550 - "GET /health HTTP/1.1" 404 Not Found
```

`GET /` 为 200，`content-type: text/html; charset=utf-8`，正文以 `<!doctype html>` 开头且含 `weblens`，`X-Frame-Options: DENY`，`X-Content-Type-Options: nosniff`。`GET /health`、`/healthz`、`/api/health` 都是 404 `{"detail":"Not Found"}`。README 没有健康检查路径，404 不记为缺陷；首页即就绪信号。`/docs`、`/redoc`、`/openapi.json` 为 404。`/data/weblens.db`、`/app.py` 为 404，数据库和源码没有被静态挂出。

进程退出码 1（`terminate()` 结束）。之后 `netstat -ano -p tcp | findstr :8000` 无输出，退出码 1，端口已释放。

抽查（同一轮 HTTP，详见 `run.md`）：

- 不存在的用户登录 401，耗时 0.005 秒；`admin` 配错密码 401，耗时 0.069 秒。8 万字符密码仍是 0.067 秒，没有把 PBKDF2 拖成数十秒，不单列缺陷。
- 未登录访问 `/api/sites/1/stats` 与 `/snippet` 均为 401。
- 登录成功 `must_change_password=true`，令牌长度 43。库内 `sessions.token` 长度 64，前缀 `2f48615c`（哈希，不是明文）。会话剩余 86243 秒，接近 24 小时（86400）。
- 140KB 登录正文：`413`，正文 `Content Too Large`，安全响应头为 `None`。
- 带登录态把 `Host` 改成 `evil.example` 时，埋点片段变成 `http://evil.example/tracker.js`。站点名 `a' OR 1=1 --` 原样入库，没有被当成 SQL。
- 小写 `bearer` 令牌返回 401。前端和测试都发送 `Bearer `。

没有在浏览器里点击登录。页面提示是否出现，依据 `static/index.html:237-239` 与 `:436`：`must_change_password` 为真时去掉隐藏类。接口已返回该字段为真，首页 HTML 含「默认账号 admin / admin123」，输入框没有预填 `value`。

## README 与实际不符处

1. `README.md:106` 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。实测 `33 passed`。`tests/test_app.py` 有 28 个 `def test_`（`:101` 至 `:503`），其中 `test_ua_classification_cases`（`:470-482`）参数化 6 条，收集数为 28 − 1 + 6 = 33。多出的 3 个是 `:178` `test_session_token_stored_hashed_not_plaintext`、`:197` `test_request_body_hard_limit_413`、`:337` `test_collect_deeply_nested_json_returns_400`。`DECISIONS.md:82` 把 README 从 25 改到 30 之后，D-9（`DECISIONS.md:97-107`）和 D-10（`DECISIONS.md:118-122`）又加了测试，README 没改。同句「真实流程自测 15 个检查点」与本次 15 条 PASS 一致。

2. `README.md:84` 写「请求体超过 64KB 时返回 400」。`/api/collect` 在 64KB 以上、128KiB 以内确实返回 400（`app.py:35`、`app.py:710-714`，测试 `tests/test_app.py:286-293`）。超过 `MAX_REQUEST_BODY = 128 * 1024`（`app.py:38`）时，外层 `RequestBodyLimitMiddleware`（`app.py:361-362`）直接返回 413。实测 140KB 登录正文：`413` / `Content Too Large`。因此「超过 64KB 就返回 400」对大于 128KiB 的请求不成立。

3. `README.md:13` 把「总 UV」和今天 / 近 7 天 / 近 30 天放在一起，读起来像所选范围内的独立访客。实现里访客哈希包含日期（`app.py:247-252`），统计用 `COUNT(DISTINCT visitor_hash)`（`app.py:631-634`）。同一个人跨天回来，在 7 天或 30 天的 `totals.uv` 里会按天各算一次。`NOTES.md:18` 写明「只按天计算 UV」，代码与 NOTES 一致，与 README 的「总 UV」措辞不一致。前端注释在 `static/index.html:286`「按天以访客指纹去重」。

4. `README.md:118` 写「钉死版本的运行/测试依赖」。直接依赖的版本号是钉死的（`requirements.txt:1-2`、`requirements-dev.txt:2-3`），本次安装也得到了这些版本。`starlette`、`pydantic` 没有出现在 requirements 里，实际解析为 starlette 1.9.0、pydantic 2.14.1。传递依赖没有钉死。

5. `README.md:109-118` 的项目结构没有 `.gitignore`。仓库根目录有 `.gitignore:1-10`，忽略 `.venv/`、`data/`、`__pycache__/`、`*.db` 等。

以下核对过，与代码一致，不列入不符：默认账号与 24 小时令牌（`README.md:9`，`app.py:28-30`，库内剩余 86243 秒）；默认只监听 `127.0.0.1:8000`（`README.md:41`、`README.md:47-48`，Uvicorn 日志）；删除站点级联删除访问（`README.md:10`，`app.py:289`，自测 PASS）；埋点标签形式（`README.md:65`，`app.py:497-500`）；UA 只读请求头（`README.md:83`，`app.py:763-764`）；文档页默认关闭（`DECISIONS.md:23-24`，实测 `/docs` 404）。

## 许可证与署名核查

仓库内部自洽。

- `LICENSE:1-3`：MIT，`Copyright (c) 2026 weblens contributors`。`README.md:120-122` 指向该文件，并写 MIT。
- `UPSTREAM.md:5-8`：上游 `https://github.com/umami-software/umami`，commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`，许可证 MIT，署名行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。
- `UPSTREAM.md:12-14` 声明该 commit 与版权行来自 2026-10-21 的上游查询，本仓库是独立实现，未复制上游源码。`NOTES.md:5-7` 的版权行与 `UPSTREAM.md:8` 逐字相同。
- 在 `app.py`、`static/index.html`、`tests/` 中检索 `Umami` / `Copyright`，业务代码没有上游项目名，也没有上游版权头。技术栈是 Python + FastAPI + SQLite，不是上游的 Node 服务。

LICENSE 的版权主体是本仓库（2026 weblens contributors）。UPSTREAM / NOTES 记录的是上游 Umami 的版权行。两边说的不是同一个对象。在「未复制源码」成立时，不需要把 Umami 的版权行写进本仓库 LICENSE，当前写法自洽。

未核实：本环境不允许抓取外网，没有复查 `e92fdab99508a8ed05249f6c5f07e140deab79e1` 是否为 2026-10-21 的默认分支 HEAD，也没有对照上游 LICENSE 原文。该条只采信仓库内的互相引用，不采信仓库对 GitHub 的转述。

## 分级修复清单

下面的文件:行号都是修改前的位置。改完之后的行号写在 `fix-report.md`。

### P0

无。测试与默认服务都能跑起来。`py` 启动器失败是本机环境，不是仓库缺陷。

### P1

1. **登录用耗时暴露用户名是否存在。** `app.py:408`：`if user is None or hash_password(...)` 在用户不存在时短路，不算 PBKDF2。实测不存在用户 0.005 秒，`admin` 配错密码 0.069 秒，响应正文都是 `用户名或密码不正确`。`README.md:50` 允许用 `WL_INITIAL_USERNAME` 换成非公开用户名，这时计时就成了用户名探针。同文件 `:408` 与 `:438` 用 `!=` 比较哈希，不是恒定时间比较。修法：用户不存在时用固定盐做一次同样的 PBKDF2，两处比较都改为 `hmac.compare_digest`。

### P2

不修。每条只写修法，本次不动代码。

1. **测试计数过时。** `README.md:106`。修法：改成 33，并注明其中 6 项仍是 UA 参数化。
2. **超大正文的状态码。** `README.md:84` 与 `app.py:38`、`app.py:361-362`。修法：README 补上超过 128KiB 返回 413，64KB 到 128KiB 的上报仍是 400。
3. **多日 UV 口径。** `README.md:13`，算法在 `app.py:247-252` 与 `app.py:631-634`，与 `NOTES.md:18` 一致。修法：README 写明 7 天 / 30 天的总 UV 是按天去重后再加总。不改哈希，避免偏离 NOTES。
4. **无条件采信转发 IP。** `app.py:199-206` 先读 `X-Forwarded-For`，再读 `X-Real-IP`。Uvicorn 默认 `proxy_headers=True`（环境内 `uvicorn/config.py:225`），`FORWARDED_ALLOW_IPS` 默认 `127.0.0.1,::1`（同文件 `:363`）。服务听在 127.0.0.1 时，对端就是受信地址，访问日志出现 `203.0.113.9:0`。`DECISIONS.md:45-46` D-6 明确不改应用层，因为测试用该头区分访客（`tests/test_app.py:68-79`）。修法若要做：只在对端是显式配置的代理时才采信转发头，并让 Uvicorn `proxy_headers=False` 或收紧 allow list。本次不改，否则 `test_stats_totals_trends_and_tops` 的 UV=2 会失败，且不许改测试。
5. **413 没有安全响应头。** 实测 `BIG_LOGIN 413 None None`。安全头中间件在 `app.py:352-358`，体长限制在其后挂上（`app.py:361-362`），413 在更外层生成，不经过安全头。修法：把安全头放到体长限制的外层，让 413 也带上 `X-Frame-Options` 与 `nosniff`。正文只是 `Content Too Large`，不做。
6. **埋点地址跟随请求 Host。** `app.py:494-500`。带登录态发送 `Host: evil.example` 时，片段 src 变成 `http://evil.example/tracker.js`。该接口要登录，只影响请求者自己拿到的片段；局域网部署需要用管理员实际访问的主机名。修法：增加显式的公开基址配置，不直接信任 Host。本次不改。
7. **域名框长度短于后端 URL 上限。** `static/index.html:340` `maxlength="253"`，后端 `app.py:34` `MAX_URL_LENGTH = 2048`，弹窗 `static/index.html:336` 允许粘贴完整 URL。修法：把 maxlength 调到 2048。
8. **埋点多传了标题。** `app.py:813-817` 的脚本带 `document.title`，收集接口不入库。修法：从脚本正文删掉 `title`。
9. **传递依赖未钉死。** 见上文 README 第 4 条。修法：把 starlette、pydantic 写入 requirements 并钉住本次版本。本次不改版本号（没有依赖冲突）。
10. **TestClient 弃用警告。** 见跑通记录与 `DECISIONS.md:47`。修法：维持 D-6，不改。
11. **小写 `bearer` 被拒绝。** `app.py:387` 只认 `Bearer `。实测小写方案 401。修法：方案名按 RFC 做大小写不敏感比较。前端已发送正确大小写，不改。
