# 截图与素材治理

本文定义 `video-transcript` 在截图、多格式导出和设计阶段的素材规则。普通公开视频 Markdown 转写不主动打断用户要求截图；截图和素材治理只在用户要求富格式、讲义、课件、截图、设计，或内容确实难以文字化时启用。

## 截图候选规则

只有当截图能提供文字、公式或自绘示意无法充分表达的信息时，才提出候选。典型触发：

- 物理效果展示：运动轨迹、光学/流体/材料现象、实验前后状态。
- 工业设计关键绘制步骤：草图构造、建模界面、参数变化、装配关系。
- 实验现象：读数、颜色变化、仪器状态、样品形态。
- 软件界面状态：菜单路径、配置面板、错误状态、关键交互前后。
- 复杂图表或推导版书：用户需要保留空间布局、箭头关系或视觉证据。

不建议截图的情况：

- 画面只是讲者头像、标题页、装饰背景或可由一句文字说明的内容。
- 截图会泄露私密登录页、账号、内部数据或未授权信息。
- 截图来源受 DRM、付费限制、水印限制或访问控制保护，且用户未明确授权。
- 候选与已有截图在同一论点、同一画面状态和同一输出用途上重复。

## 截图 Checkpoint 模板

在抓取或导入前，向用户给出可审阅清单：

```text
我建议增加这些截图，请确认是否抓取/导入：

| id | 时间戳/来源 | 截图理由 | 用途 | alt text | 建议输出格式 | 隐私/版权风险 | 处理方式 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| shot-001 | 00:03:18 | 软件设置状态难以文字化 | HTML、PPTX | 设置面板显示三项关键开关 | HTML/PPTX | 低：公开视频 | 直接截取 |

默认选择：只保留必要截图，合并重复画面。
你可以回复：确认、跳过截图、只保留 shot-001、改用自绘示意。
```

候选表必须包含时间戳或用户文件来源、理由、用途、替代文字、风险和建议插入格式。没有 alt text 或没有必要性说明的候选不得进入抓取阶段。

## 确认后抓取或导入流程

用户确认后执行：

1. 建立产物目录下的 `assets/screenshots/` 或格式子目录内的截图目录。
2. 对源视频截图时记录 `source_url`、`timestamp`、对应 `metadata.json`、转写段落 id 或时间范围。
3. 对用户提供截图记录原始文件路径、导入时间、是否需要脱敏处理。
4. 生成稳定 id，例如 `shot-001`，文件名使用 id 和时间戳，不使用含隐私的页面标题。
5. 在 `run-manifest.json.screenshots[]` 和 `assets[]` 中登记路径、hash、引用位置、alt text、授权范围、处理状态。
6. 在 Markdown、HTML、PPTX、Word/DOCX、PDF 的引用位置使用同一素材 id，避免各格式各自发明路径。

截图引用位置建议使用：

- Markdown：段落锚点、章节标题或图片语法附近的素材 id。
- HTML：元素 id、章节 id 或 data asset id。
- PPTX：slide 编号和形状名称。
- Word/DOCX：标题路径、书签或图片说明。
- PDF：来源格式和页码；PDF 不作为素材原始编辑源。

## 跳过与降级

用户跳过截图时继续产出，不把截图阶段视为失败。可选降级：

- 使用纯文字补充画面描述。
- 用公式或表格表达关键关系。
- 使用 `code-drawn` 绘制抽象示意。
- 使用明确标注的 `placeholder` 作为待补位。

`run-manifest.json` 中应记录截图阶段为 `skipped`，并说明跳过原因和采用的替代方式。发布型产物中仍存在 placeholder 时，完成汇报必须列为待补。

## 安全边界

- 遵循最小必要原则，只截取能支撑内容的区域和数量。
- 不绕过 DRM、水印、付费限制或访问控制。
- 默认不嵌入私密登录页、账号信息、后台数据、未公开用户信息或敏感页面。
- 不记录密码、token、会话值、完整浏览器 profile 敏感路径或私密 HTML。
- 需要外发发布时，checkpoint 必须记录授权来源、可引用范围、脱敏处理和版权风险。
- 对受限来源优先改用文字说明或 `code-drawn` 示意。

## 去重与数量控制

候选去重按“同一论点 + 同一画面状态 + 同一输出用途”合并。默认只保留每个关键论点 1 张截图；长视频或课程材料可以按章节保留少量关键截图，但每张都必须有：

- 明确用途。
- alt text。
- 必要性说明。
- 引用位置。
- 授权或外发限制。

