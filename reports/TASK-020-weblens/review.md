# weblens 验收

结论：依赖能装上，自动化测试 25 项通过，真实流程自测 15 项通过，默认端口首页返回 200。没有 P0。有 4 项 P1，其中 3 项改代码，1 项因现有测试约束不动。许可证与署名在仓库内部自洽；上游 commit 和版权原文未联网复核。

## 本地跑通记录

解释器：本机 `py -3 --version` 失败，原文 `Unable to create process using 'E:\python.exe --version'`。这是启动器损坏，不是项目缺陷。改用 `C:\Users\xzm\AppData\Local\Programs\Python\Python311\python.exe`，版本 `Python 3.11.9`。虚拟环境放在 `E:\muse-bridge\work\TASK-020-weblens\venv`，没有写进待审仓库。

安装：

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-020-weblens\requirements-dev.txt
```

退出码 0。末尾含 `fastapi-0.156.4`、`uvicorn-0.54.0`、`httpx-0.28.1`、`pytest-9.1.1`。

全量测试（工作目录 `E:\muse-bridge\in\TASK-020-weblens`）：

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

```
25 passed, 1 warning in 1.90s
```

警告原文是 Starlette 的 `Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败，未重试。与 README 写的 25 项一致。

真实流程：

```
E:\muse-bridge\work\TASK-020-weblens\venv\Scripts\python.exe tests\live_selftest.py
```

退出码 0，末行 `LIVE SELFTEST: ALL PASS (15 checks)`。与 README 写的 15 个检查点一致。脚本使用临时库和 `127.0.0.1:8142`，结束时自己 `terminate`。

默认端口：用 `WEBLENS_DB_PATH` 指到 `E:\muse-bridge\work\TASK-020-weblens\smoke.db` 后执行 `python app.py`。结果：

- `GET /` → 200，`content-type` 为 `text/html; charset=utf-8`，正文含 `weblens`
- `GET /health` → 404。README 没有这个路径，不记缺陷
- `GET /api/me` 无登录 → 401
- `netstat`：`TCP 0.0.0.0:8000 0.0.0.0:0 LISTENING`。监听进程是本次 `python app.py` 的子进程（父进程 28296，子进程 27196，均为 `python.exe`）
- 探针结束已 `terminate`。之后再次绑定 8000 成功，端口已释放

同一次探针还看到：带 `Origin` 时 `GET /`、`POST /api/login`、`GET /openapi.json` 的 `Access-Control-Allow-Origin` 为 `*`；11 个不同路径上报后 `top_pages` 只有 10 条而 PV 为 11；`referrer_domain` 长 30000 仍返回 201 并入库；用 token A 改密后 token B 访问 `/api/me` 仍是 200。

## README 与实际不符处

1. `README.md:41` 让用户打开 `http://127.0.0.1:8000`，`app.py:757` 却是 `uvicorn.run(app, host="0.0.0.0", port=port)`。进程在所有网卡上监听，不限于回环。netstat 原文见上节。
2. `README.md:80` 写「User-Agent 从请求头读取」。`app.py:662-667` 先取 JSON 的 `user_agent` / `userAgent`，没有才用请求头。
3. `README.md:79` 写 referrer 传入完整 URL，入库只留站外域名。`app.py:651-653` 在 JSON 带 `referrer_domain` 时只做小写和去 `www.`，不校验、不截断。探针把 30000 个字符写入 `pageviews.referrer_domain` 并得到 201。
4. `README.md:48` 的默认值写成 `data/weblens.db`。`app.py:27` 实际是 `Path(__file__).parent / "data" / "weblens.db"`，跟当前工作目录无关。
5. `README.md:47` 只列出 `WEBLENS_PORT`。`app.py:756` 在该变量缺省时还会读 `PORT`。
6. `README.md:13` 的「今天」没有时区。`app.py:45-46` 与 `app.py:549` 用 UTC 切日。`NOTES.md:25` 写了 UTC，README 没写。
7. `README.md:13` 把活跃页面数列为看板指标。`static/index.html:507` 用 `stats.top_pages.length`，而 `app.py:570` 对热门页面 `LIMIT 10`。11 个不同路径时接口只返回 10 条，页面上的活跃页面数最多是 10。

README 里「25 项测试、15 个检查点」与本次运行一致，不算不符。

## 许可证与署名核查

仓库内部是对齐的。

