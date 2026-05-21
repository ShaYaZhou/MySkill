## 背景 / 动机

当前仓库已经有 `video-transcript` 与 `yt-dlp-download` 两个视频相关工具型 skill，但跨 agent 的能力安装仍主要依赖手工复制，`video-transcript` 也只覆盖基础 Markdown 转写。随着 Claude、Codex、Cursor 都需要网页访问、前端设计、Office/PDF 产物和更复杂视频理解能力，需要把“安装哪些 skill、何时调用辅助 skill、何时停下让用户确认”规范化。

本变更将新增跨 agent skill 安装包要求，并扩展 `video-transcript` 的工作流：遇到登录网站时可调用 Web Access Skill；输出支持 Markdown、HTML、PPTX、Word/DOCX 等格式及数学公式；并按 `web-video-presentation` 的阶段化检查点思想，加入截图、格式输出和 Frontend Design Skill 设计介入的可选确认节点。

## 变更内容

- 为 Claude、Codex、Cursor 定义统一的能力 skill 包：
  - Frontend Design Skill
  - docx、xlsx、pdf、pptx Skill
  - Web Access Skill
  - PUA Skill（只作为 `quarantined` 候选项纳入安装治理；来源、用途和安全边界未明确前不作为必装或可调用能力）
- 增加跨 agent 安装/同步/验证规则，确保三个 agent 的 skill 版本、安装位置和可调用名称一致。
- 增加安装包清单与锁定文件要求，记录 skill 来源、版本、校验标识、调用名、验证探针和状态。
- 扩展 `video-transcript` 的工作流：
  - 需要登录的网站，必要时调用 Web Access Skill，且必须有用户确认和安全边界。
  - 复杂或多格式导出前生成用户可编辑的 `content-plan.md`，把忠实转写和内容重构计划分开。
  - 为章节/段落建立 evidence pool 与 must-keep 清单，确保摘要、讲义和演示材料能回链到原始转写。
  - 输出 Markdown、HTML、PPTX、Word/DOCX 等格式时支持数学公式。
  - 在关键内容处增加“是否截图”的检查点，用于文字、数学公式或自绘素材难以表达的内容。
  - 建立素材清单、placeholder、code-drawn 示意和 AI 生成素材的反伪规则。
  - 在生成 HTML/PPTX/Word/DOCX 等格式前增加格式选择检查点。
  - 在需要更高视觉质量时增加是否调用 Frontend Design Skill 的设计检查点。
  - 为复杂 HTML/PPTX/Word/DOCX 导出增加首个富格式 anchor 验收、渲染 QA 证据和反馈回流协议。
- 增加付费、外发、登录态和高成本阶段前的 dry-run 可审阅清单，以及缺工具/未鉴权时的显式退化菜单。
- 按 `web-video-presentation` 的思路设计阶段化工作流，但降级为适合工具型 skill 的“风险/可选项触发式 checkpoint”，避免默认流程过度打断。
- 本变更依赖 `improve-skill-architecture` 的共享结构、reference map、summary/schema、dry-run、退化和自检约定；实现顺序应先完成共享基础，再落本变更的具体文档和模板。
- 明确非目标：本变更本轮实现安装治理、工作流文档、模板和 schema，不直接实现具体网页访问、截图识别、PPTX/DOCX 渲染引擎或设计系统。

## 能力

### 新增能力

- `agent-skill-pack-installation`：为 Claude、Codex、Cursor 定义能力 skill 包、安装目标、版本校验和缺失处理。
- `rich-video-transcript-workflow`：扩展 `video-transcript` 的网页登录辅助、多格式输出、数学公式保留、关键截图和前端设计检查点工作流。

### 修改能力

无。当前仓库还没有已归档的 OpenSpec capability；本变更作为新增能力提出。

## 影响

- 受影响文档：根 `README.md` / `README.zh-CN.md`、各 agent 安装说明、`video-transcript/SKILL.md` 及其 references。
- 受影响脚本：后续实现可能扩展 `video-transcript/scripts/transcript.py` 的输出格式、截图元数据、Web Access 调用交接和多格式生成参数。
- 受影响 skill 安装目标：Claude、Codex、Cursor。
- 依赖或关联能力：Frontend Design Skill、docx/xlsx/pdf/pptx Skill、Web Access Skill、PUA Skill，以及可能的浏览器自动化、文档生成、演示文稿生成和 HTML 渲染工具链。
- Mavis 仍保留在仓库 README 的既有安装目标中，但不纳入本轮三端必装包治理；后续可单独扩展。
