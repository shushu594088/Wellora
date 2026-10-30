# Wellora

Android Studio 创建的空项目模板（用户于 2026-10-30 确认），尚未开发业务功能。2026-10-30 初始化本地 Git 仓库，默认分支为 `main`。

## 文档导航

- [开发规则](AGENTS.md)
- [开发记录](docs/开发记录.md)
- [Prompt 证据索引](evidence/index.md)
- [P001：初始化 Git](evidence/prompts/P001.md)

需求、架构与接口、界面设计文档及原型索引在功能开发前补齐。现有 `MainActivity` 为 Compose 的 `Hello Android!` 示例，主题和测试均为模板内容，不作为核心功能成果。

## 模板环境与命令

工程配置：Gradle 9.6.0、Android Gradle Plugin 9.4.1、Kotlin Compose 插件 2.2.10、Compose BOM 2026.02.01；包名 `com.nmy.wellora`，最低 Android API 26，编译和目标 API 37。Gradle Daemon 工具链配置为 JDK 25；源码兼容级别为 Java 11。

使用 Android Studio 打开项目并配置 Android SDK；本机 SDK 路径保存在不提交的 `local.properties`。Windows 验证命令：

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug --console=plain
```

实际验证结果见开发记录；设备测试和模拟器启动尚未验证。构建成功后可在 Android Studio 选择设备运行 `app`。

## Git 状态

默认分支为 `main`，已跟踪 `origin/main`。远端为 [shushu594088/Wellora](https://github.com/shushu594088/Wellora)，可见性为 Public。

本仓库的提交者身份已配置为 `shushu <nmy061023@gmail.com>`。首次提交 `10c6746d1f56874e7a537e897e19b22d1faac3a0` 仅保存项目规则、现有忽略规则和初始化文档，已推送并核对远端 SHA。用户确认空项目模板后，将现有应用源码和 Gradle 工程文件按初始骨架纳入版本管理；不修改模板实现。IDE 本地配置、SDK 路径和构建产物不纳入本轮提交。
