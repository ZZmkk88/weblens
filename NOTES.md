# weblens 调研笔记

## 上游对象（2026-10-21 通过 GitHub 接口实查）

- 项目：Umami（`umami-software/umami`），MIT 许可证。
- 默认分支 HEAD：`e92fdab99508a8ed05249f6c5f07e140deab79e1`。
- LICENSE 原文版权行：`Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>`（逐字复制，见 `UPSTREAM.md`）。
- 上游 README 写明的自托管要求是 Node.js 18.18+ 与 PostgreSQL 12.14+，可使用其 Docker 镜像或 Docker Compose；首次构建会建表并创建初始登录用户。

## 从上游读到的采集与数据形态

通读了 `src/app/api/send/route.ts` 与同目录测试，确认其公开采集入口不需要登录，请求体由 `type` 与 `payload` 两层组成：

- `type` 可为 `event`、`identify`、`performance`；本项目 MVP 只处理页面浏览这一类事件，不引入身份关联与性能指标。
- `payload` 的站点标识字段是 `website`，且网站、链接、像素三类来源标识必须恰好提供一个；本项目改用单一 `site_id`，避免把多来源体系带进轻量版本。
- 页面事件会用到的字段包括 `url`、`referrer`、`hostname`、`title`、`screen`、`language`，客户端信息包含浏览器、操作系统、设备；事件数据结构里还区分页面路径、查询串与来源路径/查询串/域名。
- 上游会把来源 URL 拆成路径、查询串和域名，只把来源域名用于统计；当来源域名与当前站点域名相同（站内跳转）时不保存来源域名。本项目沿用这条统计口径：只存站外来源域名，不存完整来源 URL。
- 上游的会话标识由站点、IP、User-Agent 与轮换盐共同推导，访问（visit）有 30 分钟窗口。本项目不做会话与访问窗口，只按天计算 UV：以站点无关的加盐哈希表示「IP + 浏览器大类 + 系统大类 + 设备大类 + 日期」，同一天内同一组合只计一个 UV。
- 埋点形态是一个带站点 ID 的脚本标签，脚本地址与站点 ID 分开传递。本项目对应实现为 `/tracker.js` + `data-weblens-id`，脚本把当前页面 URL 与 `document.referrer` 发往 `/api/collect`。

## 本项目的数据模型

- `users` / `sessions`：单用户账号与 24 小时 Token 会话，密码用 PBKDF2-HMAC-SHA256 加盐哈希。
- `sites`：内部整数主键 + 对外 UUID 形式的 `site_id`，另存名称、规范化域名与时间戳。删除站点时，其页面访问记录通过外键级联删除。
- `pageviews`：每次页面浏览一行，存站点内部 ID、页面路径、站外来源域名、浏览器/系统/设备大类、访客哈希、UTC 日期与时间。不存完整 IP、不存 UA 原文、不存完整来源 URL。
- `settings`：当未通过环境变量提供 UV 盐时，首次初始化在本机数据库中生成随机盐；盐不写入代码仓库。

## 本项目 MVP 取舍

做全：单用户登录与改密提示、站点增删改、专属 `site_id` 与可复制埋点脚本、公开上报接口、PV/UV、今天/近 7 天/近 30 天的日趋势、热门页面 Top 10、来源域名 Top 10、单页看板。

明确不做：团队协作与多用户、实时大屏、转化/漏斗分析、会话回放、自定义事件与事件属性分析、性能指标、身份关联。

## 资源核对结论

2026-10-21 云端实测为 2 核 CPU、7.7 GiB 内存、约 99 GiB 可用磁盘、无 GPU，系统 Python 3.12。本项目只运行一个 FastAPI/Uvicorn 进程并使用单个 SQLite 文件，不需要 Node.js、PostgreSQL、ClickHouse 或 GPU；依赖只有 FastAPI 与 Uvicorn，适合该配置。

## 隐私口径

- 完整 IP 只在请求处理期间用于生成加盐哈希，不落库。
- User-Agent 只落库为浏览器、系统、设备三类粗分类，不存原文。
- 来源只落库域名；站内来源不计入来源域名统计。
- UV 盐可通过 `WEBLENS_UV_SALT` 环境变量提供；未提供时在本机数据库 `settings` 表生成并保存，不进入仓库。
