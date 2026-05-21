## 背景

本仓库面向 Claude、Codex、Cursor 和 Mavis 管理个人 AI skills。目前 README 已列出安装目标，但没有定义跨 agent 的必装能力包，也没有验证安装是否一致。本轮先治理 Claude、Codex、Cursor 三端；Mavis 保留为既有安装目标，但不进入本次必装包矩阵。与此同时，`video-transcript` 仍主要产出 Markdown 转写；当视频来自需要登录的网站、内容包含复杂数学/物理/工业设计画面、或用户希望生成 HTML/PPTX/Word/DOCX 等更完整材料时，现有流程缺少可控的检查点和辅助 skill 调用协议。

`web-video-presentation` 的核心可借鉴点不是网页模板本身，而是阶段化工作流、强制 checkpoint、产物自检和“先对齐再制作”的协作纪律。本设计将这些纪律降级应用到 `video-transcript`：默认转写仍可快速执行；只有登录、截图、多格式输出、视觉设计等高影响或高成本选项触发时才暂停确认。

本变更在实现顺序上依赖 `improve-skill-architecture` 的共享约定：瘦入口、reference map、机器可读 summary/schema、dry-run、显式退化、自检和反馈回流。先完成共享基础，再把本变更落成 `video-transcript` 的具体文档、模板和 schema，可避免重复定义运行事实源和 checkpoint 规则。

## 目标 / 非目标

**目标：**

- 为 Claude、Codex、Cursor 定义统一能力 skill 包，并提供安装、同步和验证规则。
- 定义安装包清单和锁定文件，使外部 skill 的来源、版本、调用名、验证探针和状态可审计。
- 让 `video-transcript` 在需要网页登录时能够安全调用 Web Access Skill，并保留登录/隐私边界。
- 让复杂或多格式导出先经过用户可编辑的 `content-plan.md`，把忠实转写、内容重构和格式导出解耦。
- 为章节/段落建立 evidence pool、must-keep 清单和内容粒度映射，降低摘要和多格式导出的事实丢失风险。
- 让 `video-transcript` 的 Markdown、HTML、PPTX、Word/DOCX 等输出保留数学公式语义。
- 增加关键截图 checkpoint，捕捉无法用文字、数学公式或自绘素材充分表达的关键讲解点。
- 增加多格式输出 checkpoint，并在需要时调用 Frontend Design Skill 设计 HTML/PPTX/Word/DOCX 的视觉呈现。
- 增加素材治理、反伪素材规则、首个富格式 anchor 验收、反馈回流和高成本阶段 dry-run 硬闸门。
- 以每视频 `metadata.json` 作为转写事实源，以产物目录下的单次运行 `run-manifest.json` 作为 Web Access、多格式、截图和设计事实源，方便自检和完成汇报；skill 根目录的 `manifest.json` 只用于可选分发元数据。

**非目标：**

- 不在本变更中实现具体第三方 skill 的源码。
- 本轮实现边界是文档化工作流、模板、schema、安装矩阵和验证入口；不要求脚本具备真实 HTML/PPTX/DOCX/PDF 渲染引擎。
- 不定义 PUA Skill 的内部行为；在来源、用途、安全边界和禁止事项明确前，只把它作为 quarantined 安装项治理，不默认自动调用。
- 不要求默认转写流程每一步都暂停确认。
- 不绕过登录、付费、DRM、访问控制或网站条款。
- 不保证所有输出格式都能原生承载复杂公式；必要时允许降级为可读图片或带源 LaTeX 的 fallback，但必须在 summary 中标注。
- 不把 `video-transcript` 改造成 `web-video-presentation` 的网页视频生成器。
- 不让 AI 生成素材冒充真实截图、真实实验、真实产品图或来源证据。

## 决策

1. 使用“能力 skill 包 + agent 安装矩阵”管理跨 agent 能力。

   Claude、Codex、Cursor 都需要安装并验证以下必装能力：Frontend Design Skill、docx Skill、xlsx Skill、pdf Skill、pptx Skill、Web Access Skill。安装记录应包含 skill 名称、版本或来源、目标 agent、安装路径、校验结果和缺失项。PUA Skill 只作为 `quarantined` 候选项纳入安装治理；在来源和安全边界未明确前，它不阻塞必装能力包验证，也不得作为默认自动调用或可调用能力。

   安装治理应包含两个文件：`agent-skill-pack.yaml` 记录期望安装矩阵，`agent-skill-pack.lock.json` 记录实际锁定版本、校验标识和验证结果。每个条目至少包含 `canonicalName`、`aliases`、`capability`、`source.kind`、`source.path/url`、`version/commit/checksum`、`license/trustLevel`、`installTargets`、`callName`、`status`、`verificationProbe` 和 agent-specific caveat。

   docx/xlsx/pdf/pptx 可以实现为四个独立 skill，也可以实现为一个文档处理 skill 包的四个能力；安装矩阵必须用能力映射表说明实际形态。`xlsx` 不作为 `video-transcript` 默认输出格式，但保留在三端 Office/PDF 能力包中，用于转写后的表格、数据摘要或后续资料整理。

   备选方案：继续靠 README 手工描述。拒绝原因：多 agent 同步时容易出现某个 agent 缺少 Web Access 或文档生成能力，导致后续工作流不可复现。

