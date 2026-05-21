# 示例说明

这些示例只说明契约，不要照搬为真实产物。真实运行时以脚本输出的 `metadata.json` 和 `run-summary.json` 为准。

## 普通公开视频

```powershell
python scripts/transcript.py "https://example.invalid/watch?v=abc123"
```

## 预览后端与风险

```powershell
python scripts/transcript.py --dry-run --transcribe-backend auto "https://example.invalid/watch?v=abc123"
```

示例文件体量应保持很小，只展示字段语义、状态 token 和脱敏规则。
