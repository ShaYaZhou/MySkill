# 多格式与公式策略

本文档定义 `video-transcript` 从 Markdown 转写稿派生富格式文件时的格式选择、公式处理和 manifest 记录要求。所有面向用户生成的文档必须使用中文；保留原文片段时，需要说明其来源和用途。

## 格式选择 checkpoint

默认产物是 Markdown：`original.md` 和按需生成的 `zh.md`。除非用户在初始请求里已经明确指定输出格式，否则不要直接生成 HTML、PPTX、Word/DOCX 或 PDF。

需要询问时使用短确认：

```text
默认我会先生成 Markdown。你还需要哪种富格式？
- HTML：适合网页阅读、MathJax/KaTeX 公式和交互目录。
- Word/DOCX：适合编辑、审阅和交付文档。
- PPTX：适合演示稿或课程讲义。
- PDF：适合定稿分发，通常从 HTML、DOCX 或 PPTX 派生。

确认格式后我再生成对应文件。
```

如果用户一开始就说“生成 PPTX”“做成网页”“导出 PDF”“给我 Word/DOCX”等，不要为格式选择二次暂停；直接按该格式进入后续 checkpoint。若该格式会触发付费 API、隐私上传、覆盖已有产物或明显设计工作，再按对应规则确认。

## 输出格式契约

- Markdown：始终是事实源和最小交付格式，公式使用 Markdown LaTeX：`$...$` 和 `$$...$$`。
- HTML：从中文 Markdown 派生，公式优先用 MathJax 或 KaTeX 渲染，保留可复制的原始 LaTeX。
- Word/DOCX：优先生成可编辑公式，使用 OMML 或 MathML；无法稳定转换时，可降级为高分辨率公式图片并保留 alt text。
- PPTX：优先使用清晰可读的文本排版；复杂公式允许使用高分辨率公式图片 fallback，并在备注或相邻文本中保留 LaTeX 源。
- PDF：不作为唯一事实源，优先从 HTML、DOCX 或 PPTX 派生；派生链路必须可追溯。

派生产物建议命名：

```text
zh.md
zh.html
zh.docx
zh.pptx
zh.pdf
run-manifest.json
```

如果已有脚本使用 `run-summary.json` 作为聚合事实源，可以把同等字段写入 `run-summary.json`；若富格式流程另有 manifest，则使用 `run-manifest.json`。不要把 secret、cookie、token 或完整敏感路径写入任何 manifest。

## 公式策略

公式识别和转写时优先保留语义，其次追求视觉还原。不要为了视觉美观改写数学含义。

各格式优先级：

- Markdown：保留 `$...$` 与 `$$...$$`，必要时在正文用中文解释变量和单位。
- HTML：优先 MathJax；若项目已有 KaTeX 或用户要求轻量渲染，可用 KaTeX。必须检查公式是否实际渲染，而不是只检查源码存在。
- DOCX：优先 OMML；可从 MathML 转换为 OMML。转换失败时使用 2x 或更高分辨率的透明背景公式图片，附带 alt text 和 LaTeX 源。
- PPTX：复杂公式可直接使用高分辨率公式图片 fallback；同页或备注区保留 LaTeX 源，避免图片成为唯一语义来源。
- PDF：沿用上游格式的公式结果。若从 HTML 打印 PDF，需要确认 MathJax/KaTeX 已完成渲染后再导出。

## fallback 记录

每次公式 fallback 都要写入运行摘要或 run-manifest，至少包括：

```json
{
  "formula_fallbacks": [
    {
      "target_file": "zh.pptx",
      "location": "slide 2",
      "source_latex": "E = mc^2",
      "fallback": "formula_image",
      "reason": "PPTX native equation conversion unavailable",
      "qa": "rendered image is sharp at 200% zoom"
    }
  ]
}
```

若公式疑似识别错误，也要记录 `formula_warnings`，并在汇报中提示需要人工复核。

## PDF 派生策略

PDF 应从最稳定的已验收格式派生：

- 网页型材料：HTML 渲染通过后导出 PDF。
- 文档型材料：DOCX 渲染通过后导出 PDF。
- 演示型材料：PPTX 渲染通过后导出 PDF。

PDF 导出后至少检查首页、公式页和最后一页。若无法导出 PDF，不要伪造成功；记录原因、已完成的上游格式和下一步动作。

## 验收清单

- 用户已指定或确认非 Markdown 格式。
- 所有文档面向用户部分为中文。
- 公式在目标格式中可读、可追溯；fallback 已记录。
- PDF 有明确派生来源。
- `run-summary.json` 或 `run-manifest.json` 记录格式、公式策略、fallback、警告和 QA 证据。
