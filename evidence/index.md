# Prompt 与提交证据索引

| Prompt | 目标 | 原始记录 | commit SHA | 验证结果 |
| --- | --- | --- | --- | --- |
| [P001](prompts/P001.md) | 初始化 Git、配置远端与留存空模板（非核心功能迭代） | 待补原始证据，保存至 `evidence/raw/` | 初始化：`10c6746d1f56874e7a537e897e19b22d1faac3a0`；远端记录：`40284b7ba30749cb072e39e71cd317abfde938f4`；模板基线：`1d9a624c0fa9b28c75a4f5bf90236ed74aaec91b` | Public 仓库和 origin 已配置；模板构建及单元测试通过，详见开发记录 |
| [P002](prompts/P002.md) | 归档 Stitch 原型（非核心功能迭代） | 待补原始对话；[工具校验日志](raw/P002-prototype-verification.txt)仅为验证证据 | `61d2eb676bad6aac2ba831ea6e0517b8d3467428` | 两包 46 个文件与 ZIP 条目 SHA-256 一致，源包不变；页面和来源索引见界面设计文档 |
| [P003](prompts/P003.md) | 确认产品与技术方案，完善开发文档（非核心功能实现） | 待补原始对话；[文档验证日志](raw/P003-doc-verification.txt)仅为工具证据 | 提交后在后续记录补充 | 文档契约、链接、字节保护及回滚结果见日志；未执行业务测试或部署 |
