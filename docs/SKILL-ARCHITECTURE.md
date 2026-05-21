# Skill 架构

本仓库采用分层 skill 布局：入口保持轻，稳定细节放到 reference；只有当验证、分发或复用确实需要时，才增加 templates、examples 或 manifest。

## 标准布局

每个 skill 目录必须包含：

- `SKILL.md`：agent 入口，包含 YAML frontmatter、调用条件、默认流程、安全策略、常用选项、输出契约、完成检查，以及需要深入文档时的引用地图。
- `scripts/`：执行本地工作的辅助脚本。Python 脚本必须能在无网络、无 API key、无 cookie、无媒体下载的情况下输出 `--help`。
- `agents/openai.yaml`：面向 OpenAI/Codex 的元数据，包含展示名、短描述、默认 prompt 和调用策略。

按需可选：

- `references/`：稳定的深入说明，例如后端矩阵、输出契约、检查清单、schema 和排障。
- `templates/`：skill 会复制或生成的文件；不要为一次性例子新增模板。
- `examples/`：轻量命令配方、summary 示例和边界/失败案例。示例必须标注为示例，不能伪装成真实产物。
- `manifest.json`：可选分发元数据，只在安装器或打包流程消费它时使用。
- `README.md`：可选的人类说明；如果 `SKILL.md` 仍能快速阅读，就不强制新增。

小型单脚本 skill 可以保持 `SKILL.md`、`scripts/`、`agents/` 加短输出契约。工作流型 skill 可以按需增加 references、templates、examples、fixtures 或 manifests。

## `SKILL.md` 契约

`SKILL.md` 应在首次使用时直接回答：

- 什么时候使用这个 skill。
- 最安全的默认命令是什么。
- 哪些选项足够常用，需要写在入口。
- 哪些动作必须先取得用户确认。
- 会生成哪些文件，写到哪里。
- 运行后的事实源是哪一个 metadata 或 summary。
- 非默认情况应该读哪个 reference。

如果某段内容已经影响快速阅读，把稳定细节移到 `references/`，在 `SKILL.md` 留摘要和链接。

## 引用地图规则

引用地图是路由表，不是装饰列表。

- 每个本地 reference 链接都必须指向存在的文件。
- 重命名、合并或删除 reference 时，必须同步更新 `SKILL.md`、根 README 和可选的 per-skill README。
- 缺失 reference 文件是阻断级验证失败。
- 一个 reference 应只负责一类问题：后端策略、输出契约、检查、排障、schema 或示例。

当前建议：

- `video-transcript/SKILL.md` 可路由到 `references/BACKENDS.md`、`references/OUTPUT-CONTRACT.md`、`references/CHECKS.md` 和 `references/TROUBLESHOOTING.md`。
- `yt-dlp-download/SKILL.md` 可以保持一个聚焦 reference，只要入口里仍保留默认命令、常用选项、安全边界、输出契约和自检说明。

## Manifest Schema

`manifest.json` 是可选分发元数据。只有安装或分发工具消费它时才新增。存在时必须是合法 JSON，并包含：

- `name`：skill 目录名。
- `version`：语义化或日期型版本。
- `category`：稳定分类，例如 `video`、`download`、`transcript` 或 `workflow`。
- `description`：简短人类可读描述。
- `compat`：支持的 agent 或运行时列表。
- `dependencies`：外部命令、Python 包、API provider 和可选凭据。
- `default_output_dir`：默认输出目录。

`manifest.json` 只描述分发能力；单次运行事实源仍属于实际输出的 metadata、summary 或 run manifest。

## Summary 与 Metadata Schema 规则

机器可读 summary 和 metadata 必须区分必填字段、可选字段、状态 token 和禁止字段。

运行级 summary 建议包含：

- `schema_version`
- `tool`
- `mode`
- `argv`
- `cwd`
- `items`
- `warnings`
- `failures`

单项记录建议包含：

- `input_url` 或 `url`
- `status`
- `output_paths`
- `truth_source` 或 metadata/summary 路径
- `warnings`
- `errors` 或 `failures`

推荐状态 token：

- 转写：`source_type`、`backend`、`language_state`、`needs_zh_translation`、`privacy_gate`、`partial_failure`、`uncertain_path`。
- 下载：`media`、`subtitle`、`thumbnail`、`archive_skip`、`partial_failure`、`uncertain_path`。

稳定 `status` 值应显式：`success`、`ok`、`skipped`、`blocked`、`failed`、`partial_failure` 或 `dry_run`。

禁止字段：

- 原始 API key、token、cookie、authorization header、浏览器 session value 或完整环境变量 dump。
- 未标注为示例的伪造文件路径。
- 声称自动字幕或 API 转写已经被验证为人工文本。

可以记录脱敏 argv、工作目录、关键选项、后端选择、工具版本和重要环境变量是否存在。只记录存在性，不记录 secret 值。

## Examples 规则

examples 只有在能澄清命令、输出契约或边界案例时才有价值。

- 保持小体量：每个 skill 一到两个命令配方和一个紧凑 JSON summary 示例通常就够。
- 优先 PowerShell 命令；只有对非 Windows 用户有帮助时才补 bash。
- 示例输出必须标注为示例。
- 使用 `https://example.invalid/video` 这类占位 URL，以及 `D:/example-output` 这类占位路径。
- 不把大型真实输出复制到 examples。
- 除非 skill 真正生成项目，否则不要把 examples 做成项目模板库。

## 维护清单

发布或重新安装 skill 前：

- 确认每个 skill 有 `SKILL.md`、`scripts/` 和 `agents/openai.yaml`。
- 确认 `SKILL.md` frontmatter 的 `name` 匹配目录名。
- 确认 `agents/openai.yaml` 的 default prompt 提到同名 skill token。
- 确认 reference map 链接能在本地解析。
- 确认 schema 和 example JSON 可解析。
- 确认 Python helper 能编译且 `--help` 可离线运行。
- 确认文档优先提供 PowerShell 命令。
- 验证通过后，把 skill 目录重新安装到所有支持的 agent 目标。
