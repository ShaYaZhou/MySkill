## ADDED Requirements

### Requirement: Web Access 登录工作流
`video-transcript` MUST 在遇到需要登录、动态页面、cookie 或浏览器交互的网站时，提供可调用 Web Access Skill 的受控工作流。

#### Scenario: 检测到网页登录需求
- **WHEN** `video-transcript` 无法直接获取视频、字幕、章节信息或必要截图，且原因是登录、动态页面或 cookie 访问
- **THEN** agent 会进入 Web Access checkpoint，说明目标网站、所需访问内容、脱敏登录态类型、授权范围、隐私风险、本地残留文件和预期产物，并等待用户确认

#### Scenario: 用户确认使用 Web Access
- **WHEN** 用户确认允许调用 Web Access Skill
- **THEN** agent 会按 Web Access Skill 文档执行访问，并将脱敏登录态类型、授权范围、访问时间、抓取到的字幕/视频信息/截图候选、本地残留文件和清理状态写入产物目录下的 `run-manifest.json`

#### Scenario: 禁止记录敏感登录值
- **WHEN** Web Access 运行生成 `run-manifest.json` 或 summary
- **THEN** `run-manifest.json` 不得记录密码、cookie、token、会话值、完整浏览器 profile 敏感路径或私密 HTML 内容

#### Scenario: cookies-from-browser 需要 checkpoint
- **WHEN** `video-transcript` 需要使用 `--cookies-from-browser` 或等价浏览器登录态
- **THEN** agent 必须先通过 Web Access checkpoint 获取用户确认

#### Scenario: 用户拒绝使用 Web Access
- **WHEN** 用户拒绝调用 Web Access Skill 或拒绝提供登录态
- **THEN** `video-transcript` 会继续使用可公开访问的信息，或报告无法完成的部分，不得绕过访问控制

### Requirement: 多格式输出检查点
`video-transcript` MUST 在生成 Markdown 以外的 HTML、PPTX、Word/DOCX、PDF 等产物前提供格式选择 checkpoint。

#### Scenario: 默认 Markdown 输出
- **WHEN** 用户只要求普通转写或未指定额外格式
- **THEN** `video-transcript` 默认生成 Markdown 转写，并不自动生成 HTML、PPTX、Word/DOCX 或 PDF

#### Scenario: 用户选择额外格式
- **WHEN** 用户在格式 checkpoint 中选择 HTML、PPTX、Word/DOCX、PDF 或其组合
- **THEN** agent 会记录所选格式、所需格式 skill、输出路径、公式策略、截图策略和预计后处理步骤

#### Scenario: 初始请求已明确格式
- **WHEN** 用户初始请求已明确要求 HTML、PPTX、Word/DOCX、PDF 或其组合且不存在新的登录、截图、设计或隐私风险
- **THEN** 该格式选择视为已确认，agent 不需要为同一格式选择二次暂停

#### Scenario: 格式 skill 缺失
- **WHEN** 用户选择的输出格式依赖的 docx、pptx、pdf 或 Frontend Design Skill 不可用
- **THEN** agent 会报告缺失 skill、可用降级格式和安装建议，而不是静默生成不完整产物

### Requirement: 内容计划与证据池
`video-transcript` MUST 在复杂摘要、讲义或多格式导出前提供用户可编辑的内容规划层，使派生产物能回链到忠实转写。

#### Scenario: 生成 content-plan
- **WHEN** 用户要求 HTML、PPTX、Word/DOCX、PDF、讲义、摘要、课件，或输入视频较长且需要内容重构
- **THEN** agent 会在转写完成后生成 `content-plan.md`，包含 `section -> beat` 骨架、时间戳、关键论点、公式、截图候选、素材需求、目标格式映射、evidence pool 和 must-keep 清单

#### Scenario: 默认转写不强制 content-plan
- **WHEN** 用户只要求普通公开视频 Markdown 转写
- **THEN** agent 不强制生成 `content-plan.md`，但可以在 summary 中提示它可作为后续富格式增强

#### Scenario: Evidence pool 回链
- **WHEN** 生成 `content-plan.md`
- **THEN** 每个 section 的 evidence pool 会记录时间戳、原句摘录、术语、数字、公式、案例、屏幕状态、置信度或来源说明，便于 Markdown、HTML、PPTX、Word/DOCX 引用或折叠展示

#### Scenario: Must-keep 不可静默丢失
- **WHEN** agent 从转写生成摘要、讲义或任一富格式产物
- **THEN** 关键数字、公式、具体案例、限制条件、反方观点、例外情况和操作步骤必须进入 must-keep 清单；若目标格式无法容纳，agent 必须记录压缩或降级原因，而不是静默删除

