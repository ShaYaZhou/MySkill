## 背景

`web-video-presentation` 是一个完整工作流型 skill：它用阶段图说明全流程，用“检查点计划”一次对齐稿子、outline、主题、素材和开发模式，用 reference map 控制渐进式读取，用 anchor 和自检保证质量。`video-transcript` 已经有较丰富的 references 和富格式策略，`yt-dlp-download` 也有 doctor/dry-run 与 summary，但两者还没有形成同样清晰的“阶段化协作语言”。

本 change 的目标不是把下载和转写都变成大型前端项目，而是提炼 `web-video-presentation` 的可复用模式：轻入口、阶段总览、硬确认门、单一事实源、可选 anchor、强自检、明确退化和跨 agent 质检。两个视频类 skill 应在描述和结构上读起来像同一家工具箱，而不是两个风格不同的脚本包装。

已有 `docs/SKILL-ARCHITECTURE.md`、`docs/QUALITY-WORKFLOW.md`、`docs/VALIDATION.md` 和前序 OpenSpec changes 已经定义了瘦入口、reference map、doctor/dry-run、显式退化和事实源规则。本 change 应复用这些纪律，避免重复发明一套冲突规范。

## 目标

- 统一 `video-transcript` 与 `yt-dlp-download` 的 `SKILL.md` 叙事结构：用途、产物、阶段图、默认路径、检查点、reference map、完成检查。
- 将 `web-video-presentation` 的“阶段读取指南”迁移为两个 skill 的 reference map：什么时候读 workflow/backend/output/checks/web-access/assets/design/troubleshooting。
- 为高影响阶段建立硬确认门：登录态/cookies、API 上传、付费、批量播放列表、覆盖、截图/素材、多格式/设计。
- 为复杂输出建立 anchor 规则：`video-transcript` 的 HTML/PPTX/DOCX 首屏/前几页；`yt-dlp-download` 的下载计划/dry-run 样张和首批条目确认。
- 统一事实源：`metadata.json`、`run-summary.json`、`download-summary.json`、`run-manifest.json` 的职责边界和状态 token。
- 统一自检与 reviewer handoff：每个关键产物完成后先自检，失败先修复，再汇报。
- 保持简单路径直接：普通公开视频下载或 Markdown 转写不得因为重型检查点被打断。

## 非目标

- 不修改 `web-video-presentation` 的源码或文档。
- 不强制 `yt-dlp-download` 生成前端页面或复杂 templates。
- 不把所有 references 拆成相同文件名；可以按各自复杂度保留不同数量的 reference，但入口结构和语义必须统一。
- 不在本 change 中实现所有富格式导出、图片生成或转写 provider；这些由对应 change 或后续任务处理。
- 不降低安全边界：secret、cookie、token、session value 仍禁止写入日志和事实源。
- 不将 Vite/React、主题系统、点击式章节 stepper、录屏和旁白合成引入 `video-transcript` 或 `yt-dlp-download`，除非未来另有明确创作型 skill 需求。

## 设计决策

### 1. 抽象为“视频工作流 skill”模式

两个 skill 采用同一套顶层结构：

```text
概览
工作流总览
默认流程
快速策略
常用选项
输出契约
引用地图
检查点
完成检查
```

理由：这保留了小 skill 的轻量，也让用户能在 `video-transcript` 和 `yt-dlp-download` 之间迁移同样的心智模型。替代方案是照搬 `web-video-presentation` 的所有 phase 名称，但下载/转写没有章节开发和主题系统，照搬会显得笨重。

### 2. 分成轻量路径和高影响路径

借鉴 `web-video-presentation` 的硬检查点，但只在需要时停：

- 轻量路径：公开视频 + 默认输出 + 无覆盖 + 无登录态 + 无付费外发。
- 高影响路径：登录/cookie、无字幕 API 上传、大型 playlist、覆盖成功产物、截图/素材、多格式、设计增强。

理由：`web-video-presentation` 是创作型流程，停顿多是合理的；下载和转写是工具型流程，简单任务应该快。

### 3. 为两个 skill 明确不同的 anchor

- `video-transcript`：富格式输出时使用 HTML 首屏/首章、PPTX 前 2-3 页、DOCX 前 1-2 页作为 anchor；复杂或发布型输出必须渲染质检后给用户验收。
- `yt-dlp-download`：不做视觉 anchor，而用 `--dry-run` 的下载计划、播放列表首批条目、输出模板、字幕/缩略图候选作为执行 anchor；大型下载或覆盖前必须让用户确认。

