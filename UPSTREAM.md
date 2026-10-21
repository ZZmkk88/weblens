# 上游溯源（UPSTREAM）

本项目在设计阶段学习了开源社区同类网站统计工具的通行思路，按接力规范记录上游信息如下：

- **source_url**: https://github.com/umami-software/umami
- **source_commit**: e92fdab99508a8ed05249f6c5f07e140deab79e1
- **license**: MIT
- **attribution**: Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>

## 说明

- `source_commit` 是 2026-10-21 通过 GitHub 接口实查的上游默认分支 HEAD 提交；当日调研通读的上游内容正是这一提交，包括 `README.md`、`LICENSE`、`src/app/api/send/route.ts` 及其测试文件。
- `attribution` 的版权行逐字复制自上游仓库 `LICENSE` 原文，未做任何改动。
- 本项目代码为独立实现（Python + FastAPI + SQLite），未复制上游源码。调研依据与本项目取舍见 `NOTES.md`。
