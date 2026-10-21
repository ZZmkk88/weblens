# weblens 修复报告

审查清单里 P0 为 0 条，P1 为 0 条。任务只允许修这两级，且最多 5 项。本轮没有修改仓库源码。P2 与已决事项不修。

## 未改条目

### P0

无条目。没有「跑不起来」需要修的文件。

### P1

无条目。没有安全、数据或权限方面要改的文件。

已核对、不升格为 P1 的点：

- 不强制改密：`DECISIONS.md:5`。不改。
- `X-Forwarded-For`：`app.py:199`，`DECISIONS.md:45` 已决暂不改。改了可能影响现有测试对访客的区分，且任务不许改测试。
- 访客哈希算法：`DECISIONS.md:87` 已决不改。
- 密码比较 `app.py:408`：网络上的时差被 PBKDF2 盖住（探针约 0.07 秒），不单独立项去改。

### P2（点名了，但按规则不修）

| 编号 | 位置 | 不修原因 |
|---|---|---|
| P2-1 | `README.md:106` | 文档计数，不是 P0/P1 |
| P2-2 | `README.md:84` | 文档与 413 行为的表述，代码与测试一致，不是 P0/P1 |
| P2-3 | `README.md:51` | 盐的生成时机描述，功能上第一次上报前会写入，不是 P0/P1 |
| P2-4 | `app.py:485` | 已登录才触发的 500，响应正文无堆栈，进程不退出；未登录为 401。未升为 P1 |
| P2-5 | `app.py:738` | 类型放宽，调用方本来就能传任意路径字符串。不是权限或数据损坏级 |
| P2-6 | `static/index.html:29` | 字体名拼写，不是 P0/P1 |
| P2-7 | `README.md:24`、`README.md:34` | 目录说明，在仓库根可跑通 |
| P2-8 | `app.py:269` | 过期会话残留，不是 P0/P1 |

没有「修不动」的 P0/P1。不是做了改动又失败，而是清单里没有该修的项。

## 验证命令与结果

未改代码，因此没有逐项回归。收尾按任务重跑全量测试。

命令（仓库根目录）：

```text
E:\muse-bridge\work\TASK-092-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=line
```

退出码 0。结果行：

```text
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-092-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-092-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.60s
```

没有失败项。那 1 条是依赖里的 `StarletteDeprecationWarning`，`DECISIONS.md:47` 已决定不改测试、也不为它换依赖。审查时另一次全量结果是 `33 passed, 1 warning in 6.39s`，结论相同。

`tests/live_selftest.py` 在审查阶段已通过（`LIVE SELFTEST: ALL PASS (15 checks)`），收尾没有再跑，因为源码没变。服务在检查首页后已关，8000 端口随后 `WinError 10061` 拒绝连接。

## git status

```text
git -C E:\muse-bridge\in\TASK-092-weblens status --porcelain
```

退出码 0。输出为空（下面没有任何文件行）：

```text

```

空输出是预期：本轮没有改仓库文件，不存在「改动丢失」。没有执行 `git checkout` / `git restore` / `git stash` / `git clean` / `git commit` / `git push`。
