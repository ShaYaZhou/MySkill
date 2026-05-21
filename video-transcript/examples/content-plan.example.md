# content-plan.md 示例

> 本示例只说明契约，不代表真实产物。示例 URL、时间戳、标题、公式、素材和 evidence 均为虚构；真实运行时必须依据实际转写、`metadata.json`、用户确认和授权范围填写。

## 运行信息

- 视频标题：示例：二维运动中的能量守恒
- 视频 URL：https://example.invalid/watch?v=contract-only
- metadata 路径：D:/out/example/metadata.json
- 原始转写路径：D:/out/example/original.md
- 中文稿路径：D:/out/example/zh.md
- 计划生成原因：课件 + PPTX + Word/DOCX
- 目标格式：Markdown, PPTX, Word/DOCX, PDF
- 计划状态：draft

## 内容边界

- 本文件只说明内容结构、证据回链、保留策略和格式映射。
- 不规定 PPT 版式、HTML/CSS、DOCX 样式或具体视觉实现。
- 截图候选只表示需要确认，不代表已抓图或拥有发布授权。

## Section -> Beat 骨架

### S01 问题设定与核心变量

- 来源时间戳：00:00:10-00:03:20
- 本节目的：建立问题背景，说明质量、速度、高度和能量项。
- 压缩策略：完整保留变量定义，压缩寒暄。

| Beat ID | 时间戳 | 关键论点 / 讲解动作 | Evidence refs | 公式 | 截图候选 | 素材需求 | Must-keep refs | 压缩说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01-B01 | 00:00:18-00:01:05 | 定义质量、速度和高度，并说明能量讨论只在忽略空气阻力时成立。 | E01,E02 | F01 | none | none | M01,M02 | 保留限制条件，删除重复口头语。 |
| S01-B02 | 00:01:40-00:02:30 | 用示意图说明小球从斜面滑下的初始状态。 | E03 | none | SC01 | A01 | M03 | PPTX 可用一页，DOCX 放图注。 |

#### 目标格式映射

| 格式 | 内容策略 | 证据呈现 | 公式策略 | 截图/素材策略 |
| --- | --- | --- | --- | --- |
| Markdown | 保留变量定义和限制条件 | 内联引用时间戳 | LaTeX | 只提示截图候选 |
| HTML | 展开变量说明 | 折叠 evidence | MathJax，保留源 LaTeX | 确认后插入截图或 code-drawn 示意 |
| PPTX | 建议拆成 1-2 页，不写版式 | 讲者备注写 evidence | 公式图片 fallback 可接受 | SC01 需用户确认 |
| Word/DOCX | 正文 + 图注 | 脚注记录 evidence | 优先 OMML/MathML | 图注含 alt text |
| PDF | 由 DOCX 或 PPTX 派生 | 随来源格式 | 检查可读性 | 随来源格式 |

## Evidence Pool

| ID | 时间戳 | 类型 | 原句摘录 | 术语/对象 | 数字/公式 | 屏幕状态/案例 | 来源说明 | 置信度 | Used by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E01 | 00:00:18 | term | “我们先把质量记作 m。” | 质量 m | none | none | 人工字幕 | high | S01-B01,M01 |
| E02 | 00:00:52 | limitation | “这里先不考虑空气阻力。” | 空气阻力 | none | none | 人工字幕 | high | S01-B01,M02 |
| E03 | 00:01:48 | screen-state | “看这个斜面上的初始位置。” | 小球、斜面 | none | 斜面初始状态示意 | 人工字幕 + 页面画面候选 | medium | S01-B02,SC01,M03 |

## Must-keep 清单

| ID | 必须保留内容 | 原因 | Evidence refs | 必需格式 | 空间不足时处理 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| M01 | 质量记作 `m`，速度记作 `v`，高度记作 `h`。 | 后续公式依赖变量定义。 | E01 | Markdown,PPTX,Word/DOCX,PDF | 可合并为一行变量表。 | keep |
| M02 | 忽略空气阻力是公式成立条件。 | 防止误用结论。 | E02 | Markdown,PPTX,Word/DOCX,PDF | 必须保留，不能删。 | keep |
| M03 | 斜面初始状态需要图示或文字替代。 | 纯文字难以说明空间关系。 | E03 | PPTX,Word/DOCX | 如无截图，使用 code-drawn 示意。 | compress |

## 公式清单

| ID | 时间戳 | 源 LaTeX | 变量说明 | Evidence refs | 目标格式策略 | Fallback 风险 |
| --- | --- | --- | --- | --- | --- | --- |
| F01 | 00:02:58 | `$E = \\frac{1}{2}mv^2 + mgh$` | `m` 为质量，`v` 为速度，`h` 为高度。 | E01,E02 | Markdown 保留 LaTeX；PPTX 可用高清公式图片；DOCX 优先可编辑公式。 | PPTX fallback 需记录源 LaTeX 和 alt text。 |

## 截图候选

| ID | 时间戳 | 候选理由 | 用途 | 替代文字 | 隐私/版权风险 | 建议格式 | 用户确认状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SC01 | 00:01:48 | 斜面初始位置和小球高度关系仅靠文字不直观。 | 课件和讲义解释问题设定。 | 小球位于斜面高处，标出高度 h。 | low；需确认是否允许从公开视频取帧。 | PPTX,Word/DOCX,PDF | pending |

## 素材需求

| ID | 类型 | 来源或期望来源 | 用途 | 引用位置 | Alt text | 授权/外发限制 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | source-screenshot 或 code-drawn | 00:01:48 截图候选；若跳过则绘制示意图 | 说明斜面初始状态 | S01-B02 | 小球在斜面上方位置，标注高度 h。 | 发布前确认截图授权；code-drawn 可标为示意图。 | needed |

## 自检

- [x] 每个 section 都有来源时间戳和至少一个 beat。
- [x] 每个 beat 的关键论点能回链到 evidence pool，或已标注为推断。
- [x] Evidence pool 覆盖关键术语、公式、屏幕状态和限制条件。
- [x] Must-keep 覆盖关键公式、变量定义、限制条件和图示需求。
- [x] 公式条目有源 LaTeX、变量说明或不确定性标注。
- [x] 截图候选都有时间戳、理由、用途、替代文字和风险说明。
- [x] 素材需求区分真实截图和 code-drawn 替代。
- [x] 目标格式映射覆盖用户选择的每个格式。
- [x] 未写死版式、CSS、DOCX 样式或具体视觉实现。
- [x] 普通 Markdown 转写路径没有被强制 content-plan 或截图确认阻塞。

## 阻塞项与后续动作

- 阻塞项：SC01 尚未获得用户截图确认。
- 需要用户确认：是否允许从 00:01:48 抓取截图；若拒绝，改用 code-drawn 示意。
- 下一步：确认截图后进入 PPTX/Word anchor；若跳过截图，则先生成朴素讲义。
