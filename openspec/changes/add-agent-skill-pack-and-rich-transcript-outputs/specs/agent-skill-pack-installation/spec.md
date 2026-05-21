## ADDED Requirements

### Requirement: 三端能力 Skill 包
仓库 MUST 为 Claude、Codex、Cursor 定义统一能力 skill 包；必装能力至少包含 Frontend Design Skill、docx Skill、xlsx Skill、pdf Skill、pptx Skill 和 Web Access Skill。PUA Skill MUST 先作为 `quarantined` 候选项纳入安装治理，只有来源、用途和安全边界明确后才能提升为可调用或必装项。

#### Scenario: 生成安装矩阵
- **WHEN** 维护者查看跨 agent 安装文档
- **THEN** 文档会列出 Claude、Codex、Cursor 各自应安装的 skill 名称、canonical name、别名、来源、目标安装路径、调用名、状态和 agent-specific caveat

#### Scenario: 缺失必装能力 skill
- **WHEN** 安装验证发现某个 agent 缺少必装能力 skill
- **THEN** 验证结果会按 agent 和 skill 名称列出缺失项，并提示该缺失会影响哪些工作流

#### Scenario: PUA 仍处于隔离候选
- **WHEN** PUA Skill 的来源、用途、权限、安全边界、调用场景或禁止事项任一项缺失
- **THEN** 它会被记录为 `quarantined` 候选项，缺失不阻塞必装能力包验证，但阻塞任何默认自动调用或可调用声明

#### Scenario: Mavis 不在本轮强制矩阵
- **WHEN** 维护者查看本 change 的安装范围
- **THEN** 文档会说明本轮强制安装矩阵只覆盖 Claude、Codex、Cursor，Mavis 保留为仓库既有安装目标但不参与本轮必装包验证

### Requirement: Skill 来源与版本记录
仓库 MUST 记录必装能力 skill 和 quarantined 候选 skill 的来源、版本或可校验标识，避免三个 agent 使用不同版本导致行为漂移。

#### Scenario: 同步安装后记录版本
- **WHEN** 维护者完成 Claude、Codex、Cursor 的 skill 同步
- **THEN** 安装记录包含每个必装能力 skill 和 quarantined 候选 skill 的版本、来源路径或提交标识，以及验证时间

#### Scenario: 版本不一致
- **WHEN** 同一个 canonical skill 在不同 agent 中版本不一致
- **THEN** 验证结果会报告 drift，并要求维护者选择统一版本或记录有意差异

### Requirement: 安装包清单与锁定文件
仓库 MUST 定义 `agent-skill-pack.yaml` 与 `agent-skill-pack.lock.json`，分别记录期望安装矩阵和实际锁定安装状态。

#### Scenario: 定义安装包清单
- **WHEN** 维护者编辑 `agent-skill-pack.yaml`
- **THEN** 每个 skill 条目包含 `canonicalName`、`aliases`、`capability`、`source.kind`、`source.path/url`、`installTargets`、`callName`、`required/optional/quarantined` 状态和 `verificationProbe`

#### Scenario: 生成锁定文件
- **WHEN** 安装验证流程完成
- **THEN** `agent-skill-pack.lock.json` 会记录每个 skill 的实际版本、commit 或 checksum、安装路径、验证时间、验证状态和 drift 信息

### Requirement: 安装验证命令
仓库 MUST 提供可重复执行的安装验证流程，用于检查 Claude、Codex、Cursor 的必装能力 skill 是否存在且元数据可读，并记录 quarantined 候选 skill 的状态。

#### Scenario: 验证三端安装
- **WHEN** 维护者运行安装验证流程
- **THEN** 流程会检查三个 agent 的 skill 目录、`SKILL.md` 或 manifest、关键引用文件、可调用名称、agent-specific invocation adapter 和验证探针

#### Scenario: 某个 agent 不在当前机器
- **WHEN** 当前机器无法访问某个 agent 的安装目录
- **THEN** 验证流程会将该 agent 标记为未验证，而不是误报为 skill 本身失败

#### Scenario: 验证状态输出
- **WHEN** 安装验证流程输出结果
- **THEN** 每个条目会被标记为 `ok`、`missing`、`drift`、`unverified` 或 `quarantined`，并说明该状态是否阻塞相关 workflow

### Requirement: 格式 Skill 能力映射
仓库 MUST 说明 docx、xlsx、pdf、pptx Skill 与 `video-transcript` 输出格式之间的能力映射。

#### Scenario: 请求 Word 输出
- **WHEN** 用户要求 `video-transcript` 生成 Word 或 DOCX 内容
- **THEN** 工作流会检查 docx Skill 是否可用，并将 Word/DOCX 输出能力映射到该 skill

#### Scenario: 请求 PPT 输出
- **WHEN** 用户要求 `video-transcript` 生成 PPT 或 PPTX 内容
- **THEN** 工作流会检查 pptx Skill 是否可用，并将演示文稿输出能力映射到该 skill

#### Scenario: 请求 PDF 输出
- **WHEN** 用户要求 `video-transcript` 生成 PDF
- **THEN** 工作流会检查 pdf Skill 是否可用，或记录 PDF 从 HTML、DOCX、PPTX 渲染派生的路径

#### Scenario: xlsx 能力用途
- **WHEN** 安装矩阵列出 xlsx Skill
- **THEN** 文档会说明 xlsx Skill 不属于 `video-transcript` 默认输出格式，但作为三端 Office/PDF 能力包用于表格、数据摘要或后续资料整理

### Requirement: 安装安全边界
仓库 MUST 记录必装能力 skill 和 quarantined 候选 skill 的安全边界，特别是 Web Access Skill 和 PUA Skill 的调用必须遵循各自文档，不得隐式扩大权限。

#### Scenario: Web Access Skill 需要登录态
- **WHEN** 某工作流需要使用 Web Access Skill 访问登录网站
- **THEN** agent 必须先向用户说明访问范围、登录态使用方式和本地残留文件，再等待确认

#### Scenario: PUA Skill 缺少能力说明
- **WHEN** PUA Skill 的来源或能力边界没有文档说明
- **THEN** 安装验证会将其标记为 `quarantined`，不能把它作为默认自动调用能力

#### Scenario: PUA Skill 解除隔离
- **WHEN** PUA Skill 的来源、用途、权限、安全边界、调用场景和禁止事项都已记录
- **THEN** 维护者可以将其从 `quarantined` 调整为可调用状态，并在 lock 文件中记录该状态变化
