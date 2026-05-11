---
name: qencode-transcode
description: Use when the user wants to actually run a Qencode transcoding job — phrases like "submit", "start the job", "run this", "transcode it now", "encode and post the status", or any time the user has a video URL and wants encoded output back. Submits a `query` JSON to `POST /v1/start_encode2` via the qencode MCP server when present, falling back to raw HTTP. Returns the task_token and status_url. For status polling, hand off to `qencode-job-status` afterwards.
version: 0.1.0
---

# qencode-transcode

You submit a transcoding job and return the task_token + status_url. You do **not** compose the query — `qencode-build-query` does that. If the user only described a job in natural language (no JSON yet), invoke `qencode-build-query` first to compose, then continue here to submit.

## Two execution paths

This skill prefers the MCP server but falls back cleanly to raw HTTP.

1. **MCP path (preferred).** If the `qencode` MCP server is connected (auth via OAuth, no API key needed in this plugin), use the `mcp__qencode__start_encode2_raw` tool, passing the **inner** transcoding params (the `query.*` contents — `source`, `format`, `encoder_version`, etc.). The MCP server's client auto-wraps so passing wrapped JSON also works, but inner is safer.

   - Tool name: `mcp__qencode__start_encode2_raw`
   - Args: `query` (object) — either `{"source":..., "format":[...]}` or `{"query": {...}}`. Both shapes accepted. `payload` (string, optional).
   - Returns: `{"task_token": "...", "status_url": "...", "upload_url": "..."}`

   The `mcp__qencode__transcode_video` tool also works but expects `(source, outputs[])` separately — only convenient when the user gave a plain source URL with no `query`-level options (no stitching, no `encoder_version` override, etc.). Prefer `start_encode2_raw` when you already have a composed query.

2. **HTTP fallback.** If the MCP server isn't connected (no `mcp__qencode__*` tools available in this session), use `${CLAUDE_PLUGIN_ROOT}/scripts/http_fallback.py`. It requires `QENCODE_API_KEY` in the environment.

   ```bash
   echo '<the {"query": {...}} JSON>' \
     | QENCODE_API_KEY=$QENCODE_API_KEY \
       python3 ${CLAUDE_PLUGIN_ROOT}/scripts/http_fallback.py submit
   ```

   Output is a JSON dict with `task_token`, `status_url`, `upload_url` — same shape as the MCP tool. If `QENCODE_API_KEY` is missing, the script exits with a clear message; ask the user to set it.

## Workflow

1. **Establish the query.** Either:
   - The user/agent already produced one (passed in / on clipboard / referenced in context) — use it as-is.
   - The user described the job in natural language — invoke `qencode-build-query` first, then continue with the resulting JSON.

2. **Pick the path.**
   - Check whether tools matching `mcp__qencode__*` are available in this session.
   - If yes → MCP path. If no → HTTP fallback path.
   - Mention to the user which path you're using (one short line is enough).

3. **Submit.** Run the chosen path. Both return the same shape — `task_token` and `status_url`.

4. **Sanity-check the response.**
   - `task_token` should be a hex/UUID-ish string. If absent, the call failed.
   - `status_url` points at a master endpoint like `https://prod-nyc3-1-api-do.qencode.com/v1/status`. Note this is the **authoritative** polling endpoint per `gotchas.md` §2 — but the public `https://api.qencode.com/v1/status` also works.

5. **Report back.** Format:

   > ✅ Submitted. Task token: `<token>` · status: `<status_url>`
   >
   > <1-2 sentences describing what's running — count outputs, name destinations if any>
   >
   > To poll progress, use `qencode-job-status` with the token above (it can either fetch once or wait until terminal).

   Don't paste back the full query JSON unless the user asks — they just saw it from `qencode-build-query`.

## Error handling

If the underlying call returns a Qencode error code:

- **Error 19 ("query field is required")**: the wrapper was stripped or malformed. Re-wrap and retry once. If still failing, surface the request body to the user.
- **Error 1 / 2 (api_key / token issues)** on the HTTP path: prompt the user to refresh `QENCODE_API_KEY`.
- **Transient connection drop** (`httpx.RemoteProtocolError` / `urllib` `ConnectionError`): both the MCP client and `http_fallback.py` retry once automatically. If it still fails, surface to the user — don't retry indefinitely.
- **Other error codes**: hand the response off to `qencode-troubleshoot` (shipping in M4) or relay the error code + message verbatim.

## What NOT to do

- Don't compose the query yourself — defer to `qencode-build-query` if no JSON is provided.
- Don't poll for status here — hand off to `qencode-job-status`. Reporting "submitted" is enough for this skill.
- Don't ask for or persist `QENCODE_API_KEY`. If the HTTP path needs it and it's missing, ask the user once and let them set it in their shell.
- Don't strip the `{"query": ...}` envelope when constructing the HTTP-path body. (The MCP path is forgiving; the HTTP script normalizes; but the underlying API requires double-wrap.)

## Cross-references

- `${CLAUDE_PLUGIN_ROOT}/skills/qencode-build-query/SKILL.md` — compose first if no JSON yet
- `${CLAUDE_PLUGIN_ROOT}/skills/qencode-job-status/SKILL.md` — poll/wait after submit
- `${CLAUDE_PLUGIN_ROOT}/scripts/http_fallback.py` — raw-HTTP path
- `${CLAUDE_PLUGIN_ROOT}/assets/gotchas.md` — query double-wrap, status_url, retry-on-disconnect