- `LICENSE:1-3`：MIT，`Copyright (c) 2026 weblens contributors`。
- `README.md:5` 指向 `UPSTREAM.md`，`README.md:113-115` 写本项目是 MIT。
- `UPSTREAM.md:5-8`：上游 `https://github.com/umami-software/umami`，commit `e92fdab99508a8ed05249f6c5f07e140deab79e1`，许可证 MIT，版权行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。同文件写明独立实现、未复制上游源码。
- `NOTES.md:5-7` 与 `UPSTREAM.md` 是同一个项目、同一个 commit、同一行版权声明。

在 `app.py`、`static/index.html`、`tests/` 里检索不到 `umami`，也没有上游版权头。实现是 Python + FastAPI + SQLite，和上游的 Node.js / PostgreSQL 不是同一套代码。这和「未复制源码」一致。独立实现不需要把上游版权行再写进本仓库 `LICENSE`；上游署名放在 `UPSTREAM.md`，README 有链接，这样是自洽的。

未联网核对 commit 是否仍是默认分支 HEAD，也未核对上游 LICENSE 原文是否与 `UPSTREAM.md:8` 逐字相同。任务禁止抓取外网。这两条不记为已核实，也不记为缺陷。

## 分级修复清单

### P0

无。安装、25 项测试、15 项实流程、`GET /` 200 都已跑通。

### P1

1. `app.py:757` 默认监听 `0.0.0.0`，同时默认口令是 `admin` / `admin123`（`app.py:29-30`）。修法：默认 host 改为 `127.0.0.1`，保留 `WEBLENS_HOST` 可覆盖。
2. `app.py:298-304` 对全部路由使用 `allow_origins=["*"]`。带 `Origin` 的首页、登录和 `/openapi.json` 都返回 `Access-Control-Allow-Origin: *`，任意网页都能读到预填口令并调用登录接口。修法：删除全局 CORS，只给 `POST /api/collect` 和 `GET /tracker.js` 加跨源头。
3. `app.py:372-385` 修改密码不删除其他会话。探针里 token A 改密成功后，token B 的 `GET /api/me` 仍是 200。修法本应是删掉同一用户除当前 token 以外的会话。本次不改：`tests/test_app.py:53-56` 的 `auth` 是模块级 fixture，`tests/test_app.py:117-131` 用另一个 token 把密码改回去之后，后面的用例仍发送原来的 token。撤销其他会话会让这些用例变成 401，而本任务不许改测试。
4. `app.py:620` 起采集接口不限制请求体大小，`app.py:651-653` 把 `referrer_domain` 几乎原样入库。修法：拒绝超过 64KB 的请求体；`referrer_domain` 必须符合已有域名规则且不超过 253，否则存空字符串。

### P2

1. `static/index.html:507` 与 `app.py:570`：活跃页面数被 Top 10 截断。修法：统计接口返回区间内的不同路径数，前端改读这个字段。
2. `app.py:297` 未关闭 FastAPI 文档。`GET /docs` 与 `GET /openapi.json` 为 200。修法：把 `docs_url`、`redoc_url`、`openapi_url` 设为 `None`，或加显式开关。
3. `static/index.html:198-203` 登录框预填 `admin` / `admin123`。修法：去掉 `value`，保留同页文字提示。全局 CORS 去掉之后，其他网站不能再直接读这页。
4. `app.py:174-181` 无条件信任 `X-Forwarded-For`。`tests/test_app.py:72` 和 `tests/live_selftest.py` 靠这个头区分访客。修法：只在直连方为本机或配置了可信代理时采信。本次不改，避免破坏现有测试。监听改到回环后，风险限于本机进程。
5. `app.py:662-667` 允许 JSON 里的 `user_agent` 覆盖请求头，和 `README.md:80` 不一致。修法：只读取 `User-Agent` 头。分类结果仍然只存粗类，不造成超长字段。
6. `README.md:13` 未说明「今天」按 UTC。修法：在 README 统计一节补一句，与 `NOTES.md:25`、`app.py:549` 对齐。不改切日逻辑。
7. `app.py:204-207` 两个请求同时第一次生成 UV 盐时，后一次 `INSERT` 可能撞主键。修法：捕获完整性错误后重新读取。
8. 测试依赖的 Starlette 已提示 `httpx` TestClient 弃用。当前 25 项仍通过。修法：等上游支持 `httpx2` 再动。本次不改 `requirements` 里的版本号。
