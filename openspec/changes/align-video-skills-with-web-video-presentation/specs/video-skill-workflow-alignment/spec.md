## ADDED Requirements

### Requirement: 视频类 Skill 入口对齐
`video-transcript` 和 `yt-dlp-download` 必须 使用一致的轻量 workflow skill 入口结构，使 agent 首次读取 `SKILL.md` 时即可理解默认命令、安全边界、输出事实源、checkpoint 摘要和 reference map。

#### Scenario: 入口包含核心字段
- **当** agent 首次读取任一视频类 skill 的 `SKILL.md`
- **则** `SKILL.md` 必须 包含用途、默认命令、默认输出目录、快速策略、常用选项、输出契约、引用地图、checkpoint 摘要和完成检查

#### Scenario: 入口保持轻量
- **当** 某个流程细节超过入口快速阅读范围
- **则** `SKILL.md` 必须 将细节路由到 `references/`，并保留何时读取该 reference 的一句话说明

#### Scenario: 不复制 web-video-presentation 专属机制
- **当** 对齐 `web-video-presentation` 的做法
- **则** 两个视频类 skill 必须 只继承阶段化、checkpoint、anchor、自检和事实源纪律，不得引入 Vite/React、主题系统、录屏、章节 stepper 或旁白合成等专属机制

### Requirement: 阶段化 Reference Map
`video-transcript` 和 `yt-dlp-download` 必须 提供按阶段读取的 reference map，而不是只列出文件名。

#### Scenario: video-transcript 阶段索引
- **当** `video-transcript` 请求涉及默认转写、后端选择、Web Access、content-plan、格式选择、截图/素材、Frontend Design、anchor、完整生成、QA、run-manifest 或反馈续跑
- **则** reference map 必须 指向对应阶段的唯一或主入口 reference，并说明触发条件

#### Scenario: yt-dlp-download 阶段索引
- **当** `yt-dlp-download` 请求涉及默认下载、dry-run/download plan、cookie/Web Access、大型播放列表、覆盖/force、失败恢复或 summary 自检
- **则** reference map 必须 指向对应 reference，并说明是否需要 checkpoint

#### Scenario: Reference 链接完整
- **当** reference 文件被新增、重命名、合并或删除
- **则** `SKILL.md`、README、examples 和验证脚本中的本地链接 必须 同步更新，缺失链接 必须 视为验证失败

### Requirement: 风险触发式 Checkpoint
两个视频类 skill 必须 借鉴 `web-video-presentation` 的硬 checkpoint，但只在高影响、高成本或可选增强阶段停顿确认。

#### Scenario: 轻量路径不打断
- **当** 用户请求公开视频默认下载，或请求公开视频 Markdown 转写且已有人工字幕、无覆盖、无登录态、无外发和无富格式需求
- **则** agent 必须 直接执行默认轻量路径，不得引入重型 checkpoint 打断用户

#### Scenario: 高影响阶段必须计划确认
- **当** 请求涉及浏览器 cookie、登录态、Web Access、API 上传、付费外发、大型播放列表、覆盖成功产物、截图、素材、多格式、Frontend Design 或富格式 QA
- **则** agent 必须 先展示计划或 dry-run 摘要，说明输入范围、输出目录、事实源、风险、可选退化路径和是否继续，并等待用户确认

#### Scenario: 一次对齐多个决策
- **当** 一个任务同时涉及多个高影响选择
- **则** agent 必须 借鉴 `web-video-presentation` 的一次对齐方式，把相关决策合并成一个 checkpoint，避免为同一选择重复停顿

### Requirement: Download Plan Anchor
`yt-dlp-download` 必须 为大型、登录态、覆盖或不确定下载提供 download plan anchor，用小范围可审阅计划替代直接全量执行。

#### Scenario: 大型播放列表计划
- **当** 输入是大型播放列表、多个 URL 或预计生成大量文件
- **则** agent 必须 先运行或生成 dry-run download plan，展示条目数、建议范围、输出模板、archive 命中、字幕/缩略图策略、cookie 风险、预计失败退路和是否全量继续

