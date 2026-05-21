## ADDED Requirements

### Requirement: 条件式预检门
Skill MUST 定义 agent 何时可以立即执行，以及何时必须停下来等待用户确认后再继续。

#### Scenario: 低风险默认执行
- **WHEN** 用户请求使用公开输入和默认输出位置执行简单默认操作
- **THEN** agent 可以直接执行文档化的默认工作流，不额外增加计划检查点

#### Scenario: 高影响执行选择
- **WHEN** 执行涉及浏览器 cookie、登录态、付费或隐私敏感 API 上传、大批量处理、非默认输出位置或破坏性覆盖风险
- **THEN** agent 会给出简洁计划，并等待用户确认后再继续

### Requirement: 运行后检查真相源
Skill MUST 标明用于验证和用户汇报的运行后真相源，可以是文件、目录、metadata 或 report。

#### Scenario: 转写运行后检查
- **WHEN** 转写运行结束
- **THEN** agent 会先检查输出目录和 `metadata.json`，再判断 `original.md`、`zh.md`、后端来源、语言状态和后续翻译是否完成

#### Scenario: 下载运行后检查
- **WHEN** 下载运行结束
- **THEN** agent 会先检查输出目录、字幕 sidecar、缩略图 sidecar 和 archive 行为，再汇报完成情况

### Requirement: 完成前自检
Skill MUST 提供完成自检清单，agent 必须先处理失败检查项，再汇报成功。

#### Scenario: 自检发现可恢复问题
- **WHEN** 运行后清单发现缺少必需产物或存在可重试失败
- **THEN** agent 会在安全时先重试或修复问题，再汇报结果

#### Scenario: 自检发现不可恢复问题
- **WHEN** 某个失败检查项需要用户输入、缺失凭据、不可用依赖或外部服务访问才能修复
- **THEN** agent 会报告阻塞项、受影响产物和最小可用后续动作，而不是声称成功

#### Scenario: 独立 reviewer 仅作为增强
- **WHEN** 当前 agent 环境不支持 Agent Teams、subagent 或等价独立 reviewer
- **THEN** skill 自检流程仍可由当前 agent 按同一清单完成，不会依赖并行 reviewer 才能汇报结果

#### Scenario: Reviewer handoff 可执行
- **WHEN** agent 使用 Agent Teams、subagent 或独立 reviewer 复核产物
- **THEN** handoff 会包含产物路径、运行后真相源、检查清单、风险边界和禁止修改范围，并要求 reviewer 输出 pass/fail、证据、建议和是否阻塞

### Requirement: 完成汇报模板
Skill MUST 提供完成汇报模板，确保 agent 在结束时汇报输出路径、真相源文件、警告、失败项和后续动作。

#### Scenario: 成功完成后汇报
- **WHEN** skill 执行和自检均完成
- **THEN** agent 会按模板汇报主要输出路径、机器可读 summary 或 metadata、关键警告、跳过项和用户下一步可做的动作

#### Scenario: 部分失败后汇报
- **WHEN** skill 执行存在部分失败或不可恢复阻塞
- **THEN** agent 会按模板区分成功项、失败项、受影响文件和建议重试或补充输入的最小动作

#### Scenario: 汇报包含下一步路径
- **WHEN** skill 完成或部分完成
- **THEN** 完成汇报会包含用户最可能的下一步动作，例如查看 metadata、重试失败项、补充 key、执行翻译、打开输出目录或运行验证命令

### Requirement: 脚本级诊断和预览
工具型 skill MUST 提供或规划脚本级诊断和预览能力，使 agent 能在执行高影响操作前获得可重复的检查结果。

#### Scenario: 运行 doctor 诊断
- **WHEN** 用户或 agent 运行 `--doctor`
- **THEN** 脚本会检查本地依赖、虚拟环境包、外部命令、关键环境变量和可轻量探测的 endpoint 配置，并输出可用于汇报的诊断结果

#### Scenario: 运行 dry-run 预览
- **WHEN** 用户或 agent 运行 `--dry-run`
- **THEN** 脚本会预览 metadata、播放列表条目、字幕或后端选择、输出路径和风险，不下载媒体、不上传 API、不执行转写

#### Scenario: 高成本执行前清单
- **WHEN** 即将执行付费 API、隐私上传、登录态、cookie、大批量下载或其他高成本步骤
- **THEN** agent 会先展示 dry-run 或等价可审阅清单，说明输入、后端、是否外发、是否付费、已有产物跳过情况和预计输出，并等待用户确认

