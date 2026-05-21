## 1. 跨 Agent Skill 安装矩阵

- [x] 1.1 定义 Claude、Codex、Cursor 的 skill 安装矩阵，列出必装能力 skill：Frontend Design Skill、docx Skill、xlsx Skill、pdf Skill、pptx Skill、Web Access Skill 的 canonical name、别名、来源和目标路径；PUA Skill 只作为 `quarantined` 候选项记录。
- [x] 1.2 定义 `agent-skill-pack.yaml`，包含 `canonicalName`、aliases、capability、source kind/path/url、installTargets、callName、required/optional/quarantined 状态和 verification probe。
- [x] 1.3 定义 `agent-skill-pack.lock.json`，记录实际版本、commit 或 checksum、安装路径、验证时间、验证状态和 drift 信息。
- [x] 1.4 明确 docx/xlsx/pdf/pptx 是四个独立 skill 还是一个文档处理 skill 包的四个能力，并把能力映射结论写入安装文档。
- [x] 1.5 说明 xlsx Skill 不属于 `video-transcript` 默认输出格式，但作为三端 Office/PDF 能力包用于表格、数据摘要或后续资料整理。
- [x] 1.6 补充 PUA Skill 的来源、用途、权限、安全边界、调用场景和禁止事项；缺少任一项时必须标记为 `quarantined`/默认禁用，且不阻塞必装能力包验证。
- [x] 1.7 更新 `README.md` 和 `README.zh-CN.md`，加入三端必装能力包、quarantined 候选项、安装步骤、同步维护说明，并说明 Mavis 不纳入本轮强制矩阵。
- [x] 1.8 增加安装验证流程，检查三个 agent 的 skill 目录、`SKILL.md` 或 manifest、版本/来源标识、调用名、agent-specific invocation adapter、验证探针和缺失项。
- [x] 1.9 定义安装验证状态：`ok`、`missing`、`drift`、`unverified`、`quarantined`，并说明各状态是否阻塞相关 workflow。

## 2. Web Access Skill 调用工作流

- [x] 2.1 为 `video-transcript` 增加 Web Access checkpoint 文档，说明何时需要网页登录、cookie、动态页面或浏览器交互。
- [x] 2.2 设计 Web Access 调用模板，包含目标网站、访问范围、脱敏登录态类型、授权范围、本地残留文件、隐私风险、清理方式和用户确认语。
- [x] 2.3 在 `video-transcript` 工作流中加入 Web Access 的安全边界：不保存密码、cookie、token、会话值、完整浏览器 profile 敏感路径或私密 HTML，不绕过访问控制，不绕过 DRM，不静默扩大访问范围。
- [x] 2.4 设计 Web Access 结果交接格式，记录抓取到的字幕/视频信息/截图候选、访问时间、来源页面、本地文件路径和清理状态。
- [x] 2.5 更新 `video-transcript/SKILL.md` 或 reference map，让 agent 在网站需要登录或使用 `--cookies-from-browser` 时必须路由到 Web Access checkpoint。

## 3. 多格式输出与数学公式

- [x] 3.1 为 `video-transcript` 增加格式选择 checkpoint，默认只生成 Markdown，用户确认后才生成 HTML、PPTX、Word/DOCX、PDF 等额外格式。
- [x] 3.2 明确如果用户初始请求已指定 HTML、PPTX、Word/DOCX、PDF，则视为格式已确认，不为同一选择二次暂停。
- [x] 3.3 设计 Markdown 公式规则：行内公式 `$...$`、块级公式 `$$...$$`、公式上下文、转写提示，以及 `$` 与货币/普通文本冲突的处理。
- [x] 3.4 设计 HTML 公式规则：使用 MathJax、KaTeX 或等价机制，明确本地包/CDN 依赖记录方式，并保留源 LaTeX。
- [x] 3.5 设计 PPTX 与 Word/DOCX 公式策略：DOCX 优先 OMML/MathML 或可编辑公式，PPTX 默认允许高分辨率公式图片 fallback；所有 fallback 都在 `run-manifest.json` 中记录源 LaTeX、alt text、降级原因和验证结果。
- [x] 3.6 设计 PDF 公式策略，明确本轮默认 PDF 由 HTML、PPTX、Word/DOCX 派生，记录来源格式、公式可读性和降级原因。
- [x] 3.7 定义多格式输出目录结构和命名规则，避免 Markdown、HTML、PPTX、Word/DOCX、PDF、截图和 `run-manifest.json` 混乱。

## 4. 内容计划与证据池

