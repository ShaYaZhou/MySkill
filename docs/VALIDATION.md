# 离线验证

仓库验证脚本是 `scripts/validate_repo.py`。它必须保持离线：不下载媒体、不调用转写 API、不需要 cookie，也不需要 API key。

## PowerShell 命令

在仓库根目录运行：

```powershell
py -3 .\scripts\validate_repo.py
```

如果当前 shell 有 `rtk`，优先使用仓库维护包装器：

```powershell
rtk py -3 .\scripts\validate_repo.py
```

如果找不到 `rtk`，运行上面的直接 PowerShell 命令，并在维护报告中记录本次跳过了 RTK 包装器。

可选的语法检查：

```powershell
py -3 -m py_compile .\scripts\validate_repo.py
```

常用脚本 help 探针：

```powershell
py -3 .\video-transcript\scripts\transcript.py --help
py -3 .\yt-dlp-download\scripts\download.py --help
```

## 验证内容

- 含 `SKILL.md` 的 skill 目录。
- `SKILL.md` frontmatter 以及 name 与目录名一致性。
- `agents/openai.yaml` 可解析且包含必需元数据。
- 必需的 `scripts/` helper。
- 存在时的可选 `manifest.json` schema。
- 仓库和 skill Python 脚本语法。
- 脚本 `--help` 能在无网络、无凭据时输出。
- 本地 Markdown 链接和 reference map 目标。
- JSON examples、schemas 和 manifests。
- 未清理占位标记和疑似敏感字段的基础卫生。
- example 文件明确标注为示例。

## 阻断级失败

以下问题会阻断仓库维护：

- 缺失 reference map 目标。
- 本地 Markdown 链接损坏。
- schema、manifest 或 JSON example 不可解析。
- `agents/openai.yaml` 缺少必需元数据。
- `SKILL.md` 缺少必需 frontmatter。
- Python 语法错误。
- 脚本 `--help` 失败。
- example 输出看起来包含真实 secret 或未清理占位标记。

## RTK 降级

RTK 是本仓库推荐的维护命令包装器。这个规则只约束维护文档，不改写 skill 运行命令。

使用顺序：

1. 尝试 `rtk py -3 .\scripts\validate_repo.py`。
2. 如果当前 shell 找不到 `rtk`，运行 `py -3 .\scripts\validate_repo.py`。
3. 在维护报告里说明本次使用了降级路径。

不要仅因为当前 shell 缺少 `rtk` 就阻断本地离线验证。