#### Scenario: 显式用户选择不重复确认
- **WHEN** 用户已经明确指定 audio-only、非默认输出路径或特定后端等选项且不存在覆盖、cookie、登录态、付费 API 或隐私上传风险
- **THEN** agent 不需要为同一明确选择再次停下确认

### Requirement: 显式退化与可恢复运行
工具型 skill MUST 定义缺少工具、凭据或外部能力时的退化路径，并为批量/高成本运行提供可恢复语义。

#### Scenario: 缺工具或未鉴权
- **WHEN** 运行缺少外部命令、Python 包、API key、登录状态或辅助 skill
- **THEN** agent 会给出安装/配置、换后端、跳过阶段或报告阻塞等明确选项，并把状态记录为 `blocked` 或 `skipped`，不得生成空壳产物并汇报成功

#### Scenario: 默认跳过成功项
- **WHEN** 批量运行或重复运行发现已有成功产物和有效 summary
- **THEN** skill 默认复用成功项并只重试失败项；只有用户明确指定 `--force` 或等价选项时才覆盖成功产物

#### Scenario: 运行摘要记录脱敏 argv
- **WHEN** 生成机器可读运行摘要
- **THEN** 摘要会记录工作目录、规范化命令 argv、关键选项、后端选择和关键环境变量是否存在，但不得记录 key、token、cookie 或会话值

### Requirement: 机器可读运行摘要
工具型 skill MUST 为复杂或批量运行提供机器可读运行摘要，作为运行后真相源的一部分。

#### Scenario: 下载运行生成 summary
- **WHEN** `yt-dlp-download` 完成下载、跳过或失败
- **THEN** 运行摘要会记录输入 URL、视频标识、输出路径、字幕选择、缩略图状态、archive 状态、失败项和警告

#### Scenario: 转写运行生成 summary
- **WHEN** `video-transcript` 批量处理多个视频
- **THEN** 运行摘要会聚合每个视频的 `metadata.json` 状态、输出路径、转写来源、翻译状态、失败项和后续动作

#### Scenario: Summary schema 可验证
- **WHEN** 维护者验证机器可读 summary 示例或 schema
- **THEN** 验证会确认必填字段、可选字段、状态枚举、禁止敏感字段和不确定路径标记符合文档契约

### Requirement: 离线验证路径
仓库 MUST 提供维护者可运行的离线验证路径，不需要下载媒体或调用转写 API。

#### Scenario: 维护者验证 skill 结构
- **WHEN** 维护者运行验证路径
- **THEN** 验证会检查可解析元数据、必需文件、Python 语法、脚本 help 输出、schema 示例、reference map 目标文件，以及可行范围内的本地 Markdown 链接

#### Scenario: 验证避免不稳定外部依赖
- **WHEN** 验证在没有 API key 或视频 URL 的干净环境中运行
- **THEN** 它不要求网络访问、付费 API、登录 cookie 或媒体下载

#### Scenario: Windows 友好命令
- **WHEN** README、reference 或验证文档提供用户可复现命令
- **THEN** 它会优先提供 PowerShell 可运行命令，必要时再提供 bash 等其他 shell 版本

### Requirement: 安全与完整性交接
Skill MUST 记录安全边界和输出完整性规则，agent 不得静默绕过这些规则。

#### Scenario: 字幕或转写来源不确定
- **WHEN** 转写或字幕来源是自动生成、缺失、低置信度或后端生成
- **THEN** agent 会保留来源信息，并且不会把它描述成已验证的人工字幕

#### Scenario: 用户请求受限媒体处理
- **WHEN** 请求暗示绕过 DRM、泄露凭据或把 API key 存入 skill 文件
- **THEN** agent 会拒绝该不安全路径，并提供文档化的安全替代方案

### Requirement: 反馈回流
Skill MUST 定义用户反馈后的最小修改流程，避免无谓重跑和事实源漂移。

#### Scenario: 用户反馈定位
- **WHEN** 用户指出输出、summary、文档或运行行为有问题
- **THEN** agent 会先定位反馈层级，修改最小相关文件或产物，更新对应真相源，并说明哪些派生产物需要重建

#### Scenario: 并行执行隔离
- **WHEN** 多个 agent 并行处理批量项、格式项或验证项
- **THEN** 每个 agent 只写自己负责的目录、summary 片段或临时 report，聚合状态由主 agent 汇总
