# 运行 Manifest、Dry-run 与完成汇报

本文定义富格式、截图、Web Access、设计或高成本阶段的 `run-manifest.json`。每视频 `metadata.json` 是转写事实源，`content-plan.md` 是复杂导出的内容规划源，产物目录下的 `run-manifest.json` 是单次运行聚合事实源。skill 根目录的 `manifest.json` 只用于可选分发元数据，不得记录真实运行、用户输入、登录态或产物状态。

## 触发条件

任一条件成立时必须生成或更新 `run-manifest.json`：

- 使用 Web Access、浏览器登录态或受限页面。
- 抓取、导入或跳过截图 checkpoint。
- 生成 HTML、PPTX、Word/DOCX、PDF 等 Markdown 以外格式。
- 使用 Frontend Design、富格式 anchor 或渲染 QA。
- 使用付费后端、外发上传、大型播放列表或高成本渲染。
- 需要记录公式降级、素材、placeholder、失败项或后续动作。

普通公开视频只生成 Markdown 转写时，可以只依赖每视频 `metadata.json` 和可选 `run-summary.json`。

## Schema 摘要

建议顶层字段：

```json
{
  "schema_version": 1,
  "run_id": "vt-2026-05-22-demo",
  "contract_note": "只说明契约，不代表真实产物",
  "status": "partial",
  "inputs": [],
  "metadata_refs": [],
  "content_plan": {},
  "web_access": {},
  "formats": [],
  "outputs": [],
  "hashes": [],
  "formula_fallbacks": [],
  "assets": [],
  "screenshots": [],
  "design_checks": [],
  "qa_evidence": [],
  "redacted_argv": [],
  "privacy_and_copyright": {},
  "tool_versions": {},
  "failures": [],
  "next_actions": []
}
```

核心字段说明：

- `schema_version`：manifest 契约版本。
- `run_id`：单次运行 id，建议包含日期和短随机或短 hash。
- `status`：`ok`、`partial`、`failed`、`blocked`、`skipped`。
- `inputs[]`：URL、播放列表条目、用户文件、格式请求、确认状态。
- `metadata_refs[]`：每个视频的 `metadata.json` 路径、video id、状态和 hash。
- `content_plan`：`content-plan.md` 路径、是否生成、hash、自检状态。
- `web_access`：脱敏授权范围、访问时间、抓取结果、本地残留文件、清理状态。
- `formats[]`：Markdown、HTML、PPTX、Word/DOCX、PDF 的 selected/skipped/failed 状态、依赖 skill 和降级原因。
- `outputs[]`：每个产物路径、格式、来源、hash、状态。
- `hashes[]`：文件 hash 列表，避免只靠目录扫描判断成功。
- `formula_fallbacks[]`：源 LaTeX、目标格式、fallback 类型、alt text、降级原因、验证结果。
- `assets[]`：素材清单，详见 `ASSETS-SCREENSHOTS.md`。
- `screenshots[]`：截图候选、确认、抓取、跳过和引用状态。
- `design_checks[]`：设计 brief、anchor 验收、版式检查和是否阻塞。
- `qa_evidence[]`：HTML viewport 截图、PPTX/Word/DOCX/PDF 渲染图、页码或 slide、证据 hash。
- `redacted_argv[]`：脱敏命令行，只保留必要参数，不记录 secret 或敏感路径。
- `privacy_and_copyright`：授权、外发、脱敏、清理和版权风险处理。
- `tool_versions`：脚本、Python、yt-dlp、ffmpeg、渲染工具、相关 skill 或插件版本。
- `failures[]`：失败阶段、原因、可恢复性和最小下一步。
- `next_actions[]`：待补素材、需要用户确认、可重试失败项。

禁止记录：密码、token、会话值、完整敏感浏览器 profile 路径、私密 HTML、未脱敏账号信息、真实 API key。

## 格式状态

`formats[]` 中每项建议字段：

```json
{
  "format": "pptx",
  "requested": true,
  "selected": true,
  "status": "blocked",
  "reason": "pptx skill missing",
  "output_path": null,
  "required_skill": "pptx",
  "fallback": "html"
}
```

状态值：