#### Scenario: Content plan 边界
- **WHEN** agent 编写 `content-plan.md`
- **THEN** 该文件只规划内容结构、保留/压缩策略、证据回链、素材需求和格式映射，不写死 PPT 版式、HTML/CSS、DOCX 样式或具体视觉实现

#### Scenario: Content plan 完成前自检
- **WHEN** `content-plan.md` 生成完毕
- **THEN** agent 会先检查 section/beat 完整性、evidence pool 回链、must-keep 覆盖、公式条目、截图候选、素材需求和格式映射；可修复问题先修复，再进入富格式导出或用户确认

### Requirement: 数学公式保留
`video-transcript` MUST 在 Markdown、HTML、PPTX、Word/DOCX 和 PDF 输出中尽力保留数学公式语义，并记录任何格式降级。

#### Scenario: Markdown 公式
- **WHEN** 生成 Markdown 转写
- **THEN** 行内公式使用 `$...$`，块级公式使用 `$$...$$`，保留公式上下文说明，并避免把货币符号或普通文本误标为公式

#### Scenario: HTML 公式
- **WHEN** 生成 HTML 输出
- **THEN** HTML 会使用 MathJax、KaTeX 或等价机制渲染公式，记录本地包或 CDN 依赖，并保留源 LaTeX 以便后续编辑或调试

#### Scenario: PPTX 或 Word 公式
- **WHEN** 生成 PPTX 或 Word/DOCX 输出
- **THEN** DOCX 优先使用 OMML/MathML 或 docx Skill 的可编辑公式能力，PPTX 默认允许高分辨率公式图片 fallback；任何 fallback 都必须在 `run-manifest.json` 中记录源 LaTeX、alt text、降级原因和验证结果

#### Scenario: PDF 公式
- **WHEN** 生成 PDF 输出
- **THEN** PDF 中的公式必须可读，并在 `run-manifest.json` 中记录 PDF 是由 HTML、PPTX、Word/DOCX 或其他源格式渲染生成；本轮默认 PDF 为派生导出，不作为首选直接生成格式

### Requirement: 关键截图检查点
`video-transcript` MUST 提供可选截图 checkpoint，用于捕捉无法通过文字、数学公式或自绘素材充分表达的关键内容。

#### Scenario: 识别截图候选
- **WHEN** 转写内容包含物理效果展示、工业设计关键绘制步骤、实验现象、软件界面状态或其他难以文字化的讲解点
- **THEN** agent 会生成截图候选清单，包含时间戳、原因、用途、替代文字和可能的隐私/版权风险

#### Scenario: 用户确认截图
- **WHEN** 用户确认要在关键内容处增加截图
- **THEN** agent 会抓取或导入对应截图，保存到产物目录，并在 `run-manifest.json` 中记录截图路径、来源时间戳、说明和引用到的输出格式

#### Scenario: 截图安全边界
- **WHEN** 截图来自登录、付费、受版权保护或含敏感信息的视频/页面
- **THEN** agent 必须遵循最小必要原则，记录授权来源、外发限制和处理方式，不得绕过 DRM、水印、付费限制或访问控制，默认不嵌入私密登录页信息

#### Scenario: 截图去重和数量控制
- **WHEN** agent 生成截图候选清单
- **THEN** 清单会合并重复候选，并要求每张截图都有明确用途、替代文字和必要性说明

#### Scenario: 用户跳过截图
- **WHEN** 用户选择不增加截图
- **THEN** agent 会继续生成纯文字、公式或自绘示意版本，并在 summary 中记录截图阶段已跳过

### Requirement: 素材治理与反伪规则
`video-transcript` MUST 在截图、多格式或设计阶段维护素材清单，并禁止无来源或误导性的伪素材进入产物。

#### Scenario: 生成素材清单
- **WHEN** 运行包含截图、多格式导出、Frontend Design 或 AI/代码绘制素材
- **THEN** `run-manifest.json` 会包含 `assets[]` 或引用 `assets.md/json`，每项记录 id、类型、来源 URL/时间戳/路径、授权或外发限制、用途、引用位置、alt text 和状态

#### Scenario: 素材类型区分
- **WHEN** agent 记录素材
- **THEN** 素材类型至少区分 `source-screenshot`、`user-provided`、`code-drawn`、`ai-generated`、`placeholder`、`formula-render`，并不得把 AI 生成素材或 code-drawn 示意标记为真实来源截图

#### Scenario: Code-drawn 替代截图
- **WHEN** 截图受限、版权不清或内容可抽象表达
- **THEN** agent 会优先考虑 CSS/SVG/Canvas/JS、Office drawing 或等价机制绘制流程图、对比图、公式推导图或界面状态示意，并在 `run-manifest.json` 中标记为 `code-drawn`

