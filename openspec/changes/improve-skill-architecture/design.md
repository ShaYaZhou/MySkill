## 背景

当前仓库包含两个工具型 skill：

- `yt-dlp-download`：一个紧凑的 `yt-dlp` 下载封装，包含 `SKILL.md`、一个 Python 辅助脚本和 OpenAI agent 元数据。
- `video-transcript`：一个更复杂的视频转写封装，包含多后端回退、metadata 输出和更复杂的运行策略。

这两个 skill 都有价值，但结构上主要还是围绕单个脚本的线性说明。相比之下，`web-video-presentation` 是一个工作流型 skill：它把入口说明与深度 reference 分离，携带模板和可复用资产，定义产物契约，并通过硬检查点与自检协议保持长流程 agent 工作不跑偏。

本设计会选择性借鉴这些模式。下载和转写工具不需要主题系统、Vite 脚手架或章节级编排，但它们会受益于更清晰的契约、验证路径和维护约定。

## 目标 / 非目标

**目标：**

- 建立分层 skill 结构，同时适配小型工具 skill 和大型工作流 skill。
- 让 `SKILL.md` 成为简洁的路由入口；只有在有帮助时，才把长期稳定的细节移入专用 reference。
- 定义输出契约、验证预期、失败交接和跨 agent 元数据预期。
- 增加工具型 skill 的可诊断性和可预览性，例如 `--doctor`、`--dry-run` 和机器可读运行摘要。
- 把 reference map、schema、示例和可复现命令纳入离线验证，降低文档漂移。
- 定义可恢复运行、显式退化、reviewer handoff 和用户反馈回流的共享规则。
- 在不破坏既有命令行行为的前提下改进现有两个 skill；允许新增向后兼容的 CLI flags、summary 和验证入口。
- 形成可维护、可增量实现的 OpenSpec 任务列表。

**非目标：**

- 不把完整的 `web-video-presentation` 脚手架模型导入每个 skill。
- 不重写 Python 辅助脚本；只允许小范围修复具体 bug 或新增向后兼容的诊断、预览、summary 能力。
- 不为了文档结构而新增外部运行时依赖。
- 不强制每个 skill 都拥有模板、示例或 manifest，除非它们确实有价值。
- 不引入主题系统、CSS 变量体系、skill 调用链 registry 或组合型 pipeline skill；这些如有需要应作为独立 change 讨论。

## 决策

1. 使用分层 skill 架构，而不是一刀切目录布局。

   每个 skill 必备：`SKILL.md`；需要执行时在 `scripts/` 下放可运行资产；在 `agents/` 下放 agent 元数据；根 README 中有清晰条目。

   按需可选：

   - `references/`：放长期策略、回退矩阵、输出契约、自检清单或故障排查。
   - `templates/`：放 skill 会复制或生成的文件。
   - `examples/`：在有助于澄清边界场景时，放样例输入/输出。
   - `manifest.json`：放跨 agent 分发元数据。

   对 `yt-dlp-download` 这类小型单脚本 skill，如果 `SKILL.md` 仍能快速阅读，可以先保留单入口文档，只补输出契约和自检段落；对 `video-transcript` 这类复杂度更高的 skill，再拆少量聚焦 reference。

   备选方案：要求每个 skill 都镜像 `web-video-presentation`。拒绝原因：这会让简单工具 skill 变得嘈杂且更难维护。

2. 把 `SKILL.md` 视为入口和 reference 地图。

   `SKILL.md` 应告诉 agent 何时调用 skill、默认命令路径、最安全的策略选择，以及遇到复杂情况时该读哪个 reference。skill 变复杂后，不应把所有后端细节都堆在 `SKILL.md` 中。

   备选方案：所有指导都保留在 `SKILL.md`。拒绝原因：`video-transcript` 已经把日常流程、后端矩阵、故障排查和后处理交接混在一个长文件里。

3. 显式化产物契约。

   每个 skill 都应说明它会创建什么、默认写到哪里、持久化哪些状态，以及脚本退出后 agent 必须做什么后续动作。对转写 skill 来说，这包括 `original.md`、`zh.md`、`metadata.json` 和 `needs_zh_translation`。对下载 skill 来说，这包括媒体文件、字幕、缩略图、临时文件和 archive 文件。

   备选方案：只依赖辅助脚本作为事实来源。拒绝原因：agent 在执行前后都需要人类可读的契约。

4. 把验证作为仓库维护的一部分。

   轻量验证路径应检查 skill 元数据、可行范围内的 Markdown 链接完整性、reference map 目标文件、YAML 语法、schema 示例、Python 语法和脚本 help 输出，并且不要求网络调用或真实媒体下载。reference map 不是装饰性目录，而是 agent 路由表；缺失文件、过期链接、占位 registry、示例被误标为真实产物、明显 `TODO` 占位状态都应作为维护失败项暴露。

   备选方案：加入针对公开视频 URL 的完整集成测试。拒绝原因：作为常规验证它太慢、不稳定且依赖网络。

5. 增加脚本级诊断和预览能力。

   两个工具型 skill 都应优先支持 `--doctor` 和 `--dry-run`。`--doctor` 用于检查本地依赖、外部命令、关键环境变量和 endpoint 配置；`--dry-run` 用于解析 metadata、预览播放列表、字幕/后端选择、输出路径和风险，不下载媒体、不上传 API、不执行转写。

   备选方案：只把这些检查写进文档。拒绝原因：agent 需要可重复执行的诊断结果，不能完全依赖临场判断。