数量过多时先压缩为截图组摘要，再让用户确认是否展开。

## `assets[]` Schema

`assets[]` 可以直接嵌入 `run-manifest.json`，也可以由 manifest 引用 `assets.json` 或 `assets.md`。每项建议字段：

```json
{
  "id": "asset-001",
  "type": "source-screenshot",
  "status": "ok",
  "source": {
    "url": "https://example.invalid/watch?v=demo",
    "timestamp": "00:03:18",
    "path": "assets/screenshots/shot-001.png",
    "hash": "sha256:examplehash"
  },
  "license_or_external_use": "public-video-review-only",
  "purpose": "说明设置面板的三个关键开关",
  "references": [
    {"format": "html", "location": "section-2#shot-001"},
    {"format": "pptx", "location": "slide-04"}
  ],
  "alt_text": "设置面板中三个开关处于开启状态",
  "notes": "已裁掉账号区域"
}
```

字段要求：

- `id`：稳定、唯一，可被各格式引用。
- `type`：`source-screenshot`、`user-provided`、`code-drawn`、`ai-generated`、`placeholder`、`formula-render`。
- `status`：`candidate`、`approved`、`ok`、`skipped`、`blocked`、`needs-replacement`。
- `source`：按类型记录 URL、时间戳、用户路径、生成工具、公式源或占位说明；不得记录敏感登录值。
- `license_or_external_use`：授权范围、外发限制或未知风险。
- `purpose`：为什么需要这个素材。
- `references`：Markdown、HTML、PPTX、Word/DOCX、PDF 中的引用位置。
- `alt_text`：所有可见素材都必须有。

## 素材类型

- `source-screenshot`：来自源视频或源页面的真实截图，必须记录时间戳或页面来源。
- `user-provided`：用户上传或指定的素材，必须记录导入路径和用户授权范围。
- `code-drawn`：CSS、SVG、Canvas、JS、Office drawing 或等价机制绘制的示意，不是真实截图。
- `ai-generated`：AI 生成的概念插画或抽象辅助，不是真实证据。
- `placeholder`：待补素材占位，必须显式显示缺失原因和替换说明。
- `formula-render`：由 LaTeX/MathML/OMML 等渲染出的公式图片或对象，必须记录源公式和降级原因。

## Placeholder 规范

placeholder 必须：

- 保留目标素材的真实比例或建议比例。
- 显示素材类型、建议尺寸、缺失原因和替换说明。
- 在 `assets[]` 中标为 `placeholder` 或 `needs-replacement`。
- 在发布型产物完成汇报中列为待补，不得被描述为已完成素材。

## Code-drawn 策略

当截图受限、版权不清、画面含敏感信息，或内容可抽象表达时，优先使用 `code-drawn`。适用对象包括流程图、对比图、公式推导图、界面状态示意、设备结构简图。必须在可见说明或素材清单中标明“示意图/非真实截图”，并记录生成方式。

## AI 生成素材反伪规则

AI 生成素材只能作为概念性插画或抽象辅助。禁止：

- 冒充真实截图、真实产品界面、真实实验结果或用户案例。
- 生成或仿造 logo、商标、数据图、仪器读数、新闻/证据画面。
- 用 AI 图替代本应来自源视频的关键证据，却不标注来源差异。

`ai-generated` 必须记录生成来源、用途、发布风险和替代关系。若用户需要证据型素材，优先使用源截图、用户提供素材或 code-drawn 示意。

## 跨格式反伪检查

反伪规则适用于 Markdown、HTML、PPTX、Word/DOCX、PDF 全部输出，而不是只在视觉设计阶段检查。完成前检查：

- 各格式引用的素材 id 在 `assets[]` 中存在。
- 可见素材类型与真实来源一致。
- AI 生成、code-drawn 和 placeholder 没有被写成真实截图或真实证据。
- formula-render 保留源 LaTeX、alt text 和降级原因。
- PDF 的素材来源回链到派生源格式，不单独伪造来源。

## 截图与素材自检

完成前逐项检查：

- 文件存在且 hash 可计算。
- 引用位置有效，未出现孤儿素材或失效路径。
- 每张截图和每个可见素材都有 alt text。
- 隐私信息已裁切、遮盖或改用替代方案。
- 授权和外发限制已记录。
- 重复截图已合并。
- `run-manifest.json` 的 `screenshots[]`、`assets[]`、`privacy_and_copyright` 与完成汇报一致。
