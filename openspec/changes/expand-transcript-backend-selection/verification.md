# 验证记录

验证时间：2026-05-22

## 本地验证

- `py -3 .\scripts\validate_repo.py`：通过。
- `py -3 .\video-transcript\scripts\transcript.py --help`：通过。
- `py -3 C:\Users\zhoushaoyang\.codex\skills\video-transcript\scripts\transcript.py --help`：通过。
- `--doctor` 脱敏探针：通过，使用临时 `VIDEO_TRANSCRIPT_DEFAULT_PROVIDER_PATH` 和占位 `MINIMAX_API_KEY`，未记录真实 key。
- 函数级探针：通过，覆盖无默认 checkpoint、默认 provider 保存/复用、显式 provider 覆盖、清除默认值、旧 backend 映射、冲突检测、proxy mode 状态、endpoint 脱敏。

## 安装目标

已同步 `video-transcript` 到以下目录：

- `C:\Users\zhoushaoyang\.claude\skills\video-transcript`
- `C:\Users\zhoushaoyang\.codex\skills\video-transcript`
- `C:\Users\zhoushaoyang\.cursor\skills\video-transcript`
- `C:\Users\zhoushaoyang\.mavis\skills\video-transcript`

## 抽样 Hash

- `video-transcript/SKILL.md`：`68D9F02137FC2DAB33F5AD26AAFB4A122F07AA5615E62F3631D89FBCB315B059`
- `video-transcript/scripts/transcript.py`：`CEBCC7F2A69BCC8FC31CAE9DBFD28295E144648B1FFF8AE5BC8428E60FC18B50`
- `video-transcript/references/BACKENDS.md`：`D94214C7900D26D93E1509FCADBD694855C4D38CA4E36E7879C0DFE4A3A0C3FB`
- `video-transcript/references/CHECKS.md`：`C87947A4B6B7C7560330CF7730E20B4BED5AC794BB7F4F80F9DBE585D6E8328C`

安装目录中 `SKILL.md` 与 `scripts/transcript.py` 的抽样 hash 已与仓库一致。
