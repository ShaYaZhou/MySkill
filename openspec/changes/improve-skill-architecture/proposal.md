## 背景 / 动机

当前仓库里的 skill 很实用，但整体仍偏“脚本包装”：每个 skill 有一个简洁的 `SKILL.md`、一个辅助脚本和少量 agent 元数据。`web-video-presentation` 展示了更成熟的可复用 skill 形态：阶段化工作流、引用地图、自检协议、模板、生成资产和清晰的产物契约。

本变更要吸收这些值得借鉴的结构和交付纪律，同时避免把小型工具 skill 膨胀成大型框架。

## 变更内容

- 定义本仓库的标准 skill 信息架构，包括何时使用 `references/`、`templates/`、`scripts/`、`agents/`、示例和 manifest。
- 增加可按需采用的工作流与质量模式：阶段化执行、检查点、自检清单、输出契约和故障交接。
- 增加共享维护规范，覆盖安装、验证、依赖隔离和跨 agent 元数据。
- 将 reference map、schema 示例、summary 示例和可复现命令纳入离线验证，避免文档地图漂移。
- 增加显式退化、断点续跑、reviewer handoff、反馈回流和脱敏 argv 记录等可靠性规则。
- 先通过聚焦文档和轻量验证改造 `video-transcript` 与 `yt-dlp-download`，不重写它们的核心脚本。
- 保持工具型 skill 的轻量感：借鉴 `web-video-presentation` 的纪律，而不是照搬它的体量。

## 能力

### 新增能力

- `skill-architecture`：每个 skill 的标准结构、文档地图、产物契约和仓库约定。
- `skill-quality-workflow`：skill 执行与维护过程中的运行时检查点、自检要求、验证命令和失败交接行为。

### 修改能力

无。当前仓库还没有已有 OpenSpec capability。

## 影响

- 受影响的 skill 目录：`video-transcript/`、`yt-dlp-download/`。
- 受影响的仓库文档：`README.md`、`README.zh-CN.md`。
- 可能新增的共享资产：按需增加轻量 `references/`、`templates/` 或验证文档。
- 不破坏 `scripts/download.py` 或 `scripts/transcript.py` 的既有命令行行为；允许新增向后兼容的 `--doctor`、`--dry-run`、summary 等 additive 能力。
