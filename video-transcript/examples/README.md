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

## 设置默认 provider

```powershell
python scripts/transcript.py --transcribe-provider minimax --transcribe-mode audio-asr --save-default-provider
```

该命令只保存 provider、mode、环境变量名、模型和 endpoint label，不保存真实 API key。

## 临时覆盖默认 provider

```powershell
python scripts/transcript.py --ignore-default-provider --transcribe-provider openai "https://example.invalid/watch?v=abc123"
```

示例文件体量应保持很小，只展示字段语义、状态 token 和脱敏规则。
