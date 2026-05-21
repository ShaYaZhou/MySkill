## 1. 仓库约定

- [x] 1.1 在仓库文档中定义标准 skill 布局，包括必需文件，以及 `references/`、`templates/`、`examples/`、`manifest.json` 的可选使用规则。
- [x] 1.2 增加简洁维护清单，覆盖安装目标、跨 agent 元数据、本地验证和文档链接检查。
- [x] 1.3 明确 RTK 命令规范及当前 shell 中 `rtk` 不可用时的降级行为；该规则只用于仓库维护文档，不改写 skill 默认调用命令。
- [x] 1.4 更新 `README.md` 和 `README.zh-CN.md`，加入新的结构地图和维护工作流。

## 2. 共享质量工作流

- [x] 2.1 增加共享 skill 工作流 playbook 或 reference，定义输入识别、条件式预检门、执行、运行后真相源检查和完成汇报。
- [x] 2.2 定义高影响检查点触发条件：浏览器 cookie、登录态、付费或隐私敏感 API 上传、大批量处理、非默认输出路径和覆盖风险。
- [x] 2.3 定义完成汇报模板，要求报告输出路径、真相源文件、警告、失败项和后续动作。
- [x] 2.4 增加自检模式，要求 agent 在汇报成功前先修复可重试失败，并清楚报告无法自动修复的阻塞项。
- [x] 2.5 定义自检执行层级：当前 agent 必须能按清单完成本地自检；Agent Teams、subagent 或独立 reviewer 仅作为可用时的增强复核。
- [x] 2.6 明确不引入主题系统、skill 调用链 registry 或组合型 pipeline skill；如需这些能力，后续单独开 change。
- [x] 2.7 定义 reviewer handoff 模板，包含产物路径、真相源、检查清单、风险边界、禁止修改范围，以及 pass/fail、证据、建议和阻塞状态输出。
- [x] 2.8 定义用户反馈回流规则，要求先定位反馈层级、修改最小相关文件、更新真相源或 summary，并说明哪些派生产物需要重建。
- [x] 2.9 定义显式退化菜单：缺依赖、凭据、外部 skill 或鉴权时，提供安装/配置、换后端、跳过阶段或报告阻塞，不生成空壳产物当成功。
- [x] 2.10 定义断点续跑、`--force` 覆盖和只重试失败项语义，避免重复付费、重复上传或覆盖成功产物。

## 3. Skill 元数据与引用地图

- [x] 3.1 记录轻量 `manifest.json` schema，包括名称、版本、分类、描述、兼容性、依赖和默认输出位置；只有安装/分发流程消费它时，才为两个现有 skill 新增 manifest 文件。
- [x] 3.2 确保每个 skill 都能从 `SKILL.md` 路由到更深层文档的 reference map。
- [x] 3.3 决定每个 skill 是否必须拥有独立 README，或保持可选，并把决策一致应用到两个现有 skill。
- [x] 3.4 检查所有本地文档链接，确保 reference map 不指向缺失文件。
- [x] 3.5 定义机器可读 summary/metadata 的 schema 规则：必填字段、可选字段、状态枚举、不确定路径标记、脱敏字段和禁止记录字段。
- [x] 3.6 将能力/产物状态 token 化，例如 `source_type`、`backend`、`language_state`、`privacy_gate`、`archive_skip`、`partial_failure`、`uncertain_path`。
- [x] 3.7 明确 examples 的用途、体量上限和不要照搬原则，优先作为命令配方、summary 示例和失败/边界 case。

## 4. `video-transcript` 改造

- [x] 4.1 将稳定的转写策略细节拆分到少量聚焦 reference 中，例如 `BACKENDS.md`、`OUTPUT-CONTRACT.md`、`CHECKS.md`、`TROUBLESHOOTING.md`，避免形成文档森林。
- [x] 4.2 保持 `video-transcript/SKILL.md` 作为简洁入口，包含默认命令、回退摘要、选项摘要、检查点触发条件和 reference map。
- [x] 4.3 将 `metadata.json` 记录为运行后真相源，用于确认转写来源、语言状态、输出路径、错误和 `needs_zh_translation`。
- [x] 4.4 增加转写自检步骤，覆盖 `original.md` 非空、来源归因、预期 `zh.md` 状态、metadata 一致性、公式保留风险和未解决失败。
- [x] 4.5 增加用户确认指导：在 API 上传、付费后端、浏览器 cookie 或大型播放列表处理前必须确认。
- [x] 4.6 增加后端 fallback 阶段门：人工字幕缺失后、上传音视频前、付费 API 使用前、MiniMax endpoint 不明确时必须生成计划并等待确认。
- [x] 4.7 显式处理 MiniMax API 分支的 `requests` 依赖，纳入 venv 安装、import probe、manifest dependencies 和离线验证。
- [x] 4.8 评估并实现 `--doctor`，检查 `yt-dlp`、`openai`、`requests`、`ffmpeg/ffprobe`、OpenAI/Moonshot/MiniMax key 可见性、base URL 和可轻量探测的 endpoint 配置。
- [x] 4.9 评估并实现 `--dry-run`，预览字幕可用性、将选择的转写后端、是否需要中文翻译、预计输出路径和隐私/费用风险，不下载媒体、不上传 API。
- [x] 4.10 评估是否增加聚合型 `transcript-summary.json` 或 `run-summary.json`，汇总每个视频的 `metadata.json`、成功/失败、输出路径、`needs_zh_translation` 和后续动作。
- [x] 4.11 为 `video-transcript` 文档和 summary 设计脱敏 argv 记录，包含工作目录、关键选项、后端选择和环境变量存在性，不记录 key/token/cookie。
- [x] 4.12 明确已有 `original.md`、`zh.md`、`metadata.json` 时默认跳过、补齐或重试失败项的行为，以及 `--force` 覆盖语义。

