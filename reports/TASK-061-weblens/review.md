# weblens 验收审查

结论：按 README 的钉死版本能装能测。pytest `30 passed`，`live_selftest.py` 15 项全过，`127.0.0.1:8000` 首页 200。没有 P0。P1 有 2 项：会话令牌明文落库，以及未认证接口的请求体没有硬上限。许可证在仓库内部自洽；上游 commit 与版权行原文未核实。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。虚拟环境在 `E:\muse-bridge\work\TASK-061-weblens\.venv`，不放进仓库。

安装（退出码 0）：

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1` 均安装成功，无版本冲突。

自动化测试（退出码 0，5.51s）：

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe -m pytest tests/ -q
30 passed, 1 warning in 5.51s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 与 `DECISIONS.md:47` D-6 已记录的测试侧警告一致，不是失败。

真实流程（退出码 0）：

```
E:\muse-bridge\work\TASK-061-weblens\.venv\Scripts\python.exe tests\live_selftest.py
LIVE SELFTEST: ALL PASS (15 checks)
```

15 行均为 `PASS`，含首页、埋点脚本、登录、建站、上报、今日 PV 4 / UV 2、近 7 天趋势、改名、删除、删除后 404。

服务：`python app.py`，`WEBLENS_HOST=127.0.0.1`，`WEBLENS_PORT=8000`，数据库放在工作目录。日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

`GET /` → 200，`text/html`，标题为 `weblens · 网站访问统计`。`GET /health` 与 `GET /api/health` → 404 `{"detail":"Not Found"}`。`app.py` 没有健康检查路由，README 也没写，不记为故障；首页 200 即存活。`GET /docs` 与 `GET /openapi.json` → 404。未登录 `GET /api/sites` → 401。`admin/admin123` 登录 → 200，`GET /api/me` → 200。

无 `Content-Length` 的分块 `POST /api/collect`（约 70KB）→ `HTTP/1.1 400`，`{"detail":"请求体过大"}`，是读完才拒绝。5000 字符密码登录 → 401，0.071 秒，没有可观察的 CPU 卡死。

进程已停。`terminate()` 瞬间端口仍可连（子进程 pid 35420 晚于 Popen pid 35224）。复查 `Get-NetTCPConnection -LocalPort 8000 -State Listen` 无监听，`Get-Process -Id 35420,35224` 两个进程都不在。

## README 与实际不符处

1. `README.md:106` 写「当前自动化测试 25 项」。`tests/test_app.py:424` 的 `test_ua_classification_cases` 用 6 组参数展开。`def test_` 共 25 个，pytest 收集数是 30。本次输出是 `30 passed`，不是 25 passed。15 个真实流程检查点与输出一致，这句的后半是对的。

2. `README.md:51` 写 `WEBLENS_UV_SALT` 不设置时「首次启动在本机数据库中生成」。`app.py:246` 的 `init_db()` 不写 `settings`。盐在 `app.py:210` 的 `get_uv_salt()`，第一次计算访客哈希时才插入。证据：服务启动并登录后查库，`settings` 为空（`inspect_settings.py` 输出 `settings []`）。

3. `README.md:49` 默认库路径写 `data/weblens.db`。`app.py:26` 实际是 `app.py` 所在目录下的 `data/weblens.db`，不是进程当前工作目录。按 README 先 `cd` 到项目目录再启动时两者重合；从别的目录执行 `python app.py` 则不是 cwd 下的 `data/`。

4. `README.md:109` 起的项目结构没有列出仓库里存在的 `DECISIONS.md`、`LICENSE`、`requirements.txt`、`requirements-dev.txt`。这是清单遗漏，不是相反描述。

已核对、与代码一致、不记为不符：默认 `127.0.0.1:8000`（`app.py:846`）、默认账号、Token 24 小时（`app.py:27`）、删除站点级联删访问、上报只存路径/站外域名/UA 粗分类、正文超过 64KB 返回 400（有 Content-Length 时 `app.py:696` 在读正文前拒绝）、`/docs` 默认关闭。

## 许可证与署名核查

仓库内部自洽，上游事实未改，也没有确凿反证。

- `LICENSE:1` 起是标准 MIT 正文。`LICENSE:3` 为 `Copyright (c) 2026 weblens contributors`。
- `README.md:118` 写 MIT，并指向 LICENSE，与许可证文件一致。
- `UPSTREAM.md:7` 写上游 license 为 MIT，署名对象是 Umami，与本仓库 `LICENSE:3` 的版权人不是同一个主体，两者可以并存。
- `UPSTREAM.md:14` 称代码为独立实现、未复制上游源码。仓库内是 Python + FastAPI + SQLite，没有上游那套 TypeScript/React 源码，也没有第二份 GPL/Apache 许可证头。这与自述一致。
- `UPSTREAM.md:5` 的 `source_commit`（`e92fdab99508a8ed05249f6c5f07e140deab79e1`）以及 `UPSTREAM.md:8`、`UPSTREAM.md:12`「版权行逐字复制自上游 LICENSE」：**未核实**。本任务禁止访问外网，没有对照 GitHub。没有确凿错误，不改 LICENSE / UPSTREAM。

## 分级修复清单

### P0

无。安装、pytest、真实流程自测、8000 端口首页均已跑通。

### P1

1. 会话令牌明文落库。`app.py:396` 把 `secrets.token_urlsafe` 的原值写入 `sessions.token`，`app.py:377` 按原值查询。查库：密码哈希长度 64，会话令牌长度 43，与登录响应 `token_len=43` 相同。数据库文件被拷走后，24 小时内可直接冒充登录，密码哈希挡不住。修法：`sessions.token` 只存 `sha256(token)`，接口仍返回原始令牌；登录写入、校验、登出、改密吊销都走哈希。

2. 未认证接口的请求体没有硬上限。`app.py:694` 只在 Content-Length 为纯数字且超限时提前返回；否则 `app.py:698` `await request.body()` 先把正文读完。分块探测（无 Content-Length、约 70KB）得到 400，但是读完才拒绝。`app.py:387` 的登录没有体长检查，Pydantic 会把正文整段读入。修法：在安全响应头中间件之外加请求体硬上限（128KiB，高于测试里约 72KiB 的超限样例，避免 413 抢走 `tests/test_app.py:260` 期望的 400「过大」）。`/api/collect` 原有的 64KB / 400 逻辑保留。

### P2

1. `README.md:106` 的「25 项」与 pytest 的 30 不一致。修法：改成「25 个测试函数，参数化展开后 30 条」。
2. `README.md:51` 的 UV 盐生成时机与 `app.py:210` 不符。修法：写成第一次计算 UV 时写入 `settings`。
3. `README.md:49` 与 `app.py:26` 的数据库路径锚点。修法：写明相对 `app.py` 所在目录。
4. `app.py:189` 无条件采信 `X-Forwarded-For`。修法：不改。`DECISIONS.md:45` D-6 已关闭；测试用该头区分访客，改了会打红用例，且不许改测试。
5. `app.py:203` 的 `get_conn()` 放在 `with` 里只提交、不关闭连接（`sqlite3.Connection` 的上下文管理器不 close）。`app.py:405` 还在 `with` 之外读取 `sqlite3.Row`。修法：关闭连接前把行转成 dict。本轮不改，牵涉所有数据库调用。
6. `app.py:394` 用 `!=` 比较密码哈希。修法：`hmac.compare_digest`。PBKDF2 的耗时远大于比较本身，不单独立项。
7. `app.py:387` 登录没有失败限速。修法：不改。测试在数秒内连续登录，限速会打红现有用例。
8. `static/index.html:340` 域名框 `maxlength="253"`，`app.py:33` 允许 URL 最长 2048。超长地址会被浏览器截断后再解析。修法：前端上限改为 2048。
9. `DECISIONS.md:47` 的 httpx/TestClient 弃用警告。修法：不改测试。

不列入待修：`DECISIONS.md:7` D-1 规定首次改密只提示、不强制，与 `README.md:9` 和 `app.py:422` 附近「不拦截业务接口」一致。5000 字符密码 0.071 秒返回 401，不构成可观察的 CPU 拒绝服务。
