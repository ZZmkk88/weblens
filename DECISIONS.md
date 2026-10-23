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

## D-10 TASK-065-weblens 收口决定（2026-10-21）

该分支基座落后 main 3 个提交（00c1a38 vs 1acc81b：TASK-061 fix、TASK-061
回归测试、D-9 文档），未整支合并，只手工搬运与报告声称一致的唯一改动
（app.py +2/-1；测试文件未动）。回退检查：分支仍含 session_key() 令牌哈希、
MAX_REQUEST_BODY 128KiB 上限、TASK-058 的 IPv6 兜底，无回退无重复。

- 采纳 P1-1：`/api/collect` 的 `json.loads` except 增加 `RecursionError`，
  深度嵌套 JSON 由未捕获的 500 改为 400「请求体不是合法 JSON」。Grok 在真实
  服务上验证过修复前 500→修复后 400。配回归测试
  `test_collect_deeply_nested_json_returns_400`（20000 层嵌套，本环境
  Python 3.12 下稳定触发 RecursionError，正文约 40KB，走得到 json.loads）。
- P2 九条全部不改（其中 3 条已决事项按 DECISIONS 维持）。
- 审查结论：无"强制改密"回潮（口径#1，报告主动引用 D-1/D-2/D-3/D-6/D-8）；
  /docs 三入口 404 关闭；WEBLENS_HOST 口径一致；改密吊销留本次一致；
  P2-7（X-Forwarded-For）/P2-8（访客哈希）维持 D-6/D-8 不改。

## D-11 TASK-071/073/068 三合一收口决定（2026-10-22）

三分支测试文件均未动、无"强制改密"回潮，均在 main（91e08ef）上手工处理；
tests/ 只新增、未改动已有断言（红线）。

- **TASK-071（review+fix，基座即 main head，直接搬运）**：采纳 P1-1——新增
  `is_utf8_text()` 守卫，5 处（hash_password/登录用户名/validate_site_name/
  parse_page_path/domain_from_value）与 review 处方逐字对应；孤立代理字符
  不再抛未捕获的 UnicodeEncodeError（500）。配回归测试
  `test_surrogate_unicode_400_not_500`（登录用户名/密码 400、站点名 400、
  上报 URL 400、referrer 记空串照常 201；已验证守卫失效时该测试失败）。
  P2 采纳 P2-1（README 测试数→36）、P2-2（400/413 分界）、P2-3（库路径相对
  app.py）、P2-4（域名规范化说明）；P2-5 不做（禁改测试文件）；P2-6（埋点
  脚本地址取请求 Host）评估后维持现状——Host 拼地址是零配置反代场景需要的，
  片段不落库且默认只监听本机，风险低优暂不改；P2-8 按事实错误关闭（"仓库根
  没有 .gitignore"不实，main 早有）；P2-7/P2-9/P2-10 按 D-6/D-8 关闭。
- **TASK-073（纯 review，基座即 main）**：采纳 P2-1~P2-4（测试数、400/413、
  UV 盐"首次上报计算 UV 时写入 settings"、结构清单补 .gitignore）与 P2-7
  （字体名 ui-sans-system→ui-sans-serif，与 068 同项只做一次）；**P2-5 按
  口径#8 升级采纳**：登录与改密验旧密码两处 `!=` 比对口令哈希改为
  `secrets.compare_digest`（令牌校验走 DB 参数化查询，不算字面比对，无需改；
  断言结果不变，属非弱化改写）；P2-6（登录/上报限流）不采纳，属新增行为，
  暂缓。
- **TASK-068（纯 review，基座旧 3 commit，P2-1 数字已过时按 main 现状 36 项
  处理）**：采纳 P2-1~P2-7（P2-3 取"README 注明 title 字段不入库"的文档方案，
  不动埋点脚本；P2-4 改"直接依赖钉死版本"措辞，不碰 requirements.txt 版本号）；
  采纳 **P2-8**：安全响应头中间件移到请求体上限中间件之外，413 也带
  X-Frame-Options/X-Content-Type-Options，附断言测试
  `test_413_response_has_security_headers`（实测确认原顺序下 413 无头）；
  采纳 **P2-9**：登录响应与看板页加 `Cache-Control: no-store`，附断言测试
  `test_login_and_dashboard_no_store`；P2-10（登录失败限速）不采纳，属新增
  行为且会碰现有测试断言，关闭。