#### Scenario: 首条或首批 anchor
- **当** 用户需要确认命名、字幕语言、缩略图、格式或 archive 行为
- **则** agent 必须 先用首条或首批条目作为 anchor 计划或试跑结果，用户确认后再全量执行

#### Scenario: Force 覆盖计划
- **当** 用户请求 `--force` 或等价覆盖成功产物
- **则** agent 必须 在执行前列出会覆盖或重跑的范围、可能重复下载的项目、archive 影响和恢复方式

### Requirement: 富格式 Anchor 与设计边界
`video-transcript` 必须 在富格式、截图、素材、设计或发布型输出中使用可验收 anchor，同时明确脚本和 agent workflow 的职责边界。

#### Scenario: 富格式 anchor
- **当** 用户选择 HTML、PPTX、Word/DOCX 或 PDF 且启用设计、截图、复杂公式、素材或发布型输出
- **则** agent 必须 先生成可验收 anchor：HTML 首屏或首章、PPTX 前 2-3 页、Word/DOCX 前 1-2 页，完成渲染 QA 后暂停给用户验收

#### Scenario: HTML 输出边界
- **当** 用户要求额外生成 HTML
- **则** `video-transcript` reference 必须 明确 HTML 目录、首屏 anchor 要素、移动/桌面 QA、公式渲染、素材 id 引用、禁止伪素材和 `run-manifest.json` 写入点

#### Scenario: 脚本与 agent workflow 边界
- **当** 文档描述 HTML、PPTX、Word/DOCX、PDF、截图、素材或 Frontend Design 阶段
- **则** 文档 必须 明确 `scripts/transcript.py` 负责转写母本，富格式阶段由 agent 与相关 skill 按 reference workflow 执行，除非脚本实际已经实现该格式导出

### Requirement: 事实源分层
两个视频类 skill 必须 明确分发 metadata 与运行事实源的边界，并避免 `run-summary.json`、`run-manifest.json`、`metadata.json` 和 `download-summary.json` 语义漂移。

#### Scenario: Skill manifest 仅用于分发
- **当** skill 根目录存在 `manifest.json`
- **则** 它 必须 只描述分发元数据、依赖和兼容性，不得记录真实 URL、用户输入、登录态、输出路径或单次运行状态

#### Scenario: video-transcript 事实源
- **当** `video-transcript` 只执行普通 Markdown 转写
- **则** 每视频事实源 必须 是 `metadata.json`，批量轻量摘要 可以 使用 `run-summary.json`

#### Scenario: video-transcript 富格式事实源
- **当** `video-transcript` 运行包含 Web Access、截图、素材、多格式、Frontend Design、anchor、渲染 QA 或高成本阶段
- **则** 产物目录 必须 生成 `run-manifest.json`；`run-summary.json` 只能作为轻量批处理摘要，不得承载富格式决策事实

#### Scenario: yt-dlp-download 事实源
- **当** `yt-dlp-download` 完成或计划一次下载运行
- **则** `download-summary.json` 必须 是下载结果唯一运行事实源，终端输出不得替代 summary 汇报成功

### Requirement: Download Summary Schema 一致性
`yt-dlp-download` 必须 保持 reference、examples 和脚本实际 `download-summary.json` 字段一致。

#### Scenario: Summary 字段一致
- **当** `yt-dlp-download` 文档展示 `download-summary.json` schema 或 example
- **则** 字段名、状态 token、嵌套结构和脚本实际输出 必须 一致，包括媒体路径、字幕状态、缩略图状态、archive skip、dry-run 计划、失败项和 warnings

#### Scenario: 不确定路径
- **当** 输出路径来自 glob、yt-dlp 推断或无法稳定确认
- **则** `download-summary.json` 必须 标记 `uncertain_path` 或等价状态，不得把不确定路径汇报为已验证文件

