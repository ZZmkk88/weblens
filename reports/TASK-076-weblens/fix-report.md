# weblens 修复报告

结论：`review.md` 的分级清单里 P0 为 0 条、P1 为 0 条。没有修改仓库源码。P2 共 12 条，按任务只修 P0/P1，全部未改。

## 问题编号

没有进入修复的 P0/P1 编号。

下面这些在审查时考虑过、仍定为 P2 或不改，原因如下：

- P2-6 `app.py:362`：140KB 登录正文实测 `413`，响应体为 `Content Too Large`，同时没有两个安全响应头。看板页面（`GET /`）实测带有 `X-Frame-Options: DENY`。这条 413 没有敏感页面，不构成数据或权限问题，不改。
- P2-7 `app.py:718`：缺少 `site_id` 的上报实测 `400`，且 `access-control-allow-origin` 为空。埋点用 `sendBeacon` 发送 `text/plain`，不读取响应；成功路径在 `app.py:802` 带跨源头。不改。
- P2-8 `app.py:199`：`X-Forwarded-For` 无条件采信。`DECISIONS.md:45` 已决定维持，默认监听仍是 `127.0.0.1`（`app.py:861`）。不改。
- P2-9 `app.py:246`：访客哈希可被同库盐穷举。`DECISIONS.md:87` 已决定不改算法。不改。
- P2-11：pytest 警告 `StarletteDeprecationWarning` 来自虚拟环境 `fastapi/testclient.py:1`，测试结果仍是 passed。`DECISIONS.md:47` 已决定不改。任务禁止为非冲突去改已有依赖版本。不改。
- P2-12 `static/index.html:203`：登录页写明默认口令。`DECISIONS.md:36` 已决定保留这段提示。不改。
- P2-1 至 P2-5、P2-10：README 计数/口径和一处字体名，不影响启动和测试。不改。

## 全量测试

源码未改。审查结束后重跑：

```
E:\muse-bridge\work\TASK-076-weblens\venv\Scripts\python.exe -m pytest tests/ -q -o cache_dir=E:\muse-bridge\work\TASK-076-weblens\pytest-cache
```

输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-076-weblens\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.00s
```

失败用例：无。那一条是依赖弃用警告，退出码 0。

## git status --porcelain

命令在仓库 `E:\muse-bridge\in\TASK-076-weblens` 执行。下面是收尾时的原样输出。空输出表示工作区没有改动，与「P0/P1 为 0、未改源码」一致。

```
git status --porcelain
```

```
```