- 环境备忘：本仓 starlette 1.9.0 下实测"后挂载的中间件在外层"（与直觉的
  reversed 堆叠相反，以实测为准）；413 响应体为固定文本 `Content Too Large`，
  非用户数据，带安全头无回显风险。

## D-12 TASK-086 收口决定（2026-10-22）

分支基座 91e08ef 落后 main（db98493）3 个提交，未整支合并。分支改动与
main 的 071/073 改动在 login/改密两处重叠，手工融合：保留 071 的
is_utf8_text 守卫与用户名预处理，采纳 086 的时序思想。

- 采纳 P1（登录用户名枚举时序）：新增 `password_matches()`（PBKDF2 +
  `secrets.compare_digest`，按口径#8 字面用 secrets 而非分支的 hmac，
  startdeck TASK-039 有一贯先例）；用户不存在时用固定哑盐
  `_UNKNOWN_USER_SALT`/`_UNKNOWN_USER_HASH` 跑一遍 PBKDF2 再 401，使
  "用户不存在"与"密码错误"的响应时间一致（Grok 实测修复前 5ms vs 69ms，
  修复后均为 70–80ms）。配回归测试
  `test_login_unknown_user_runs_dummy_pbkdf2`（401 + 耗时 > 50ms 断言；
  PBKDF2 实测约 110ms，阈值只防"完全没跑"的退化）。
- TASK-080 的 P2-6（同一时序问题）按重复关闭，不另派。
- README 补改密吊销说明一句（派单文档项其余均已在 D-11 落地：测试数 36、
  400/413 分界、库路径、UV 盐、字体名）。
- 关闭项（不复议）：X-Forwarded-For 按 D-6 维持；访客哈希穷举按 D-8 维持；
  "413 无安全头"已由 068 P2-8 修掉（非关闭，是已解决）；上报 400 无 CORS 头
  暂缓（beacon 上报不读响应体，影响小）；传递依赖不钉死（只钉直接依赖，
  Grok 自述不改版本号）；get_conn() 未显式关闭（sqlite 上下文管理器已处理，
  未造成失败）；登录页默认账号提示措辞经复核已清晰，按 D-5 保留不改；
  域名框 maxlength 不加；登录限速不加（默认只监听本机，与口径#3 一致）；
  080 P2-10（UV 哈希不含 site_id）按 D-8 维持。
- 审查结论：分支测试文件未动；无"强制改密"回潮（四份报告均按口径#1 销项）。

## D-13 TASK-102-weblens 收口决定（2026-10-24）

分支基座即当前 main（fffc58a），未整支合并，手工搬运唯一改动（app.py；
测试文件未动）。搬运时把内联的路径解析抽成纯函数 `resolve_db_path()`，
行为与分支逐字一致（去空白→空走默认→绝对原样→相对接 BASE_DIR），只为
让回归测试无需子进程、不碰 os.environ。

- 采纳 P1-1：`WEBLENS_DB_PATH` 设相对路径时按进程当前目录解析库位置，
  换目录启动会另建一套带默认口令 admin/admin123 的新库——与 README
  「相对 app.py 所在目录」的声明不符。修复后相对路径锚到 BASE_DIR。
  端到端验证：从 /tmp 启动、WEBLENS_DB_PATH=e2e-check.db，库文件落在
  app.py 目录下，不在当前目录。
- 配回归测试 `test_db_path_resolution`（相对/绝对/空/未设置/前后空白，
  7 断言；纯函数，不污染环境）。
- P2 六条本次不修（A+B 下纯 P2 攒着等 P0/P1 或用户要求时一并派）。
- 审查结论：无"强制改密"回潮（报告按口径#1 销项）；口径#3/#6/#8/#17/#20
  均无冲突。
