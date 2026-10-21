# weblens · 网站访问统计

一句话定位：一个轻量、可自托管的网站访问统计工具——给站点生成一段埋点脚本，网页被打开时自动上报，后台集中看访问量、访客、趋势、热门页面与来源域名。

本项目的设计学习了开源社区同类工具的通行思路，代码为独立实现。上游溯源与署名见 [UPSTREAM.md](UPSTREAM.md)。

## 功能清单

- **单用户登录**：Token 24 小时有效，首次登录提示改密；默认账号 `admin` / `admin123`。修改密码成功后，该账号的其他登录会话会被吊销（当前会话保留，需重新登录的是其他设备）。
- **站点管理**：站点可新建、改名、换域名、删除；删除站点时一并删除其访问记录
- **埋点接入**：每个站点生成唯一 `site_id`，站点详情中可直接复制一段脚本；脚本由本服务提供，页面打开后自动上报当前页面与来源
- **公开上报接口**：`POST /api/collect` 无需登录，凭 `site_id` 记录页面路径、站外来源域名与 UA 粗分类
- **统计看板**：按今天 / 近 7 天 / 近 30 天查看总 PV、总 UV、人均浏览、活跃页面数。这里的「今天」以及按天切分使用 UTC
- **趋势与排行**：按天 PV/UV 趋势图、热门页面 Top 10、来源域名 Top 10
- **隐私减量**：不保存完整 IP、UA 原文或完整来源 URL；UV 使用加盐哈希按天去重

## 安装与启动

需要 Python 3.10 或更高版本。

### Linux / macOS

```bash
cd weblens
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Windows（PowerShell）

```powershell
cd weblens
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

启动后打开 http://127.0.0.1:8000 ，使用默认账号 **admin / admin123** 登录。首次登录会提示修改密码。

可选环境变量：

| 变量 | 说明 | 默认 |
|---|---|---|
| `WEBLENS_HOST` | 监听地址；默认只监听本机 | `127.0.0.1` |
| `WEBLENS_PORT` | 监听端口（未设置时再看 `PORT`） | `8000` |
| `WEBLENS_DB_PATH` | SQLite 数据库文件位置（相对 `app.py` 所在目录） | `data/weblens.db` |
| `WL_INITIAL_USERNAME` / `WL_INITIAL_PASSWORD` | 首次启动创建的初始账号 | `admin` / `admin123` |
| `WEBLENS_UV_SALT` | UV 哈希盐；不设置时首次上报计算 UV 时写入本机数据库 | 无 |

> 需要局域网或对外访问时，把 `WEBLENS_HOST` 改成 `0.0.0.0`；放开前请先改掉默认密码。

## 接入一个网站

1. 登录 weblens，新建站点并填写名称与域名。域名可填 `example.com`，也可粘贴完整地址，系统会自动去掉协议、路径和开头的 `www.`，只保留主机名。
2. 在站点详情中复制埋点脚本。
3. 把脚本粘贴到目标网站每个页面的 `</body>` 前，或放进网站的公共模板。
4. 打开目标网页后回到 weblens，选择时间范围即可查看统计。

埋点脚本示例（实际 `site_id` 以站点详情为准）：

```html
<script defer src="http://127.0.0.1:8000/tracker.js" data-weblens-id="你的-site_id"></script>
```

## 上报接口

`POST /api/collect` 接收 JSON；为方便浏览器 `sendBeacon`，也接受 `text/plain` 形式的 JSON 字符串。

```json
{
  "site_id": "站点详情中的 UUID",
  "url": "https://example.com/products?from=test",
  "referrer": "https://www.google.com/search"
}
```

- `site_id` 必填且必须对应已创建的站点；不存在时返回 404。
- `url` 可传完整 URL 或页面路径，入库时只保留路径部分。
- `referrer` 可传完整来源 URL，入库时只保留站外来源域名。
- User-Agent 从请求头读取并只保存浏览器、系统、设备三类粗分类。
- 埋点脚本会顺带上报页面标题（`title` 字段），服务端目前不入库，仅保留页面路径。
- 请求体在 64KiB 到 128KiB 之间时返回 400「请求体过大」；超过 128KiB 时由框架直接返回 413。

## 测试

先安装开发依赖，再运行自动化测试与真实流程自测：

### Linux / macOS

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
python tests/live_selftest.py
```

### Windows（PowerShell）

```powershell
pip install -r requirements-dev.txt
python -m pytest tests/ -q
python tests/live_selftest.py
```

`live_selftest.py` 会在临时数据库上真的启动一个 Uvicorn 服务，走完建站、埋点上报、统计断言、改名与删除流程。当前自动化测试 37 项（其中 6 项为 UA 分类的参数化用例）、真实流程自测 15 个检查点，均已在干净虚拟环境中按钉死依赖版本复验通过。

## 项目结构

- `app.py` — 后端（FastAPI + SQLite）：账号、站点、上报与统计接口
- `static/index.html` — 单页前端（原生 HTML/CSS/JS，无构建步骤）
- `tests/test_app.py` — 自动化测试
- `tests/live_selftest.py` — 真实服务自测脚本
- `NOTES.md` — 调研与设计笔记
- `UPSTREAM.md` — 上游溯源信息
- `DECISIONS.md` — 本仓决定记录（用户决策与复核结论）
- `LICENSE` — MIT 许可证文本
- `requirements.txt` / `requirements-dev.txt` — 运行/测试的直接依赖，版本已钉死
- `.gitignore` — 忽略本地数据库、虚拟环境等不入库文件

## 许可证

MIT（见 [LICENSE](LICENSE)）。