2. 将 Web Access Skill 作为登录网站的受控辅助能力。

   `video-transcript` 遇到需要登录、cookie、动态页面或浏览器访问才能获取视频/字幕/截图的站点时，可以进入 Web Access checkpoint。该 checkpoint 必须说明目标站点、需要访问的内容、是否使用浏览器登录态、授权范围、可能产生的本地残留文件和清理方式，并等待用户确认。Web Access Skill 不得要求用户把密码写入 skill 文件，也不得绕过访问控制。

   `run-manifest.json` 只记录脱敏信息：登录态类型、授权范围、用户确认时间、访问时间、本地残留文件路径和清理状态。`run-manifest.json` 不得记录密码、cookie、token、会话值、完整浏览器 profile 敏感路径或私密 HTML 内容。`--cookies-from-browser` 也必须经过 Web Access checkpoint 才能使用。

   备选方案：让 `yt-dlp` 或 cookies 参数静默处理。拒绝原因：登录态和隐私内容属于高影响操作，必须显式确认。

3. 将 `video-transcript` 扩展为“转写核心 + 可选产物生成”。

   默认输出仍是 Markdown 转写；HTML、PPTX、Word/DOCX、PDF 等格式作为可选导出阶段。格式选择应在转写计划中 checkpoint，用户可以选择只要 Markdown、要全部格式，或只要其中几种。如果用户初始请求已经明确指定 HTML/PPTX/Word/DOCX/PDF，则该选择视为已确认，不再二次询问；多个可选项应尽量合并到一次转写计划 checkpoint。

   当输入较长、用户请求摘要/讲义/课件，或导出 HTML/PPTX/Word/DOCX/PDF 时，工作流应在转写后生成 `content-plan.md`。该文件是人类可编辑的 Markdown 中间产物，包含 `section -> beat` 骨架、时间戳、关键论点、公式、截图候选、素材需求、目标格式映射、evidence pool 和 must-keep 清单。`content-plan.md` 只规划内容结构、保留/压缩策略、证据回链和输出用途，不写死 PPT 版式、HTML/CSS、DOCX 样式或具体视觉实现。简单公开视频 Markdown 转写可以不生成该文件。

   备选方案：让每个格式直接从长转写生成。拒绝原因：长转写会让不同格式各自切结构，容易丢失关键事实、论证链、限制条件和例外。

   备选方案：默认生成所有格式。拒绝原因：这会增加依赖、时间和文件噪音，也可能引入视觉设计成本。

4. 数学公式以语义优先、渲染可降级为原则。

   Markdown 输出保留 LaTeX，并处理 `$` 与货币或普通文本的冲突；HTML 输出优先使用本地打包的 MathJax/KaTeX 或等价渲染，使用 CDN 时必须记录外部依赖，并保留源 LaTeX；Word/DOCX 优先使用 OMML/MathML 或对应 docx Skill 的可编辑公式能力，失败时使用高分辨率公式图片 fallback；PPTX 默认允许高分辨率公式图片 fallback，并附带源 LaTeX、alt text 和降级原因；PDF 默认由 HTML、DOCX 或 PPTX 派生，不作为首选直接生成格式，必须保留公式可读性和来源格式。

   备选方案：把公式当普通文本。拒绝原因：教学、工程和技术视频会丢失核心信息。

5. 关键截图使用用户确认的“素材增强”阶段。

   转写完成后，agent 应根据内容提出截图建议：仅当关键讲解点无法用文字、公式或自绘示意充分表达时才建议截图，例如物理效果展示、工业设计关键绘制步骤、软件界面状态或实验现象。用户确认后才抓取或导出截图，并记录时间戳、来源、用途和替代文本。截图必须遵循最小必要原则，默认不嵌入私密登录页信息，不绕过 DRM、水印、付费限制或访问控制；需要外发发布时必须在 checkpoint 中确认授权和版权风险。

   备选方案：自动大量截图。拒绝原因：截图会增加存储、版权/隐私风险和整理成本。