#### Scenario: Placeholder 规范
- **WHEN** 必要素材缺失且用户未提供
- **THEN** agent 会使用保留真实比例的 placeholder，显示素材类型、建议尺寸、缺失原因和替换说明，并在完成汇报中列为待补素材

#### Scenario: 禁止伪造真实材料
- **WHEN** agent 生成或选择素材
- **THEN** agent 不得编造截图、logo、数据、用户数、实验结果、产品界面或来源证据；AI 生成素材只能作为概念性插画或抽象辅助，并必须记录生成来源、用途和发布风险

### Requirement: Frontend Design Skill 设计检查点
`video-transcript` MUST 在生成面向展示或发布的 HTML、PPTX、Word/DOCX 内容前，提供是否调用 Frontend Design Skill 的设计检查点。

#### Scenario: 默认朴素模板
- **WHEN** 用户选择 HTML、PPTX 或 Word/DOCX 但未要求视觉设计
- **THEN** agent 使用默认可读模板生成内容，不强制调用 Frontend Design Skill

#### Scenario: 用户确认调用 Frontend Design
- **WHEN** 用户确认需要 Frontend Design Skill
- **THEN** agent 会生成设计 brief，说明受众、输出格式、版式目标、公式和截图处理规则、禁用的装饰性伪素材，以及验收清单

#### Scenario: 设计完成后自检
- **WHEN** Frontend Design Skill 参与了 HTML、PPTX 或 Word/DOCX 产物生成
- **THEN** agent 会检查公式可读性、截图引用、层级结构、文本不溢出、不遮挡、对比度、截图来源、无伪素材、移动/打印或演示适配性，并将检查结果写入 summary

#### Scenario: 设计产物渲染检查
- **WHEN** Frontend Design Skill 参与生成 HTML、PPTX、Word/DOCX 或 PDF
- **THEN** HTML 需要桌面/移动截图检查，PPTX、Word/DOCX、PDF 需要渲染为页面或幻灯片图后检查版式和公式清晰度

### Requirement: 富格式 Anchor 验收
`video-transcript` MUST 在复杂 HTML、PPTX、Word/DOCX 富格式产物批量生成前提供首个可验收样板。

#### Scenario: 生成首个 anchor
- **WHEN** 用户选择 HTML、PPTX 或 Word/DOCX 且启用设计、截图、复杂公式或发布型输出
- **THEN** agent 会先生成可验收 anchor：HTML 首屏或首个章节、PPTX 前 2-3 页、Word/DOCX 前 1-2 页，并完成渲染 QA 后暂停给用户验收

#### Scenario: Anchor 不可跳过
- **WHEN** 用户选择逐段验收、顺序生成后统一验收或并行生成
- **THEN** 首个富格式 anchor 仍由主 agent 先完成并等待用户验收，除非用户明确要求只生成朴素草稿且接受后续返工风险

#### Scenario: Anchor 验收项
- **WHEN** agent 请求用户验收富格式 anchor
- **THEN** agent 会列出内容忠实、章节结构、公式清晰度、素材来源、placeholder、截图必要性、版式溢出、目标受众和是否继续当前模式等检查项

#### Scenario: QA 证据
- **WHEN** agent 完成富格式 anchor 或最终富格式产物
- **THEN** HTML 桌面/移动截图、PPTX/Word/DOCX/PDF 页面或幻灯片渲染图、viewport、页码/slide 编号、检查结果和失败证据路径会写入 `run-manifest.json`

### Requirement: 多格式运行 Manifest
`video-transcript` MUST 为多格式、截图或 Web Access 运行在产物目录生成 `run-manifest.json`，用于记录决策、产物和自检状态；每视频 `metadata.json` 是转写事实源，`run-manifest.json` 是单次运行聚合事实源。Skill 根目录的 `manifest.json` 若存在，只能作为分发元数据，不能与运行事实源混用。

#### Scenario: 生成多格式 run manifest
- **WHEN** 运行包含 Web Access、截图、HTML、PPTX、Word/DOCX、PDF 或 Frontend Design 任一可选阶段
- **THEN** `run-manifest.json` 会记录 run id、输入 URL、引用到的每视频 `metadata.json`、`content-plan.md` 路径、脱敏授权范围、选定/跳过/失败格式、每个输出文件路径和 hash、公式降级条目、素材条目、截图条目、设计检查结果、渲染 QA 证据、脱敏 argv、隐私/版权处理、工具版本、失败项和后续动作

