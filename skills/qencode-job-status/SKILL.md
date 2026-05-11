---
name: qencode-job-status
description: Use when the user wants to check, poll, or wait for a Qencode transcoding job — phrases like "check the status of token X", "is the job done?", "wait for the encode to finish", "poll until ready", "what's the progress?". Queries `POST /v1/status` (or the equivalent MCP tool) once or in a loop until terminal. Summarizes percent done, output URLs, errors, and warnings.
version: 0.1.0
---

# qencode-job-status

You fetch the status of a Qencode transcoding job and summarize it cleanly. You can do this once (snapshot) or in a loop until the job reaches a terminal state.

## Inputs

You need a `task_token` — usually from `qencode-transcode`'s submit response. If the user only has a `status_url`, the token is the last path segment in some cases, but it's safer to ask them for the token explicitly.

Decide the mode based on what the user asked for:

| Phrase | Mode |
|---|---|
| "what's the status of X?", "is it done?", "snapshot" | **once** — one status call, report and stop |
| "wait until it's done", "poll until ready", "let me know when it finishes" | **wait** — loop until terminal or timeout |

If unclear, default to **once** and tell the user how to switch to wait.

## Two execution paths

1. **MCP path (preferred).** If the `qencode` MCP server is connected:
   - One-shot snapshot: `mcp__qencode__get_job_status` with `task_token`.
   - Wait until terminal: `mcp__qencode__wait_for_job` with `task_token`, `timeout_seconds` (default 600), `poll_interval` (default 5.0).

   Both return the status dict directly.

2. **HTTP fallback.** If no MCP server is connected, use `${CLAUDE_PLUGIN_ROOT}/scripts/http_fallback.py`. Needs `QENCODE_API_KEY`:

   ```bash
   # one-shot
   QENCODE_API_KEY=$QENCODE_API_KEY python3 ${CLAUDE_PLUGIN_ROOT}/scripts/http_fallback.py status <token>

   # wait until terminal (exponential backoff 5s → 60s, capped at --timeout)
   QENCODE_API_KEY=$QENCODE_API_KEY python3 ${CLAUDE_PLUGIN_ROOT}/scripts/http_fallback.py wait <token> --timeout 600
   ```

   Both print the same JSON shape as the MCP tools.

## Workflow

1. **Pick the path.** MCP if `mcp__qencode__get_job_status` is available, otherwise HTTP fallback. One short line to tell the user which.

2. **Run the call.** In wait mode, surface a short note when starting ("polling every 5–60s, up to 10 minutes…") so the user understands there will be a delay. Don't print intermediate state — only the final summary.

3. **Parse the response.** Expected fields (see `${CLAUDE_PLUGIN_ROOT}/assets/schema-digest.md` for the full status object):
   - `status` — one of `queued`, `started`, `processing`, `completed`, `error`, `failed`, etc. Terminal: `completed`, `error`, `failed`.
   - `percent` — overall completion (0–100).
   - `status_url` — the master endpoint for follow-up polls.
   - `videos[]`, `audios[]`, `images[]`, `texts[]` — output objects (URL, format, size, duration). Each typically has its own `status` and `percent` for ABR ladders.
   - `error`, `error_description` — populated if the job failed.
   - `warnings[]` — soft warnings (e.g. source had unusual metadata).

4. **Summarize.** Match this format:

   **In progress (snapshot mode):**

   > ⏳ `<status>` — <percent>% complete
   >
   > Outputs in progress: <count and short list>
   > Started: <start_time if present, else "—">

   **Completed:**

   > ✅ Completed.
   >
   > Outputs:
   > - <url> · <output type / resolution> · <duration> · <size>
   > - …
   >
   > Warnings: <list any non-empty warnings, else omit this line>

   **Failed:**

   > ❌ Failed: error code <N> — <error_description>
   >
   > <Suggested next step: invoke `qencode-troubleshoot` with the error code (M4), or paste the relevant `assets/error-codes.md` entry inline if there is one>

5. **Don't paste the full raw status JSON** unless the user asks ("show me the full response") — it's noisy. The summary is the value-add.

## Notes on polling cadence

The public `/v1/status` endpoint is rate-limited per project. Both the MCP `wait_for_job` and the HTTP `wait` subcommand use sane defaults (5s → exponential backoff to 60s cap). Don't poll faster than every 5 seconds; you'll get throttled.

For very long jobs (4K, multi-hour content), raise `timeout_seconds`/`--timeout` to e.g. 3600 (one hour) and warn the user that the call will sit for that long. Better yet: do a snapshot first, eyeball the `percent`, and pick a timeout based on the remaining work.

## Trap to avoid: don't parallel-call `wait_for_job` with other MCP tools

Empirically, dispatching `mcp__qencode__wait_for_job` in the same parallel tool-call batch as `mcp__qencode__get_job_status` (or any other MCP tool) causes `wait_for_job` to return an early intermediate snapshot instead of polling. Call `wait_for_job` **alone** in its tool-use block. Sequential calls are fine; parallel ones aren't.

## Cross-references

- `${CLAUDE_PLUGIN_ROOT}/skills/qencode-transcode/SKILL.md` — got here from there typically
- `${CLAUDE_PLUGIN_ROOT}/scripts/http_fallback.py` — raw-HTTP path (`status` / `wait` subcommands)
- `${CLAUDE_PLUGIN_ROOT}/assets/gotchas.md` — `status_url` master-endpoint nuance, polling cadence
- `${CLAUDE_PLUGIN_ROOT}/assets/error-codes.md` — error code → fix
- `${CLAUDE_PLUGIN_ROOT}/assets/schema-digest.md` — full `status` response shape under `status.returns.status`
