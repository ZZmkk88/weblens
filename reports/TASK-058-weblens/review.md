# weblens 验收审查

结论：按 README 能在本机装起并跑通。pytest **28 passed**（6.98s），`live_selftest.py` **15 项全部 PASS**（4.677s），`python app.py` 监听 **http://127.0.0.1:8000**，首页 **200**。没有健康检查路由（`/health` 等为 404）。P0 没有。P1 有 1 条：畸形 IPv6 字符串会让公开上报接口抛 `ValueError`，这次访问不会入库。许可证三份声明内部一致；上游 commit 与上游 LICENSE 原文未做外网复核。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。本机 `py -3 --version` 失败，原文：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

这是本机启动器损坏，不是仓库问题。虚拟环境建在 `E:\muse-bridge\work\TASK-058-weblens\venv`，没有写进仓库。

安装（均 exit 0）：

```
...\venv\Scripts\python.exe -m pip install -r requirements.txt
Successfully installed ... fastapi-0.156.4 ... uvicorn-0.54.0

...\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Successfully installed ... httpx-0.28.1 ... pytest-9.1.1
```

全量测试（工作目录为仓库根，TEMP 改到 `E:\muse-bridge\work\TASK-058-weblens\tmp`）：

```
...\venv\Scripts\python.exe -m pytest tests/ -q --tb=short
............................                                             [100%]
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
28 passed, 1 warning in 6.98s
```

警告与 `DECISIONS.md` D-6 已记录的 TestClient/httpx 弃用一致，不记为失败。

真实流程（脚本自行监听 `127.0.0.1:8142`，跑完会 terminate 子进程）：

```
...\venv\Scripts\python.exe tests/live_selftest.py
PASS 首页能打开且是 weblens 页面
PASS 登录成功 | {"username":"admin","must_change_password":true}（token 已截断）
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
EXIT 0
```

耗时 4.677s。15 个 `check()` 全部通过。

按 README 起服务（未设置 `WEBLENS_HOST` / `WEBLENS_PORT`；继承的 `PORT` 为 None；数据库放到工作目录 `run-server.db`，避免在仓库里生成 `data/weblens.db`）：

```
...\venv\Scripts\python.exe app.py
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

启动到首次响应 1.49s。

```
GET /             200  text/html; charset=utf-8  len=28316  正文含 weblens
GET /health       404
GET /api/health   404
GET /healthz      404
GET /docs         404
GET /redoc        404
GET /openapi.json 404
GET /tracker.js   200  含 /api/collect 与 data-weblens-id
POST /api/login   200  must_change_password=true
POST /api/collect 体长超过 64KiB  400  {"detail":"请求体过大"}
```

首页响应头只有 `server: uvicorn` 与 `content-type`。随后 terminate 子进程，再连 `127.0.0.1:8000` 得到 `TimeoutError`，端口已关闭。

修前探针（`referrer` = `http://[`）原文：

```
File "app.py", line 710, in collect
    referrer_domain = domain_from_value(str(referrer_value))
File "app.py", line 88, in domain_from_value
    host = urllib.parse.urlparse(raw).hostname or ""
ValueError: Invalid IPv6 URL
```

同一输入在 `domain_from_value`、`parse_page_path`、`normalize_domain_input`、`page_hostname` 上都是这个 `ValueError`。`http://[::1`、`http://[gggg::1]/` 同样抛错。合法地址 `http://[::1]/x` 能解析出 hostname `::1`。

## README 与实际不符处

1. `README.md:106` 写「当前自动化测试 25 项」。实测 pytest 收集并跑完 **28** 项：`tests/test_app.py` 有 23 个测试函数，其中 `tests/test_app.py:383` 起的 `test_ua_classification_cases` 参数化 6 条（`:385-392`），22 + 6 = 28。同句的「真实流程自测 15 个检查点」与 `tests/live_selftest.py` 的 15 次 `check()` 以及本次 `ALL PASS (15 checks)` 一致。
2. `README.md:13` 写按「今天 / 近 7 天 / 近 30 天」查看，没有写时区。`app.py:45` 的 `utcnow()` 使用 `datetime.now(timezone.utc)`，`app.py:576` 的统计截止日是 `utcnow().date()`。`NOTES.md:25` 写明按 UTC 日期。中国时区 0:00–8:00 的「今天」与 UTC 日期不是同一天。
3. `README.md:9` 写「单用户登录」。`app.py:270-284` 只检查 `WL_INITIAL_USERNAME` 这一个名字是否已存在，不存在就再插入一个 `must_change_password=1` 的用户。初始用户已经在库里时，把该环境变量改成另一个名字再启动，库里会有两个可登录账号。默认配置下仍然只有 admin。
4. `README.md:110-115` 的项目结构没有列出仓库里存在的 `DECISIONS.md`、`LICENSE`、`requirements.txt`、`requirements-dev.txt`。这是清单遗漏，不是行为描述写反。

