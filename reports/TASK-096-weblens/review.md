# weblens 验收报告

结论：仓库能在本机装好并跑通。pytest 33 项通过，live 自测 15 项通过，按 README 在 `127.0.0.1:8000` 起服务后首页 200，进程已关掉。没有 P0，也没有要改代码的 P1。README 有几处与代码不符，都是文档或已决取舍，本次不改源码。

## 本地跑通记录

环境：Python 3.11.9。虚拟环境在 `E:\muse-bridge\work\TASK-096-weblens\.venv`，没有写进仓库。依赖按 `requirements.txt` / `requirements-dev.txt` 安装成功：fastapi 0.156.4、uvicorn 0.54.0、starlette 1.9.0、httpx 0.28.1、pytest 9.1.1。

README 的 Windows 步骤写 `py -m venv`。本机执行 `py -3 --version` 失败，原文：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

这是本机 `py` 启动器损坏，不是仓库缺陷。改用已可用的 `python -m venv` 后安装与测试都成功。

全量测试命令与结果：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short -o cache_dir=E:\muse-bridge\work\TASK-096-weblens\pytest_cache
```

```
33 passed, 1 warning in 6.00s
```

唯一警告是依赖库原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。`DECISIONS.md:47` 已写明这条警告不改。

收集结果：`33 tests collected in 0.87s`。6 条是 `test_ua_classification_cases` 的参数化用例，另外 27 条。

真实流程自测（临时库、端口 8142，脚本结束时关掉子进程）：

```
LIVE SELFTEST: ALL PASS (15 checks)
```

按 README 再起一次服务（`WEBLENS_HOST=127.0.0.1`、`WEBLENS_PORT=8000`、数据库放在工作目录）。日志原文：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

| 请求 | 结果 |
|---|---|
| `GET /` | 200，`text/html`，正文含 `weblens · 网站访问统计`，`X-Frame-Options: DENY`，`X-Content-Type-Options: nosniff` |
| `GET /tracker.js` | 200，`application/javascript` |
| `GET /health`、`GET /api/health` | 404 `{"detail":"Not Found"}` |
| `GET /docs`、`/redoc`、`/openapi.json` | 404 |
| `GET /api/me`（无令牌） | 401 `{"detail":"未登录"}` |
| `POST /api/login` admin / admin123 | 200，`must_change_password` 为 true |

仓库没有健康检查路由，README 也没承诺 `/health`。首页 200 即本次健康检查。20000 层嵌套 JSON 打到 `/api/login`、`/api/collect`、`/api/change-password` 都是 400，之后 `GET /` 仍是 200。进程 `terminate` 后端口不再接受连接（`port_still_accepts False ReadError`）。

未做浏览器点击走查（本环境没有浏览器工具）。登录、建站、上报、统计、改名、删除由 `live_selftest.py` 走了一遍。

启动后、任何上报之前，`settings` 表为空（`settings_before_collect []`）。第一次成功上报之后才有 `uv_salt`（`settings_after_collect ['uv_salt']`）。

## README 与实际不符处

1. `README.md:106` 写「自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。实际 `pytest --collect-only` 为 33 项：UA 参数化确实是 6 条（`tests/test_app.py:470`），另外 27 条。多出来的 3 条是 `test_session_token_stored_hashed_not_plaintext`（`tests/test_app.py:178`）、`test_request_body_hard_limit_413`（`tests/test_app.py:197`）、`test_collect_deeply_nested_json_returns_400`（`tests/test_app.py:337`）。同句「15 个检查点」与 `tests/live_selftest.py:164` 的 `ALL PASS (15 checks)` 一致，这项不用改。

2. `README.md:84` 写「请求体超过 64KB 时返回 400」。`app.py:35` 的 64KB 上限在 `app.py:710-714` 确实返回 400；但 `app.py:38` 与 `app.py:362` 对超过 128KiB 的正文由 `RequestBodyLimitMiddleware` 直接返回 413。超过 128KiB 时不会走到 400。`tests/test_app.py:197` 已断言 140KB 登录为 413、70KB 上报为 400，测试通过。

3. `README.md:51` 写 `WEBLENS_UV_SALT` 不设置时「首次启动在本机数据库中生成」。`init_db`（`app.py:256-320`）只建表和初始用户，不写盐。盐在 `get_uv_salt`（`app.py:220-243`）第一次被调用时插入，也就是第一次上报。冒烟库在上报前 `settings` 为空，上报后才出现 `uv_salt`。同句在 `NOTES.md:26` 写成「首次初始化」，与代码同样不一致。`README.md:50` 的初始账号「首次启动创建」与 `init_db` 相符，不是问题。

4. `README.md:13` 的「总 UV」和 `README.md:15` 的「按天去重」叠在一起时，多日区间容易理解成区间内唯一访客。实现是哈希材料含日期（`app.py:247-252`），统计用 `COUNT(DISTINCT visitor_hash)`（`app.py:631-634`）。同一访客跨天会在 7 日/30 日总 UV 里累加。这与 `NOTES.md:18`「只按天计算 UV」一致，和「总 UV」四个字不一致。

5. `README.md:72-83` 只写了 `site_id`、`url`、`referrer`。`app.py:729-760` 还接受 `siteId`、`website_id`、`page_url`、`path`、`referrer_domain`、`referer`，以及请求头 `Referer`。埋点脚本还会带上 `title`（`app.py:813-818`），服务端不入库。

6. `README.md:9` 与 `README.md:41` 只说首次登录提示改密。新密码短于 6 位会 400，见 `app.py:436`；页面文案在 `static/index.html:352`。README 没写这个下限。

7. `README.md:108-118` 的项目结构没有列出已存在的 `.gitignore`（`.gitignore:1`，忽略 `.venv/`、`data/`、`*.db`）。

下列与 README 一致，不记为不符：默认 `127.0.0.1:8000`（`app.py:861-863`）、Token 24 小时（`app.py:28`）、今天按 UTC 切日（`app.py:49-50` 与 `app.py:625`）、文档页默认关闭（`app.py:334-339`）、删除站点级联删除访问（`app.py:289`，测试通过）、MIT（`README.md:122` 与 `LICENSE:1`）。本次服务端时间戳为 `2026-10-21T17:22:44+00:00`，趋势最后一天是 `2026-10-21`，与「按 UTC 切日」相符。

## 许可证与署名核查

仓库内四方一致，未改 `LICENSE` 与 `UPSTREAM.md`。

- `LICENSE:1-3`：MIT，版权行 `Copyright (c) 2026 weblens contributors`。
- `README.md:6` 指向 `UPSTREAM.md`，并写明代码为独立实现。`README.md:122` 为 MIT。
- `UPSTREAM.md:5-8`：上游 `https://github.com/umami-software/umami`，commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`，许可证 MIT，署名行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。
- `NOTES.md:5-7` 的项目名、许可证和版权行与 `UPSTREAM.md:8` 相同。
- `UPSTREAM.md:14` 与 `NOTES.md:14` 声明未复制上游源码。仓库里只有 Python/FastAPI/SQLite 与一份静态页，没有 Umami 的 TypeScript 源码或上游文件头。独立实现与「LICENSE 只署本项目、上游版权记在 UPSTREAM」不冲突。MIT 的保留版权声明义务针对上游软件的副本或实质部分；在「未复制源码」这个前提下，不必把 Umami 版权行写进 `LICENSE`。

