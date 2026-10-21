# weblens 修复记录

结论：review.md 里 P0 为空、P1 为空。按任务只修这两级，且最多 5 项。本轮没有修改仓库源码，也没有改测试、依赖版本、LICENSE、UPSTREAM。

## 问题编号与处理

### P0

无条目。没有「跑不起来」或阻断项。

证据（审查阶段，详见 run.md）：

- `pip install -r requirements.txt` 与 `pip install -r requirements-dev.txt` 退出码 0
- pytest：`33 passed, 1 warning in 5.83s`
- live_selftest：`LIVE SELFTEST: ALL PASS (15 checks)`
- `Uvicorn running on http://127.0.0.1:8000`，`GET /` 200，`POST /api/login` 200

本机 `py -3 -m venv` 失败是启动器指向无效的 `E:\python.exe`，改用 Python 3.11.9 后虚拟环境创建成功。不记为仓库缺陷，也不改 README 的 Windows 说明。

### P1

无条目。没有在本轮改动的安全、数据或权限缺陷。

已核对、但不升为待修 P1 的项：

| 编号 | 位置 | 为何不改 |
|---|---|---|
| 已决 D-1 | DECISIONS.md:5-8，app.py:313，README.md:9 | 首次登录只提示改密。强制改密会违背决定记录。 |
| 已决 D-6 | app.py:199-206，DECISIONS.md:45-46 | `X-Forwarded-For` 无条件采信。tests/test_app.py:75 与 tests/live_selftest.py:41 用这个头区分访客。改了会让现有测试失败，本任务不许改测试。 |
| 已决 D-5 | static/index.html:203，DECISIONS.md:37 | 登录页保留默认账号提示。这是已决事项，且只在改了初始账号环境变量时才会误导，列为 P2。 |
| 已决 D-8 | app.py:250-252，DECISIONS.md:87 | 访客哈希算法维持现状。 |
| Host 进埋点脚本 | app.py:495-499 | 已实测 `Host: evil.example` 会写成 `http://evil.example/tracker.js`。拿片段需要登录；默认只监听 127.0.0.1（app.py:861）；引号 Host 没有写进片段。写死 127.0.0.1 会破坏局域网脚本地址。列为 P2，本轮不改。 |

### P2

清单里的 P2 按任务不修。没有改 README.md、static/index.html、app.py。

## 收尾全量测试

未改源码之后重跑。命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-080-weblens\run_pytest.py
```

脚本内部命令：

```
E:\muse-bridge\in\TASK-080-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short -p no:cacheprovider
```

工作目录：`E:\muse-bridge\in\TASK-080-weblens`。退出码 0。输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-080-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.29s
```

没有失败项。那 1 条是依赖里的弃用警告，DECISIONS.md:47 已决定不动。

服务端口在测试前已确认释放：`PORT_8000_FREE`、`PORT_8142_FREE`。

## git status --porcelain

命令：

```
git -C E:\muse-bridge\in\TASK-080-weblens status --porcelain
```

输出原样（标准输出为空，退出码 0）：

```
```

空输出是预期结果：本轮没有修改仓库里的源码或文档。审查产物在 `E:\muse-bridge\out\TASK-080-weblens\`，不在仓库内。`.venv/` 被仓库 `.gitignore` 第 1 行忽略，不会出现在 porcelain 里。这里没有用 `git checkout`、`git restore`、`git stash` 或 `git clean` 丢改动。
