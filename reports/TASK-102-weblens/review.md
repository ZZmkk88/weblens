# weblens 验收审查

结论：仓库能按 README 在本机跑通。pytest 37 项通过，真实流程自测 15 项通过，默认地址 `http://127.0.0.1:8000` 首页返回 200。没有 P0。有 1 条 P1：`WEBLENS_DB_PATH` 设成相对路径时，库文件落在进程工作目录，不在 `app.py` 旁边，和 README 写的解析规则不一致，会另建一套带默认口令的新库。许可证与署名在仓库内部自洽。上游 commit 未联网复核。

## 本地跑通记录

环境：Windows，`python --version` 为 `Python 3.11.9`（exit 0）。README 要求 Python 3.10+。

README Windows 步骤写 `py -m venv`。本机执行 `py -3 --version` 失败，原文：

```
Unable to create process using 'E:\python.exe --version': ???????????
```

exit 1。这是本机启动器指向不存在的 `E:\python.exe`，不是仓库缺陷。后面改用 `python`。

建环境（仓库目录，`.venv` 已被 `.gitignore` 忽略）：

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements-dev.txt
```

两步 pip 都是 exit 0。装上了 `fastapi-0.156.4`、`uvicorn-0.54.0`、`starlette-1.9.0`、`httpx-0.28.1`、`pytest-9.1.1`。

全量测试（`TEMP`/`TMP` 指到 `E:\muse-bridge\work\TASK-102-weblens`）：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_pytest.py
```

```
.....................................                                    [100%]
37 passed, 1 warning in 14.20s
```

警告原文是 StarletteDeprecationWarning：`Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 与 `DECISIONS.md:47` 已记录的测试侧警告相同。

真实流程（脚本自己在 `127.0.0.1:8142` 起 Uvicorn，结束时关掉）：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_live.py
```

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"<临时库令牌已省略>","username":"admin","must_change_password":true}
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
LIVE SELFTEST: ALL PASS (15 checks)
```

exit 0。15 个检查点全部 PASS。

按 README 起服务（库放在工作目录 `server.db`，主机 `127.0.0.1`，端口 `8000`）：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_server.py
```

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

`probe_http.py` 结果：`GET /` 为 200，正文含 `weblens`，响应头有 `cache-control: no-store`、`x-frame-options: DENY`、`x-content-type-options: nosniff`。`GET /health`、`/healthz`、`/api/health` 都是 `404 {"detail":"Not Found"}`。README 没有健康检查路由，首页即存活检查。`/docs`、`/redoc`、`/openapi.json` 为 404。未登录 `GET /api/sites` 为 `401 {"detail":"未登录"}`。`POST /api/login` 为 200，`must_change_password` 为 true，`cache-control` 为 `no-store`。登出后 `GET /api/me` 为 401。

关掉：后台任务已终止。`probe_netstat.py` 只打印 `DONE`，没有 `:8000` 或 `:8142` 监听。

## README 与实际不符处

1. `README.md:49` 写 `WEBLENS_DB_PATH` 的位置「相对 `app.py` 所在目录」，默认 `data/weblens.db`。`app.py:27` 只有在环境变量缺省时才用 `BASE_DIR / "data" / "weblens.db"`；变量一旦设置，原样交给 `sqlite3.connect`，相对路径按进程当前目录解析。实测：当前目录在工作目录、`WEBLENS_DB_PATH=relative-from-cwd.db` 时，`DB_PATH` 打印为 `relative-from-cwd.db`，文件出现在工作目录，`app.py` 旁边没有该文件。

2. `README.md:9` 和 `README.md:41` 写「首次登录」提示改密。`app.py:345` 插入用户时把 `must_change_password` 置 1，`app.py:498` 只在改密成功时清 0。`index.html:436` 每次 `GET /api/me` 看到该标志就显示 `index.html:237` 的提示。未改密之前，第二次登录仍会提示，不是只在第一次。

3. `README.md:63` 到 `README.md:65` 的埋点示例把地址写成 `http://127.0.0.1:8000/tracker.js`，并说实际变化的是 `site_id`。`app.py:544` 到 `app.py:548` 用 `request.base_url` 拼 `src`。实测带请求头 `Host: evil.example` 建站时，返回的 `script_url` 是 `http://evil.example/tracker.js`。

4. `README.md:85` 写请求体「在 64KiB 到 128KiB 之间」返回 400，「超过 128KiB」返回 413。`app.py:35` 的上限是 `64 * 1024`，`app.py:759` 和 `app.py:762` 用的是 `>`，所以正好 65536 字节不会因体积被拒。框架 413 同样是大于 `app.py:38` 的 `128 * 1024` 才触发（已安装的 `starlette/middleware/body_limit.py:111` 也是 `>`）。正好 64KiB、正好 128KiB 都不落在 README 这句的拒绝区间里。