`source_commit` 与上游 LICENSE 原文是否逐字相符：未联网核实（本任务禁止抓取外部页面）。只核到仓库内部自洽，没有发现必须改 `LICENSE` / `UPSTREAM.md` 的事实错误。

## 分级修复清单

### P0

无。安装、pytest、live 自测、8000 端口首页均已跑通。

### P1

无需要改代码的开放项。下面这些安全相关点在本仓决定里已经关闭，本次不重开、不改：

- 默认口令只提示不强制，页面保留 `admin / admin123` 提示。`DECISIONS.md:5-8`（D-1）、`DECISIONS.md:36-37`（D-5）、`static/index.html:203`。修法若做成强制改密，与已决口径冲突。
- `X-Forwarded-For` / `X-Real-IP` 无条件采信。`app.py:199-206`，`DECISIONS.md:45-46`（D-6）写明暂不动，避免改坏访客区分。本次冒烟日志出现 `203.0.113.9:0`，是因为已安装的 uvicorn 默认 `proxy_headers=True`（`uvicorn/config.py:225`），`app.py:863` 没有关掉它。应用层仍按 D-6 保持现状。
- 访客哈希可被穷举，算法不改。`app.py:247-252`，`DECISIONS.md:87`（D-8）。
- httpx/TestClient 弃用警告不改测试。`DECISIONS.md:47`（D-6）。测试文件本次也未动。

另查过、不够成 P1 的点：带合法 `Host: evil.example` 且持有登录令牌时，当次响应的埋点地址会变成 `http://evil.example/tracker.js`（`app.py:494-500`）。该地址不入库，下一次用真实 Host 访问会恢复。没有令牌不能调用建站接口。带引号的 Host 没有破坏属性。深度嵌套 JSON 对公开接口返回 400，进程不退出。

### P2

1. `README.md:106` 测试数 30 与实际 33 不符。修法：改成 33，并点名多出的 3 个用例。
2. `README.md:84` 未写 128KiB 以上返回 413。修法：补一句，对应 `app.py:38` 与 `app.py:362`。
3. `README.md:51`、`NOTES.md:26` 把 UV 盐写成启动时生成。修法：改成「第一次写入访问记录时在 `settings` 表生成」。
4. `README.md:13` 的「总 UV」容易理解成跨天唯一。修法：写明多日总数是按天指纹的去重计数，同一人跨天累加；算法保持 `app.py:247-252`，不改。
5. `README.md:72-83` 未写 collect 别名，也未写埋点里的 `title` 会被丢弃（`app.py:729-760`、`app.py:817`）。修法：在上报接口一节补上。
6. `README.md:9` 未写新密码至少 6 位（`app.py:436`）。修法：在登录说明里补一句。
7. `README.md:108-118` 未列 `.gitignore`。修法：项目结构补一行。
8. `app.py:401` 登录没有失败限速；`app.py:706` 公开上报没有条数上限。修法：仅在需要对外监听时再加限速。默认只绑本机，本次不改。
9. `app.py:863` 未显式关闭 uvicorn 的 `proxy_headers`。修法：若前面没有可信反代，传 `proxy_headers=False`。与 D-6 的应用层采信是两件事；本次不改，避免和已决口径缠在一起。
10. `app.py:269-273` 过期会话只在校验时拒绝，不删除。修法：`init_db` 里删掉 `expires_at` 已过的行。
11. `app.py:408` 密码比较没用常量时间比较。修法：改为 `hmac.compare_digest`。PBKDF2 占主要耗时，实际风险低。

本次只允许修 P0 与 P1，且最多 5 项。P0/P1 为空，所以上面的 P2 一律不改。
