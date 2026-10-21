# weblens 验收审查

结论：本机可以按 README 把依赖装上并跑通。pytest **33 passed**（5.83s，收尾重跑 5.29s），`live_selftest.py` **15 项全过**，`127.0.0.1:8000` 首页 **200**、默认账号登录 **200**。没有 `/health`，该路径 **404**。P0 为空，P1 为空。本轮没有改仓库源码。

审查环境：Python 3.11.9（`python --version`），虚拟环境由 `C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe -m venv` 创建。钉死版本安装结果：fastapi 0.156.4、uvicorn 0.54.0、starlette 1.9.0、httpx 0.28.1、pytest 9.1.1。

## 本地跑通记录

命令与原文见 `run.md`。这里只保留判定用的片段。

### 安装

README Windows 节写的是 `py -m venv .venv`（README.md:35）。本机执行：

```
py -3 -m venv E:\muse-bridge\in\TASK-080-weblens\.venv
```

退出码 1：

```
Unable to create process using 'E:\python.exe -m venv E:\muse-bridge\in\TASK-080-weblens\.venv': ???????????
```

这是本机 `py` 启动器指向无效的 `E:\python.exe`，不是仓库缺陷。改用已核实的 Python 3.11.9 创建 `.venv` 后，下面两条均退出码 0：

```
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`Successfully installed ... fastapi-0.156.4 ... uvicorn-0.54.0 ... starlette-1.9.0`  
`Successfully installed ... httpx-0.28.1 ... pytest-9.1.1`

### 测试

```
.venv\Scripts\python.exe -m pytest tests/ -q --tb=short -p no:cacheprovider
```

工作目录是仓库根。`TEMP`/`TMP` 指向 `E:\muse-bridge\work\TASK-080-weblens\tmp`。

```
33 passed, 1 warning in 5.83s
```

警告全文：

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

位置在已安装包 `.venv\Lib\site-packages\fastapi\testclient.py:1`，不是本仓测试失败。

`tests\live_selftest.py` 在临时库上自行拉起 `app.py`（端口 8142），退出码 0，末尾：

```
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

趋势里有访问的那一天是 `2026-10-21`，响应时间 `created_at` 为 `2026-10-21T16:29:46+00:00`。与 README.md:14「按天切分使用 UTC」一致。

### 服务

`WEBLENS_DB_PATH` 放在 `E:\muse-bridge\work\TASK-080-weblens\server-data\weblens.db`，避免在仓库写出数据库（任务禁止用 del/rm 回收）。启动日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:60895 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:60895 - "GET /health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60895 - "GET /api/health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:60895 - "POST /api/login HTTP/1.1" 200 OK
```

首页正文含 `<title>weblens · 网站访问统计</title>`，响应头有 `x-frame-options: DENY` 与 `x-content-type-options: nosniff`。登录返回 `"username":"admin","must_change_password":true`。`/docs` 为 404。`/tracker.js` 为 200，`content-type: application/javascript`。

没有浏览器工具，没有做页面点击。服务在脚本 `finally` 里 `terminate()`。事后绑定检查：`PORT_8000_FREE`、`PORT_8142_FREE`。

另一次短时启动确认：`Host: evil.example` 时，埋点片段变成 `http://evil.example/tracker.js`；`Host` 带引号时片段仍是 `http://127.0.0.1:8000/tracker.js`。服务随后已停。

## README 与实际不符处

### 硬性不符

1. README.md:106 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。  
   实际：`tests/test_app.py` 有 28 个 `def test_`（从 tests/test_app.py:101 到 tests/test_app.py:503）。其中 `test_ua_classification_cases`（tests/test_app.py:470 起参数化，函数在 tests/test_app.py:481）展开为 6 条。28 − 1 + 6 = 33。pytest 原文是 `33 passed`。6 条 UA 参数化这个分句是对的，总数 30 是旧的。DECISIONS.md:82 记录当时把 README 从 25 改成 30；其后又加了 tests/test_app.py:178、tests/test_app.py:197、tests/test_app.py:337 三个用例，README 总数没跟着改。  
   同一句里的「真实流程自测 15 个检查点」与本次 `LIVE SELFTEST: ALL PASS (15 checks)` 一致。「钉死依赖复验通过」本次也复现了，只是项数应为 33。

2. README.md:84 写「请求体超过 64KB 时返回 400」。  
   实际上报接口在 64KB 以上、128KB 以内仍返回 400（app.py:35、app.py:710-714）。超过 128KB 时，`RequestBodyLimitMiddleware` 先返回 413（app.py:38、app.py:362）。tests/test_app.py:197-207 把这个差异写成了断言：约 70KB 的上报为 400，约 140KB 的登录正文为 413。该用例在本次 33 passed 里。README 没有 413 这一层。

### 读起来会误解，但不是反话

3. README.md:50 与 app.py:29-30 允许用 `WL_INITIAL_USERNAME` / `WL_INITIAL_PASSWORD` 改初始账号。static/index.html:203 把「默认账号 admin / admin123」写在静态 HTML 里，不读环境变量。未改环境变量时，这句话与默认值一致。改了环境变量后，页面仍显示 admin / admin123。DECISIONS.md:37 明确要求保留这句提示。

4. README.md:14 的「总 UV」加上 README.md:16「按天去重」。app.py:250-252 的访客哈希含日期，app.py:631-634 对整个区间做 `COUNT(DISTINCT visitor_hash)`。同一个人跨两天会在区间总 UV 里计两次。这和「按天去重」的字面一致，和「这 7 天一共有多少个不同的人」不是一回事。

