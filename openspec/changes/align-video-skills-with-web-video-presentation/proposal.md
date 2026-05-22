## 背景

`web-video-presentation` 已经沉淀出一套更成熟的工作流型 skill 形态：阶段图、一次对齐检查点、按阶段读取 reference、anchor 样张、硬性自检和事实源约定。`video-transcript` 与 `yt-dlp-download` 虽已完成基础分层，但两者的流程描述、确认门、输出事实源、自检协议和跨 agent 协作方式仍不够统一，导致用户在下载、转写、富格式导出和失败恢复之间切换时心智成本较高。

## 变更内容

- 将 `video-transcript` 和 `yt-dlp-download` 统一升级为“轻量工作流型 skill”：入口仍保持轻量，但补齐与 `web-video-presentation` 一致的阶段总览、检查点、reference map、事实源、自检和完成汇报格式。
- 为两个 skill 定义统一的阶段语言：输入识别、计划/预览、执行、可选增强、质检/自检、完成汇报；简单路径不强制停顿，高风险路径必须检查点确认。
- 为 `video-transcript` 强化 `web-video-presentation` 式的内容计划、富格式 anchor、Frontend Design 检查点、素材/占位/反伪规则和用户验收描述。
- 为 `yt-dlp-download` 增加更清晰的下载计划检查点、Web Access/cookie 确认、批量播放列表策略、输出 summary 事实源、失败恢复和自检 reference，并修正文档 schema 与脚本实际 `download-summary.json` 字段漂移。
- 统一两个 skill 的 `SKILL.md` 描述风格：先说明核心产物和默认路径，再给阶段图、工作目录约定、硬性确认门、引用地图和完成检查。
- 统一 examples、manifest、doctor/dry-run、summary/metadata/run-manifest 的字段命名和禁止记录 secret 的规则。
- 不改变 `web-video-presentation` 本身；它只作为架构参考和文案/流程模式来源。不得把 Vite/React、主题系统、录屏、章节 stepper 或旁白合成等专属机制搬进两个工具型 skill。

## 能力变更

### 新增能力

- `video-skill-workflow-alignment`：定义 `video-transcript` 与 `yt-dlp-download` 向 `web-video-presentation` 靠拢的共同工作流架构、检查点、reference map、事实源、自检、anchor 和跨 agent 质检要求。

### 修改能力

- 无。

## 影响范围

- 影响 `video-transcript/SKILL.md`、`video-transcript/references/*`、`video-transcript/templates/*`、`video-transcript/examples/*`、`video-transcript/manifest.json`。
- 影响 `yt-dlp-download/SKILL.md`、`yt-dlp-download/references/*`、`yt-dlp-download/examples/*`、`yt-dlp-download/manifest.json`。
- 可能新增 `yt-dlp-download/references/WORKFLOW.md`、`CHECKPOINTS.md`、`WEB-ACCESS.md` 或合并后的等价 reference。
- 影响 `scripts/validate_repo.py` 的验证规则，可能需要检查阶段图、reference map、summary 示例、manifest 字段和本地链接。
- 不要求重写下载或转写核心逻辑；重点是架构、文档契约、输出事实源和质检流程统一。实现阶段可按风险逐步调整脚本字段和 summary。
- 与 `expand-transcript-backend-selection` 的关系：本 change 只统一视频类 skill 工作流纪律；无人工字幕 provider 扩展仍由该 change 负责，避免两个 change 同时定义同一后端能力边界。
