# weblens 决定记录（DECISIONS.md）

> 本仓的用户决定与复核不采纳项。审查再报已决事项时，直接引用本文件关闭，不反复复议。

## D-1 首次改密只提示、不强制（口径第 1 条）

默认账号 admin / admin123 首次登录只给醒目提示、可跳过；不拦截任何业务功能。
Grok 若再报"强制改密"，按口径第 1 条直接关闭，不以任何实现形式合回。

## D-2 改密成功后吊销其他会话（口径第 2 条）

改密成功时在同一事务里删除该用户除本次会话外的全部登录会话，本次会话保留；
取不到当前令牌时不删，避免把自己踢下线。配回归测试
（`test_change_password_revokes_other_sessions`：旧会话 401、本次会话 200）。

## D-3 默认只监听本机（口径第 3 条）

`WEBLENS_HOST` 环境变量，默认 `127.0.0.1`；对外放开走该变量显式设置，
放开前先改掉默认密码（README 环境变量表已注记）。
TASK-014 的硬编码 `127.0.0.1` 版本已按本条丢弃，改用环境变量口径。

## D-4 接口文档页默认关闭（口径第 6 条）

`/docs`、`/redoc`、`/openapi.json` 默认关闭（`docs_url=None` 等）。

## D-5 TASK-014 / TASK-020 综合合并决定（2026-10-21）

- 采纳 020：`WEBLENS_HOST` 环境变量口径、CORS 收窄（只给 `/api/collect`
  与 `/tracker.js` 加跨源头＋OPTIONS 预检）、请求体 64KB 上限（超了 400）。
- 采纳 014：UA 分类只读请求头（正文 `user_agent`/`userAgent` 不再采信，
  与 README"User-Agent 从请求头读取"对齐）、`site_stats` 顶层 `active_pages`
 （`COUNT(DISTINCT page_path)`）＋前端优先显示。
- referrer 归一化两轮都有：以 020 的规则为准（显式 `referrer_domain` 先
  `normalize_host`，再做域名正则＋253 上限校验，不合规则记空串）。
- 014 的 P1-1（host 硬编码）未采纳，已被 D-3 的环境变量口径取代。
- 014 的 P2（登录框预填 `admin`/`admin123`）已修：去掉两个输入框的 `value`，
  页面下方的"默认账号 admin / admin123"文字提示保留。
- 020 的 P2-5（正文 UA 可覆盖请求头）已随"UA 只读请求头"一并解决。
- 两轮的 P1-5/P1-3（改密吊销其他会话）在 main 上正经实现，
  测试的模块级共享 `auth` fixture 改为每用例独立登录（用例只增不减、
  断言不弱化，属口径第 17 条允许的"按新规格正当改写"）。

## D-6 暂不处理项（两轮 Grok 亦未改，记录备查）

- `X-Forwarded-For` 无条件采信：监听已收敛到本机，风险限于本机进程；改动会
  破坏现有测试的访客区分，暂不动。
- Starlette TestClient 的 httpx 弃用警告：仅测试侧警告，不影响运行，暂不动。

## D-7 TASK-054-weblens-p2 收口决定（2026-10-21）

该分支基座为旧 main（4af0b00e），未整支合并，只手工搬运真实新增量。

- 采纳 P2-6：README 统计看板条目补"这里的「今天」以及按天切分使用 UTC"，
  与 NOTES.md:25 及 `utcnow().date()` 切日逻辑对齐。
- 采纳 P2-7：`get_uv_salt` 并发首次写入撞主键时捕获 `sqlite3.IntegrityError`，
  回滚后重读对方已提交的盐（读不到则原错抛出）。原 D-6 中"UV 盐撞主键暂不动"
  一条就此作废。
- 不重复搬运（main 已有）：P2-1（active_pages，014 已合）、P2-2（关闭 /docs，
  D-4）、P2-3（登录框去预填，014 已合）、P2-5（UA 只读请求头，014 已合）。
