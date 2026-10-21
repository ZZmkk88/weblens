# weblens 验收审查

结论：仓库能装、能测、能起。本机 Python 3.11.9 下 pytest **33 passed**，`live_selftest.py` **15 项全部 PASS**，默认服务听在 **127.0.0.1:8000**，首页 200，探完已关掉。没有新的 P0 或 P1。README 有两处硬伤（测试总数、超大请求体的状态码），许可证在仓内自洽，上游 commit 与版权行未联网复核。

## 本地跑通记录

环境：Windows，`python --version` → `Python 3.11.9`。README 要求 3.10+，满足。

README Windows 步骤写 `py -m venv`。本机执行 `py --version` 失败（exit 1）：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

这是本机 `py` 启动器指向不存在的 `E:\python.exe`，记为环境限制，不记项目缺陷。虚拟环境改用 `python -m venv .venv`，位置仍是仓库内 `.venv`（`.gitignore` 已忽略）。

安装（均 exit 0）：

```
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

装上 fastapi==0.156.4、uvicorn==0.54.0、httpx==0.28.1、pytest==9.1.1。传递依赖里实际解出 starlette==1.9.0、pydantic==2.14.1。未升级 pip。

全量测试（工作目录为仓库根；`TEMP`/`TMP` 指向 `E:\muse-bridge\work\TASK-084-weblens\tmp`）：

```
.venv\Scripts\python.exe -m pytest tests/ -q
```

```
.................................                                        [100%]
33 passed, 1 warning in 11.98s
```

警告原文：

```
.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

真实流程（脚本自己拉起 127.0.0.1:8142，结束时 `terminate()`）：

```
.venv\Scripts\python.exe tests/live_selftest.py
```

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | username=admin must_change_password=true
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id | src="http://127.0.0.1:8142/tracker.js"
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 末日 date=2026-10-21 pv=4 uv=2
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

趋势末日是 UTC 的 2026-10-21。当时本机本地时间已是 2026-10-22 00:51，与 README「今天按 UTC」一致。

默认服务（未改端口和监听地址，数据库指到工作目录）：

```
.venv\Scripts\python.exe app.py
```

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
GET /            status=200  text/html  X-Frame-Options=DENY  X-Content-Type-Options=nosniff
                 正文以 weblens · 网站访问统计 开头
GET /health      status=404  {"detail":"Not Found"}
GET /api/health  status=404  {"detail":"Not Found"}
GET /docs        status=404
GET /redoc       status=404
GET /openapi.json status=404
GET /tracker.js  status=200  application/javascript
GET /api/me      status=401  {"detail":"未登录"}
POST /api/login  status=200  username=admin must_change_password=true
GET /api/me      status=200  （带登录令牌）
```

README 没有健康检查路由。`/health` 与 `/api/health` 均为 404，首页 200。随后 `terminate()` 关掉进程，再请求 `/` 得到 `ConnectTimeout`，端口已释放。

## README 与实际不符处

1. **测试总数写错。** `README.md:106` 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。本机 `pytest tests/ -q` 结果是 `33 passed`。6 项 UA 参数化这句仍然对（`tests/test_app.py:470` 起 6 组参数）。多出来的 3 项是后来加的回归，README 停在 `DECISIONS.md:82` 的「25→30」：`test_session_token_stored_hashed_not_plaintext`（`tests/test_app.py:178`）、`test_request_body_hard_limit_413`（`tests/test_app.py:197`）、`test_collect_deeply_nested_json_returns_400`（`tests/test_app.py:337`）。同句的「真实流程自测 15 个检查点」与本次 15 条 PASS 一致。

2. **超过 64KB 并不总是 400。** `README.md:84` 写「请求体超过 64KB 时返回 400」。`app.py:35` 的上报上限是 64KB，`app.py:38` 与 `app.py:362` 另有 128KB 框架上限，超限直接 413。实测：70KB 上报 `status=400`，正文 `{"detail":"请求体过大"}`；140KB 上报 `status=413`，正文 `Content Too Large`（`text/plain`）。64KB 到 128KB 之间 README 是对的，再大就不是 400。

3. **埋点多送了 title，README 没写，库里也不存。** `README.md:11` 与 `README.md:70` 只说上报当前页面与来源。`app.py:817` 的脚本还发送 `title: document.title`。`app.py:778` 的 INSERT 没有 title 列，该字段被丢掉。

4. **上报字段别名 README 未列出。** `README.md:72` 的示例只有 `site_id`、`url`、`referrer`。`app.py:730` 还接受 `siteId`、`website_id`；`app.py:740` 还接受 `page_url`、`path`；`app.py:747` 还接受 `referrer_domain`，`app.py:755` 还读 `referer` 以及请求头 `Referer`。

5. **域名会去掉开头的 www.，README 没说。** `README.md:57` 只说填写名称与域名。`app.py:71` 的 `normalize_host` 会删掉前缀 `www.`。界面 `static/index.html:336` 有说明，README 没有。

6. **「钉死版本」只覆盖直接依赖。** `README.md:106` 与 `README.md:118` 写依赖版本已钉死。`requirements.txt:1` 只钉 fastapi==0.156.4 与 uvicorn==0.54.0。本次安装解出的 starlette==1.9.0、pydantic==2.14.1 没有写进 requirements，下次安装可能变。

以下 README 陈述与代码一致，不列入不符：默认账号与 24 小时令牌（`app.py:28`、`app.py:401`）、只监听 `127.0.0.1`（`app.py:861`，日志已印出）、端口 8000（`app.py:862`）、UTC 切日（`app.py:49`、`app.py:625`）、删除站点级联删除访问（`app.py:289`，live 第 15 项 404）、`/docs` `/redoc` `/openapi.json` 关闭（`app.py:334`，实测 404）、项目结构里列出的文件都在。

## 许可证与署名核查

仓内自洽，外部原文未核实。

- `LICENSE:1` 起是 MIT 正文。`LICENSE:3` 版权行是 `Copyright (c) 2026 weblens contributors`。
- `README.md:5` 指向 `UPSTREAM.md`，`README.md:122` 写 MIT 并指向 `LICENSE`。三处许可证名称一致。
- `UPSTREAM.md:5` 至 `UPSTREAM.md:8`：上游 `https://github.com/umami-software/umami`，commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`，许可证 MIT，署名 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。
- `NOTES.md:5` 至 `NOTES.md:7` 与上面的项目、commit、版权行一致。
- `UPSTREAM.md:14` 写明本仓是独立实现，未复制上游源码。仓库是 Python + FastAPI + SQLite，没有上游的 TypeScript 树，源码文件头也没有粘贴 Umami 版权行。在这个前提下，本仓 MIT（2026 weblens contributors）和单独的上游署名文件可以并存。
- 任务禁止抓取外网，因此没有核对：该 commit 在 2026-10-21 是否真是默认分支 HEAD，以及版权行是否与上游 `LICENSE` 逐字相同。这两句维持「未核实」，不改 `LICENSE` 与 `UPSTREAM.md`。

