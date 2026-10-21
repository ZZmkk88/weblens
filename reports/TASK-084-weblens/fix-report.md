# weblens 修复记录

结论：审查清单里没有 P0，也没有 P1。未修改仓库源码。P2 共 13 条，按任务范围本轮不改。

全量测试在此结论之后重跑：`33 passed, 1 warning in 5.59s`。没有失败项。

## P0

无。不改文件。依据：`pytest tests/ -q` 为 33 passed；`tests/live_selftest.py` 为 `LIVE SELFTEST: ALL PASS (15 checks)`；`python app.py` 日志为 `Uvicorn running on http://127.0.0.1:8000`，`GET /` 为 200。

## P1

无。不改文件。会话哈希、128KB 正文上限、畸形 IPv6、深度 JSON、改密吊销、关闭文档页都在上述 33 项中通过。探针里伪造用户名返回 401。`X-Forwarded-For`、413 缺响应头、Host 写入脚本地址不升为 P1，理由见 `review.md` 分级清单，本轮不改。

## P2（未改，逐条说明）

1. 问题编号 P2-1。文件 `README.md:106`。改法：未改。原因：文档计数错误，不是跑不起来，也不是安全/数据/权限问题。
2. 问题编号 P2-2。文件 `README.md:84`（对应 `app.py:38`、`app.py:362`）。改法：未改。原因：超过 128KB 返回 413 是已实现行为，只是 README 少写了一句。70KB 仍是 400，现有测试通过。
3. 问题编号 P2-3。文件 `app.py:817`。改法：未改。原因：多送的 `title` 不入库，不阻断、不扩大权限。
4. 问题编号 P2-4。文件 `app.py:730`、`app.py:740`、`app.py:747`。改法：未改。原因：多接受的字段别名与 README 示例不冲突，删掉可能弄坏已有客户端。
5. 问题编号 P2-5。文件 `app.py:71`。改法：未改。原因：去掉 `www.` 是既有规范化，README 未写而已。
6. 问题编号 P2-6。文件 `requirements.txt:1`。改法：未改。原因：任务禁止改已有依赖的版本号，除非是依赖冲突。本次安装没有冲突。
7. 问题编号 P2-7。文件 `app.py:362`。改法：未改。原因：413 正文是固定的 `Content Too Large`，没有会话或业务数据。实测 `xfo=None`，不构成可利用的数据或权限问题。
8. 问题编号 P2-8。文件 `app.py:213`。改法：未改。原因：连接未显式关闭，但本次全量测试和实服务都没有因此失败。
9. 问题编号 P2-9。文件 `app.py:495`。改法：未改。原因：脚本地址跟随当前访问 Host。带引号的 Host 没有写进片段。改成固定基址会改变局域网下的正确地址。
10. 问题编号 P2-10。文件 `static/index.html:340`。改法：未改。原因：输入框长度是界面限制，接口本身仍接受更长 URL。
11. 问题编号 P2-11。文件 `static/index.html:29`。改法：未改。原因：字体名拼写不影响功能。
12. 问题编号 P2-12。文件 `app.py:401`。改法：未改。原因：默认只监听 127.0.0.1；加登录限速会碰到测试里的连续登录。
13. 问题编号 P2-13。文件 `tests/test_app.py:17`（警告实际来自站点包）。改法：未改。原因：任务禁止改测试，也禁止为这种警告去改依赖版本。`DECISIONS.md:47` 已决暂不动。

未改 `LICENSE`、`UPSTREAM.md`。仓内陈述互相一致，上游 commit 与版权原文未联网核实，没有确凿错误可改。

## 全量测试

审查结束、确认不改源码之后执行。工作目录 `E:\muse-bridge\in\TASK-084-weblens`。`TEMP`/`TMP` 为 `E:\muse-bridge\work\TASK-084-weblens\tmp`。

命令：

```
.venv\Scripts\python.exe -m pytest tests/ -q
```

输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-084-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.59s
```

失败项：无。那 1 条是依赖库的弃用警告，不是失败。

## git status --porcelain

命令（仓库根目录）：

```
git status --porcelain
```

输出：空（exit 0）。

空输出是因为本轮没有修改仓库源码。`.venv/`、`data/`、`__pycache__/` 在 `.gitignore` 里。审查报告写在 `E:\muse-bridge\out\TASK-084-weblens\`，不在仓库内。没有需要恢复的改动。
