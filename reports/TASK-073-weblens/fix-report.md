# weblens 修复报告

## 结论

`review.md` 分级清单里 P0 为 0 条，P1 为 0 条。任务只允许修 P0/P1，且最多 5 项。本轮没有修改仓库源码。

## 逐条

没有可修条目。P2 共 7 条（见 `review.md`），按范围不改，不是修失败。

已决事项不复议、不改代码：

- D-1 不强制改密（`DECISIONS.md:5-8`）
- D-5 保留登录页默认账号提示（`DECISIONS.md:36-37`，`static/index.html:203`）
- D-6 `X-Forwarded-For`（`app.py:199-206`，`DECISIONS.md:45-46`）。若修改，`tests/test_app.py` 里靠该头区分访客的 UV 断言会失败，且禁止改测试
- D-6 httpx/TestClient 弃用警告（`DECISIONS.md:47`）。不改 `requirements*.txt` 里的版本

## 全量测试（清单确认后重跑）

没有改仓库文件。下面是确认清单之后重跑的结果，没有失败项。

命令：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_pytest.py
```

输出（exit 0）：

```
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\in\TASK-073-weblens\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.86s
```

命令：

```
.venv\Scripts\python.exe E:\muse-bridge\work\TASK-073-weblens\run_live.py
```

输出（exit 0；令牌截断）：

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"GvNk…（截断）","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

结果行：`33 passed, 1 warning in 5.86s`；`LIVE SELFTEST: ALL PASS (15 checks)`。没有失败用例。警告仍是依赖里的 StarletteDeprecationWarning，按 D-6 不改。

## git status --porcelain

在仓库根目录 `E:\muse-bridge\in\TASK-073-weblens` 执行：

```
git status --porcelain
```

输出为空（exit 0，无文件行）。

这是预期结果：本轮没有修改仓库源码，所以工作区相对 HEAD 没有差异。`review.md`、`run.md`、`fix-report.md` 写在 `E:\muse-bridge\out\TASK-073-weblens\`，不在这个 git 仓库里。`.venv/` 被 `.gitignore` 忽略。没有需要改回来的丢失改动。
