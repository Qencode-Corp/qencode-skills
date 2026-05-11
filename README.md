# qencode-skills

Claude Code plugin that gives agents the knowledge and recipes to use the [Qencode Transcoding API](https://docs.qencode.com/api-reference/transcoding/) end-to-end: compose a `query` JSON, submit a job, poll for status, and troubleshoot failures.

**v1 scope:** transcoding API only. CDN, streaming, and player APIs are deferred.

## What's inside

| Skill | Status | When it runs |
|---|---|---|
| `qencode-build-query` | ✅ shipped | The user asks to transcode/encode/convert a video. Composes a validated `query` JSON without submitting. |
| `qencode-api-reference` | ✅ shipped | The user asks what an attribute means or what values it accepts. |
| `qencode-transcode` | ✅ shipped | End-to-end job submission. Uses MCP if connected; falls back to raw HTTP. |
| `qencode-job-status` | ✅ shipped | Poll or wait for a running job. |
| `qencode-troubleshoot` | ✅ shipped | Map a Qencode error code (or failed-job `error_description`) to a likely cause and fix. |

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

## Install (Claude Code)

This repo is a self-hosted Claude Code marketplace. Two commands in any Claude Code session:

```text
/plugin marketplace add Qencode-Corp/qencode-skills
/plugin install qencode-skills@qencode
```

The first registers this repo as a marketplace named `qencode`. The second installs the `qencode-skills` plugin from it.

On install, Claude Code will also prompt you to approve adding the `qencode` MCP server pointing at `https://mcp-qa.qencode.com/mcp`. On first tool use the browser opens for the OAuth handshake (no API key in client config — see `.mcp.json`).

### Updating

```text
/plugin update qencode-skills@qencode
```

Or `/plugin marketplace update qencode` to pull the latest entries.

### Removing

```text
/plugin uninstall qencode-skills@qencode
/plugin marketplace remove qencode
```

### Local-dev install (without publishing)

When iterating on the plugin itself, point Claude Code at your working copy instead of GitHub:

```text
/plugin marketplace add /path/to/qencode-skills
/plugin install qencode-skills@qencode
```

## Configuration

The MCP server installed with the plugin uses **OAuth** — there's nothing to configure in this plugin's settings. On first tool use, your browser opens `auth-qa.qencode.com` for consent and the token is persisted locally by Claude Code.

### HTTP fallback (no MCP)

The `qencode-transcode` and `qencode-job-status` skills can also call the public API directly via `scripts/http_fallback.py` when no MCP is connected. The fallback uses a project API key:

```bash
export QENCODE_API_KEY=...   # from https://portal.qencode.com/project/my_projects
```

MCP is preferred — it handles OAuth, session-token caching, and retries on transient disconnects. Use the fallback only if you can't run MCP in your environment.

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
