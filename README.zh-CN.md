# MySkill

个人 AI skill 仓库，面向 Claude、Codex、Cursor 和 Mavis。

## Skill 列表

| Skill | 用途 |
| --- | --- |
| `video-transcript` | 从视频或播放列表 URL 生成 Markdown 转写文档。优先使用人工字幕，也可以回退到 OpenAI、Kimi 或 MiniMax API 转写，并包含数学公式转写提示。 |
| `yt-dlp-download` | 使用 `yt-dlp` 下载视频、人工字幕和缩略图，支持播放列表和浏览器 Cookie 重试。 |

## 仓库地图

| 路径 | 用途 |
| --- | --- |
| `README.md` / `README.zh-CN.md` | 仓库概览、安装目标和维护流程。 |
| [docs/SKILL-ARCHITECTURE.md](docs/SKILL-ARCHITECTURE.md) | 标准 skill 布局、reference map、manifest、schema 和 examples 规则。 |
| [docs/QUALITY-WORKFLOW.md](docs/QUALITY-WORKFLOW.md) | 共享运行检查、确认门、自检、退化、续跑和汇报规则。 |
| [docs/VALIDATION.md](docs/VALIDATION.md) | 离线验证命令和失败策略。 |
| [docs/AGENT-SKILL-PACK.md](docs/AGENT-SKILL-PACK.md) | Claude、Codex、Cursor 三端能力包矩阵、lock、状态和同步治理。 |
| `agent-skill-pack.yaml` | 三端必装能力包的期望安装矩阵。 |
| `agent-skill-pack.lock.json` | 三端能力包的示例锁定状态和后续验证输出目标。 |
| `scripts/validate_repo.py` | 离线仓库验证脚本。 |

## 标准 Skill 布局

每个 skill 必需包含：

- `SKILL.md`：简洁的 agent 入口，包含 frontmatter、默认工作流、安全策略、常用选项、输出契约、完成清单，以及需要深入文档时的 reference map。
- `scripts/`：可执行 skill 的本地辅助脚本。脚本必须能在不访问网络、不需要 API key、不需要 cookie、不下载媒体的情况下输出 `--help`。
- `agents/openai.yaml`：跨 agent 元数据，包含展示名称、短描述、默认 prompt 和调用策略。

按需可选：

- `references/`：后端策略、输出契约、检查清单、schema 或故障排查。
- `templates/`：skill 会复制或生成的文件。
- `examples/`：少量命令配方、summary 示例或边界案例，并明确标注为示例。
- `manifest.json`：仅在安装器或分发流程消费时使用的分发元数据。
- 单个 skill 的 `README.md`：可选；如果小型 skill 的 `SKILL.md` 仍能快速阅读，就不强制新增。

## 安装目标

把本仓库中的每个 skill 目录安装到各 agent 的本地 skill 目录：

| Agent | Skill 目录 |
| --- | --- |
| Claude | `%USERPROFILE%\.claude\skills` |
| Codex | `%USERPROFILE%\.codex\skills` |
| Cursor | `%USERPROFILE%\.cursor\skills` |
| Mavis | `%USERPROFILE%\.mavis\skills` |

安装后，每个 skill 都保留自己的 `SKILL.md`、`scripts`、可选 `references`、可选 `examples`、可选 `templates` 和 `agents` 文件。

## 三端必装能力包

除本仓库自带 skill 外，Claude、Codex、Cursor 本轮还需要统一治理以下必装能力：Frontend Design、docx、xlsx、pdf、pptx、Web Access。PUA 只作为 `quarantined` 候选项记录，缺失不阻塞必装能力包验证，也不得默认自动调用。

能力包以两个根文件维护：

- `agent-skill-pack.yaml`：期望矩阵，记录 `canonicalName`、别名、能力、来源、安装目标、调用名、状态、验证探针和 agent caveat。
- `agent-skill-pack.lock.json`：锁定状态，记录版本、commit、checksum、安装路径、验证时间、验证状态和 drift。

docx、xlsx、pdf、pptx 按四个独立能力治理；实际实现可以来自四个 skill，也可以来自一个文档处理 skill 包的四个能力。`xlsx` 不属于 `video-transcript` 默认输出格式，但作为三端 Office/PDF 能力包用于表格、数据摘要和后续资料整理。普通 `video-transcript` 默认仍只生成 Markdown；缺少某个格式能力时，只阻塞依赖该能力的富格式 workflow。

Mavis 保留为 README 里的既有安装目标，但不纳入本轮 Claude/Codex/Cursor 强制矩阵；Mavis 缺少上述能力不影响本 change 的必装包验证。

详见 [docs/AGENT-SKILL-PACK.md](docs/AGENT-SKILL-PACK.md)。

## RTK 命令规范

本仓库的维护命令遵循本地 RTK 规范。

推荐维护命令：

```powershell
rtk git status
rtk py -3 .\scripts\validate_repo.py
rtk py -3 -m py_compile .\scripts\validate_repo.py
```

常用 RTK 检查：

```powershell
rtk --version
rtk gain
Get-Command rtk
```

如果当前 shell 找不到 `rtk`，运行等价的直接 PowerShell 命令，并在维护报告里说明本次使用了降级路径：

```powershell
py -3 .\scripts\validate_repo.py
```

这条 RTK 规则只用于仓库维护文档，不改写各个 skill 内部的默认运行命令。

## 离线验证

重新安装或发布 skill 前运行：

```powershell
py -3 .\scripts\validate_repo.py
```

验证脚本会检查 `SKILL.md` frontmatter、`agents/openai.yaml`、必需文件、可选 manifest 形状、Python 语法、脚本 `--help`、本地 Markdown 链接、reference map 目标、JSON 示例、未清理占位标记和疑似敏感字段。它不要求网络、API key、浏览器 cookie 或媒体下载。

验证脚本还会离线检查 `agent-skill-pack.yaml` 和 `agent-skill-pack.lock.json` 是否可读、关键字段是否存在、状态 token 是否属于允许集合。它不会假装已经访问到三端真实安装目录；实际安装目录、checksum 和 drift 的验证结果应写入 lock。

## 维护清单

- 使用上面的 PowerShell 命令验证仓库。
- 确认跨 agent 元数据仍然匹配 skill 名称和 prompt token。
- 确认本地文档链接和 reference map 都能解析。
- 确认 schema、manifest、metadata、summary 和 example 文件在存在时可解析。
- 确认 `agent-skill-pack.yaml` 与 `agent-skill-pack.lock.json` 的 canonical name、状态和三端安装目标一致。
- 确认 PUA 仍是 `quarantined`，除非来源、用途、权限、安全边界、调用场景和禁止事项已经全部补齐。
- 确认 examples 体量小、明确标注为示例，且没有被当作真实产物。
- 验证通过后，把 skill 目录重新安装到所有目标 agent。

## 使用方式

可以在对话中按名称调用 skill，例如：

```text
使用 $video-transcript 从这个视频链接生成转写文档。
使用 $yt-dlp-download 下载这个视频链接。
```
