# weblens 修复记录

P0 无。P1 只修了 1 条。P2 和已决事项没有改。

## P1-1 相对数据库路径按 app.py 目录解析

- 问题编号：P1-1
- 文件:行号：`app.py:27` 至 `app.py:34`（替换原来的单行 `DB_PATH = os.environ.get(...)`）
- 改法：环境变量去掉空白后若为空，仍用 `BASE_DIR / "data" / "weblens.db"`。`os.path.isabs` 为真则原样使用。否则接到 `BASE_DIR` 下。相对路径不再跟着进程当前目录走，避免换目录启动时另建一套带默认口令 `admin` / `admin123` 的新库。

### 验证命令与结果

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\check_db_path.py`

当前目录在工作目录，不在仓库里。

```
--- relative
exit 0
stdout E:\muse-bridge\in\TASK-102-weblens\..\..\work\TASK-102-weblens\only-resolved.db
resolved E:\muse-bridge\work\TASK-102-weblens\only-resolved.db
anchored_to_app_dir True
file_exists True
resolved_under_work True
user_row ('admin', 1)
--- absolute
exit 0
stdout E:\muse-bridge\work\TASK-102-weblens\abs-check.db
absolute_unchanged True
absolute_exists True
```

相对路径被接到 `app.py` 所在目录上，解析后的文件在工作目录，不在仓库里。新库里的用户是 `admin`，`must_change_password` 为 1，说明这就是会带默认口令的那套库，现在落在按 `app.py` 解析的位置。绝对路径保持原字符串。

回归（修完后的全量 pytest，只有这一处源码改动）：

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_pytest.py`

```
.....................................                                    [100%]
37 passed, 1 warning in 7.48s
```

exit 0。警告仍是 StarletteDeprecationWarning（TestClient / httpx），与修改前相同，不是这次改动引入的。没有失败项。

真实服务自测：

命令：`.venv\Scripts\python.exe E:\muse-bridge\work\TASK-102-weblens\run_live.py`

```
PASS 首页能打开且是 weblens 页面
PASS 埋点脚本可取回且指向 collect 接口
PASS 登录成功 | must_change_password=true（临时令牌已省略）
PASS 今日 PV/UV 正确：PV 4、UV 2
LIVE SELFTEST: ALL PASS (15 checks)
```

exit 0。15 个检查点全部通过。该脚本给子进程的 `WEBLENS_DB_PATH` 是绝对路径，走的是绝对路径分支。

## 全量测试（改动后）

同上两条，修完后立即重跑，中间没有再改源码。

- pytest：`37 passed, 1 warning in 7.48s`（exit 0）
- live_selftest：`LIVE SELFTEST: ALL PASS (15 checks)`（exit 0）

没有失败项。

## 未改的项

- P0：无
- P2 六条：只记在 review.md，没有改 README，也没有改鉴权缓存头、Server 头、非字符串 url
- 已决事项（强制改密、X-Forwarded-For、Host 拼进埋点、登录限速）：没有改

## git status --porcelain

命令：`git status --porcelain`

```
 M app.py
```

工作区仍保留 `app.py` 的修改。没有其它已跟踪文件被改动。
