# Agent Skill 能力包安装治理

本文定义 Claude、Codex、Cursor 三端统一能力包。它只治理跨 agent 必装能力、隔离候选项、安装目标、验证状态和同步维护；不修改任何具体 skill 的业务脚本。

## 范围

本轮强制矩阵只覆盖：

| Agent | 本轮状态 | 默认 skill 目录 |
| --- | --- | --- |
| Claude | 纳入必装能力包验证 | `%USERPROFILE%\.claude\skills` |
| Codex | 纳入必装能力包验证 | `%USERPROFILE%\.codex\skills` |
| Cursor | 纳入必装能力包验证 | `%USERPROFILE%\.cursor\skills` |
| Mavis | 保留为仓库既有安装目标，不纳入本轮强制矩阵 | `%USERPROFILE%\.mavis\skills` |

Mavis 后续可以单独扩展到同一治理模型，但本 change 不把 Mavis 缺失能力视为阻断项。

## 必装能力矩阵

Claude、Codex、Cursor 都必须具备以下能力。矩阵中的 canonical name 是跨 agent 汇报、lock 和 drift 检查使用的稳定名称；别名用于匹配各 agent 本地实际命名。

| 能力 | Canonical name | 常用别名 | 状态 | Claude 目标 | Codex 目标 | Cursor 目标 |
| --- | --- | --- | --- | --- | --- | --- |
| 前端设计 | `frontend-design` | `Frontend Design Skill`, `frontend-design-skill`, `design` | `required` | `%USERPROFILE%\.claude\skills\frontend-design` | `%USERPROFILE%\.codex\skills\frontend-design` | `%USERPROFILE%\.cursor\skills\frontend-design` |
| Word/DOCX | `docx` | `docx Skill`, `documents`, `word` | `required` | `%USERPROFILE%\.claude\skills\docx` | `%USERPROFILE%\.codex\skills\docx` | `%USERPROFILE%\.cursor\skills\docx` |
| Excel/XLSX | `xlsx` | `xlsx Skill`, `spreadsheets`, `excel` | `required` | `%USERPROFILE%\.claude\skills\xlsx` | `%USERPROFILE%\.codex\skills\xlsx` | `%USERPROFILE%\.cursor\skills\xlsx` |
| PDF | `pdf` | `pdf Skill`, `pdf-export`, `render-pdf` | `required` | `%USERPROFILE%\.claude\skills\pdf` | `%USERPROFILE%\.codex\skills\pdf` | `%USERPROFILE%\.cursor\skills\pdf` |
| PowerPoint/PPTX | `pptx` | `pptx Skill`, `presentations`, `slides` | `required` | `%USERPROFILE%\.claude\skills\pptx` | `%USERPROFILE%\.codex\skills\pptx` | `%USERPROFILE%\.cursor\skills\pptx` |
| 网页访问 | `web-access` | `Web Access Skill`, `browser`, `web-access-skill` | `required` | `%USERPROFILE%\.claude\skills\web-access` | `%USERPROFILE%\.codex\skills\web-access` | `%USERPROFILE%\.cursor\skills\web-access` |
| PUA 候选 | `pua` | `PUA Skill`, `persuasion-audit`, `unsafe-persuasion` | `quarantined` | `%USERPROFILE%\.claude\skills\pua` | `%USERPROFILE%\.codex\skills\pua` | `%USERPROFILE%\.cursor\skills\pua` |

PUA 只作为隔离候选项记录。缺少 PUA 不阻塞必装能力包验证；任何 agent 都不得把 PUA 声明为默认可调用、自动调用或推荐调用能力，除非其来源、用途、权限、安全边界、调用场景和禁止事项全部补齐并经过人工提升状态。

## 能力与输出格式映射

`docx`、`xlsx`、`pdf`、`pptx` 在治理上按四个独立能力记录。实际实现可以是四个独立 skill，也可以是一个文档处理 skill 包暴露出的四个能力；无论实现形态如何，`agent-skill-pack.yaml` 必须逐项记录能力映射、调用名、安装目标和验证探针。

| 能力 | `video-transcript` 关系 | 默认输出 | 说明 |
| --- | --- | --- | --- |
| `docx` | Word/DOCX 富格式导出依赖 | 否 | 用户明确选择 Word/DOCX、讲义或可编辑文档时才需要。 |
| `xlsx` | 表格、数据摘要、后续资料整理依赖 | 否 | `xlsx` 不属于 `video-transcript` 默认输出格式，但属于三端 Office/PDF 能力包。 |
| `pdf` | PDF 派生导出依赖 | 否 | 本轮默认 PDF 从 HTML、DOCX 或 PPTX 派生，并记录来源格式。 |
| `pptx` | PPT/PPTX 课件或演示导出依赖 | 否 | 用户明确选择 PPTX 或课件输出时才需要。 |

`video-transcript` 的默认输出仍是 Markdown。缺少某个格式能力时，只阻塞依赖该能力的富格式 workflow，不应阻塞普通 Markdown 转写。

## `agent-skill-pack.yaml` 字段

