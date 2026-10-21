# weblens 修复记录

只修了 review.md 清单里的 P1-1。没有 P0。P2 与已决事项未改。

## P1-1 深度嵌套 JSON 让 `/api/collect` 返回 500

- 问题编号：P1-1
- 文件：`app.py:717-720`（原 `app.py:717-719`）
- 改法：`json.loads` 的 `except` 增加 `RecursionError`，与原来的解码错误一样返回 400，详情仍是「请求体不是合法 JSON」。

验证命令（真实服务，临时库 `E:\muse-bridge\work\TASK-065-weblens\probe.db`，探测后进程已退出）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-065-weblens\probe_nested.py
```

输出：

```
/api/login 8000 400 {"detail":"There was an error parsing the body"}
/api/login 12001 400 {"detail":"There was an error parsing the body"}
/api/collect 8000 400 {"detail":"请求体不是合法 JSON"}
/api/change-password 8000 400 {"detail":"There was an error parsing the body"}
EXIT 1
```

修复前同脚本的 `/api/collect` 是 `500 Internal Server Error`。现在是 400。退出码 1 是 Windows 上 `terminate` 结束子进程的结果，随后没有再占用端口。

回归（exit 0，4.80s）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pytest tests -q -o cache_dir=E:\muse-bridge\work\TASK-065-weblens\pytest_cache
```

```
30 passed, 1 warning in 4.80s
```

警告仍是 D-6 记录过的 `StarletteDeprecationWarning`（httpx / TestClient），不是本次改动引入的失败。

## 全量重跑

修复完成后重跑 README 里的两套检查。没有失败项。

命令（exit 0，4.68s）：

```
E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe -m pytest tests -q -o cache_dir=E:\muse-bridge\work\TASK-065-weblens\pytest_cache
```

```
30 passed, 1 warning in 4.68s
```

警告原文仍是 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 未计为失败。

命令（exit 0）：

```
cmd /c "set TMP=E:\muse-bridge\work\TASK-065-weblens&& set TEMP=E:\muse-bridge\work\TASK-065-weblens&& E:\muse-bridge\work\TASK-065-weblens\.venv\Scripts\python.exe tests\live_selftest.py"
```

```
LIVE SELFTEST: ALL PASS (15 checks)
```

15 条检查全部 PASS（首页、埋点、登录、建站、PV 4 / UV 2、热门页、来源、7 日趋势、改名、删除、删除后 404）。

## git status --porcelain

命令：

```
git -C E:\muse-bridge\in\TASK-065-weblens status --porcelain
```

输出：

```
 M app.py
```

工作区只剩 `app.py` 这一处未提交改动，就是 P1-1。没有改测试、依赖版本、LICENSE 或 UPSTREAM。
