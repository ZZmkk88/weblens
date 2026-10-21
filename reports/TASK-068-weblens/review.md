# weblens 验收

能跑通。pytest **32 passed**（1 条库弃用警告），`live_selftest.py` **15/15 PASS**，`127.0.0.1:8000` 首页 **200**、登录 **200**。没有 P0。没有要改代码的 P1。本轮不改仓库源码。

## 本地跑通记录

环境：Python 3.11.9（`E:\muse-bridge\env\TASK-068-weblens\Scripts\python.exe`），满足 README「3.10+」。本机 `py` 启动器失败，原文：

```
Unable to create process using 'E:\python.exe -c "import sys; print(sys.version)"': ???????????
```

这是启动器指向不存在的 `E:\python.exe`，不是项目缺陷。依赖用已有虚拟环境安装。

`python -m pip install -r requirements-dev.txt`（exit 0）：fastapi 0.156.4、uvicorn 0.54.0 已满足；本次装上 httpx 0.28.1、pytest 9.1.1。传递依赖解析到 starlette 1.9.0、pydantic 2.14.1。

`python -m pytest tests/ -q --tb=short`：

```
32 passed, 1 warning in 4.82s
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

`python tests/live_selftest.py`（自起 127.0.0.1:8142，结束时进程自行退出）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | username=admin must_change_password=true
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

服务：`serve.py` 把库放到 `E:\muse-bridge\work\TASK-068-weblens\weblens.db`，监听 `127.0.0.1:8000`。

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
GET / status=200 ctype=text/html; charset=utf-8  （正文含 weblens）
GET /health status=404 {"detail":"Not Found"}
GET /docs /redoc /openapi.json status=404
GET /tracker.js status=200
GET /api/sites status=401 {"detail":"未登录"}
POST /api/login status=200 must_change=true user=admin
GET /api/me status=200
```

README 没有健康检查路由，`/health` 404 不记为缺陷。关掉后再次请求：`httpx.ConnectError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。`

逻辑探针（TestClient）：70KB 上报 **400**「请求体过大」且带 `X-Frame-Options: DENY`；140KB 上报 **413**、正文 `Content Too Large`、**没有**这两个安全头。站点名 `a' OR '1'='1` 原样入库。坏域名 **400**。连续两次 `init_db` 后用户数仍为 1，密码哈希长度 64，不是明文。

与 README 一致、本轮不再单列的行为：默认只监听 127.0.0.1（`app.py:860`）、令牌 24 小时（`app.py:28`）、今天按 UTC 切日（`app.py:49-50`、`app.py:625`）、删除站点级联清访问（`app.py:289`，自测与 `tests/test_app.py:489`）、文档页默认关闭（`app.py:334-339`）、单用户只建一次（`app.py:305-309`）、首次登录只提示改密（`index.html:237-239`，`DECISIONS.md:5-8`）。

## README 与实际不符处

1. **测试总数。** `README.md:106` 写「自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。`python -m pytest tests/ -q` 两次都是 **32 passed**。6 条参数化本身是对的（`tests/test_app.py:455-468`）。多出来的两条是 `tests/test_app.py:178` `test_session_token_stored_hashed_not_plaintext` 和 `tests/test_app.py:197` `test_request_body_hard_limit_413`。`DECISIONS.md:82` 把 README 从 25 改到 30，`DECISIONS.md:96-107` 又加了这两条，README 没跟着改。15 个自测点与输出一致，这半句没错。

2. **超大请求体的状态码。** `README.md:84` 写「请求体超过 64KB 时返回 400」。`app.py:35` 与 `app.py:710-714` 只覆盖上报接口的 64KB，返回 400。`app.py:38` 与 `app.py:362` 另有 128KB 硬上限，超过则中间件直接 413。探针：70KB → 400；140KB → 413，正文是 `Content Too Large`，不是「请求体过大」。

3. **埋点多传了 title。** `README.md:72-78` 的示例和 `README.md:80-83` 的入库说明只有 `site_id`、`url`、`referrer`。`app.py:812-817` 的脚本还发送 `title`。`collect`（`app.py:737-763`）不读这个字段，也不入库。

