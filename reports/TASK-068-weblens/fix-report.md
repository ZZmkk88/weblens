# 修复报告

清单里的 P0、P1 都是空的，仓库源码没有改。

## 问题编号

无。`review.md` 分级清单的 P0 为「无」，P1 为「无待改项」。P2 共 10 条，按任务只修 P0/P1，这 10 条不动。

已核对后明确不改的两项：

- `app.py:199-206` 的 `X-Forwarded-For`。原因：`DECISIONS.md:44-46` 已关闭；现有测试用这个头区分访客，改了会动到不能改的测试断言。
- TestClient / httpx 弃用警告。原因：`DECISIONS.md:46` 已关闭；警告不导致失败，修它要么改测试要么改依赖版本，两条都不允许。

## 文件与改法

没有改仓库里的文件。`review.md`、`run.md`、`fix-report.md` 写在 `E:\muse-bridge\out\TASK-068-weblens\`，不在待审仓库内。

## 验证

未做源码改动，所以没有「修一条、跑一条」的中间命令。审查结束后按全量重跑了一次。

命令（cwd = `E:\muse-bridge\in\TASK-068-weblens`）：

```
python -m pytest tests/ -q --tb=short; python tests/live_selftest.py
```

真实结果（exit 0）：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\env\TASK-068-weblens\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\env\TASK-068-weblens\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 3.41s
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | {"token":"<一次性令牌已打码>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 建站成功并规范化域名 | domain=demo.example.com
PASS 埋点片段含专属 site_id
PASS 访客 A 三次上报全部成功
PASS 访客 B 上报成功 | page_path=/pricing
PASS 今日 PV/UV 正确：PV 4、UV 2 | {'pv': 4, 'uv': 2}
PASS 热门页面正确：/pricing 3 次居首
PASS 来源排行正确：google.com 3 次居首
PASS 近 7 天趋势长度与合计正确 | 7 天，末日 2026-10-21 pv 4 uv 2
PASS 站点改名生效
PASS 删除站点成功
PASS 删除后统计接口返回 404
LIVE SELFTEST: ALL PASS (15 checks)
```

没有失败项。那条警告与审查时相同，按 D-6 不记为本次回归。

## git status

下面是收尾命令和原文。无输出，因为没有改仓库文件，不是改动丢失。

```
git -C E:\muse-bridge\in\TASK-068-weblens status --porcelain
```

stdout 为空，exit 0。
