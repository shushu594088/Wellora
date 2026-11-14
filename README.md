# Wellora（知安）

面向全年龄用户的健康管理与就医辅助应用，默认标准模式，可切长辈模式。重点是档案、报告校对解读与对比、咨询和科室参考、用药与家属协助。首阶段仅面向不超过 20 个成年试用账号。

当前状态：截至 2026-11-14，账号／本人档案后端及本人健康记录 API 已部署至北京测试服务器；PostgreSQL Alembic 为 `0002 (head)`，16 项远端虚构账号／健康记录冒烟全部通过，清理后账号、档案、会话、健康记录和幂等表均为 0；共享登录限流表保留 7 个哈希键，其中 1 个部署前已有，6 个测试时间段新增的零失败键未删除以避免误伤共享 IP 状态。API 仅绑定 WireGuard 私网 `10.66.0.1:8000`、DB 无宿主机端口映射，API 健康 200；临时 Cloudflare Quick Tunnel 仍运行，WireGuard peer 握手时间仍为 0，因此不代表手机 App 业务验收。正式公网接入仍待备案与 TLS。

## 文档导航

- [开发规则](AGENTS.md)
- [需求](docs/需求.md)
- [架构与接口](docs/架构与接口.md)
- [界面设计与原型索引](docs/界面设计.md)
- [原型资源](docs/prototypes/)
- [开发记录](docs/开发记录.md)
- [Prompt 证据索引](evidence/index.md)
- [后端测试服务说明](server/README.md)
- [P017：账号与本人档案后端测试版](evidence/prompts/P017.md)
- [P018：Android 临时 HTTPS 联调](evidence/prompts/P018.md)
- [P020：测试后端自动验收](evidence/prompts/P020.md)
- [P021：本人健康记录 API](evidence/prompts/P021.md)
- [P022：私有 OSS 文件 API](evidence/prompts/P022.md)
- [P001：初始化 Git](evidence/prompts/P001.md)
- [P002：归档 Stitch 原型](evidence/prompts/P002.md)
- [P003：需求、架构与界面文档](evidence/prompts/P003.md)
- [P004：S01 原生 Compose 代表页](evidence/prompts/P004.md)

需求文档定义 R001–R016 与逐项验收；架构文档定义模块、数据、接口、权限和预算；界面文档映射 20 个核心画面、子流程和有效视觉规范。全部功能分 A–E 阶段验收，任务和前置条件见开发记录。现有 `MainActivity`、主题和测试均为模板内容。

## 已确认技术方案与待接入项

- Android：Kotlin + Compose、ViewModel、Repository；双模式共享业务，联网为主，本地仅保护草稿、缓存和提醒。
- Android UI：S01 代表页使用 `ui/feature/home/HomeScreen.kt`、`ui/navigation/WelloraNavigation.kt` 和 `ui/theme/`；禁止 WebView、iframe、浏览器容器和 HTML 页面加载。Stitch HTML/CSS/JS/screen.png 只作视觉参考。
- 新增官方依赖：`androidx.compose.material:material-icons-extended`，用于本地 Compose 矢量图标（AndroidX、Apache-2.0、由 Compose BOM 2026.02.01 管理）。
- 后端：FastAPI + SQLAlchemy + Alembic + PostgreSQL，独立 worker 使用数据库持久队列；Docker Compose 单机部署，不引入微服务。
- 服务器：北京 Ubuntu Server 24.04、2 核 2GiB、40GiB、100GB 流量、峰值 2Mbit/s。已有阿里云 OSS（具体地域待核实），后端域名 api.shushu520.top 尚未配置 HTTPS；暂不备案，先内部验证。
- 服务：DeepSeek、讯飞 OCR／普通话识别、系统 TTS；外部服务月预算目标 100 元。具体产品、模型、价格和配额待核实，未声称已联调。
- 登录：用户名密码，首版无验证码及邮件找回。删除立即封锁并清理在线数据，灾备最长 30 天，恢复不得复活已删资料。

后端位于 `server/`，依赖由 `uv.lock` 锁定。注册、登录、退出、本人基础档案和健康记录已实现；服务器验证覆盖 PostgreSQL `0002`、两账号隔离、未知／无／有记录、幂等、分页、版本冲突与清理。当前仍仅使用虚构测试资料，不得用于真实健康数据。密码复验、改密、删除、报告／OCR／分析等未完成。
R003 健康记录支持本人的来源标注与版本化读写；AI 解释保持未确认，未知／无／有记录分开存储。P022 已实现本机鉴权文件上传／下载和可注入存储适配器，当前使用假存储验证，尚未连接真实 OSS。真实联调依赖密钥轮换确认及 Bucket 权限／加密／生命周期核验；OCR、DeepSeek 分析仍未实现。

