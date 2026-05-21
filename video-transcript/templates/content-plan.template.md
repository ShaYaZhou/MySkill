# content-plan.md 模板

> 本模板用于中文内容计划。请替换所有 `<...>` 占位符。普通公开视频 Markdown 转写不强制生成本文件，也不主动打断用户确认截图。

## 运行信息

- 视频标题：<title>
- 视频 URL：<url>
- metadata 路径：<metadata.json path>
- 原始转写路径：<original.md path>
- 中文稿路径：<zh.md path 或 none>
- 计划生成原因：<复杂摘要 / 讲义 / 课件 / HTML / PPTX / Word/DOCX / PDF / 长视频重构>
- 目标格式：<markdown / html / pptx / docx / pdf>
- 计划状态：draft / ready / blocked

## 内容边界

- 本文件只规划内容结构、保留/压缩策略、证据回链、素材需求和格式映射。
- 不写死 PPT 版式、HTML/CSS、DOCX 样式、字体、颜色、动画或具体视觉实现。
- 截图候选只代表“建议确认”，不代表已授权抓图或已生成素材。

## Section -> Beat 骨架

### S01 <section title>

- 来源时间戳：<00:00:00-00:00:00>
- 本节目的：<purpose>
- 压缩策略：<完整保留 / 压缩 / 合并 / 移至附录 / 跳过并说明原因>

| Beat ID | 时间戳 | 关键论点 / 讲解动作 | Evidence refs | 公式 | 截图候选 | 素材需求 | Must-keep refs | 压缩说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01-B01 | <00:00:00-00:00:00> | <key claim> | <E01> | <F01 或 none> | <SC01 或 none> | <A01 或 none> | <M01> | <note> |

#### 目标格式映射

| 格式 | 内容策略 | 证据呈现 | 公式策略 | 截图/素材策略 |
| --- | --- | --- | --- | --- |
| Markdown | <保留 / 摘要 / 跳过> | <内联引用 / 附录 / 不展示> | <LaTeX / none> | <文字替代 / 候选提示 / none> |
| HTML | <保留 / 摘要 / 跳过> | <展开 / 折叠 / 附录> | <MathJax/KaTeX/源 LaTeX> | <确认后插入 / placeholder / code-drawn> |
| PPTX | <拆页建议，不写版式> | <讲者备注 / 页内摘要> | <可编辑 / 图片 fallback> | <确认后插入 / 示意图 / none> |
| Word/DOCX | <正文 / 表格 / 附录> | <脚注 / 附录 / 内联> | <OMML/MathML/源 LaTeX> | <图注 / 替代文字 / none> |
| PDF | <派生自 HTML/DOCX/PPTX> | <随来源格式> | <可读性检查> | <随来源格式> |

## Evidence Pool

| ID | 时间戳 | 类型 | 原句摘录 | 术语/对象 | 数字/公式 | 屏幕状态/案例 | 来源说明 | 置信度 | Used by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E01 | <00:00:00> | <claim/term/number/formula/case/screen-state/operation-step/limitation/counterpoint/exception> | <短摘录> | <term/entity 或 none> | <number/formula 或 none> | <state/case 或 none> | <人工字幕/自动转写/页面 metadata/用户材料> | <high/medium/low> | <S01-B01,M01> |

## Must-keep 清单

| ID | 必须保留内容 | 原因 | Evidence refs | 必需格式 | 空间不足时处理 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| M01 | <关键数字/公式/案例/限制/反方观点/例外/步骤> | <why> | <E01> | <markdown/html/pptx/docx/pdf> | <压缩方式或降级原因> | <keep/compress/block> |

## 公式清单

| ID | 时间戳 | 源 LaTeX | 变量说明 | Evidence refs | 目标格式策略 | Fallback 风险 |
| --- | --- | --- | --- | --- | --- | --- |
| F01 | <00:00:00> | <$...$ 或 $$...$$> | <variables> | <E01> | <Markdown LaTeX / HTML MathJax / DOCX OMML / PPTX image fallback> | <none / 需验证 / 不确定> |

## 截图候选

| ID | 时间戳 | 候选理由 | 用途 | 替代文字 | 隐私/版权风险 | 建议格式 | 用户确认状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SC01 | <00:00:00> | <文字/公式难以表达的原因> | <explain/use> | <alt text> | <none/low/medium/high + note> | <html/pptx/docx/pdf> | <pending/approved/skipped> |

## 素材需求

| ID | 类型 | 来源或期望来源 | 用途 | 引用位置 | Alt text | 授权/外发限制 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | <source-screenshot/user-provided/code-drawn/ai-generated/placeholder/formula-render> | <url/timestamp/path/待用户提供> | <purpose> | <S01-B01 / format> | <alt text> | <restriction> | <needed/available/skipped/blocked> |

## 自检

- [ ] 每个 section 都有来源时间戳和至少一个 beat。
- [ ] 每个 beat 的关键论点能回链到 evidence pool，或已标注为推断。
- [ ] Evidence pool 覆盖关键术语、数字、公式、案例、屏幕状态和操作步骤。
- [ ] Must-keep 覆盖关键数字、公式、案例、限制条件、反方观点、例外情况和操作步骤。
- [ ] 公式条目有源 LaTeX、变量说明或不确定性标注。
- [ ] 截图候选都有时间戳、理由、用途、替代文字和风险说明。
- [ ] 素材需求区分真实来源、待补、code-drawn、formula-render、placeholder 或 AI 概念图。
- [ ] 目标格式映射覆盖用户选择的每个格式。
- [ ] 未写死版式、CSS、DOCX 样式或具体视觉实现。
- [ ] 普通 Markdown 转写路径没有被强制 content-plan 或截图确认阻塞。

## 阻塞项与后续动作

- 阻塞项：<none 或 list>
- 需要用户确认：<格式 / 截图 / 素材 / Web Access / none>
- 下一步：<进入富格式导出 / 请求确认 / 修复计划 / 仅交付 Markdown>