## 分级修复清单

### P0

无。依赖能装上，pytest 33 项通过，live 15 项通过，`127.0.0.1:8000` 首页返回 200 后已关闭。

### P1

无。先前收口的会话令牌哈希、128KB 正文上限、畸形 IPv6、深度嵌套 JSON、改密吊销其他会话、关闭接口文档，都在这次 33 项里通过。探针未见鉴权绕过或 SQL 注入（伪造用户名 401）。

下面三条不升到 P1，也不进本轮修改：

- `app.py:199` 无条件采信 `X-Forwarded-For`。`DECISIONS.md:45` D-6 已决：监听收在本机，改动会破坏现有测试的访客区分。不复议。
- `app.py:362` 的 413 不带安全响应头。实测 140KB 上报 `xfo=None`，正文是固定字符串 `Content Too Large`，没有会话或业务数据。
- `app.py:495` 把请求 Host 写进埋点 `script src`。实测 `Host: evil.example:8000` 会变成 `http://evil.example:8000/tracker.js`。带引号的 Host 被 Starlette 丢掉（`starlette/_utils.py` 的 Host 字符集不含 `"`）。这是「用当前访问地址生成绝对脚本地址」，默认监听 127.0.0.1 时 live 片段是 `http://127.0.0.1:8142/tracker.js`。

长口令不会放大 PBKDF2：200000 次下，8 字节与 65536 字节都是约 0.07 秒。不单列缺陷。

### P2

1. `README.md:106` 测试数 30 与实际 33 不符。修法：把「30 项」改成「33 项」。
2. `README.md:84` 与 `app.py:38`、`app.py:362`：超过 128KB 是 413 不是 400。修法：在该句后补「超过 128KB 时框架直接返回 413」。
3. `app.py:817` 发送 `title`，`app.py:778` 不入库，`README.md:70` 未写。修法：从埋点脚本去掉 `title`，或在 README 写明该字段不入库。
4. `app.py:730`、`app.py:740`、`app.py:747` 接受 README 未列的字段别名。修法：在 `README.md:72` 的示例下补一句别名；不要删别名，避免把已有客户端弄坏。
5. `app.py:71` 去掉 `www.` 前缀，`README.md:57` 未写。修法：接入步骤补一句「主机名去掉开头的 www.」。
6. `requirements.txt:1` 未钉 starlette、pydantic。修法：若要可复现构建，把本次的 starlette==1.9.0、pydantic==2.14.1 写入锁文件。本轮不改版本号。
7. `app.py:362` 的 413 响应没有 `X-Frame-Options`。修法：生成 413 时补上与 `app.py:356` 相同的两个响应头。正文无敏感数据，本轮不改。
8. `app.py:213` 的 `get_conn()` 在 `with` 退出时只提交事务，不关闭连接。修法：包一层 contextmanager，在 `finally` 里 `close()`。本次测试和实服务都没有因此失败，本轮不改。
9. `app.py:495` 把 Host 写进要贴到别人网站上的脚本地址。修法：若部署要固定对外地址，再增加显式基址配置；默认行为先保持。本轮不改。
10. `static/index.html:340` 的域名框 `maxlength="253"`，而 `app.py:34` 允许原始输入到 2048。修法：把 maxlength 调到 2048，避免长 URL 在提交前被浏览器截断。
11. `static/index.html:29` 字体名写成 `ui-sans-system`。修法：改成 `ui-sans-serif`。
12. `app.py:401` 登录没有速率限制。修法：仅在明确要监听 `0.0.0.0` 时再加；现在加会碰到测试里的连续登录。默认只监听本机（`app.py:861`），README 已要求放开前先改密码。本轮不改。
13. `tests/test_app.py:17` 触发 StarletteDeprecationWarning，警告在站点包 `fastapi/testclient.py:1`。`DECISIONS.md:47` 已决暂不动。修法：不改测试、不改依赖版本。

本轮只修 P0 与 P1。上面 P2 都不改源码。