#### Scenario: 真相源字段归属
- **WHEN** `metadata.json` 与 `run-manifest.json` 都存在
- **THEN** 转写来源、语言、原文路径和翻译状态归属每视频 `metadata.json`；内容结构和证据回链归属 `content-plan.md`；导出格式、截图、素材、Web Access、设计检查、输出 hash 和批量运行状态归属 `run-manifest.json`

#### Scenario: 派生产物一致性
- **WHEN** Markdown/HTML/PPTX/Word/DOCX/PDF 同时存在
- **THEN** agent 会校验章节数、标题、术语、公式源、截图/素材引用、hash 和降级项与 `metadata.json`、`content-plan.md`、`run-manifest.json` 一致；格式之间可调整版式，但不得改变事实或遗漏 must-keep 项

#### Scenario: 完成前自检
- **WHEN** 所有选定格式生成完毕
- **THEN** agent 会依据 `run-manifest.json` 检查每个格式文件存在、公式可读、截图和素材引用有效、placeholder 已显式标注、设计检查完成、QA 证据存在，并在失败项修复或明确阻塞后再汇报完成

### Requirement: 付费外发 Dry-run 闸门与显式退化
`video-transcript` MUST 在付费、外发、登录态或高成本阶段执行前提供可审阅计划，并在依赖缺失时给出显式退化路径。

#### Scenario: 生成可审阅 dry-run 清单
- **WHEN** 运行即将使用 API 上传、付费后端、Web Access、浏览器登录态、批量播放列表、多格式渲染或截图抓取
- **THEN** agent 会先生成 dry-run 计划，列出每个输入 URL、预计后端、是否下载或上传、可能分片数、已有产物是否跳过、是否外发、是否付费、所需工具/skill、预计输出和风险，并等待用户确认

#### Scenario: 缺工具或未鉴权
- **WHEN** 缺少 `ffmpeg`、API key、Web Access、docx/pptx/pdf skill、Frontend Design Skill 或其他必需依赖
- **THEN** agent 会给出安装/配置、换后端、跳过该阶段等显式选项，把该阶段状态写为 `blocked` 或 `skipped`，不得生成空壳产物并汇报成功

#### Scenario: 可恢复运行
- **WHEN** 批量运行中已有成功产物、失败项和待跳过项
- **THEN** 默认复用已有 `metadata.json`、`content-plan.md` 和输出文件，只重试失败项；只有用户显式指定 `--force` 或等价选项时才覆盖成功产物

### Requirement: 反馈回流与并行隔离
`video-transcript` MUST 定义用户反馈、reviewer 复核和并行 agent 执行时的最小修改与文件隔离规则。

#### Scenario: 用户反馈回流
- **WHEN** 用户反馈转写、内容计划、公式、截图/素材、设计或格式导出存在问题
- **THEN** agent 会先判定反馈层级，修改最小产物切片，更新对应 `metadata.json`、`content-plan.md` 或 `run-manifest.json`，并汇报修改了什么和哪些派生产物需要重建

#### Scenario: Reviewer handoff
- **WHEN** agent 使用 reviewer、Agent Teams 或 subagent 复核产物
- **THEN** handoff 会包含产物路径、真相源、检查清单、风险边界、禁止修改范围，并要求 reviewer 输出 pass/fail、证据、建议和是否阻塞

#### Scenario: 并行写入隔离
- **WHEN** 多个 agent 并行处理多个视频、多个格式或多个辅助阶段
- **THEN** 每个 agent 只写自己的视频目录、格式子目录或临时 report，不直接修改聚合 `run-manifest.json`；主 agent 负责汇总并解决冲突

### Requirement: Web-video 风格的阶段化但轻量检查点
`video-transcript` MUST 借鉴 `web-video-presentation` 的阶段化协作方式，但只在高影响或可选产物阶段停顿确认。

#### Scenario: 生成转写计划
- **WHEN** 输入视频需要登录访问、多格式输出、截图或设计介入
- **THEN** agent 会先生成一次性计划，列出访问方式、输出格式、`content-plan.md` 是否生成、截图候选策略、素材策略、设计选项、成本/隐私风险、默认推荐和用户只需回复的最短选项，让用户一次确认关键选择，避免为同一选择重复停顿

#### Scenario: 默认简单转写
- **WHEN** 输入是公开视频且用户只要求 Markdown 转写
- **THEN** agent 不会强制进入多轮 checkpoint，而是直接执行默认转写流程

#### Scenario: 普通转写不主动截图确认
- **WHEN** 输入是公开视频且用户只要求 Markdown 转写
- **THEN** agent 不会在转写后主动打断用户要求截图确认，只会在 summary 中提示可作为后续增强
