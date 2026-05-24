## ADDED Requirements

### Requirement: Artifact layer model

`video-transcript` MUST distinguish raw ASR, speech transcript, chapter handout, and HTML render artifacts in outputs and metadata.

#### Scenario: raw ASR artifact

- **WHEN** the system produces strict speech-to-text output from human subtitles, local ASR, MiniMax audio-asr, OpenAI audio-asr, or a compatible ASR proxy
- **THEN** it MUST record the artifact as `raw_asr` and write it to `original.asr.md` or an equivalent clearly marked raw ASR path

#### Scenario: speech transcript artifact

- **WHEN** the system produces a lightly cleaned timeline-preserving transcript such as a Kimi video-understanding manuscript
- **THEN** it MUST record the artifact as `speech_transcript` and write it to `speech.md` or an equivalent clearly marked speech path

#### Scenario: chapter handout artifact

- **WHEN** the system produces a chapterized learning document with headings, tables, summaries, or reordered explanations
- **THEN** it MUST record the artifact as `chapter_handout` and write it under `chapters/`

#### Scenario: HTML artifact

- **WHEN** the system renders a chapter handout or transcript to HTML
- **THEN** it MUST record the artifact as `html_render` and identify the source Markdown artifact

### Requirement: Explicit output selection

`video-transcript` MUST let users choose which artifact layers to generate.

#### Scenario: output profile selected

- **WHEN** the user passes `--output-profile raw`, `speech`, `chapters`, `html`, or `all`
- **THEN** the system MUST map the profile to the corresponding artifact layer set

#### Scenario: explicit artifacts selected

- **WHEN** the user passes one or more `--artifact` values
- **THEN** the system MUST use the explicit artifact list instead of inferring from `--output-profile`

#### Scenario: default profile

- **WHEN** the user does not select a profile or artifact list
- **THEN** the system MUST keep the lightweight default behavior while recording which artifact type was actually produced

### Requirement: Artifact metadata

`video-transcript` MUST record every generated or skipped artifact in `metadata.json` and `run-summary.json`.

#### Scenario: generated artifact

- **WHEN** an artifact is generated
- **THEN** metadata MUST include `artifact_type`, `path`, `source_artifact`, `source_type`, `provider`, `model`, `allowed_transform`, `derivation_stage`, and `status`

#### Scenario: skipped artifact

- **WHEN** an artifact cannot be generated because the provider or source layer is unavailable
- **THEN** metadata MUST record the artifact as `skipped` or `blocked` with a clear reason

#### Scenario: compatibility original path

- **WHEN** the system writes or reuses `original.md`
- **THEN** metadata MUST identify which artifact it mirrors or represents

### Requirement: Provider capability boundaries

`video-transcript` MUST not label video-understanding output as strict ASR.

#### Scenario: Kimi video-understanding output

- **WHEN** Moonshot/Kimi runs in `video-understanding` mode
- **THEN** the output MUST be recorded as `speech_transcript` or a derived artifact, not `raw_asr`

#### Scenario: user requests raw ASR with non-ASR provider

- **WHEN** the user requests `raw` but the selected provider is not an ASR-capable provider
- **THEN** the system MUST warn or block the raw artifact and suggest an ASR-capable provider or local ASR

### Requirement: Derivation rules

Derived artifacts MUST be created from prior text artifacts and disclose their transform boundary.

#### Scenario: speech from raw ASR

- **WHEN** the system creates `speech_transcript` from `raw_asr`
- **THEN** it MUST preserve the original timeline order and use `allowed_transform` value `light_cleanup_no_reorder`

#### Scenario: chapters from speech

- **WHEN** the system creates `chapter_handout` from `speech_transcript`
- **THEN** it MAY restructure, summarize, add tables, and add summaries, but MUST use `allowed_transform` value `summarize_restructure_add_tables`

#### Scenario: HTML from chapter markdown

- **WHEN** the system creates HTML from chapter Markdown
- **THEN** it MUST use `allowed_transform` value `html_render_from_markdown` and keep the source artifact path

### Requirement: Dry-run visibility

`video-transcript` MUST expose the planned artifact layers in dry-run mode without downloading media or calling transcription APIs.

#### Scenario: dry-run artifact plan

- **WHEN** the user runs `--dry-run`
- **THEN** the run summary MUST include the requested profile, planned artifacts, provider capability notes, and expected output paths

### Requirement: Documentation consistency

The skill documentation MUST describe raw ASR, speech transcript, chapter handout, and HTML as different artifact layers.

#### Scenario: user reads the skill entry

- **WHEN** an agent reads `SKILL.md` or the artifact layer reference
- **THEN** it MUST be clear which outputs are strict transcription and which outputs are derived learning materials
