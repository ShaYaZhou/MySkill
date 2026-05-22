# 反馈回流、Reviewer 交接与并行隔离

本文定义富格式 `video-transcript` 工作流中的协作规则。原则是：先定位反馈层级，再修改最小产物切片；并行 agent 不直接争写聚合事实源。

## 用户反馈回流

收到反馈后先归类：

- 转写：修改 `original.md`、`zh.md` 或重新生成对应视频的 `metadata.json` 状态。
- 内容计划：修改 `content-plan.md` 的 section、beat、evidence pool、must-keep、格式映射。
- 公式：修改源 LaTeX、公式上下文或 `formula_fallbacks[]`，并标记受影响格式。
- 截图/素材：修改 `assets[]`、`screenshots[]`、引用位置、alt text、placeholder 或脱敏处理。
- 设计：修改设计 brief、anchor、版式实现或 `design_checks[]`。
- 格式导出：只重建受影响的 HTML、PPTX、Word/DOCX、PDF 子目录或文件。
- 安装能力：更新安装治理事实，不把缺 skill 误写成产物失败。

反馈处理步骤：

1. 找到真相源：`metadata.json`、`content-plan.md` 或 `run-manifest.json`。
2. 标出受影响派生产物，不立即全量重跑。
3. 修改最小切片，并更新 hash、状态和 next action。
4. 只重建必要格式；默认保留未受影响的成功产物。
5. 汇报改了什么、哪些派生产物已重建、哪些仍需用户确认。

示例：

```text
反馈层级：截图/素材
已修改：assets[] 中 asset-003 的 alt text 和外发限制
已重建：HTML section-4、PPTX slide-08
未重建：Markdown、DOCX，因为未引用该素材
仍需确认：placeholder asset-006 是否由用户提供图片替换
```

## Reviewer 交接模板

需要 reviewer、Agent Teams 或 subagent 复核时，交接必须限制范围：

```text
Reviewer handoff

目标：复核 <产物/阶段>
产物路径：
- run manifest: <path>
- metadata refs: <paths>
- content plan: <path or skipped>
- outputs: <paths>

真相源：
- 转写事实以 metadata.json 和 original.md 为准。
- 内容结构以 content-plan.md 为准。
- 截图、素材、格式、QA 以 run-manifest.json 为准。

检查清单：
- 内容忠实和 must-keep 未丢失。
- 公式源和 fallback 记录完整。
- 截图/素材来源、alt text、授权和反伪规则通过。
- HTML/PPTX/Word/DOCX/PDF 文件存在、hash 和 QA 证据存在。
- 隐私、版权和脱敏边界没有越界。

风险边界：
- 不读取、不输出、不记录 secret、登录值、私密 HTML 或敏感 profile 路径。
- 不绕过访问控制、DRM、付费限制或水印限制。

禁止修改范围：
- 不直接修改聚合 run-manifest.json。
- 不覆盖已成功产物。
- 不改其他 agent 的视频目录或格式子目录。

请返回：
- pass/fail
- 证据路径或具体位置
- 修复建议
- 是否阻塞完成汇报
```

Reviewer 输出应能被主 agent 汇总进 `run-manifest.json.design_checks[]`、`qa_evidence[]`、`failures[]` 或 `next_actions[]`。

## 并行写入隔离

并行 agent 的写入边界：

- 每个 agent 只写分配给自己的视频目录、格式子目录或临时 report。
- 格式 worker 可以写 `html/`、`pptx/`、`docx/`、`pdf/` 等专属子目录，但不改其他格式目录。
- 截图/素材 worker 可以写 `assets/` 中分配的 id 范围，或写临时素材 report。
- reviewer 默认只读；如需写入，只写 review report。
- 聚合 `run-manifest.json` 只由主 agent 汇总，其他 agent 不直接修改。

推荐临时 report 命名：

```text
.work/reports/<agent-id>-<stage>.json
.work/reports/<agent-id>-review.md
```

主 agent 汇总时负责：

- 校验素材 id、截图 id 和输出路径不冲突。
- 合并 hash、QA 证据、失败项和 next action。
- 解决同一格式或同一素材的状态冲突。
- 把并行 agent 的临时 report 路径记录为证据，而不是把未核验内容直接当事实。

## 冲突处理

常见冲突与处理：

- 两个 agent 写同一素材 id：保留先确认的 id，后者重命名并更新引用。
- 一个 agent 标记格式 ok，reviewer 标记 fail：最终状态为 `failed` 或 `blocked`，直到主 agent 修复并重新 QA。
- 用户撤销某格式，格式 worker 已生成文件：保留文件但在 manifest 标为 `skipped-by-user` 或移入归档目录，完成汇报说明未采用。
- 用户追加格式，已有转写和内容计划可复用：新增格式只读真相源并生成自己的子目录。

## 中途追加或撤销

追加格式、截图或设计选择时：

- 复用已有 `metadata.json` 和 `content-plan.md`。
- 只新增对应 `formats[]`、`assets[]`、`screenshots[]`、`design_checks[]` 和 `qa_evidence[]`。
- 对新增的高成本、外发或登录态阶段重新 dry-run。
- 不重跑已成功转写，除非用户反馈转写事实错误。

撤销格式、截图或设计选择时：

- 不删除事实源；在 `run-manifest.json` 记录用户撤销时间、范围和原因。
- 未发布的派生产物可标记为 `skipped` 或 `superseded`。
- 已被其他格式引用的素材必须先检查引用关系，再替换为文字、公式、code-drawn 或 placeholder。
- 完成汇报说明哪些文件保留但未采用。

## 反馈自检

每次反馈回流或并行汇总后检查：

- 真相源归属没有混乱：转写归 `metadata.json`，内容归 `content-plan.md`，运行聚合归 `run-manifest.json`。
- 修改范围与反馈层级匹配，没有无关重写。
- 受影响派生产物的 hash、QA 证据和状态已更新。
- 并行 report 已汇总或明确保留为未处理。
- 用户新增或撤销的选择不会触发不必要的重复付费、重复上传或覆盖成功产物。