- P2-4（X-Forwarded-For）、P2-8（httpx 弃用警告）Grok 本轮亦未改，维持 D-6。
- 审查结论：分支未动测试文件；未碰登录/改密逻辑，无"强制改密"回潮（口径#1）；
  未碰 host（分支基座仍是旧的 0.0.0.0，main 已是 WEBLENS_HOST 口径#3，无需搬运）；
  weblens 无服务端对外抓取，SSRF（口径#9）不适用。

## D-8 TASK-058-weblens 收口决定（2026-10-21）

该分支基座落后 main 1 个 commit（91943cc vs 7a34b729，区域不重叠），未整支合并，
只手工搬运。分支 diff 与报告声称一致：仅 app.py 四处 URL 解析函数加
try/except，无范围外改动；测试文件未动。

- 采纳 P1-1（真增量）：畸形 IPv6（如 `http://[`）此前让公开上报接口抛未捕获的
  `ValueError`（500）并丢掉这次访问。修法：`normalize_domain_input`→400
  "域名格式不正确"；`domain_from_value`（来源）→记空串继续入库（与现有 referrer
  归一化"不合规则记空串"对齐）；`parse_page_path`→400；`page_hostname`→回退
  站点域名。合法地址（含 `http://[::1]/x`）不受影响。与口径#10（超长输入明确
  拒绝）精神一致。Grok 未带测试，已按口径#17 补回归测试
  `test_collect_malformed_ipv6_does_not_500`（坏来源 201 且入库空串、坏页面地址
  400、坏建站域名 400，另断言合法 IPv6 来源不受影响）。
- 采纳 P2-5：加安全响应头中间件（`X-Frame-Options: DENY`、
  `X-Content-Type-Options: nosniff`），参考 dailymemo TASK-040 做法；配断言测试
  `test_security_headers_present`。
- 采纳 P2-1/P2-4/P2-7 文档项：README 测试数 25→30（注 6 项 UA 参数化）、
  项目结构清单补 DECISIONS.md/LICENSE/两份 requirements、新建站点弹窗注明去 www.。
- 采纳 P2-3：`init_db` 改为库里已有任意用户时不再追加初始账号（单用户设计；
  换 `WL_INITIAL_USERNAME` 不会再悄悄产生第二个登录账号）。
- 不重复：P2-2（README 补 UTC）已在 7a34b729 落地。
- 维持 D-6：P2-6（访客哈希穷举属设计取舍，不改算法）。
- 审查结论：无"强制改密"回潮（口径#1，分支报告已决事项节亦逐条引用关闭）；
  改密吊销仍是"删其他留本次"（口径#2）；host 仍是 WEBLENS_HOST 口径（口径#3）；
  SSRF 不适用（口径#9）。

## D-9 TASK-061-weblens 收口决定（2026-10-21）

该分支基座落后 main 1 个 commit（ed44961 vs 9bed740，main 侧只加了文档），
未整支合并，只手工搬运；搬运版与分支版逐行比对零功能差异（仅注释措辞不同）。

- 采纳 P1-1：会话令牌改 SHA-256 哈希入库。新增 `session_key()`（令牌熵足够，
  不加盐），登录写入、鉴权校验、登出删除、改密吊销四处统一走哈希；接口返回
  给客户端的仍是原始令牌。**副作用：此前明文入库的旧会话全部失效，需重新
  登录**（dailymemo/quicklink/startdeck 之前同类改造亦如此）。配回归测试
  `test_session_token_stored_hashed_not_plaintext`（入库非明文＋原始令牌可用＋
  登出后 401）。
- 采纳 P1-2：未认证接口请求体硬上限。`RequestBodyLimitMiddleware`
 （`MAX_REQUEST_BODY = 128 * 1024`）挂在安全响应头中间件之外；`/api/collect`
  原有的 64KB→400 逻辑保留（70KB 上报仍 400"请求体过大"，140KB 登录正文
  413）。已在钉死依赖的干净环境验证 `starlette.middleware.body_limit` 可用
  （starlette 1.9.0）。配回归测试 `test_request_body_hard_limit_413`。
- P2 九条不动（Grok 自己标不修；P2-4/P2-7 按 D-6 关闭）。
- 审查结论：分支未动测试文件；无口径冲突。
