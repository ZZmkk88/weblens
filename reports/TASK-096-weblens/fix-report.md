# weblens 修复报告

结论：`review.md` 的 P0 为空，P1 没有要改代码的开放项。按「只修 P0/P1、最多 5 项，清单以外不动」未修改仓库任何文件。没有修不动的 P0/P1。

## 条目

问题编号：无（P0 无；P1 无开放项）

文件：无

改法：不改源码，也不改 README。P2 共 11 条只记在 `review.md`，本次不修。已决事项（默认口令只提示、`X-Forwarded-For` 继续采信、访客哈希算法、测试里的 httpx 弃用警告）按 `DECISIONS.md` 关闭，不重开。

验证：下面是审查结束后、未改文件的情况下重跑的全量测试。没有失败项。

## 全量测试（审查结束后重跑）

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe -m pytest tests/ -q --tb=line -o cache_dir=E:\muse-bridge\work\TASK-096-weblens\pytest_cache
```

输出：

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\work\TASK-096-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-096-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 6.38s
PYTEST_EXIT 0
```

命令：

```
E:\muse-bridge\work\TASK-096-weblens\.venv\Scripts\python.exe E:\muse-bridge\in\TASK-096-weblens\tests\live_selftest.py
```

输出：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"vH2rvUhXIxwSzJxISrwUXqJWLRuSEfV9PkVxlptke_Y","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | {"id":1,"site_id":"c73ec28e-6590-45a7-be21-f10c03229f2d","name":"演示站","domain":"demo.example.com","created_at":"2026-10-21T17:30:06+00:00","updated_at":"2026-10
PASS 埋点片段含专属 site_id | <script defer src="http://127.0.0.1:8142/tracker.js" data-weblens-id="c73ec28e-6590-45a7-be21-f10c03229f2d"></script>
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | {"ok":true,"site_id":"c73ec28e-6590-45a7-be21-f10c03229f2d","pageview_id":4,"page_path":"/pricing"}
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首 | [{'path': '/pricing', 'count': 3}, {'path': '/docs', 'count': 1}]
PASS 来源排行正确：google.com 3 次居首 | [{'domain': 'google.com', 'count': 3}, {'domain': 'bing.com', 'count': 1}]
PASS 近 7 天趋势长度与合计正确 | [{'date': '2026-10-15', 'pv': 0, 'uv': 0}, {'date': '2026-10-16', 'pv': 0, 'uv': 0}, {'date': '2026-10-17', 'pv': 0, 'uv': 0}, {'date': '2026-10-18', 'pv': 0, 'uv': 0}, {'date': '2026-10-19', 'pv': 0, 'uv': 0}, {'date': '2026-10-20', 'pv': 0, 'uv': 0}, {'date': '2026-10-21', 'pv': 4, 'uv': 2}]
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
LIVE_EXIT 0
```

失败原因：无。警告是 Starlette 对 httpx 的弃用提示，`DECISIONS.md` D-6 已决定不改，也不计入失败。

## git status

命令：

```
git status --porcelain
```

输出（退出码 0，空）：

```
```

空输出是因为本次没有改仓库文件，不是改动丢失。没有执行 `git checkout`、`git restore`、`git stash`、`git clean`，也没有手动还原。审查开始时 porcelain 同样为空。
