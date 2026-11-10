# Prompt 与提交证据索引

| Prompt | 目标 | 原始记录 | commit SHA | 验证结果 |
| --- | --- | --- | --- | --- |
| [P001](prompts/P001.md) | 初始化 Git、配置远端与留存空模板（非核心功能迭代） | 待补原始证据，保存至 `evidence/raw/` | 初始化：`10c6746d1f56874e7a537e897e19b22d1faac3a0`；远端记录：`40284b7ba30749cb072e39e71cd317abfde938f4`；模板基线：`1d9a624c0fa9b28c75a4f5bf90236ed74aaec91b` | Public 仓库和 origin 已配置；模板构建及单元测试通过，详见开发记录 |
| [P002](prompts/P002.md) | 归档 Stitch 原型（非核心功能迭代） | 待补原始对话；[工具校验日志](raw/P002-prototype-verification.txt)仅为验证证据 | `61d2eb676bad6aac2ba831ea6e0517b8d3467428` | 两包 46 个文件与 ZIP 条目 SHA-256 一致，源包不变；页面和来源索引见界面设计文档 |
| [P003](prompts/P003.md) | 确认产品与技术方案，完善开发文档（非核心功能实现） | 待补原始对话；[文档验证日志](raw/P003-doc-verification.txt)仅为工具证据 | 文档：`b580f5381dcb5d8e2db09684f9feb127a48f0a7d`；本条为后续证据登记 | R001–R016、10 对核心画面、65 个本地链接有效；46 原型和其余保护字节不变；副本回滚 96/96 哈希一致；未执行业务测试或部署 |
| [P004](prompts/P004.md) | S01 标准模式首页原生 Compose 代表页 | 待补原始对话；[模拟器截图](raw/P004-home-compose.png)、[UIAutomator 层级](raw/P004-home-hierarchy.xml) | `d8a28e35015681b3a294cb2b59913626c6a99c3d` | `:app:testDebugUnitTest`、`:app:assembleDebug`、`:app:connectedDebugAndroidTest` 通过；模拟器安装和原生语义节点检查通过；真机视觉验收待补 |
| [P017](prompts/P017.md) | 后端测试版：账号、本人档案与内部服务器验证 | 待补原始对话；[本机交易](transactions/P017-backend/VERIFICATION.txt)、[服务器实测](transactions/P017-backend/SERVER_VERIFICATION.json) | 测试骨架：`5fe467de44aacf66c195b876a210a2b255f36429`；文档：`4db3858`（完整 SHA 见提交后登记） | 本机 API 14 项；服务器 Docker 构建、PG 迁移、隔离／冲突／退出／并发上限／重启持久化和样本清理通过；db/api 私有运行，公网与 Android 待办 |
| [P018](prompts/P018.md) | Android 账号／档案与临时 Cloudflare HTTPS 联调（WireGuard 未握手后切换） | 待补原始对话；[字面执行记录](transactions/P017-backend/P018_EXECUTION.json)、[交付哈希及服务器状态](transactions/P017-backend/android/HTTPS_DELIVERY.json)、[11 项测试报告](transactions/P017-backend/android/HTTPS_DEVICE_TEST_RESULTS.xml) | HTTPS 验收：`3afd96939397259d84dac92462c1edcb1801c880` | HTTPS 健康 200；单元／构建通过、模拟器 11 项通过；数据清理至四表 0；真机待用户验收 |