本机测试（Python 3.12、uv）：

```powershell
cd server
uv sync --locked --group dev --default-index https://pypi.org/simple
uv run --no-sync pytest -q
```

API 测试自行使用隔离 SQLite；手动启动服务须显式配置 `DATABASE_URL` 并运行 Alembic 迁移。生产测试使用 `server/docker-compose.yml`、私有 PostgreSQL 和 Caddy HTTPS 反代。部署步骤、域名、流量端口及未验证项见 [server/README.md](server/README.md)；禁止把测试 API 明文暴露到公网。

## 模板环境与命令

工程配置：Gradle 9.6.0、Android Gradle Plugin 9.4.1、Kotlin Compose 插件 2.2.10、Compose BOM 2026.02.01；包名 `com.nmy.wellora`，最低 Android API 26，编译和目标 API 37。Gradle Daemon 工具链配置为 JDK 25；源码兼容级别为 Java 11。

使用 Android Studio 打开项目并配置 Android SDK；本机 SDK 路径保存在不提交的 `local.properties`。Windows 验证命令：

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug --console=plain
```

模板构建和单元测试在 P001 曾通过，详见开发记录；P003 仅验证文档与字节完整性，未重跑 Gradle、设备测试或视觉验收。构建成功后可在 Android Studio 选择设备运行 `app`。

## Git 状态

默认分支为 `main`，已跟踪 `origin/main`。远端为 [shushu594088/Wellora](https://github.com/shushu594088/Wellora)，可见性为 Public。

本仓库的提交者身份已配置为 `shushu <nmy061023@gmail.com>`。首次提交 `10c6746d1f56874e7a537e897e19b22d1faac3a0` 仅保存项目规则、现有忽略规则和初始化文档，已推送并核对远端 SHA。用户确认空项目模板后，将现有应用源码和 Gradle 工程文件按初始骨架纳入版本管理；不修改模板实现。IDE 本地配置、SDK 路径和构建产物不纳入本轮提交。

## P023 香港主服务器部署

用户指定 `server1`（Ubuntu 22.04，`38.76.195.17`）作为 Wellora 主机。该机已有 `shushu520.top` 主站和其他服务；Wellora 使用独立 Compose override `server/docker-compose.hk.yml`、本机 `127.0.0.1:8010` API 端口及 `server/deploy/nginx-api.conf` 子域虚拟主机，保留现有主站。已为 API 子域签发 HTTPS 证书并部署专属 vhost；OSS 密钥不得在聊天或 Git 保存，未设置凭据时文件 API 应返回 503。数据库密码由服务器随机生成。只有在阿里云撤销聊天中已披露的旧 key、创建新的最小权限 RAM OSS key 后，才可在项目根目录执行 `powershell -ExecutionPolicy Bypass -File .\server\deploy\configure-hk-oss.ps1`：脚本 SecureString 交互采集新 AccessKey，通过 `ssh server1` stdin 传入服务器、写为 0600 私有 `.env` 并重启 Wellora API，不在命令行或日志回显 secret。当前只实现了 OSS 凭据接入；DeepSeek／讯飞 key 尚未接入 API/Compose。部署状态及实际命令见 `docs/开发记录.md` P023 和 `evidence/transactions/P023-hk-server/VERIFICATION.txt`。

## P023 香港主服务器部署

用户指定 `server1`（Ubuntu 22.04，`38.76.195.17`）作为 Wellora 主机。该机已有 `shushu520.top` 主站和其他服务；Wellora 使用独立 Compose override `server/docker-compose.hk.yml`、本机 `127.0.0.1:8010` API 端口及 `server/deploy/nginx-api.conf` 子域虚拟主机，保留现有主站。API 子域已启用 HTTPS，OSS 凭据由本地 PowerShell 安全提示写入服务器私有 `.env`；已用虚构 PNG 验证鉴权 API 上传／下载成功并清理对象。Bucket ACL 为 private 且公共访问阻断，但当前未配置服务端加密或生命周期规则，禁止存入真实健康文件直至补齐并核验。数据库密码由服务器随机生成。今后运行 `powershell -ExecutionPolicy Bypass -File .\server\deploy\configure-hk-oss.ps1` 时，只使用旧披露凭据已撤销后新建的最小权限 RAM key；输入大写 `ROTATED` 后在本地安全提示录入，不要发到聊天。若最新运行所用 ID 是先前贴入聊天的 key，应先禁用并重新生成。该脚本只处理 OSS；DeepSeek／讯飞 key 尚未接入 API/Compose。验证记录见 `evidence/transactions/P023-hk-server/VERIFICATION.txt`。
