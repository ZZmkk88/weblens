# weblens 修复记录

只改了 `review.md` 清单里的 P1-1。P0 没有。P2 未改。

## P0

无。未改文件。

## P1-1 登录用耗时暴露用户名是否存在

- 问题编号：P1-1
- 文件：`app.py`（修改前判定在 `:408`、`:438`；修改后在下面这些行）
- 改法：新增 `password_matches`（`app.py:69-73`），用 PBKDF2 之后做 `hmac.compare_digest`（`app.py:9` 引入 `hmac`）。用户不存在时用固定盐 `_UNKNOWN_USER_SALT` / `_UNKNOWN_USER_HASH`（`app.py:64-66`）先算一次再返回 401（`app.py:421-423`）。已存在用户的登录比较在 `app.py:424-425`。改密时的旧密码比较在 `app.py:454-455`。错误正文不变，仍是「用户名或密码不正确」/「旧密码不正确」。

验证 1，登录与改密相关用例：

```
cmd /c 'set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& cd /d E:\muse-bridge\in\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pytest tests/test_app.py -q -p no:cacheprovider -k "login or password"'
```

```
....                                                                     [100%]
4 passed, 29 deselected, 1 warning in 2.38s
```

退出码 0。警告仍是修复前就有的 `StarletteDeprecationWarning`（`fastapi/testclient.py:1`），不是这次改动引入的。

验证 2，修复后的登录耗时（`E:\muse-bridge\work\TASK-086-weblens\time_login.py`，TestClient，各 3 次，密码都是错误的）：

```
cmd /c "set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe E:\muse-bridge\work\TASK-086-weblens\time_login.py"
```

```
MISSING 401/0.080 401/0.076 401/0.076
WRONGPW 401/0.075 401/0.070 401/0.071
```

修复前同一口径：不存在用户 0.005 秒，错误密码 0.069 秒。修复后两边都在 0.070–0.080 秒，状态码仍是 401。

## P2

11 条都不改。原因：清单里定为 P2；其中转发 IP 受 `DECISIONS.md` D-6 约束，改了会让现有 UV 断言失败，且不许改测试；依赖版本不许在没有冲突时改动。详见 `review.md` 分级修复清单 P2。

## 全量测试（修改后）

```
cmd /c "set PYTHONDONTWRITEBYTECODE=1&& set TEMP=E:\muse-bridge\work\TASK-086-weblens&& set TMP=E:\muse-bridge\work\TASK-086-weblens&& cd /d E:\muse-bridge\in\TASK-086-weblens&& E:\muse-bridge\env\TASK-086-weblens\Scripts\python.exe -m pytest tests/ -q -p no:cacheprovider"
```

```
.................................                                        [100%]
============================== warnings summary ===============================
..\..\env\TASK-086-weblens\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\env\TASK-086-weblens\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
33 passed, 1 warning in 5.61s
```

退出码 0。没有失败项。警告与修改前相同，按 D-6 不记为本次缺陷。

同一环境又跑了 `python tests/live_selftest.py`，末行：

```
LIVE SELFTEST: ALL PASS (15 checks)
```

退出码 0。登录、建站、上报、统计、改名、删除均 PASS。

## git status --porcelain

命令：

```
git -C E:\muse-bridge\in\TASK-086-weblens status --porcelain
```

输出：

```
 M app.py
```