以下 README 陈述与本次运行一致，不列入不符：默认 `127.0.0.1:8000`（`app.py:811-812`）、请求体超过 64KiB 返回 400（`app.py:34`，探针返回「请求体过大」）、Token 24 小时（`app.py:27`）、删除站点级联删除访问记录（pytest `test_delete_site_cascades_pageviews` 通过）、`/docs` `/redoc` `/openapi.json` 关闭（`app.py:298-303`，实探均为 404）。README 没有承诺 `/health`，代码也没有该路由。

## 许可证与署名核查

- `LICENSE:1-3` 是标准 MIT 文本，版权行为 `Copyright (c) 2026 weblens contributors`。`README.md:117-119` 写 MIT 并指向该文件。两者一致。
- `UPSTREAM.md:5-8` 与 `NOTES.md:5-7` 一致：上游为 umami（`https://github.com/umami-software/umami`），许可证 MIT，署名行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`，并写明本仓库是独立实现、未复制上游源码。
- 抽查结果与「未复制源码」相符：仓库只有 Python / 单页 HTML / 测试，没有上游的 Node、Next 或 `src/app/api/send` 源码。本项目 `LICENSE` 不包含 Umami 版权行；在未复制源码的前提下，把上游署名放在 `UPSTREAM.md` 而不是写进自己的 `LICENSE`，与 MIT 的「复制了才必须附带原文版权声明」不冲突。
- `UPSTREAM.md:12-13` 称 `source_commit` `e92fdab99508a8ed05249f6c5f07e140deab79e1` 是 2026-10-21 经 GitHub 实查的默认分支 HEAD，且署名行逐字来自上游 `LICENSE`。本次任务禁止抓取外部页面，**这两句没有外网复核，不能证实也不能证伪**。格式上该 commit 是 40 位十六进制。没有发现可以改 `LICENSE` 或 `UPSTREAM.md` 的仓库内证据，这两个文件不改。

## 已决事项（不列入待修）

`DECISIONS.md:3` 要求已决事项直接引用关闭。

- D-1（`DECISIONS.md:5-8`）：首次改密只提示、不拦截。`app.py:415-420` 只返回标志，各业务接口不检查它。不改成强制改密。
- D-5（`DECISIONS.md:36-37`）：登录框不预填密码，页面文字提示保留。`static/index.html:198-203` 输入框没有 `value`，提示语仍在。不删这行提示。
- D-6（`DECISIONS.md:44-48`）：`X-Forwarded-For` 无条件采信（`app.py:174-181`）、UV 盐并发插入可能撞主键（`app.py:204-207`）、TestClient 的 httpx 弃用警告。这三项维持原决定，不改。本次 pytest 的那条 warning 就是第三项。

## 分级修复清单

### P0

无。依赖按钉死版本安装成功，测试与真实流程通过，服务能在默认端口起停。

### P1

1. **畸形 IPv6 让公开上报抛异常并丢掉这次访问。** `app.py:88`（`domain_from_value`）对 `referrer` `http://[` 执行 `urlparse(...).hostname` 时抛出 `ValueError: Invalid IPv6 URL`，调用点在 `app.py:710`。同输入在 `app.py:98`（`parse_page_path`）、`app.py:71`（`normalize_domain_input`）、`app.py:111`（`page_hostname`）同样抛错。公开接口 `POST /api/collect` 不需要登录，异常发生在入库之前，这次 pageview 不会写入。显式 `referrer_domain` 不合规则时会记空串（`app.py:696-701`），URL 解析这条路径没有同样的兜底。修法：在上述四个函数里捕获 `ValueError` 与 `UnicodeError`；来源域名改记空串并继续入库，页面地址与站点域名返回 400。

### P2

1. `README.md:106` 的测试数量写成 25。修法：改成 28，并注明其中 6 条来自 UA 参数化。
2. `README.md:13` 的「今天」未写 UTC。修法：在该条或环境变量表旁注明统计日界是 UTC，与 `NOTES.md:25` 对齐。
3. `app.py:270-284` 在更换 `WL_INITIAL_USERNAME` 后会再插入用户，与 `README.md:9` 的单用户说法不一致。修法：库里已经有任意用户时不再自动插入。
4. `README.md:110-115` 未列出 `DECISIONS.md`、`LICENSE`、两份 requirements。修法：补进项目结构。
5. 首页响应没有 `X-Frame-Options`（实探 `GET /` 的头只有 `server` 与 `content-type`，见 `app.py:800-802`）。修法：给页面响应加上 `X-Frame-Options: DENY` 和 `X-Content-Type-Options: nosniff`。默认只监听本机，故不升为 P1。
6. `app.py:211-218` 的访客哈希是 SHA-256(盐 + IP + UA 粗类 + 日期)，盐写在同一库的 `settings` 表（`app.py:204-207`）。明文 IP 不落库，但拿到数据库文件的人可以穷举 IPv4。修法：盐放到库外，或对 IP 使用慢哈希。这是设计取舍，本次不改算法。
7. `static/index.html:336` 写「只保留主机名」，`app.py:61-62` 还会去掉开头的 `www.`（测试要求这样）。修法：把这句说明补上会去掉 `www.` 前缀。