4. **「钉死版本」只钉了直接依赖。** `README.md:106` 与 `README.md:118` 写按钉死版本复验。`requirements.txt:1-2` 只钉 fastapi、uvicorn；`requirements-dev.txt:2-3` 只钉 httpx、pytest。本次实际装上的 starlette 1.9.0、pydantic 2.14.1 不在这两份文件里。安装和测试仍然成功，所以这不是跑不起来的原因。

5. **默认数据库路径的锚点。** `README.md:49` 写默认 `data/weblens.db`。`app.py:27` 是 `Path(__file__).parent / "data" / "weblens.db"`，跟 `app.py` 所在目录走，不跟进程当前目录走。按 README 先 `cd` 到仓库再 `python app.py` 时，两条路径重合。

6. **项目结构漏了 `.gitignore`。** `README.md:108-118` 的清单没有它。文件在 `.gitignore:1-10`，并忽略了 `.venv/`、`data/`、`*.db`。

## 许可证与署名核查

仓库内部自洽，上游原文未联网核实（本任务禁止抓取外部页面）。

- `LICENSE:1` 为 MIT，`LICENSE:3` 版权行是 `Copyright (c) 2026 weblens contributors`。`README.md:120-122` 写 MIT 并指向该文件，一致。
- `UPSTREAM.md:5-8` 与 `NOTES.md:5-7` 对上游的说法一致：Umami、commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`、MIT、版权行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。`README.md:5` 指向 `UPSTREAM.md`。
- `UPSTREAM.md:14` 称代码为独立实现、未复制上游源码。仓库里只有 Python / 静态页，没有上游的 TypeScript。本仓 MIT 与上游 MIT 不冲突；上游版权记在 `UPSTREAM.md`，没有写进本仓 `LICENSE`。对「独立实现 + 另行署名」这个说法，内部是说得通的。
- commit 是否为 2026-10-21 的默认分支 HEAD、版权行是否与上游 LICENSE 逐字相同：未核实。没有证据就改 `LICENSE` 或 `UPSTREAM.md`，所以这两个文件不动。

## 分级修复清单

### P0

无。测试与 README 所述的启动方式都能跑完。

### P1

无待改项。

下面两项按仓内已决记录关闭，不列入待修：

- `app.py:199-206` 无条件采信 `X-Forwarded-For` / `X-Real-IP`。`DECISIONS.md:44-46`（D-6）写明暂不改，避免破坏用该头区分访客的现有测试。
- pytest 的 `StarletteDeprecationWarning`。`DECISIONS.md:46` 记为测试侧警告，不改运行代码，也不改测试。

### P2

1. `README.md:106`：把「30 项」改成「32 项」。
2. `README.md:84`：补上「64KB 到 128KB 的上报返回 400；超过 128KB 返回 413」。
3. `app.py:816`：从埋点脚本去掉不入库的 `title`，或在 `README.md:72` 注明该字段会被丢弃。
4. `README.md:118`：改成「直接依赖钉死版本」；不要为这句话去改 `requirements.txt` 里已经能装上的版本号。
5. `README.md:49`：注明默认库文件相对 `app.py` 所在目录（`app.py:27`）。
6. `README.md:108`：项目结构补上 `.gitignore`。
7. `index.html:29`：无效字体名 `ui-sans-system` 改为 `ui-sans-serif`。后面还有 `system-ui`，页面仍能排版。
8. `app.py:352-362`：安全响应头加在请求体限制中间件的外面，让 413 也带上 `X-Frame-Options` 和 `X-Content-Type-Options`。140KB 探针里这两项为空；响应正文是固定的 `Content Too Large`，不是用户数据。
9. `app.py:401`：给登录和看板接口加 `Cache-Control: no-store`。探针里这些响应没有该头。默认只监听本机，优先级低。
10. `app.py:402`：`/api/login` 没有失败限速。对外监听时再加短时退避。本轮不加，现有测试会在几秒内连续登录多次，收紧会碰到断言。默认口令只提示、不强制，按 `DECISIONS.md:5-8` 维持。