理由：anchor 的本质是“批量执行前的小范围可验收样板”，不是必须都是页面 1。

### 4. Reference map 必须按阶段服务，不只是列文件

`SKILL.md` 中每个 reference 必须说明“何时读”。建议：

- `video-transcript` 保留多 references，但增加阶段总览和读取表。
- `yt-dlp-download` 至少拆出或强化 workflow/checkpoints/web-access/output/troubleshooting，避免所有细节挤在 `OUTPUT-AND-CHECKS.md`。

理由：`web-video-presentation` 的强项是让 agent 在长会话中知道“此刻该读哪份文件”。这比单纯拆文档更重要。

### 5. 统一事实源和反伪规则

两个 skill 都必须明确：

- 运行事实源是什么。
- 哪些字段是状态 token。
- 哪些字段禁止记录。
- 什么算 `ok`、`skipped`、`blocked`、`failed`、`partial_failure`。
- 不确定路径、placeholder、自动字幕、API 结果和截图/素材不能被汇报成已验证事实。

理由：下载/转写/富格式输出最容易在“看起来成功”时混入不确定状态，事实源约定比口头汇报更可靠。

### 6. 先修正 `yt-dlp-download` summary 契约漂移

`yt-dlp-download/references/OUTPUT-AND-CHECKS.md` 的示例字段与脚本实际 summary 字段存在漂移，例如示例使用 `media_paths`、`subtitle_paths`、`thumbnail_path`、`archive_skip`，而脚本实际可能输出 `output.actual_files`、`archive.skip`、`subtitle_language`、`thumbnail.status` 和 `dry_run_planned` 等状态。实现本 change 时必须先让 reference、example 和脚本达成一致，再新增更多检查点文案。

理由：`web-video-presentation` 的可靠性来自“真相源不漂”。如果 summary schema 本身不可信，后续恢复、质检和跨 agent 协作都会失效。

## 风险与取舍

- 风险：过度向 `web-video-presentation` 靠拢会让简单下载变重。缓解：规范明确轻量路径不强制检查点，只在高影响阶段停。
- 风险：两个 skill reference 文件数量差异大。缓解：统一结构语义，不强求文件名完全一致；小 skill 可合并 reference。
- 风险：文档更新与脚本行为漂移。缓解：tasks 要求同步 doctor/dry-run、summary 示例和验证脚本。
- 风险：anchor 概念在下载场景显得别扭。缓解：将下载 anchor 定义为 dry-run/下载计划/首批条目确认，而不是视觉样张。
- 风险：多个 active changes 互相重叠。缓解：本 change 只定义架构统一；后端 provider 扩展继续归 `expand-transcript-backend-selection`。
- 风险：文档 schema 与脚本输出不一致继续扩大。缓解：把 `yt-dlp-download` summary 契约一致性列为 P0 任务，并用 examples/validation 锁住。

## 迁移计划

1. 先更新 OpenSpec 和文档契约，避免直接大改脚本。
2. 调整两个 `SKILL.md` 的结构和文案，使其共享阶段语言和 reference map。
3. 增补或重组 `yt-dlp-download` references，使下载流程也有 workflow/checkpoint/output/troubleshooting 层。
4. 调整 `video-transcript` 的阶段图、富格式 anchor、素材/AI 生成反伪描述和完成检查，使它更接近 `web-video-presentation` 的硬节点表达。
5. 更新 examples 和 manifest，统一字段和状态 token。
6. 扩展 `validate_repo.py` 以检查 reference map、JSON 示例、脚本 help 和敏感字段。
7. 安装到 Claude、Codex、Cursor、Mavis 后分别做 `--doctor` 和 `--dry-run` smoke check。

## 待确认问题

- `yt-dlp-download` 是否需要独立 `references/WORKFLOW.md`，还是增强现有 `OUTPUT-AND-CHECKS.md` 即可？
- `video-transcript` 是否要显式引入与 `web-video-presentation` 相同的“检查点计划”命名，还是保留更通用的“内容计划 / 设计检查点 / anchor”？
- AI 生成素材是否要在本 change 中统一指定默认 provider，还是另开 change 处理？
