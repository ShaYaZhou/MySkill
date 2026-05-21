# 内容计划（Content Plan）

`content-plan.md` 是复杂导出前的中文内容规划层。它把忠实转写、内容重构和派生产物分开，使摘要、讲义、课件、HTML、PPTX、Word/DOCX、PDF 等输出都能回链到原始转写。

## 触发条件

必须生成 `content-plan.md`：

- 用户要求复杂摘要、讲义、课件、教学材料、演示文稿或可发布材料。
- 用户要求 HTML、PPTX、Word/DOCX、PDF 或多格式导出。
- 视频较长、章节多、论证链复杂，且需要重构、压缩、合并或改写。
- 内容包含关键公式、数字、实验、案例、操作步骤、反方观点或例外条件，直接摘要可能丢失事实。

不强制生成：

- 普通公开视频 Markdown 转写。
- 用户只要求原文字幕、中文转写或轻量翻译。
- 用户明确要求先只交付 Markdown 母本。

普通 Markdown 转写也不主动打断用户做截图确认；截图、素材和富格式规划只作为完成汇报中的后续增强提示。

## 文件位置

建议放在对应视频或运行目录：

```text
<video-output-dir>/
├── original.md
├── zh.md
├── metadata.json
├── content-plan.md
└── run-manifest.json       # 仅 Web Access / 截图 / 富格式等可选阶段需要
```

`metadata.json` 是转写事实源，`content-plan.md` 是内容规划源，`run-manifest.json` 是单次运行聚合事实源。

## 内容边界

`content-plan.md` 只规划：

- section -> beat 的内容结构。
- 保留、压缩、合并、删除或延后处理策略。
- evidence pool 回链。
- must-keep 清单。
- 公式、截图候选、素材需求。
- 目标格式映射。

不得写死：

- PPT 具体版式、主题、字体、颜色、动画。
- HTML/CSS 细节或组件实现。
- DOCX 样式、页眉页脚、分页策略。
- 具体视觉设计方案。

视觉呈现、版式和渲染 QA 应交给后续格式、设计或 anchor checkpoint。

## Section -> Beat 结构

每个 section 表示一个可独立理解的内容段，每个 beat 表示 section 内一个最小讲解动作或论点。建议字段：

- `section_id`：稳定编号，例如 `S01`。
- `section_title`：中文标题。
- `source_range`：来源时间戳范围，例如 `00:00:12-00:04:30`。
- `purpose`：本 section 在派生产物中的作用。
- `beats[]`：beat 列表。
- `target_format_mapping`：Markdown、HTML、PPTX、Word/DOCX、PDF 的保留或压缩策略。

Beat 建议字段：

- `beat_id`：例如 `S01-B02`。
- `timestamp`：单点或范围。
- `key_claim`：关键论点或讲解动作。
- `source_excerpt`：短原句摘录或忠实转写片段。
- `evidence_refs`：引用 evidence pool 的 id。
- `formulas`：公式 id 或源 LaTeX。
- `screenshot_candidates`：截图候选 id。
- `asset_needs`：素材需求 id。
- `must_keep_refs`：引用 must-keep id。
- `compression_note`：压缩、合并或保留原因。

## Evidence Pool

Evidence pool 记录可回链证据，供摘要、讲义和富格式输出引用。每条 evidence 建议包含：

- `id`：例如 `E01`。
- `timestamp`：时间戳或范围。
- `source_excerpt`：原句摘录，保持短小，不大段复制。
- `type`：`term`、`number`、`formula`、`case`、`screen-state`、`operation-step`、`claim`、`limitation`、`counterpoint`、`exception`。
- `term_or_entity`：术语、人物、工具、对象或变量。
- `number_or_formula`：数字、单位、比例或 LaTeX。
- `source_note`：来源说明，例如人工字幕、自动转写、页面 metadata、用户提供材料。
- `confidence`：`high`、`medium`、`low`。
- `used_by`：被哪些 beat、must-keep 或格式映射使用。

低置信度 evidence 不得作为强事实直接写入发布型产物；应标注不确定性或回到转写核查。

## Must-keep 规则

Must-keep 清单用于防止摘要或富格式导出静默丢失关键事实。必须纳入：

- 关键数字、单位、比例、阈值、时间、版本号。
- 公式、变量定义、推导约束和适用条件。
- 具体案例、实验结果、软件操作步骤、工业设计关键步骤。
- 限制条件、例外情况、反方观点、失败条件和安全注意事项。
- 用户明确要求保留的段落、术语或表达。

每条 must-keep 建议包含：

- `id`
- `text`
- `reason`
- `evidence_refs`
- `required_formats`
- `if_space_limited`
- `status`

如果目标格式无法完整容纳，必须写明压缩方式或降级原因，不得静默删除。

## 公式、截图候选与素材需求

公式条目应记录源 LaTeX、变量说明、来源时间戳、目标格式策略和 fallback 风险。

截图候选只记录候选，不代表已经授权抓图。每项应包含时间戳、理由、用途、替代文字、隐私/版权风险、建议格式和是否需要用户确认。普通 Markdown 转写不主动打断用户确认截图。

素材需求记录真实截图、用户提供素材、code-drawn 示意、formula-render、placeholder 或 AI 概念图的需求，但不得把待补素材写成已存在事实。

## 目标格式映射

为每个 section 或 beat 记录不同格式的处理策略：

- `markdown`：保留完整转写、轻量摘要或跳过。
- `html`：是否展开证据、是否需要交互目录、是否依赖公式渲染。
- `pptx`：建议拆成几页或是否合并，不写具体版式。
- `docx`：讲义段落、表格、脚注或附录策略。
- `pdf`：来源格式、阅读密度和公式可读性要求。

格式映射只说明内容层级和保真要求，不说明视觉实现。

## 自检清单

进入富格式导出或交给用户确认前，检查：

- 每个 section 都有来源时间戳和至少一个 beat。
- 每个 beat 的关键论点能回链到 evidence pool 或标注为推断。
- evidence pool 覆盖关键术语、数字、公式、案例、屏幕状态和操作步骤。
- must-keep 覆盖关键数字、公式、案例、限制条件、反方观点、例外情况和操作步骤。
- 公式条目有源 LaTeX、变量说明或不确定性标注。
- 截图候选都有时间戳、理由、用途、替代文字和风险说明。
- 素材需求区分真实来源、待补、code-drawn、formula-render、placeholder 或 AI 概念图。
- 目标格式映射覆盖用户选择的每个格式。
- 未把版式、CSS、DOCX 样式或具体视觉实现写死在内容计划里。
- 普通 Markdown 转写路径没有被强制 content-plan 或截图确认阻塞。

失败项先修复；不能修复时，在 `run-manifest.json` 或完成汇报中标为 `blocked`、`skipped` 或 `risk-accepted`。

## 模板和示例

- 模板：`templates/content-plan.template.md`
- 示例：`examples/content-plan.example.md`

示例只说明契约，不代表真实产物；真实运行必须根据实际转写、metadata、用户选择和授权范围填写。