已核对且相符的部分：默认主机 `127.0.0.1`、端口 `8000`（`app.py:914` 到 `app.py:915`），初始账号 `admin` / `admin123`（`app.py:29` 到 `app.py:30`），令牌 24 小时（`app.py:28`），统计按 UTC 切日（`app.py:49` 到 `app.py:50`、`app.py:674`），Top 10（`app.py:695`、`app.py:703`），收集接口 64KiB 以上到 128KiB 的 400 与更大body的 413 分工（测试 `tests/test_app.py:198` 起已覆盖，本机 37 项通过），项目结构里列出的文件都在，包括 `.gitignore`。测试数量 37（其中 6 项为 `tests/test_app.py:471` 的 UA 参数化）和自测 15 项，与 `README.md:107` 一致。

## 许可证与署名核查

`LICENSE:1` 到 `LICENSE:3` 是 MIT，版权行为 `Copyright (c) 2026 weblens contributors`。`README.md:5` 和 `README.md:124` 指向这份 MIT，并让署名去看 `UPSTREAM.md`。

`UPSTREAM.md:5` 到 `UPSTREAM.md:8` 记录上游 Umami 为 MIT，`source_commit` 为 `e92fdab99508a8ed05249f6c5f07e140deab79e1`，版权行 `Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`。`UPSTREAM.md:14` 写明本项目是独立实现，未复制上游源码。`NOTES.md:5` 到 `NOTES.md:7` 与上述三句话一致。

仓库内检索 `umami` / 该版权行，只命中 `UPSTREAM.md` 和 `NOTES.md`，`app.py` 与 `static/index.html` 没有上游源码或上游版权头。这和「独立实现、本仓另发 MIT、上游信息单独写在 UPSTREAM」是同一套说法，内部自洽。MIT 对「复制了上游软件」才要求附带上游版权声明；在未复制源码的前提下，LICENSE 不重复 Umami 版权行并不矛盾。

`source_commit` 是否真是 2026-10-21 的上游 HEAD，以及版权行是否与上游 LICENSE 逐字相同：本任务禁止访问外网，未复核，标为未核实。仓库内没有能证明 UPSTREAM 这两句写错的材料，因此不改 `LICENSE` 和 `UPSTREAM.md`。

## 分级修复清单

下面的 `app.py` 行号是修改前的。P1-1 在原第 27 行换成了 8 行，该行之后的行号顺延 7 行。改后的位置见 `fix-report.md`。

### P0

无。服务能启动，首页 200，pytest 与 live selftest 都通过。

### P1

1. `app.py:27`：`WEBLENS_DB_PATH` 为相对路径时按当前工作目录打开数据库，不按 `app.py` 目录。换目录启动会新建一套库，并在 `app.py:341` 到 `app.py:351` 写入默认口令 `admin` / `admin123`。修法：非绝对路径改接到 `BASE_DIR` 下再连接，空值仍用 `data/weblens.db`。

### P2

1. `README.md:9`、`README.md:41`：把「首次登录才提示」改成「改掉初始密码之前，每次登录都提示」，与 `app.py:345`、`app.py:498`、`index.html:436` 对齐。
2. `README.md:65`：补一句埋点脚本的主机和端口取自当前访问地址（`app.py:544`），示例里的 `127.0.0.1:8000` 只是默认监听。
3. `README.md:85`：改成「大于 64KiB 且不超过 128KiB 返回 400，大于 128KiB 返回 413」，与 `app.py:759` 的 `>` 一致。
4. `app.py:787` 到 `app.py:793`：`url` 不是字符串时 `str()` 后照样入库。实测对象被存成 `/{'a': 1}`。修法：不是字符串就返回 400。
5. `app.py:578` 的站点列表以及同文件里直接 `return` 字典的鉴权接口没有 `Cache-Control: no-store`。登录（`app.py:458`）和首页（`app.py:902`）已经加了。修法：鉴权 JSON 响应同样加 `no-store`。
6. `app.py:916` 的 `uvicorn.run` 未关默认 Server 头。探针看到 `server: uvicorn`。该版本 `uvicorn/config.py:226` 有 `server_header` 参数，默认 True。修法：传入 `server_header=False`。

### 已决不修（不进入上面的待办）

- 不强制改密：`DECISIONS.md:5` 到 `DECISIONS.md:8`。登录页保留默认账号提示：`DECISIONS.md:36` 到 `DECISIONS.md:37`。
- 无条件采信 `X-Forwarded-For`：`DECISIONS.md:45` 到 `DECISIONS.md:46`，`app.py:231` 到 `app.py:238`。改掉会破坏现有测试的访客区分，本轮不改。同函数里的 `X-Real-IP` 是同一类取舍。
- Host 写入埋点地址：`DECISIONS.md:140` 到 `DECISIONS.md:143` 写明维持现状。本轮复现了 `Host: evil.example` 会进入 `script_url`，仍按该决定不改代码。
- 登录限速、访客哈希不含 `site_id`、传递依赖不钉死：`DECISIONS.md:181` 到 `DECISIONS.md:187`。
- TestClient 的 httpx 弃用警告：`DECISIONS.md:47`。本机 pytest 仍打出这一条，不改测试、不改依赖版本。