5. README.md:65 的示例脚本主机是 `http://127.0.0.1:8000`。运行时 `tracking_snippet` 用 `request.base_url`（app.py:495-499）。从 `127.0.0.1:8000` 打开时与示例一致。本次原始请求 `Host: evil.example` 得到的片段是 `http://evil.example/tracker.js`。示例没有说主机被写死。

6. app.py:813-817 的埋点脚本还会发送 `title`。`collect`（app.py:738 起）不读 `title`，也不入库。README.md:12 只承诺上报当前页面与来源，没有承诺保存标题。

7. README.md:72-77 的示例字段是 `site_id`、`url`、`referrer`。app.py:729-760 还接受 `siteId`、`website_id`、`page_url`、`path`、`referer`，以及请求头 `Referer`。文档没写这些别名，也没有说拒绝它们。

## 许可证与署名核查

自洽，本次不改 LICENSE 和 UPSTREAM。

- LICENSE:1-3 是标准 MIT 正文，版权行是 `Copyright (c) 2026 weblens contributors`。README.md:122 指向这份 LICENSE，一致。
- UPSTREAM.md:5-8 把上游记为 `https://github.com/umami-software/umami`，许可证 MIT，署名行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。UPSTREAM.md:14 与 README.md:5 都写本仓是独立实现，没有复制上游源码。
- 本仓实现是 Python + FastAPI + SQLite（app.py:1-6、requirements.txt:1-2）。上游 Umami 是 Node/Next 技术栈（NOTES.md:8）。抽查 app.py 没有成段的上游源码。在「未复制源码」这个前提下，本仓 LICENSE 只署 weblens contributors，上游版权只出现在 UPSTREAM.md，两套署名不打架。
- `source_commit` `e92fdab99508a8ed05249f6c5f07e140deab79e1`（UPSTREAM.md:6）以及「版权行逐字复制」（UPSTREAM.md:13）本次按任务禁止外网，**未核实**。没有确凿反证，所以不改 UPSTREAM。
- 没有 AUTHORS 文件。MIT 版权行写成 “weblens contributors” 仍然是完整的许可证文本，不构成内部矛盾。

## 分级修复清单

### P0

无。依赖能安装，导入不报错，33 项测试通过，15 项实流程通过，8000 端口首页与登录正常。本机 `py` 启动器损坏记为环境限制，不记入项目缺陷。

### P1

无。下面几项看起来像安全问题，但有的已经写进决定记录，有的构不成要改代码的缺陷：

- 不强制改掉默认密码：DECISIONS.md:5-8（D-1）。首次登录只提示。本次登录响应 `must_change_password: true`，与 README.md:9 一致。
- `X-Forwarded-For` 无条件进入访客哈希：app.py:199-206。DECISIONS.md:45-46 写明暂不动，因为现有测试靠这个头区分访客（tests/test_app.py:75，tests/live_selftest.py:41）。升回 P1 再改会直接打红现有测试，而本任务不许改测试。
- 登录页保留默认账号文字：DECISIONS.md:37。
- 访客哈希算法维持现状：DECISIONS.md:87。
- 会话令牌哈希入库、128KB 正文上限、畸形 IPv6、深度嵌套 JSON、安全响应头，代码和回归测试都在，本次测试通过。

`Host: evil.example` 会进埋点脚本（app.py:495）。要拿到这段脚本必须先登录。默认监听是 127.0.0.1（app.py:861）。浏览器不能替 `http://127.0.0.1:8000` 这个源伪造 Host。带引号的 Host 本次没有写进片段。把它改成写死 127.0.0.1 会让 README.md:53 说的局域网访问拿到错误脚本地址。所以放到 P2，本轮不改。

### P2

1. README.md:106 测试总数 30 与实际 33 不符。修法：改成「33 项（其中 6 项为 UA 分类的参数化用例）」。
2. README.md:84 与 app.py:38、app.py:362、app.py:710 的状态码分层不符。修法：写明上报超过 64KB 且不超过 128KB 返回 400，任何接口正文超过 128KB 返回 413。
3. static/index.html:203 的默认账号提示不随 app.py:29-30 的环境变量变化。修法：提示改为「未设置 WL_INITIAL_USERNAME / WL_INITIAL_PASSWORD 时默认 admin / admin123」。DECISIONS.md:37 要求保留默认账号这句话，改动时保留这层意思。
4. app.py:199-206 无条件采信 `X-Forwarded-For`。修法：只在对端是明确配置的受信代理时采信。本轮不改，理由见 P1 节对 D-6 的引用。
5. app.py:495-499 埋点脚本主机等于请求 Host。修法：增加显式的公开基址配置，未配置时再使用请求主机。不要改成写死 127.0.0.1。
6. app.py:408 用 `!=` 比较密码哈希，用户不存在时跳过 PBKDF2。修法：用 `hmac.compare_digest`，用户不存在时也对一段哑哈希算一次。默认用户名已经写在 README 和登录页上，实际收益很小。
7. static/index.html:29 写了 `ui-sans-system`，后面还有 `system-ui` 能接上。修法：改成 `ui-sans-serif`。
8. app.py:817 多传 `title`，服务端丢弃。修法：从 `TRACKER_JS` 删掉 `title` 字段。
9. 测试收集时的 httpx/TestClient 弃用警告（安装包 `fastapi/testclient.py:1`）。修法：跟随 Starlette 改用 httpx2。不改：DECISIONS.md:47，而且会动依赖版本。
10. app.py:250-252 哈希不含 `site_id`，同一实例上的多个站点可以按哈希互相关联。修法：把站点 id 算进哈希材料。不改：DECISIONS.md:87 维持算法；改了以后旧数据的 UV 对不上。
