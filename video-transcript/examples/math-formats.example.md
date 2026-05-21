# 数学与多格式契约示例

本示例 example 只说明契约，不代表真实产物。真实运行时以脚本输出的 `metadata.json`、`run-summary.json` 或 `run-manifest.json` 为准。

## 输入片段

```markdown
## 例：能量公式

讲者提到质量和能量的关系：

$$
E = mc^2
$$

其中 `m` 表示质量，`c` 表示光速。
```

## Markdown 契约

- 保留公式为 Markdown LaTeX。
- 中文解释变量和单位。
- 不把公式图片作为 Markdown 的唯一来源。

```markdown
$$
E = mc^2
$$

其中 `m` 表示质量，`c` 表示光速。
```

## HTML 契约

- 使用 MathJax 或 KaTeX 渲染。
- 保留原始 LaTeX，便于复制和排错。
- 导出 PDF 前确认公式已完成渲染。

```html
<div class="math" data-latex="E = mc^2">$$E = mc^2$$</div>
```

## DOCX 契约

- 优先转换为 OMML 或 MathML 可编辑公式。
- 转换失败时使用高分辨率公式图片 fallback。
- fallback 必须有 alt text 和 LaTeX 源。

```json
{
  "target_file": "zh.docx",
  "location": "page 2",
  "source_latex": "E = mc^2",
  "fallback": "formula_image",
  "reason": "OMML conversion unavailable",
  "qa": "page preview shows sharp formula and alt text is present"
}
```

## PPTX 契约

- 复杂公式可用高分辨率公式图片。
- 同页备注或 manifest 保留 LaTeX 源。
- 前 2-3 页 anchor 至少覆盖一个公式样例。

```json
{
  "target_file": "zh.pptx",
  "location": "slide 3",
  "source_latex": "\\int_0^1 x^2 dx = \\frac{1}{3}",
  "fallback": "formula_image",
  "reason": "native equation rendering is not reliable in target runtime",
  "qa": "rendered slide preview is readable at 16:9"
}
```

## PDF 契约

- PDF 从已验收的 HTML、DOCX 或 PPTX 派生。
- 检查首页、公式页和最后一页。
- 如果 PDF 导出失败，记录上游格式和失败原因，不报告 PDF 已完成。