## 5. `yt-dlp-download` 改造

- [x] 5.1 轻量整理下载策略；如果 `SKILL.md` 仍可快速阅读，则只补输出契约和自检段落，必要时才新增一个聚焦 reference。
- [x] 5.2 保持 `yt-dlp-download/SKILL.md` 作为简洁入口，包含默认命令、策略摘要、选项摘要、检查点触发条件和 reference map。
- [x] 5.3 记录预期输出产物：媒体文件、字幕 sidecar、缩略图 sidecar、临时文件和 `.yt-dlp-archive.txt`。
- [x] 5.4 增加下载自检步骤，覆盖已完成媒体、已选择字幕、缩略图、被 archive 跳过的条目、单项失败和重试建议。
- [x] 5.5 增加用户确认指导：仅在请求含糊、agent 自行选择、存在覆盖风险、cookie/登录态、隐私上传或付费 API 风险时确认；用户明确指定的 audio-only 或输出路径不重复确认。
- [x] 5.6 增加 `download-summary.json` 或等价机器可读 report，记录输入 URL、标题/id、播放列表位置、输出文件、字幕语言、缩略图、archive skip、失败项、警告和不确定路径。
- [x] 5.7 评估并实现 `--doctor`，检查 `yt-dlp`、`ffmpeg/ffprobe`、输出目录可写性、浏览器 cookie 配置可用性和 venv 状态。
- [x] 5.8 评估并实现 `--dry-run`，预览 metadata、播放列表条目、字幕语言选择、输出模板、archive 文件和潜在 cookie/格式风险，不下载媒体。
- [x] 5.9 明确 existing file skip、archive skip、`--force` 覆盖、只重试失败项和不确定路径标记的语义。
- [x] 5.10 为 `download-summary.json` 记录脱敏 argv、工作目录、关键选项、工具版本和失败重试建议。

## 6. 验证与测试框架

- [x] 6.1 增加离线验证脚本或文档化命令集，检查 `SKILL.md` frontmatter、`agents/*.yaml`、可选 manifest 和必需文件是否存在。
- [x] 6.2 验证 Python 辅助脚本语法和 `--help` 输出，且不要求网络访问、API key、cookie 或媒体下载。
- [x] 6.3 为仓库文档和每个 skill 的 reference map 增加本地 Markdown/reference 链接验证。
- [x] 6.4 在可行且不重构核心脚本的前提下增加轻量纯函数测试或 fixture，覆盖重复工具行为，例如语言匹配、安全路径名、字幕清理和播放列表条目处理。
- [x] 6.5 验证 `--doctor` 和 `--dry-run` 在无 URL、无 API key、无网络的情况下能给出可解释结果或明确降级提示。
- [x] 6.6 评估是否抽取共享 Python helper；仅在能减少重复且不破坏每个 skill 独立 `.venv` 的前提下抽取语言匹配、路径清理、subprocess 运行和 playlist 展开等逻辑。
- [x] 6.7 验证 schema 示例、summary 示例、manifest 示例和 examples 不包含过期链接、未替换 TODO、伪真实产物或敏感值。
- [x] 6.8 README 和 reference 中的用户可复现命令优先提供 PowerShell 版本，必要时补 bash 版本。
- [x] 6.9 把 reference map 缺失文件、schema 不可解析、agent yaml 不一致和示例冒充真实产物作为阻断级验证问题。

## 7. 轻量示例

- [x] 7.1 决定 examples 的位置和体量，优先采用轻量命令配方与典型输出结构，不照搬 `web-video-presentation` 的大型案例目录。
- [x] 7.2 为 `video-transcript` 增加 1-2 个命令示例和一个典型 `metadata.json` 或聚合 summary 示例。
- [x] 7.3 为 `yt-dlp-download` 增加 1-2 个命令示例和一个典型 `download-summary.json` 示例。
- [x] 7.4 在每个示例中标注用途、适用边界、体量上限和不要照搬，避免 examples 变成模板库。

## 8. 最终验证

- [x] 8.1 对 `improve-skill-architecture` 运行 OpenSpec 校验。
- [x] 8.2 运行离线 skill 验证路径，并修复所有报告的问题。
- [x] 8.3 人工确认两个 skill 在快速阅读 `SKILL.md` 时仍能找到默认命令、常用选项、故障排查路径和安全边界。
- [x] 8.4 确认没有任务把 web-video 专属的 Vite、React、主题、音频或录屏实现细节引入这些工具型 skill。

