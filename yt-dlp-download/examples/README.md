# 示例说明

这些示例只说明契约，不要照搬为真实产物。真实运行时以脚本输出的 `download-summary.json` 和实际文件为准。

## 下载公开视频

```powershell
python scripts/download.py "https://example.invalid/watch?v=abc123"
```

## 只预览不下载

```powershell
python scripts/download.py --dry-run "https://example.invalid/watch?v=abc123"
```

示例应保持轻量，只展示字段语义、状态 token、脱敏规则和失败边界。
