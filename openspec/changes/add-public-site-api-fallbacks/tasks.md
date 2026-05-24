## 1. 契约与文档

- [x] 1.1 新增公开接口 fallback reference，写明 adapter registry、支持阶段、字段映射、脱敏规则和安全边界。
- [x] 1.2 更新 `video-transcript` 的 `SKILL.md`，说明 `yt-dlp` 失败后的公开接口 fallback、Web Access checkpoint 和 API 转写衔接。
- [x] 1.3 更新 `yt-dlp-download` 的 `SKILL.md`，说明 metadata、字幕、媒体地址 fallback 与下载摘要字段。
- [x] 1.4 统一两个 skill 的术语、状态值、summary 字段、dry-run 输出和用户提示文案。

## 2. Adapter Registry

- [x] 2.1 设计并实现站点 adapter registry，包含域名匹配、阶段能力、endpoint label、必要请求头、限速和失败分类。
- [x] 2.2 实现公开接口请求封装，支持超时、重试上限、错误分类、敏感信息脱敏和无 cookie 默认策略。
- [x] 2.3 增加禁用公开接口 fallback 的配置或参数，并在摘要中记录禁用原因。
- [x] 2.4 为 registry 增加 `--doctor` 可读输出，列出已注册 adapter、支持域名和支持阶段。

## 3. Bilibili Adapter

- [x] 3.1 实现 Bilibili URL 标识提取，支持 `BV` 和 `av`。
- [x] 3.2 接入 Bilibili 公开 metadata 接口，映射标题、aid、cid、分 P、时长、封面、简介和 owner。
- [x] 3.3 接入 Bilibili 字幕状态探测，区分可用、为空、需要登录和接口失败。
- [x] 3.4 接入 Bilibili 公开播放地址探测，获取公开视频音频或视频流候选，并记录 Referer 和时效边界。
- [x] 3.5 为 Bilibili adapter 增加 mock 响应样例和字段映射验证。

## 4. video-transcript 接入

- [x] 4.1 在 metadata 获取失败或信息不足时接入公开接口 metadata fallback。
- [x] 4.2 在人工字幕探测失败或缺失时接入公开字幕 fallback，并正确触发 Web Access checkpoint 或 API 转写。
- [x] 4.3 在需要音频输入且默认下载失败时接入公开播放地址 fallback。
- [x] 4.4 更新 `metadata.json` 和 `run-summary.json`，写入 fallback adapter、阶段、endpoint label、状态、失败原因和脱敏事实。
- [x] 4.5 更新 `--dry-run`，展示 fallback 计划和结果，且不下载媒体、不上传转写 API。

## 5. yt-dlp-download 接入

- [x] 5.1 在 metadata 获取失败或信息不足时接入公开接口 metadata fallback。
- [x] 5.2 在字幕下载或字幕列表探测失败时接入公开字幕 fallback，并记录字幕真实状态。
- [x] 5.3 在媒体下载或地址探测失败时接入公开播放地址 fallback。
- [x] 5.4 更新 `download-summary.json`，写入 fallback adapter、阶段、endpoint label、状态、失败原因和脱敏事实。
- [x] 5.5 更新 `--dry-run`，展示下载计划中的 fallback 路径和不可用原因。

## 6. 验证与发布

- [x] 6.1 添加单元测试或脚本级 mock 验证，覆盖 adapter 命中、无 adapter、metadata 成功、字幕需要登录、媒体地址失败和脱敏日志。
- [x] 6.2 运行仓库验证命令和 OpenSpec 校验，确认 proposal、design、spec、tasks 可解析。
- [x] 6.3 用 Bilibili 公开视频运行 dry-run，确认网页抓取失败时会展示公开接口 fallback 计划。
- [x] 6.4 重新安装或同步 `video-transcript` 与 `yt-dlp-download` skill，让 Codex、Claude、Cursor、Mavis 的本地副本生效。
- [x] 6.5 提交并推送变更前检查 `git status`，确认只包含本次公开接口 fallback 相关文件。