6. 让机器可读摘要成为运行后真相源的一部分。

   `video-transcript` 已有每视频 `metadata.json`，可按需增加聚合型 `transcript-summary.json`。`yt-dlp-download` 缺少等价产物，应增加 `download-summary.json` 或同等 report，用于记录成功、失败、跳过、输出路径、字幕、缩略图、archive 状态和警告。summary schema 应像 `web-video-presentation` 的 token 契约一样区分必填字段、可选字段和禁止记录字段；例如转写状态中的 `source_type`、`backend`、`language_state`、`needs_zh_translation`、`privacy_gate`，以及下载状态中的 `media`、`subtitle`、`thumbnail`、`archive_skip`、`partial_failure`、`uncertain_path`。

   备选方案：只检查输出目录。拒绝原因：目录扫描难以稳定还原失败项、跳过项、字幕选择和警告。

7. 让检查点与 skill 风险成比例。

   `web-video-presentation` 需要硬检查点，因为它执行创造性、多阶段生产。工具型 skill 只需要更小的条件式检查点：使用浏览器 cookie 前、多后端可选且可能使用付费/转写 API 前，以及脚本输出后需要人工翻译或重试时。

   备选方案：每个阶段前都要求用户确认。拒绝原因：这会让简单下载/转写请求变得烦琐。

8. 自检必须有本地兜底，独立 reviewer 只是增强。

   当前 agent 必须能按清单完成本地自检；当环境支持 Agent Teams 或 subagent 时，可以把独立 reviewer 作为增强检查产物、summary 和失败项。reviewer handoff 应包含产物路径、真相源、检查清单、风险边界、禁止修改范围，并要求 reviewer 输出 pass/fail、证据、建议和是否阻塞。该机制借鉴 `web-video-presentation` 的隔离复核，但不要求所有环境都具备并行 agent 能力。

   备选方案：强制每次都开独立 agent。拒绝原因：工具环境不一定支持，且简单下载/转写不应被重型流程阻塞。

9. 让工具型 skill 支持可恢复运行和显式退化。

   批量或高成本运行应默认跳过已有成功产物、只重试失败项，并在用户显式指定 `--force` 或等价选项时才覆盖。缺少依赖、凭据、外部 skill 或鉴权时，agent 应进入显式退化菜单：安装/配置、换后端、跳过阶段或报告阻塞。运行摘要应记录脱敏 argv、工作目录、关键选项、后端选择和环境变量存在性，但不得记录 key、token、cookie 或会话值。

   备选方案：失败后只在自然语言里解释。拒绝原因：可恢复和可复现是批量视频任务的基本可靠性要求。

10. 反馈回流遵循最小切片原则。

   用户对产物提出反馈时，agent 应先定位层级：输入理解、后端选择、转写、下载、字幕、输出契约、summary、文档或安装能力；然后只修改最小相关文件，更新对应真相源或 summary，并汇报改了什么。不要因为一个字段错误重做整个运行或整套文档。

   备选方案：把反馈视为重跑整个 skill。拒绝原因：这会增加成本、覆盖风险和用户等待时间。

## 风险 / 取舍

- [风险] 文档增长快于行为变化 -> 保持 `SKILL.md` 简洁，只把稳定细节移入 references。
- [风险] 验证对个人 skill 迭代过于严格 -> 先从结构性和离线检查开始，网络 smoke test 保持可选。
- [风险] 跨 agent 元数据漂移 -> 增加根维护清单，并验证已知 `agents/*.yaml` 文件。
- [风险] 特定后端的转写指导过期 -> 将后端矩阵隔离到 references 中，便于独立审查。
- [风险] 可选 manifest 造成重复元数据 -> 将 manifest 视为分发元数据，而不是运行真相源。
- [风险] `download-summary.json` 的真实文件路径不准确 -> 优先使用 `yt-dlp` 的机器可读输出或 after-move 路径事件，无法可靠获取时在 summary 中标记不确定性。
- [风险] `--doctor` 被误认为能保证外部服务可用 -> 明确它只检查本地依赖、凭据可见性和轻量 endpoint 探测，不承诺第三方服务成功。
- [风险] README 或 reference map 链接漂移 -> 将本地链接和 schema 示例纳入离线验证，并把缺失链接作为阻断级维护问题。
- [风险] POSIX 示例在 Windows 环境不可用 -> 用户可复现命令优先给 PowerShell 版本，必要时再给 bash 版本。
- [风险] 示例膨胀成模板库 -> examples 只作为契约样例和边界样例，标注用途、体量上限和不要照搬。

## 迁移计划

1. 增加仓库级约定和验证指导。
2. 先重构 `video-transcript` 文档，因为它的运行复杂度最高。
3. 用更小的 reference 集重构 `yt-dlp-download` 文档。
4. 增加轻量验证工具并在本地运行，覆盖 reference map、schema 示例和 PowerShell 友好命令。
5. 更新 README 文档，加入新的维护工作流、可复现验证命令和失败时的退化说明。

回滚以文档为主：回退新增 references 和验证文档；如已新增向后兼容 CLI flags，可保留不影响既有调用，或按需回退相关小 patch。

## 未决问题

- `manifest.json` 本轮先作为轻量分发元数据 schema；两个现有 skill 是否实际新增文件，取决于安装/分发流程是否消费它。
- 示例应放在 `examples/`，还是为了与大型 skill 保持一致而放在 `references/EXAMPLES/`？
- 验证应只作为根脚本存在，还是每个 skill 都暴露自己的 `scripts/validate.*` 入口？
