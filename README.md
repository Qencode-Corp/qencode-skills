# qencode-skills

Claude Code plugin that gives agents the knowledge and recipes to use the [Qencode Transcoding API](https://docs.qencode.com/api-reference/transcoding/) end-to-end: compose a `query` JSON, submit a job, poll for status, and troubleshoot failures.

**v1 scope:** transcoding API only. CDN, streaming, and player APIs are deferred.

## What's inside

| Skill | Status | When it runs |
|---|---|---|
| `qencode-build-query` | ✅ shipped | The user asks to transcode/encode/convert a video. Composes a validated `query` JSON without submitting. |
| `qencode-api-reference` | ✅ shipped | The user asks what an attribute means or what values it accepts. |
| `qencode-transcode` | _planned (M3)_ | End-to-end job submission. Uses MCP if configured; falls back to raw HTTP. |
| `qencode-job-status` | _planned (M3)_ | Poll or wait for a running job. |
| `qencode-troubleshoot` | _planned (M4)_ | Map a Qencode error code to a likely cause and fix. |

The skills read from a shared knowledge base under `assets/`:

| File | Purpose |
|---|---|
| `assets/schema-digest.md` | Generated digest of every endpoint and `query` attribute |
| `assets/schema-index.json` | Path-keyed index for fast attribute lookup |
| `assets/best-practices.md` | Composition defaults (encoder v2, libfdk_aac, CRF + per-title, ABR stream-level params, …) |
| `assets/storage.md` | Output destinations — supported prefixes, per-provider param compatibility, fan-out, cache headers |
| `assets/gotchas.md` | Non-obvious operational quirks (query double-wrap, status_url, retries, …) |
| `assets/error-codes.md` | Error code → cause → fix table |
| `assets/recipes/*.md` | Named recipes (HLS ABR, MP4 ladder, thumbnails, …) |

## Install

```bash
# from inside Claude Code:
/plugin install qencode-skills
```

Or clone locally and point Claude Code at the directory.

## Configuration

Set your Qencode API key in the shell that launches Claude Code:

```bash
export QENCODE_API_KEY=...
```

The plugin prefers the [`qencode-mcp`](https://github.com/Qencode-Corp/qencode-mcp) server if it's on your `PATH`, and falls back to raw HTTP via `curl`/`httpx` otherwise. Install the MCP server for nicer error handling and session-token caching:

```bash
pipx install qencode-mcp
```

## Updating the schema digest

The skills read a digest generated from the canonical schema in the docs repo. Regenerate after any schema change:

```bash
# point the script at your docs checkout
export QENCODE_DOCS_PATH=~/projects/qencode/docs_getsby5
python scripts/build_assets.py

# or pass the path explicitly:
python scripts/build_assets.py --docs-path ~/projects/qencode/docs_getsby5
```

The script reads `<docs>/src/data/api/transcoding.json` and writes `assets/schema-digest.md` and `assets/schema-index.json`. Commit the regenerated assets.