根目录 `agent-skill-pack.yaml` 是期望安装矩阵。每个 `skills[]` 条目必须包含：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `canonicalName` | 是 | 跨 agent 稳定名称，使用小写短横线。 |
| `aliases` | 是 | 可匹配的本地名称、插件名或旧称。 |
| `capability` | 是 | 能力归类，例如 `frontend-design`、`office-docx`、`web-access`。 |
| `source.kind` | 是 | 来源类型，例如 `local`、`plugin`、`external`、`manual`。 |
| `source.path` / `source.url` | 至少一个 | 本地来源路径或外部来源 URL；未知时必须写明 `manual-review-required`。 |
| `installTargets` | 是 | Claude、Codex、Cursor 的安装路径、调用名和 caveat。 |
| `callName` | 是 | 默认调用名。若三端不同，在 `installTargets[].callName` 覆盖。 |
| `status` | 是 | 只允许 `required`、`optional`、`quarantined`。 |
| `verificationProbe` | 是 | 离线验证探针，例如检查 `SKILL.md`、manifest、适配器或帮助文本。 |
| `agent caveat` | 是 | 每个 agent 的调用差异、权限提示或限制。 |

清单不得记录密码、cookie、token、会话值或私密浏览器 profile。Web Access 的登录态只在单次运行的脱敏 manifest 中记录授权范围，不写入安装包清单。

## `agent-skill-pack.lock.json` 字段

根目录 `agent-skill-pack.lock.json` 是示例锁定状态和后续安装验证输出目标。每个条目必须记录：

| 字段 | 说明 |
| --- | --- |
| `canonicalName` | 对应 YAML 中的 canonical name。 |
| `version` | 语义化版本、日期版本或 `unknown`。 |
| `commit` | 来源仓库 commit；没有时写 `unknown`。 |
| `checksum` | 来源文件或安装目录 checksum；没有时写 `unknown`。 |
| `source` | 锁定时使用的来源 kind/path/url。 |
| `installations[]` | 每个 agent 的安装路径、验证时间、验证状态和探针结果。 |
| `status` | 聚合验证状态，只允许 `ok`、`missing`、`drift`、`unverified`、`quarantined`。 |
| `drift` | 是否发现版本、checksum、调用名或安装内容漂移，以及期望值和实际值。 |

示例 lock 可以包含 `unverified`，表示当前机器无法证明安装存在；它不得把未验证安装写成 `ok`。

## 验证状态与阻塞规则

| 状态 | 含义 | 是否阻塞 |
| --- | --- | --- |
| `ok` | 已找到安装目录，元数据可读，调用名和探针匹配。 | 不阻塞。 |
| `missing` | 必装能力在目标 agent 缺失。 | 阻塞依赖该能力的 workflow。 |
| `drift` | 同一 canonical skill 在版本、checksum、调用名或来源上不一致。 | 阻塞发布或同步；可由维护者记录有意差异后解除。 |
| `unverified` | 当前机器无法访问目标目录或缺少验证证据。 | 不等同失败，但阻塞声明“三端已验证”。 |
| `quarantined` | 仅作为隔离候选记录，默认禁用。 | 不阻塞必装包验证；阻塞任何默认调用。 |

安装验证应检查三个 agent 的 skill 目录、`SKILL.md` 或 manifest、版本或来源标识、调用名、agent-specific invocation adapter、验证探针和缺失项。当前仓库离线脚本只检查 YAML/lock 的可读性、关键字段和状态 token；实际复制、checksum 和 agent 目录探测可由后续安装器或人工验证补充。

## PUA 隔离规则

PUA 候选项必须保持 `quarantined`，直到以下信息全部存在：

- 来源：来源仓库、作者、版本、许可证或内部维护者。
- 用途：它解决什么工作流问题，为什么需要跨 agent 安装。
- 权限：是否访问网络、浏览器、剪贴板、本地文件、模型外发或用户隐私数据。
- 安全边界：不得操控用户、不得规避平台规则、不得扩大权限、不得隐藏意图。
- 调用场景：只能由用户明确点名，还是可被某类 workflow 间接调用。
- 禁止事项：默认自动调用、无用户确认调用、处理敏感个人关系或诱导性话术、绕过 agent 安全策略。

缺少任一项时，PUA 不参与必装验证成功率，也不能在 README 或 skill 入口中宣传为可用能力。

## 维护流程

1. 维护 `agent-skill-pack.yaml` 的期望矩阵，所有文档中的 canonical name 和别名以它为准。
2. 安装或同步 Claude、Codex、Cursor 的能力 skill。
3. 记录或更新 `agent-skill-pack.lock.json` 的版本、commit、checksum、安装路径和验证时间。
4. 运行离线验证：

```powershell
py -3 .\scripts\validate_repo.py
```

5. 如果状态为 `missing`、`drift` 或 `unverified`，在维护报告中说明影响的 agent、能力和 workflow。
6. 不要因为 PUA 缺失而阻断必装能力包；只要 PUA 仍是 `quarantined`，它的缺失属于预期隔离状态。
