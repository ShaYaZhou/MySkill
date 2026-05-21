## ADDED Requirements

### Requirement: Skill 入口契约
每个 skill MUST 将 `SKILL.md` 保持为面向 agent 的简洁运行入口，包含 frontmatter、调用条件、默认工作流、安全策略摘要、选项摘要，以及存在深层文档时的 reference map。

#### Scenario: Agent 阅读 skill 入口
- **WHEN** agent 打开某个 skill 的 `SKILL.md`
- **THEN** agent 能判断何时使用该 skill、默认运行什么命令、适用哪些安全约束，以及非默认场景应阅读哪个深层 reference

#### Scenario: Skill 超出入口文档承载范围
- **WHEN** 运行指导变得过长，已经不适合 agent 快速阅读
- **THEN** 稳定细节会移入 `references/` 下的链接文件，而 `SKILL.md` 保留摘要和路由说明

### Requirement: 分层 Skill 目录结构
仓库 MUST 定义分层 skill 目录结构：所有 skill 的必需文件、复杂 skill 的可选 reference 资产，以及脚手架或模板驱动 skill 的可选生成资产。

#### Scenario: 工具型 skill 保持轻量
- **WHEN** 某个 skill 只封装一到两个脚本
- **THEN** 它可以保持为 `SKILL.md`、`scripts/`、`agents/`，以及少量真正增加运行价值的定向 `references/` 文件

#### Scenario: 小型单脚本 skill 保持单入口文档
- **WHEN** 小型单脚本 skill 的 `SKILL.md` 仍能快速说明默认命令、选项、安全边界和完成检查
- **THEN** 仓库不会强制为该 skill 拆分多个 reference、README、templates 或 examples

#### Scenario: 工作流型 skill 需要更丰富资产
- **WHEN** 某个 skill 会生成项目、复制可复用文件，或需要可复用示例
- **THEN** 它可以增加 `templates/`、`examples/`、themes、fixtures 或 manifests，而不改变小型 skill 的基础契约

### Requirement: 产物契约文档
每个 skill MUST 记录输出契约，包括默认输出位置、生成文件、持久化状态、临时文件，以及执行后期望的后续动作。

#### Scenario: 检查下载 skill 输出
- **WHEN** `yt-dlp-download` 完成执行
- **THEN** skill 文档会说明媒体文件、字幕、缩略图、临时文件和 archive 状态应位于何处

#### Scenario: 检查转写 skill 输出
- **WHEN** `video-transcript` 完成执行
- **THEN** skill 文档会说明 `original.md`、`zh.md`、`metadata.json`、转写来源、语言状态，以及是否仍需要人工中文翻译

### Requirement: 跨 Agent 元数据
仓库 MUST 维护支持的 agent 环境可发现元数据，包括展示名称、短描述、默认 prompt，以及使用到的兼容性或分发元数据。

#### Scenario: 维护者使用仓库 README 安装
- **WHEN** 维护者阅读仓库 README
- **THEN** README 会说明支持的 agent、安装目标，以及每个 skill 使用的元数据文件

#### Scenario: 验证 skill 元数据
- **WHEN** 对某个 skill 运行验证
- **THEN** 必需 agent 元数据可以被解析，并且与 `SKILL.md` 中的 skill 名称一致

### Requirement: 产物与能力 Schema 契约
仓库 MUST 为机器可读 summary、metadata、manifest 或安装矩阵定义清晰 schema，区分必填字段、可选字段和禁止记录字段。

#### Scenario: 定义运行摘要字段
- **WHEN** skill 新增 `metadata.json`、`download-summary.json`、`run-summary.json` 或等价机器可读文件
- **THEN** schema 会说明每个字段的含义、何时为空、何时不确定、是否可脱敏记录，以及哪些字段不得伪造或记录敏感值

#### Scenario: 能力 token 化
- **WHEN** skill 文档描述后端、输出或依赖状态
- **THEN** 它会优先使用稳定状态值，例如 `source_type`、`backend`、`language_state`、`privacy_gate`、`archive_skip`、`partial_failure` 或 `uncertain_path`，而不是只依赖自由文本

#### Scenario: Capability 边界
- **WHEN** 仓库定义外部能力或辅助 skill 的使用方式
- **THEN** 文档会区分强契约、具体 skill 可自由实现的部分，以及需要另开 change 的越界行为

### Requirement: Reference Map 完整性
仓库 MUST 通过自动验证或人工检查，避免文档地图过期，并确认链接到的本地 reference 文件存在。

#### Scenario: Reference 被重命名
- **WHEN** 某个 reference 文档被重命名、删除或合并
- **THEN** `SKILL.md`、每个 skill 的 README 和根 README 引用都会同步更新，避免 agent 被路由到缺失文件

#### Scenario: Reference map 作为阻断级验证对象
- **WHEN** 维护者运行离线验证
- **THEN** 验证会检查 reference map 中的本地文件、Markdown 链接、frontmatter、agent yaml、manifest 或 schema 示例是否存在且可解析；缺失或过期引用会阻断通过

### Requirement: 轻量 Examples 契约
仓库 MUST 只在示例能澄清命令、边界或输出契约时增加 examples，并避免把示例变成大型模板库。

#### Scenario: 示例解释输出契约
- **WHEN** 某个 skill 增加 examples
- **THEN** 示例会标注用途、体量上限、适用边界和不要照搬，并优先展示命令配方、典型 summary 或失败/边界 case

#### Scenario: 示例不得冒充真实产物
- **WHEN** 验证或人工检查 examples
- **THEN** 示例输出、占位路径或 `TODO` 状态不会被 README、reference map、manifest 或安装文档误标为真实可用产物