- `ok`：文件存在、hash 已记录、自检通过。
- `skipped`：用户或策略明确跳过。
- `blocked`：缺工具、缺授权、缺确认或风险未解除。
- `failed`：执行失败，需要修复或重试。
- `pending`：已选择但尚未执行，不能作为完成状态汇报。

## Dry-run 硬闸门

以下阶段执行前必须先 dry-run 并等待确认：

- API 上传、付费后端或外发处理。
- Web Access、浏览器登录态或受限页面访问。
- 大型播放列表、批量下载、长视频分片。
- 多格式批量渲染、截图抓取、设计 anchor 批量展开。
- 覆盖已有成功产物或 `--force`。

Dry-run 清单至少包含：

- 输入 URL 或文件数量。
- 预计后端和是否下载/上传。
- 可能分片数和成本/外发风险。
- 已有产物处理：skip、retry failed、force。
- 所需工具或 skill：Web Access、Frontend Design、docx、pptx、pdf 等。
- 预计输出路径和会写入的事实源。
- 跳过项、阻塞项和用户可选退化路径。

确认语建议：

```text
确认后我会执行上述高成本/外发步骤；如要避免外发，可选择只用已有字幕、跳过截图或只生成 Markdown。
```

## 显式退化菜单

缺工具、未鉴权或风险未确认时，不得生成空壳产物当成功。给用户菜单：

```text
当前阶段被阻塞：<stage>
原因：<missing tool/auth/risk>

可选：
1. 安装或配置缺失工具后重试该阶段。
2. 换用可用后端或较低成本格式。
3. 跳过该阶段，并在 run-manifest.json 标记为 skipped。
4. 只重试已有失败项，保留成功产物。
```

写入规则：

- 用户选择安装/配置但尚未完成：`blocked`。
- 用户明确不要该阶段：`skipped`。
- 有替代格式成功：原格式 `skipped` 或 `blocked`，替代格式 `ok`，并记录原因。

## 续跑、Force 与只重试失败项

默认续跑策略：

- 已有成功 `metadata.json`、`content-plan.md`、输出文件和 hash 时复用。
- 只重试 `failed` 或用户指定的 `blocked` 阶段。
- 不重复上传、不重复付费、不覆盖成功产物。
- 新增格式只读取既有转写真相源和内容计划，不重跑全流程。

`--force` 或等价明确请求才允许覆盖成功产物。执行前必须 dry-run 说明会覆盖哪些文件、哪些阶段可能重复付费或外发，并在 `run-manifest.json.next_actions` 或 `failures` 中记录覆盖原因。

## 完成汇报模板

富格式运行完成时，按阶段汇报：

```text
完成状态：<ok/partial/blocked>
运行事实源：<run-manifest.json path>

- Markdown：<ok/skipped/failed> <path/原因>
- content-plan：<ok/skipped/failed> <path/原因>
- HTML：<ok/skipped/failed> <path/原因>
- PPTX：<ok/skipped/failed> <path/原因>
- Word/DOCX：<ok/skipped/failed> <path/原因>
- PDF：<ok/skipped/failed> <path/原因>
- 截图：<数量/跳过/阻塞> <关键风险>
- 素材：<数量/placeholder 待补>
- Web Access：<未使用/已脱敏记录/已清理/阻塞>
- 设计检查：<通过/未启用/阻塞>
- QA 证据：<路径/缺失原因>
- 后续动作：<最小下一步>
```

## 完成前自检

汇报成功前必须检查：

- 所有 selected 格式都有存在的文件、hash 和状态。
- `metadata_refs[]` 指向可解析 `metadata.json`。
- `content_plan.path` 存在时 hash 与自检状态记录完整。
- 公式降级条目有源 LaTeX、alt text、降级原因和验证结果。
- `assets[]` 与 `screenshots[]` 引用路径存在，placeholder 明确标注。
- 设计检查和 QA 证据满足所选格式；复杂 HTML/PPTX/Word/DOCX 已完成 anchor 验收或记录用户跳过风险。
- 脱敏 argv、隐私版权处理和工具版本已记录。
- 失败项有最小可执行下一步。

任何选定格式缺文件、缺 hash、缺 QA 证据或素材伪装为真实来源时，不得汇报为成功。
