# MySkill

Personal AI skill repository for Claude, Codex, Cursor, and Mavis.

## Skills

| Skill | Purpose |
| --- | --- |
| `video-transcript` | Create Markdown transcript documents from video or playlist URLs. It prefers human subtitles and can fall back to OpenAI, Kimi, or a configured MiniMax CLI command. |
| `yt-dlp-download` | Download videos, human subtitles, and thumbnails with `yt-dlp`, including playlist support and browser-cookie retries. |

## Install Targets

Install every skill directory in this repository into each agent's local skill directory:

| Agent | Skill directory |
| --- | --- |
| Claude | `C:\Users\zhoushaoyang\.claude\skills` |
| Codex | `C:\Users\zhoushaoyang\.codex\skills` |
| Cursor | `C:\Users\zhoushaoyang\.cursor\skills` |
| Mavis | `C:\Users\zhoushaoyang\.mavis\skills` |

Each installed skill keeps its normal `SKILL.md`, `scripts`, and `agents` files.

## RTK Command Rule

This repository follows the local RTK specification from `C:\Users\zhoushaoyang\.codex\RTK.md`.

Always prefix shell commands with `rtk`:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

Useful RTK checks:

```bash
rtk --version
rtk gain
which rtk
```

If `rtk` is not available in the current shell, verify the installation or PATH before relying on the proxy.

## Usage

Ask the agent to use a skill by name, for example:

```text
Use $video-transcript to create a transcript document from this video link.
Use $yt-dlp-download to download this video link.
```

## Maintenance

After pulling repository changes, reinstall the skill directories to all target agents so Claude, Codex, Cursor, and Mavis receive the same version.