6. 素材治理必须区分真实来源、代码绘制、AI 生成和 placeholder。

   多格式、截图或设计阶段应维护 `assets[]` 清单或由 `run-manifest.json` 引用的 `assets.md/json`。每个素材至少记录 id、类型、来源 URL/时间戳/路径、授权或外发限制、用途、引用位置、alt text 和状态。素材类型包括 `source-screenshot`、`user-provided`、`code-drawn`、`ai-generated`、`placeholder`、`formula-render`。真实截图和用户提供素材优先；当截图受限、版权不清或内容可抽象表达时，优先使用 CSS/SVG/Canvas/JS 或对应文档能力绘制 code-drawn 示意；AI 生成素材只能作为概念性插画或抽象辅助，必须标注生成来源和用途，不得冒充真实截图、真实产品图、真实实验结果、logo、数据或用户案例。缺素材时使用明确标注且保留真实比例的 placeholder，并在完成汇报中列为待补。

   备选方案：由设计阶段自由寻找或生成图片。拒绝原因：无来源素材会破坏可信度，并增加版权、隐私和事实风险。

7. Frontend Design Skill 只在视觉产物需要设计时介入。

   HTML、PPTX、Word/DOCX 输出如果只是朴素材料，可使用默认模板；如果用户希望面向展示、发布或教学课件，进入设计 checkpoint，询问是否调用 Frontend Design Skill。调用后应产出设计 brief、版式约束、公式/截图处理规则和验收检查，而不是无边界美化。HTML 应做桌面/移动截图检查；PPTX、Word/DOCX、PDF 应渲染为页面或幻灯片图进行检查，覆盖文本不溢出、不遮挡、对比度、截图来源、无伪素材、公式清晰度和打印/演示尺寸。

   当用户选择复杂 HTML/PPTX/Word/DOCX 且启用发布型输出、设计、截图或复杂公式时，应先生成首个富格式 anchor：HTML 首屏或首个章节、PPTX 前 2-3 页、Word/DOCX 前 1-2 页。该 anchor 必须完成渲染 QA 并暂停给用户验收后，才批量生成剩余部分。用户可以选择逐段验收、顺序生成后统一验收或并行生成；发布型、设计、截图或复杂公式场景的首个 anchor 不可跳过。朴素草稿可以由用户明确跳过 anchor，但 `run-manifest.json` 必须记录返工风险。

   备选方案：默认所有 HTML/PPTX/Word 都走设计。拒绝原因：默认转写材料应保持快速、准确、可编辑。

8. 付费、外发和高成本阶段前使用可审阅 dry-run 清单。

   在 API 上传、Web Access、浏览器登录态、批量播放列表、多格式渲染、截图抓取或付费后端前，agent 应先生成可审阅清单：输入 URL、预计后端、是否下载或上传、可能分片数、已有产物是否跳过、是否外发、是否付费、所需工具/skill、预计输出和风险。用户确认后才执行高成本步骤。缺少 `ffmpeg`、API key、Web Access、docx/pptx/pdf skill 或其他依赖时，必须进入显式退化菜单，给出安装/配置、换后端、跳过阶段等选项，并把状态写成 `blocked` 或 `skipped`，不得生成空壳产物当成功。

   备选方案：脚本失败后再解释。拒绝原因：上传、付费和批量处理的错误成本高，应在执行前可复核。

9. 用产物 `run-manifest.json` 串联多格式输出。

   每个视频的 `metadata.json` 是转写事实源，记录标题、URL、原始转写路径、中文路径、转写来源、语言、错误和翻译状态。`content-plan.md` 是复杂导出的内容规划源。单次运行的 `run-manifest.json` 是聚合事实源，记录 run id、输入、Web Access 脱敏授权范围、content-plan 路径、evidence/must-keep 状态、选定/跳过/失败格式、每个输出文件路径和 hash、公式降级条目、素材条目、截图条目、设计检查结果、渲染 QA 证据、脱敏 argv、隐私/版权处理、工具版本、失败项和后续动作。截图和素材清单嵌入 `run-manifest.json` 或由其引用，不作为第三个并列真相源。skill 根目录的 `manifest.json` 若存在，只能表示分发元数据，不能表示运行事实。

   Markdown/转写内容是母本，HTML/PPTX/Word/DOCX/PDF 是派生产物。完成前必须校验章节数、标题、术语、公式源、截图/素材引用、hash 和降级项与 `metadata.json`、`content-plan.md`、`run-manifest.json` 一致；不同格式可以有不同版式，但内容一致性不能漂移。

   备选方案：只靠文件目录。拒绝原因：多格式输出和截图会让目录扫描难以还原决策过程。

