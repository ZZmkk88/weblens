# weblens 验收审查

结论：按 README 用 Python 3.11.9 装钉死依赖后，自动化测试 **33 passed**（6.39s），真实流程自测 **15/15 PASS**，`127.0.0.1:8000` 首页 **200**。没有跑不起来的 P0，也没有需要改代码的 P1。README 有 4 处与代码不符（测试计数、请求体状态码、UV 盐生成时机、非字符串 `url`）。许可证与署名在仓库内部自洽。本轮不改源码。

## 本地跑通记录

环境：Windows，`python --version` 为 `Python 3.11.9`。虚拟环境在 `E:\muse-bridge\work\TASK-092-weblens\.venv`，没有写进仓库。依赖命令：

```text
python -m venv E:\muse-bridge\work\TASK-092-weblens\.venv
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-092-weblens\requirements-dev.txt
```

pip 退出码 0。关键行：`Successfully installed ... fastapi-0.156.4 ... httpx-0.28.1 ... pytest-9.1.1 ... starlette-1.9.0 ... uvicorn-0.54.0`。

按 README 的 Windows 第一步 `py -3 --version` 在本机失败，原文：

```text
Unable to create process using 'E:\python.exe --version': ???????????
```

这是本机 `py` 启动器指向不存在的 `E:\python.exe`，记为环境限制。改用已可用的 `python` 后，安装、测试、起服务都走通。未执行 `Activate.ps1`，直接调用 venv 里的 `python.exe`。

全量测试（工作目录为仓库根）：

```text
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=line
```

```text
.................................                                        [100%]
33 passed, 1 warning in 6.39s
```

警告原文（来自依赖，不是失败）：

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

真实服务自测：

```text
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe tests\live_selftest.py
```

退出码 0。末行：`LIVE SELFTEST: ALL PASS (15 checks)`。节选：`PASS 首页能打开且是 weblens 页面`、`PASS 今日 PV/UV 正确：PV 4、UV 2`、`PASS 删除后统计接口返回 404`。趋势最后一天是 `2026-10-21`，`created_at` 为 `2026-10-21T17:07:51+00:00`（北京时间 2026-10-22 01:07）。与 README「今天以及按天切分使用 UTC」一致。令牌字段已从本报告截断。

按 README 起服务（库文件改到工作目录，避免把 `data\weblens.db` 写进仓库；监听仍是默认的 `127.0.0.1:8000`）：

```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

本机 HTTP 检查（`urllib`，未用 curl）：

| 请求 | 结果 |
|---|---|
| `GET /` | 200，`text/html`，正文含 `<title>weblens · 网站访问统计</title>`，`X-Frame-Options: DENY`，`X-Content-Type-Options: nosniff` |
| `GET /tracker.js` | 200，`application/javascript`，正文含 `/api/collect` |
| `GET /docs` | 404 `{"detail":"Not Found"}` |
| `POST /api/login` `admin` / `admin123` | 200，`must_change_password: true` |
| `GET /api/me` 带令牌 | 200 |
| `GET /health`、`GET /api/health` | 404 `{"detail":"Not Found"}` |

仓库没有健康检查路由，README 也没写。首页即 README 指定的入口，返回正常。检查后已停进程。`netstat` 上 `127.0.0.1:8000` 不再是 LISTENING，只剩 TIME_WAIT。再次连接原文：`ConnectionRefusedError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。`

测试不访问外网，没有因抓标题之类失败的用例，无需重试。

## README 与实际不符处

1. **测试条数。** `README.md:106` 写「当前自动化测试 30 项（其中 6 项为 UA 分类的参数化用例）」。实测 `33 passed`。`tests/test_app.py` 有 28 个 `def test_`（`grep` 计数），其中 `tests/test_app.py:481` 的 `test_ua_classification_cases` 展开 6 条，33 = 28 − 1 + 6。多出来的 3 个函数是 `tests/test_app.py:178`、`tests/test_app.py:197`、`tests/test_app.py:337`。同句里的「真实流程自测 15 个检查点」与实测一致。

2. **超限请求体的状态码。** `README.md:84` 写「请求体超过 64KB 时返回 400」。`app.py:35` 的上报上限是 64KB 并在 `app.py:710` 返回 400；`app.py:38` 与 `app.py:362` 另有 128KiB 框架上限，再大则 413。`tests/test_app.py:197` 明确要求约 140KB 的登录正文返回 413。超过 128KiB 时 README 这句话不成立。

3. **UV 盐不是启动时生成。** `README.md:51` 写「不设置时首次启动在本机数据库中生成」。`init_db`（`app.py:256`）只建表和初始用户，不写 `uv_salt`。盐在 `get_uv_salt`（`app.py:220`）里惰性插入，而它只被 `visitor_hash`（`app.py:249`）调用，调用点在上报 `app.py:777`。旁证：服务起来并登录后、尚未上报时，工作库 `settings` 查询结果为 `[]`。`NOTES.md:26` 与 `NOTES.md:43` 是同一说法。

4. **非字符串 `url` 会入库。** `README.md:81` 写 `url` 可传完整 URL 或页面路径，入库只留路径。`app.py:738` 对 `url` / `page_url` / `path` 直接 `str()`。探针 `POST /api/collect` 正文 `{"url": {"a": 1}}` 返回 201，`page_path` 为 `/{'a': 1}`。

另外两处低级别路径说明，不构成行为错误：

- `README.md:24` 与 `README.md:34` 的 `cd weblens`：本交付根目录就是项目根，下面没有 `weblens` 子目录。在仓库根执行后续命令可以跑通。
- `README.md:49` 默认库路径 `data/weblens.db` 与 `app.py:27` 的文件名一致，但代码锚定的是 `app.py` 所在目录（`BASE_DIR`），不是进程当前工作目录。

抽查与代码一致、不列入不符：默认账号与 24 小时令牌（`app.py:28`）、只监听 `127.0.0.1`（`app.py:861`）、端口先看 `WEBLENS_PORT` 再看 `PORT`（`app.py:862`）、删除站点级联删除访问（`app.py:289` 与 `app.py:603`）、`/docs` 关闭（`app.py:334`）、统计区间 UTC（`app.py:625`）、埋点标签形态（`app.py:497`）。

## 许可证与署名核查

内部自洽，未改 `LICENSE` 与 `UPSTREAM.md`。

- `LICENSE:3` 为 `Copyright (c) 2026 weblens contributors`，后文是标准 MIT 许可。`README.md:122` 写 MIT 并指向该文件。
- `UPSTREAM.md:5-8` 记录上游 `https://github.com/umami-software/umami`、提交 `e92fdab99508a8ed05249f6c5f07e140deab79e1`、许可证 MIT、署名行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。`NOTES.md:5-7` 与这三行相同。`UPSTREAM.md:14` 与 `README.md:5` 都写明本仓是独立实现，署名另见 UPSTREAM。
- 两套版权指向两个作品：本仓 MIT 归「weblens contributors」，上游 MIT 署名放在 `UPSTREAM.md`，不放进 `LICENSE`。在「未复制上游源码」这一前提下，这样拆是自洽的。本仓是 Python，`NOTES.md:8` 写上游要求 Node.js 与 PostgreSQL，仓库里没有上游源码树。
- 任务禁止抓取外部页面，因此 **未对照 GitHub 复核** `source_commit` 是否仍是默认分支 HEAD，也 **未核实** 上游 LICENSE 原文是否与 `UPSTREAM.md:8` 逐字相同。仓库内部文件之间没有互相矛盾。没有确凿错误，所以不改这两个文件。

