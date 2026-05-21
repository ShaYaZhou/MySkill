# MySkill

个人 AI skill 仓库，面向 Claude、Codex、Cursor 和 Mavis。

## Skill 列表

| Skill | 用途 |
| --- | --- |
| `video-transcript` | 从视频或播放列表 URL 生成 Markdown 转写文档。优先使用人工字幕，也可以回退到 OpenAI、Kimi 或 MiniMax API 转写，并包含数学公式转写提示。 |
| `yt-dlp-download` | 使用 `yt-dlp` 下载视频、人工字幕和缩略图，支持播放列表和浏览器 Cookie 重试。 |

## 安装目标

把本仓库中的每个 skill 目录安装到各 agent 的本地 skill 目录：

| Agent | Skill 目录 |
| --- | --- |
| Claude | `C:\Users\zhoushaoyang\.claude\skills` |
| Codex | `C:\Users\zhoushaoyang\.codex\skills` |
| Cursor | `C:\Users\zhoushaoyang\.cursor\skills` |
| Mavis | `C:\Users\zhoushaoyang\.mavis\skills` |

安装后，每个 skill 都保留原有的 `SKILL.md`、`scripts` 和 `agents` 文件。

## RTK 命令规范

本仓库遵循 `C:\Users\zhoushaoyang\.codex\RTK.md` 中的本地 RTK 规范。

所有 shell 命令都必须以 `rtk` 作为前缀：

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

常用验证命令：

```bash
rtk --version
rtk gain
which rtk
```

如果当前 shell 里找不到 `rtk`，先检查安装状态或 PATH，再依赖该代理执行命令。

## 使用方式

可以在对话中按名称调用 skill，例如：

```text
Use $video-transcript to create a transcript document from this video link.
Use $yt-dlp-download to download this video link.
```

## 维护方式

每次拉取仓库更新后，重新把 skill 目录安装到所有目标 agent，确保 Claude、Codex、Cursor 和 Mavis 使用同一版本。
