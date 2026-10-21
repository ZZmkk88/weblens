# weblens 修复记录

结论：`review.md` 分级清单里 P0、P1 都是空的，所以没有改仓库源码。P2 五条按任务边界不修。下面没有「改了哪个文件」的条目。

## 未改条目

| 编号 | 位置 | 为什么不动 |
|---|---|---|
| P0 | 无 | 依赖安装、pytest、live 自测、8000 首页都已跑通 |
| P1 | 无 | 见 review.md「已关闭」：改密不强制、X-Forwarded-For、访客哈希、TestClient 警告。X-Forwarded-For 一改就会让现有 UV 测试失败，而本任务不许改测试 |
| P2-1 | README.md:106 | 只是文档数字 30→33，不阻断、不是安全或数据问题 |
| P2-2 | README.md:84 | 文档未写 413；代码行为已有测试覆盖 |
| P2-3 | README.md:51 | 文档把盐的写入时机写早了；功能本身正确 |
| P2-4 | static/index.html:29 | 字体名笔误，有后续字体兜底 |
| P2-5 | app.py:352 与 app.py:362 | 413 缺安全头，正文是固定的 `Content Too Large`，构不成点击劫持或数据泄露 |

没有修不动的 P0/P1。没有改 LICENSE、UPSTREAM、测试、依赖版本号。

## 全量测试（审查结束后重跑）

命令：`.venv\Scripts\python.exe -m pytest tests/ -q --tb=line`

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-099-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.65s
```

exit: 0。没有失败项。那条警告是依赖库里的 StarletteDeprecationWarning，审查阶段已经出现，不是这次改动引入的（没有改动）。

审查阶段已跑过的 `python tests/live_selftest.py` 结果仍是 `LIVE SELFTEST: ALL PASS (15 checks)`，exit 0。源码未变，没有再跑第二遍。

## git status

命令：`git status --porcelain`

```
```

stdout 为空，exit 0。这是预期结果：P0/P1 为空，没有改仓库里的文件。审查报告在 `E:\muse-bridge\out\TASK-099-weblens\`，不在仓库工作区。没有执行 `git checkout`、`git restore`、`git stash`、`git clean`、`git commit`、`git push`。