#### Scenario: 失败项恢复信息
- **当** 下载项失败、部分失败或被阻塞
- **则** `download-summary.json` 必须 包含错误、阻塞原因、最小下一步、是否可重试、是否需要 cookie/ffmpeg/update/force/audio-only 等建议

### Requirement: 自检与 Reviewer Handoff
两个视频类 skill 必须 对关键产物执行“自检 → 修复 → 再汇报”的闭环，必要时可交给 reviewer 或 subagent 质检。

#### Scenario: 关键产物自检
- **当** 生成 `metadata.json`、`run-summary.json`、`download-summary.json`、`content-plan.md`、`run-manifest.json`、富格式 anchor 或最终富格式产物
- **则** agent 必须 按对应 reference 的自检清单验证；发现可修复失败项时 必须 先修复再汇报完成

#### Scenario: Reviewer handoff
- **当** agent 使用 reviewer、Agent Teams 或 subagent 质检
- **则** handoff 必须 包含产物路径、事实源路径、检查清单、禁止读取 secret 的边界、禁止修改范围，并要求返回 pass/fail、证据、建议和是否阻塞

#### Scenario: 失败不得冒充完成
- **当** 缺工具、缺授权、缺文件、缺 QA 证据、summary 不可解析、素材伪装真实来源或状态不确定
- **则** agent 必须 将阶段标记为 `blocked`、`failed`、`partial_failure`、`skipped` 或等价状态，不得汇报为成功

### Requirement: 素材与反伪规则统一
`video-transcript` 必须 保持素材反伪规则；`yt-dlp-download` 必须 使用同等诚实原则记录下载事实，不伪造成功。

#### Scenario: video-transcript 素材类型
- **当** `video-transcript` 在 HTML、PPTX、Word/DOCX、PDF 或设计阶段使用素材
- **则** 素材 必须 区分 `source-screenshot`、`user-provided`、`code-drawn`、`ai-generated`、`placeholder`、`formula-render`，并记录来源、用途、alt text、授权或外发限制

#### Scenario: AI 生成素材
- **当** 使用 AI 生成素材
- **则** 该素材 必须 只作为概念插画或抽象辅助，记录生成来源、prompt 摘要、用途和发布风险，不得冒充真实截图、真实产品界面、真实实验结果、logo、数据图或证据画面

#### Scenario: yt-dlp-download 不伪造下载事实
- **当** 字幕、缩略图、媒体文件、archive skip 或登录态下载失败或不可确定
- **则** `yt-dlp-download` 必须 在 summary 中如实记录缺失、跳过、阻塞或不确定状态，不得用空壳路径或口头描述冒充成功

### Requirement: 离线验证与跨 Agent 安装
对齐后的两个视频类 skill 必须 通过离线验证，并重新安装到支持的 agent 目录。

#### Scenario: 仓库离线验证
- **当** 实现此 change 后
- **则** `py -3 .\scripts\validate_repo.py` 必须 通过，并覆盖 frontmatter、agent metadata、manifest/example JSON、reference map、本地 Markdown 链接、Python 语法、脚本 `--help` 和敏感字段检查

#### Scenario: OpenSpec 状态验证
- **当** change artifacts 创建完成
- **则** `openspec status --change align-video-skills-with-web-video-presentation` 必须 显示 proposal、design、specs、tasks 全部完成

#### Scenario: 脚本离线探针
- **当** skill 文档或脚本契约被更新
- **则** `video-transcript/scripts/transcript.py --help`、`yt-dlp-download/scripts/download.py --help`、必要的 `--doctor` 和不外发的 `--dry-run` 探针 必须 可在无 API key、无 cookie、无媒体下载的安全条件下运行或被明确跳过并说明原因

#### Scenario: 跨 Agent 安装
- **当** 更新通过验证
- **则** 更新后的 `video-transcript` 和 `yt-dlp-download` 必须 重新安装到 Claude、Codex、Cursor、Mavis 的 skill 目录，或在维护报告中说明未安装目标和原因

