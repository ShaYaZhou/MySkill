---
name: video-transcript
description: 当用户提供一个或多个视频或播放列表 URL，并希望生成转写稿、口播稿、讲义、双语文档或后续富格式材料时使用。默认优先使用人工字幕，缺字幕时再按确认流程降级到 OpenAI、Kimi 或 MiniMax 转写。
---

# Video Transcript

从视频或播放列表 URL 生成 Markdown 转写文档。默认优先使用人工字幕，因为它最快、成本最低、隐私风险也最小；只有字幕不可用或用户明确要求时，才进入音视频下载和 API 转写路径。

## 默认流程

在本 skill 目录运行：

```powershell
python scripts/transcript.py "VIDEO_OR_PLAYLIST_URL"
```

多个 URL 可以一次传入：

```powershell
python scripts/transcript.py "URL_1" "URL_2"
```

默认输出到 `~/Documents/video-transcripts`。脚本会在 skill 目录内维护独立 `.venv`。

## 快速策略

- 优先使用人工字幕；默认不使用平台自动生成字幕。
- 字幕不可用时，`--transcribe-backend auto` 按可见配置选择 OpenAI、Kimi video、MiniMax API。
- 数学内容保留为 Markdown LaTeX：`$...$` 和 `$$...$$`。
- 任何 API key、cookie、token、session value 都不得写入 skill 文件、日志或 summary。
- 涉及登录、浏览器 cookie、付费 API、隐私敏感上传或大型播放列表时，先给出短计划并等待确认。
- 普通公开视频的 Markdown 转写请求可以直接执行，不强制进入重型多阶段 checkpoint。
- 默认只生成 Markdown；用户确认后才生成 HTML、PPTX、Word/DOCX 或 PDF。初始请求已明确指定格式时，不为格式选择二次暂停。
- 富格式输出涉及公式、Frontend Design 或 anchor 样张时，按 reference map 读取对应规范，并把 fallback、QA 证据和跳过理由写入运行摘要或 run-manifest。

## 常用选项

```powershell
python scripts/transcript.py --output-dir "D:\transcripts" "URL"
python scripts/transcript.py --timestamps "URL"
python scripts/transcript.py --transcribe-backend openai "URL"
python scripts/transcript.py --transcribe-backend minimax-api "URL"
python scripts/transcript.py --cookies-from-browser chrome "URL"
python scripts/transcript.py --doctor
python scripts/transcript.py --dry-run "URL"
python scripts/transcript.py --force "URL"
```

`--doctor` 只诊断本地依赖和可见配置，不处理媒体。`--dry-run` 预览 metadata、候选后端、输出路径和风险，不下载媒体、不上传 API。`--force` 表示允许覆盖或重跑已有成功产物，使用前需要确认覆盖风险。

## 输出契约

每个视频写入独立目录，典型产物包括：

- `original.md`：原始语言转写稿。
- `zh.md`：需要中文稿或翻译已完成时生成。
- `metadata.json`：每个视频的事实源，记录标题、URL、来源、语言、输出路径、翻译状态和错误。
- `run-summary.json`：批量运行或显式 summary 运行的聚合事实源。

运行后先检查 `metadata.json`。如果 `needs_zh_translation` 为 `true`，再忠实翻译 `original.md`，并把 `zh.md` 写到 metadata 记录的路径。

## 引用地图

只有请求需要细节时才继续读取：

- [`references/BACKENDS.md`](references/BACKENDS.md)：字幕、OpenAI、Kimi、MiniMax 的 fallback 策略。
- [`references/OUTPUT-CONTRACT.md`](references/OUTPUT-CONTRACT.md)：文件、metadata 字段、summary schema 和状态 token。
- [`references/CHECKS.md`](references/CHECKS.md)：checkpoint、doctor/dry-run、自检、重试、force、reviewer handoff 和反馈回流。
- [`references/WEB-ACCESS.md`](references/WEB-ACCESS.md)：网页登录、cookie、动态页面或浏览器交互的确认模板、安全边界、结果交接和脱敏记录。
- [`references/CONTENT-PLAN.md`](references/CONTENT-PLAN.md)：复杂摘要、讲义、课件和富格式导出前的 `content-plan.md` 触发条件、结构、自检和示例入口。
- [`references/FORMATS-AND-MATH.md`](references/FORMATS-AND-MATH.md)：多格式输出选择、公式渲染策略、PDF 派生和 run-manifest 记录要求。
- [`references/DESIGN-AND-ANCHOR.md`](references/DESIGN-AND-ANCHOR.md)：Frontend Design checkpoint、设计 brief、富格式 anchor、渲染 QA 和可跳过边界。
- [`references/ASSETS-SCREENSHOTS.md`](references/ASSETS-SCREENSHOTS.md)：截图候选、确认后抓取/导入、跳过降级、素材 schema、placeholder/code-drawn/AI 生成素材反伪规则。
- [`references/RUN-MANIFEST.md`](references/RUN-MANIFEST.md)：富格式 `run-manifest.json` schema、dry-run 闸门、退化菜单、续跑/force/只重试失败项和完成汇报模板。
- [`references/FEEDBACK-AND-PARALLEL.md`](references/FEEDBACK-AND-PARALLEL.md)：用户反馈回流、reviewer handoff、并行写入隔离，以及中途追加或撤销格式/截图/设计选择。
- [`references/TROUBLESHOOTING.md`](references/TROUBLESHOOTING.md)：后端、endpoint、cookie、公式和媒体提取问题。

## 可选检查点摘要

- Web Access：网站需要登录、cookie、动态页面、浏览器交互或 `--cookies-from-browser` 时，先按 Web Access checkpoint 确认；用户拒绝时只使用公开可访问资料或汇报无法完成的部分。
- Content plan：复杂摘要、讲义、课件、长视频内容重构，或用户要求 HTML/PPTX/Word/DOCX/PDF 等富格式导出时，转写后生成用户可编辑的 `content-plan.md`。
- 默认轻量路径：普通公开视频 Markdown 转写不强制生成 `content-plan.md`，也不在转写后主动打断用户要求截图确认；只在完成汇报中提示这些能力可作为后续增强。

## 完成检查

- 每个已处理视频都有可解析的 `metadata.json`。
- 成功项的 `original.md` 存在且非空。
- metadata 说明中文稿已完成时，`zh.md` 存在。
- 非 Markdown 格式只有在用户已指定或已确认后生成；对应 anchor、公式 fallback、设计自检和渲染 QA 证据已记录。
- 如果进入 Web Access、截图、素材、多格式、设计或富格式 QA 阶段，产物目录必须有 `run-manifest.json`，并通过对应 reference 的 checkpoint 摘要自检。
- 默认公开视频 Markdown 转写不因这些富格式 checkpoint 被强制打断；只有登录、外发、付费、截图、多格式、设计或覆盖风险触发确认。
- 汇报输出路径、失败/跳过项、警告和下一步动作。
- 可恢复且安全的失败先重试，再汇报结果。
