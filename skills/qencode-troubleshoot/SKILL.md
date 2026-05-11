---
name: qencode-troubleshoot
description: Use when a Qencode transcoding job or API call has failed and the user wants help understanding why. Triggers — "what does error N mean?", "my job failed", "why is this error happening?", "Qencode returned error 19", "the status shows error_description X", or any time the user pastes a non-zero `error` code or a `failed`/`error` status payload. Maps the error to its likely cause, suggests concrete fixes, and (when relevant) inspects the original query JSON for misconfigurations.
version: 0.1.0
---

# qencode-troubleshoot

You diagnose Qencode failures and recommend fixes. You do **not** re-submit, re-encode, or modify the user's project — diagnosis only. If the user wants to fix and re-run, hand the suggested change to `qencode-build-query` (to regenerate the query) or `qencode-transcode` (to re-submit).

## What you receive

The user typically gives you one or more of:

- An **error code** (numeric, returned by an API call). Examples: `error 19`, `Qencode error 8`.
- A **`error_description`** string from a failed job's `/v1/status` response.
- A **task_token** for a failed job — you can fetch its status via `qencode-job-status` first.
- The **query JSON** they submitted, if they want a config review.
- A **callback payload** received from a webhook.

If they only said "my job failed" without context, ask for at minimum the error code OR the failed task_token. Don't guess from nothing.

## Workflow

1. **Identify the layer.** API-level error vs job-level error matters — they're diagnosed differently.

   | Signal | Layer |
   |---|---|
   | Synchronous response from `POST /v1/...` has `error: <N>` where N ≠ 0 | **API-level** |
   | `/v1/status` response shows `status: "error"` or `"failed"` with `error_description: "..."` | **Job-level** |
   | Callback payload with `event: "error"` and an `error_code` field | API-level (use the `error_code`) |

2. **Look up the error.** Read `${CLAUDE_PLUGIN_ROOT}/assets/error-codes.md`.
   - API-level: find the code in the "API-level errors" section.
   - Job-level: read the "Job-level errors" categories and match the `error_description` to one.
   - If the code/message isn't documented, fall back to the "Generic fallback" guidance at the bottom of the file.

3. **Cross-reference with gotchas.** Read `${CLAUDE_PLUGIN_ROOT}/assets/gotchas.md`. Some errors are non-obvious — for example, error 19 is a query-wrapping issue, and "permission denied" on a Cloudflare R2 destination is the `permissions` field trap.

4. **Inspect context** when the user shared it:
   - **Query JSON**: scan for the eight common defaults from `best-practices.md`. If the failure is destination-related, check the destination shape against `storage.md` per-provider compatibility.
   - **Source URL**: try `curl -I <url>` to confirm reachability and content-type. If the user can't run shell commands, ask them to.
   - **Destination URL**: check the path-vs-folder rule (HLS/DASH → folder, MP4/MP3/thumbnail → full file path). See `storage.md`.
   - **Task token**: if provided and the user can re-run a status fetch, suggest invoking `qencode-job-status` for the full failed status payload (warnings, partial outputs, exact error_description).

5. **Recommend a fix.** Output format:

   > ### Diagnosis
   > **Error:** `<code or category>` — `<short title>`
   > **Likely cause:** <1–2 sentences>
   >
   > ### Suggested fix
   > <numbered list of concrete actions — change X to Y, run command Z, etc.>
   >
   > ### Verify
   > <how to confirm the fix worked: a curl command, a test job shape, expected status response, etc.>
   >
   > ### Cross-references
   > - `assets/error-codes.md` § <relevant section>
   > - `assets/gotchas.md` § <if applicable>
   > - `assets/storage.md` (if destination-related)

   Lead with the most-likely cause, but list 1–2 alternates if the symptom is ambiguous. Be specific — "set `permissions: \"public-read\"` only on AWS, omit on Qencode S3" beats "fix the permissions".

6. **Escalate when needed.** If the error matches the "Internal server error" codes (1, 7), the user has already exhausted documented fixes, OR the symptom doesn't match anything in `error-codes.md`:

   > **Next step:** This looks like a backend issue rather than a config problem. Collect the full request body (credentials redacted) and the full response, then email `support@qencode.com` or open a ticket at https://portal.qencode.com. Include the `task_token` if you have one — it lets support trace the job through their logs.

## What NOT to do

- **Don't** assume the error is the user's fault when codes 1 or 7 (internal server error) appear — those are backend issues and the right answer is "retry + escalate".
- **Don't** invent error codes that aren't in `error-codes.md`. If the user reports an undocumented code, say so and apply the generic fallback.
- **Don't** SSH into Qencode infrastructure, run database queries, or otherwise act as Qencode internal support. This skill is for external customers using public APIs only. (Internal Qencode engineers have a separate `/troubleshoot-job` skill that uses infra access.)
- **Don't** auto-resubmit a fixed job. Always show the user the suggested change first; let them invoke `qencode-build-query` + `qencode-transcode` themselves once they agree.

## Cross-references

- `${CLAUDE_PLUGIN_ROOT}/assets/error-codes.md` — full error code table
- `${CLAUDE_PLUGIN_ROOT}/assets/gotchas.md` — non-obvious quirks behind common errors
- `${CLAUDE_PLUGIN_ROOT}/assets/storage.md` — destination-related failures
- `${CLAUDE_PLUGIN_ROOT}/assets/best-practices.md` — composition defaults a failing query may have violated
- `${CLAUDE_PLUGIN_ROOT}/skills/qencode-job-status/SKILL.md` — fetch the failed status first if only a token was provided
- `${CLAUDE_PLUGIN_ROOT}/skills/qencode-build-query/SKILL.md` — regenerate the corrected query