- [x] 4.1 设计 `content-plan.md` 模板，包含 `section -> beat` 骨架、时间戳、关键论点、公式、截图候选、素材需求、目标格式映射、evidence pool 和 must-keep 清单。
- [x] 4.2 明确 `content-plan.md` 的触发条件：复杂摘要、讲义、课件、HTML/PPTX/Word/DOCX/PDF 或长视频内容重构；普通 Markdown 转写不强制生成。
- [x] 4.3 设计 evidence pool 字段，记录时间戳、原句摘录、术语、数字、公式、案例、屏幕状态、置信度或来源说明。
- [x] 4.4 设计 must-keep 规则，确保关键数字、公式、案例、限制条件、反方观点、例外情况和操作步骤不会在摘要或多格式导出中静默丢失。
- [x] 4.5 定义内容计划边界：只规划内容结构、保留/压缩策略、证据回链、素材需求和格式映射，不写死版式、CSS、DOCX 样式或具体视觉实现。
- [x] 4.6 增加 `content-plan.md` 自检清单，覆盖 section/beat 完整性、evidence pool 回链、must-keep 覆盖、公式条目、截图候选、素材需求和格式映射；失败项先修复再进入富格式导出。

## 5. 关键截图 Checkpoint

- [x] 5.1 为 `video-transcript` 增加截图候选识别规则，覆盖物理效果展示、工业设计关键绘制步骤、实验现象、软件界面状态等文字难以表达的内容。
- [x] 5.2 设计截图 checkpoint 模板，列出候选时间戳、截图理由、用途、替代文字、隐私/版权风险和建议插入的输出格式。
- [x] 5.3 设计用户确认后的截图抓取或导入流程，记录截图路径、来源时间戳、对应转写段落和引用位置。
- [x] 5.4 设计用户跳过截图时的降级路径，继续使用文字、公式或自绘示意，并在 summary 中标记截图阶段已跳过。
- [x] 5.5 增加截图安全边界：遵循最小必要原则，记录授权来源、外发限制和处理方式，不绕过 DRM、水印、付费限制或访问控制，默认不嵌入私密登录页信息。
- [x] 5.6 增加截图去重和数量控制，要求每张截图都有明确用途、替代文字和必要性说明。
- [x] 5.7 增加截图自检清单，检查文件存在、引用有效、替代文字存在、隐私信息已处理、`run-manifest.json` 记录完整。

## 6. 素材治理与反伪规则

- [x] 6.1 设计 `assets[]` 或 `assets.md/json` schema，记录 id、类型、来源 URL/时间戳/路径、授权或外发限制、用途、引用位置、alt text 和状态。
- [x] 6.2 定义素材类型：`source-screenshot`、`user-provided`、`code-drawn`、`ai-generated`、`placeholder`、`formula-render`。
- [x] 6.3 设计 placeholder 规范：保留真实比例，显示素材类型、建议尺寸、缺失原因和替换说明；发布型产物必须在完成汇报中列为待补。
- [x] 6.4 设计 code-drawn 策略：截图受限、版权不清或内容可抽象表达时，优先用 CSS/SVG/Canvas/JS、Office drawing 或等价机制绘制示意，并记录为非真实截图。
- [x] 6.5 定义 AI 生成素材边界：只能作为概念性插画或抽象辅助，必须记录生成来源、用途和发布风险，不得冒充真实截图、产品图、实验结果、logo、数据或用户案例。
- [x] 6.6 将反伪规则扩展到所有 Markdown、HTML、PPTX、Word/DOCX、PDF 输出，而不是只在 Frontend Design 阶段检查。

## 7. Frontend Design Skill 与富格式 Anchor

- [x] 7.1 为 HTML、PPTX、Word/DOCX 输出增加是否调用 Frontend Design Skill 的设计 checkpoint。
- [x] 7.2 设计 Frontend Design brief 模板，包含受众、输出格式、版式目标、公式处理、截图处理、素材策略、禁用伪素材和验收清单。
- [x] 7.3 明确默认朴素模板路径：用户不需要设计时不调用 Frontend Design Skill。
- [x] 7.4 定义设计后自检清单，覆盖公式可读性、截图/素材引用、层级结构、文本不溢出、不遮挡、对比度、截图来源、演示/打印适配性和无伪造素材。
- [x] 7.5 定义首个富格式 anchor 验收：HTML 首屏或首个章节、PPTX 前 2-3 页、Word/DOCX 前 1-2 页，完成渲染 QA 后暂停给用户确认。
- [x] 7.6 定义渲染 QA 证据：HTML desktop/mobile 截图，PPTX/Word/DOCX/PDF 逐页或逐 slide render 图，viewport、页码/slide、检查项、失败证据路径和 hash。
- [x] 7.7 更新 `video-transcript` reference map，让多格式输出阶段能路由到设计 checkpoint 和 anchor 验收。