## 分级修复清单

### P0

无。依赖可安装，33 项测试通过，自测 15 项通过，首页在 8000 端口返回 200。

### P1

无。登录、会话哈希、未登录 401、文档页关闭、上报校验、删除级联，均与现有测试和本次探针一致。下面几项看起来像安全问题，但已有决定或够不上 P1，不修：

- 首次改密只提示、不拦截。`DECISIONS.md:5`。探针在 `must_change_password: true` 时建站返回 200。
- `X-Forwarded-For` 无条件采信。`app.py:199`，`DECISIONS.md:45` 写明暂不改。
- 访客哈希可被穷举还原 IP。`DECISIONS.md:87` 定为设计取舍，不改算法。
- 密码比较用 `!=`（`app.py:408`）。错误密码路径仍要做 20 万次 PBKDF2；探针里 1000 字符与 60000 字符密码都约 0.07 秒。默认用户名已公开。不单列为待修 P1。

### P2

1. `README.md:106`。测试数写成 30，实测 33。修法：改为 33，并注明 6 条来自 UA 参数化。
2. `README.md:84`（对应 `app.py:35`、`app.py:362`、`app.py:710`）。超过 128KiB 实际是 413。修法：补上「64KB 到 128KiB 的上报为 400，更大的正文为 413」。
3. `README.md:51`（对应 `app.py:220`、`app.py:256`、`app.py:777`）。盐在第一次上报时写入，不是启动时。修法：改 README 与 `NOTES.md:26` 的时机描述。
4. `app.py:485`（入口 `app.py:562`）。已登录访问超过 SQLite 整数上限的站点 ID 时 `OverflowError`，实服务回 `500` 正文 `Internal Server Error`，且该响应没有 `X-Frame-Options`。未登录同一路径是 401。之后首页仍 200，进程没退出。修法：`site_pk` 超出 `1 .. 2^63-1` 时直接 404。
5. `app.py:738`（对照 `README.md:81`）。非字符串 `url` 被 `str()` 后当路径入库。修法：不是字符串就返回 400。
6. `static/index.html:29`。字体名 `ui-sans-system` 拼错。修法：改为 `ui-sans-serif`。
7. `README.md:24` 与 `README.md:34`。`cd weblens` 在本交付目录不存在。修法：改成「在仓库根目录执行」。
8. `app.py:269`。过期会话不清理。修法：登录时删掉 `expires_at` 已过的行。

已决不改、也不升格：`DECISIONS.md:45` 的转发头、`DECISIONS.md:47` 的 httpx 弃用警告（本轮 pytest 仍有 1 条）、`DECISIONS.md:87` 的哈希算法。改这些会动测试假设或依赖版本，任务不允许。
