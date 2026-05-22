## 1. 基线审计

- [ ] 对比 `web-video-presentation`、`video-transcript`、`yt-dlp-download` 的入口结构、引用地图、示例、manifest 和检查点文案。
- [ ] 记录 `video-transcript` 当前事实源分层，重点确认 `metadata.json`、`run-summary.json`、`run-manifest.json` 的用途边界。
- [ ] 记录 `yt-dlp-download` 脚本实际生成的 summary schema，并与文档示例逐项比对。
- [ ] 找出可能误导读者的表述，避免让人以为 `video-transcript` 或 `yt-dlp-download` 已经包含演示页渲染、旁白合成或 Web 应用生成能力。

## 2. 共享工作流对齐

- [ ] 更新两个 skill 的入口，让 `SKILL.md` 作为简洁工作流控制器，并让阶段命名与 `web-video-presentation` 的做法保持一致。
- [ ] 为两个 skill 新增或更新阶段化引用地图，覆盖输入识别、计划或 dry-run 预览、执行、可选增强、质检和最终汇报。
- [ ] 统一风险触发式检查点：登录/cookies、付费或上传 API 处理、大型播放列表、缺人工字幕、高成本输出、可发布富文档。
- [ ] 保持简单路径轻量：普通下载和普通 Markdown 转写必须能直接执行，不能被强制拉进多页面或 Web 设计流程。

## 3. `video-transcript` 对齐

- [ ] 明确转写脚本只负责生成转写母本，HTML、slides、docs 等富格式是叠加在母本之上的 agent 工作流。
- [ ] 新增或整合内容计划检查点，覆盖缺人工字幕、后端/provider 选择、代理选择、API 上传风险、数学公式处理和预期输出格式。
- [ ] 强化富格式 anchor 流程：HTML 或同类视觉输出先生成 anchor 页面或章节，高风险时等待用户验收，再继续完整生成。
- [ ] 当用户要求设计型 HTML 或 presentation-grade 视觉输出时，明确提示可以调用 Frontend Design。
- [ ] 明确产物事实源：普通转写使用轻量 metadata 或 run summary；截图、素材、设计、渲染质检流程使用 `run-manifest.json`。
- [ ] 确保素材规则禁止假截图、假 logo、假图表、假数据证据，禁止把 AI 生成素材伪装成来源证据。
- [ ] 更新示例和 reviewer handoff 文档，展示用户决策、跳过的确认、去密钥化的 provider 选择、输出路径和已知限制。

## 4. `yt-dlp-download` 对齐

- [ ] 新增下载计划检查点，执行前可展示目标 URL、检测到的类型、预计 playlist 范围、格式 preset、字幕、缩略图、archive 行为、cookies 和输出目录。
- [ ] 新增 Web Access/cookie 指南，覆盖登录限制、年龄限制、地区限制、反爬限制，以及何时必须暂停等待用户确认。
- [ ] 新增大型 playlist 策略，覆盖范围选择、首条验证、archive 复用和 force 重下行为。
- [ ] 修正文档中的下载 summary schema，使示例与脚本实际输出一致；如果要改 schema，则脚本和示例必须一起改。
- [ ] 新增重试和恢复指南，覆盖部分失败、格式不可用、字幕缺失、archive skip、cookie 失败和 ffmpeg 后处理失败。
- [ ] 新增自检和 reviewer handoff 字段，记录完成项、跳过项、失败项、实际文件、warnings 和下一步恢复命令。

## 5. 示例、Manifest 与验证

- [ ] 每个 skill 至少补齐一个普通路径示例和一个检查点密集路径示例。
- [ ] 更新每个 skill 的 manifest 或 metadata，使描述与新的工作流架构一致，且不夸大能力。
- [ ] 运行仓库结构和文档一致性的离线验证。
- [ ] 实现后将更新后的 skill 重新安装或重新加载到 Claude、Codex、Cursor、Mavis 的 skill 目录。

## 6. OpenSpec 质检

- [ ] 运行 `openspec status --change align-video-skills-with-web-video-presentation`，确认 proposal、design、spec、tasks 全部完整。
- [ ] 运行仓库验证脚本，修复所有 schema 或格式失败。
- [ ] 检查与 `expand-transcript-backend-selection` 的重叠，确保 provider 扩展要求继续保留在独立 change 中。