## 8. 运行 Manifest、Dry-run 与完成汇报

- [x] 8.1 设计 `video-transcript` 多格式运行 `run-manifest.json` schema，记录 run id、输入 URL、引用到的每视频 `metadata.json`、`content-plan.md`、脱敏授权范围、选定/跳过/失败格式、每个输出文件路径和 hash、公式降级条目、素材条目、截图条目、设计检查结果、QA 证据、脱敏 argv、隐私/版权处理、工具版本、失败项和后续动作；明确 skill 根目录 `manifest.json` 只用于可选分发元数据。
- [x] 8.2 明确每视频 `metadata.json` 是转写事实源，`content-plan.md` 是复杂导出的内容规划源，`run-manifest.json` 是单次运行聚合事实源。
- [x] 8.3 设计付费/外发/高成本阶段的 dry-run 可审阅清单，覆盖 URL、后端、下载/上传、分片、跳过项、付费/外发、所需工具和风险。
- [x] 8.4 设计缺工具/未鉴权时的显式退化菜单，覆盖安装/配置、换后端、跳过阶段，并将状态写为 `blocked` 或 `skipped`。
- [x] 8.5 设计断点续跑、`--force` 覆盖和只重试失败项语义，避免重复付费、重复上传或覆盖成功产物。
- [x] 8.6 设计完成汇报模板，按 Markdown、content-plan、HTML、PPTX、Word/DOCX、PDF、截图、素材、Web Access、设计检查、QA 证据分别列出成功、跳过、失败和后续动作。
- [x] 8.7 将 `run-manifest.json` 纳入完成前自检，要求所有选定格式存在、公式可读、截图/素材引用有效、placeholder 显式标注、设计检查和 QA 证据完成后才能汇报成功。

## 9. 协作回流与并行隔离

- [x] 9.1 设计用户反馈回流规则，按转写、内容计划、公式、截图/素材、设计、格式导出、安装能力分层定位，并修改最小产物切片。
- [x] 9.2 设计 reviewer handoff 模板，包含产物路径、真相源、检查清单、风险边界、禁止修改范围，以及 pass/fail、证据、建议和阻塞状态输出。
- [x] 9.3 设计并行 agent 写入隔离规则：每个 agent 只写自己的视频目录、格式子目录或临时 report，聚合 `run-manifest.json` 由主 agent 汇总。
- [x] 9.4 定义中途追加或撤销格式/截图/设计选择时的行为：复用已有转写真相源，只更新新增或撤销阶段，不重跑全流程。

## 10. 文档与 Skill 入口更新

- [x] 10.1 更新 `video-transcript/SKILL.md`，保留默认快速转写入口，并新增网页登录、content-plan、多格式、截图、素材、设计 checkpoint 的 reference map。
- [x] 10.2 新增或更新 `video-transcript/references/` 文档，覆盖 Web Access、内容计划、输出格式、公式、截图、素材治理、设计、`run-manifest.json` 和反馈回流。
- [x] 10.3 更新 agent 安装文档，说明缺少 Frontend Design、Web Access、docx/xlsx/pdf/pptx 或 PUA Skill 时哪些 workflow 不可用。
- [x] 10.4 增加示例：含公式的 Markdown/HTML 输出片段、`content-plan.md` 片段、素材/截图 `run-manifest.json` 样例、多格式导出 summary 样例。

## 11. 验证

- [x] 11.1 运行 OpenSpec 校验，确认新 change 有效。
- [x] 11.2 验证安装矩阵文档中所有 skill 名称、路径和别名可追踪。
- [x] 11.3 离线验证 `video-transcript` 文档路径、reference map、`run-manifest.json`/content-plan/assets schema 和示例文件链接。
- [x] 11.4 人工检查默认公开视频 Markdown 转写流程没有被强制多轮 checkpoint 阻塞。
- [x] 11.5 人工检查登录、截图、素材、多格式、content-plan 和 Frontend Design checkpoint 都包含用户确认、安全边界、输出真相源、跳过路径和敏感信息禁止记录规则。
- [x] 11.6 人工检查富格式 anchor、反馈回流、dry-run 硬闸门和显式退化菜单不会把 `video-transcript` 默认流程变成重型网页视频生成器。

## 12. Agent 质检

- [x] 12.1 高风险变更时至少开 2 个 agent 从安装治理、`video-transcript` 工作流、多格式/公式/截图/素材安全等角度质检 OpenSpec。
- [x] 12.2 汇总 agent 质检意见，修订 proposal、design、spec 或 tasks 中遗漏或过重的部分。
- [x] 12.3 再次运行 OpenSpec 校验，并记录最终状态。