10. 反馈回流、并行执行和可恢复运行使用最小变更原则。

   用户反馈回来后，agent 应先判断反馈层级：转写、内容计划、公式、截图/素材、设计、格式导出或安装能力；然后修改最小产物切片，更新对应 `metadata.json`、`content-plan.md` 或 `run-manifest.json`，并简短汇报改了什么。并行 agent 只能写自己的视频目录、格式子目录或临时 report，不得直接修改聚合 `run-manifest.json`；由主 agent 汇总。已有成功产物默认跳过，`--force` 或明确用户要求才覆盖；批量运行优先只重试失败项，避免重复付费或重复上传。

   备选方案：反馈后整段重做或每个并行 agent 直接写全局状态。拒绝原因：这会增加成本、冲突和事实漂移。

## 风险 / 取舍

- [风险] 安装项名称在不同 agent 中不一致 -> 维护一个 canonical name、别名和安装路径矩阵，验证时按 canonical name 汇报。
- [风险] Web Access 涉及隐私和登录态 -> 必须 checkpoint，禁止保存密码、cookie、token、会话值和私密 HTML，输出 summary 中只记录脱敏访问范围和本地残留文件。
- [风险] 截图过多导致材料臃肿 -> 默认只建议关键截图，要求每张截图有理由、时间戳和替代文本。
- [风险] PPTX/Word 公式支持不稳定 -> 允许公式图片 fallback，但必须保留源 LaTeX 并在 summary 标注。
- [风险] Frontend Design Skill 过度美化转写材料 -> 设计 checkpoint 必须绑定具体输出格式和使用场景，默认模板仍可跳过设计。
- [风险] PUA Skill 名称语义不明 -> 只将其作为 quarantined 候选项纳入安装治理；只有来源、用途、安全边界和禁止事项齐全后才允许提升为可调用或必装项。
- [风险] 安装锁定信息不足导致不可复现 -> 使用 `agent-skill-pack.yaml` 与 `agent-skill-pack.lock.json` 记录来源、版本、校验标识、调用名、探针和状态。
- [风险] 字幕、转写和截图涉及版权或访问限制 -> checkpoint 中记录授权来源、可引用范围、是否允许外发发布和必要的替代方案。
- [风险] 多格式摘要丢失关键事实 -> 使用 `content-plan.md`、evidence pool、must-keep 清单和内容一致性自检。
- [风险] AI 生成素材或无来源素材误导读者 -> 素材清单必须区分真实来源、code-drawn、AI 生成和 placeholder，并在发布型产物中显式标注。
- [风险] 用户反馈导致大范围返工 -> 使用反馈层级判断和最小切片修改，复用已有转写真相源和已成功产物。

## 迁移计划

1. 定义跨 agent skill 包矩阵、`agent-skill-pack.yaml` 和 `agent-skill-pack.lock.json`。
2. 更新 README，说明 Claude、Codex、Cursor 的必装能力包、quarantined 候选项和验证命令。
3. 扩展 `video-transcript` 文档：加入 Web Access checkpoint、内容计划、证据池、截图 checkpoint、多格式 checkpoint、素材治理、Frontend Design checkpoint。
4. 设计并记录多格式输出 `run-manifest.json` schema、`content-plan.md` 结构、素材/截图清单、公式保留策略和反馈回流规则。
5. 后续实现脚本参数与导出流程，并用离线样例验证 Markdown/HTML/PPTX/Word/DOCX 的公式、素材、证据回链和截图引用。

回滚策略：删除新安装包矩阵和 `video-transcript` 新工作流文档，不影响现有 Markdown 转写默认流程。

## 未决问题

- PUA Skill 的真实来源、安装路径、能力边界和安全说明是什么？在回答前它保持 quarantined/默认禁用。
- docx/xlsx/pdf/pptx Skill 是四个独立 skill，还是一个文档处理 skill 包中的四个能力？安装矩阵必须记录最终形态。
- Web Access Skill 在 Claude、Codex、Cursor 中的 canonical 名称和调用接口是否一致？
- HTML/PPTX/Word/DOCX 的默认模板应放在 `video-transcript/templates/`，还是交给对应格式 skill 管理？
- PDF 本轮默认作为 HTML/DOCX/PPTX 的派生导出；是否直接生成 PDF 以后续实现验证为准。
- `content-plan.md` 的生成应由 `video-transcript` 脚本实现，还是先作为 agent 文档工作流实现？
