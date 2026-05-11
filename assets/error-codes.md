# Qencode Transcoding API — Error Codes

Reference for the `qencode-troubleshoot` skill. Errors come in two flavors — **API-level** (returned synchronously from `POST /v1/...` calls in the response body's `error` field) and **job-level** (returned in the `/v1/status` response's `error_description` field for jobs that failed at runtime). Each is diagnosed differently.

## API-level errors

These come back in the response body of `POST /v1/access_token`, `/v1/create_task`, `/v1/start_encode2`, `/v1/status`, and `/v1/upload_file`. The shape is:

```json
{
  "error": <N>,
  "message": "...",                  // sometimes
  "error_description": "..."         // sometimes
}
```

`error: 0` means success — any other value is a failure.

### Code 0 — Success
**Returned by:** all endpoints (the normal case).
**Meaning:** no error; the call succeeded.

### Code 1 — Internal server error
**Returned by:** any endpoint.
**Likely cause:** transient backend issue.
**How to fix:** retry once after a short delay. If it persists, contact support@qencode.com with the request body and the response.

### Code 2 — API key did not pass validation
**Returned by:** `/v1/access_token`.
**Likely cause:** malformed `api_key` value (wrong characters, truncated, padded with whitespace).
**How to fix:** confirm the key in https://portal.qencode.com/project/my_projects and re-export `QENCODE_API_KEY` verbatim. Don't wrap in quotes when setting the env var.

### Code 3 — API key not found
**Returned by:** `/v1/access_token`.
**Likely cause:** key is correctly formatted but doesn't match any project (revoked, deleted project, wrong environment).
**How to fix:** verify the key is current at https://portal.qencode.com/project/my_projects. If you rotated keys, update `QENCODE_API_KEY`.

### Code 4 — Token did not pass validation
**Returned by:** any endpoint taking a `token` argument (`/v1/create_task`, `/v1/status` if you pass a session token).
**Likely cause:** the session token from `/v1/access_token` is malformed (truncated, edited).
**How to fix:** re-issue a session token via `/v1/access_token`.

### Code 5 — Token not found / expired
**Returned by:** any endpoint taking a `token` argument.
**Likely cause:** the session token aged out (default ~24h) or was issued against a since-deleted project.
**How to fix:** re-issue a fresh session token via `/v1/access_token`. Production code should refresh proactively before the `expire` time returned by `/v1/access_token`.

### Code 6 — Service is suspended
**Returned by:** any endpoint.
**Likely cause:** billing issue on the project (unpaid invoice, hard-credit limit hit).
**How to fix:** resolve at https://portal.qencode.com — billing/usage tabs.

### Code 7 — Internal server error
**Returned by:** any endpoint. Same as code 1; backend distinguishes the two internally.
**Likely cause:** transient backend issue.
**How to fix:** retry once. Persistent failures → contact support@qencode.com.

### Code 8 — System busy
**Returned by:** any endpoint, especially `/v1/start_encode2` during peak load.
**Likely cause:** rate limit or capacity throttle.
**How to fix:** wait the number of seconds returned in the response (look for a `retry_after` field) and retry. Don't retry faster than the suggested delay or you'll deepen the backoff.

### Code 9 — Payload value is too long
**Returned by:** `/v1/start_encode2` when `payload` is set.
**Likely cause:** the `payload` argument (opaque user data passed through to callbacks) exceeds the size limit.
**How to fix:** shrink the payload or store it externally and reference by ID instead.

### Code 10 — Project not found
**Returned by:** any endpoint.
**Likely cause:** unusual — the API key resolved to a project that no longer exists or was migrated.
**How to fix:** contact support@qencode.com with your project ID.

### Code 11 — Profile field value did not pass validation
**Returned by:** `/v1/start_encode2` when using profile references.
**Likely cause:** profile reference is malformed.
**How to fix:** double-check the profile name/UUID in https://portal.qencode.com; case-sensitive.

### Code 12 — Profile not found
**Returned by:** `/v1/start_encode2` when using profile references.
**Likely cause:** the named profile doesn't exist in this project (typo, wrong project, deleted profile).
**How to fix:** list profiles in the portal; use the exact name. Profiles are per-project — a profile in project A is invisible to project B.

### Code 13 — task_tokens field did not pass validation
**Returned by:** `/v1/status`.
**Likely cause:** the `task_tokens` value sent isn't a string or comma-separated list of strings.
**How to fix:** ensure it's `"abc123"` or `"abc123,def456"`, not a JSON array or other shape.

### Code 14 — A required field is missing
**Returned by:** any endpoint.
**Likely cause:** a required parameter wasn't sent.
**How to fix:** check the response — it usually names the missing field. Cross-reference `assets/schema-digest.md` for which fields are required per endpoint.

### Code 19 — "query field is required"
**Returned by:** `/v1/start_encode2`.
**Likely cause:** the `query` form field was sent as the inner transcoding params alone instead of double-wrapped as `{"query": {...inner...}}`. See `gotchas.md` §1.
**How to fix:** wrap the JSON: `{"query": {"source": "...", "format": [...]}}`. The outer `"query"` key is mandatory even though the schema field's `data_type` is `"json"`.

> Code 19 is not currently in the published code table — it's been observed empirically. If you hit other unlisted codes, please report them.

## Job-level errors

These appear in the `/v1/status` response (or callback payload) for jobs that **submitted successfully but failed during execution**. The shape is:

```json
{
  "status": "error",                 // or "failed"
  "percent": <N>,
  "error": 1,                        // 0 or 1 — job-level boolean
  "error_description": "...",        // human-readable message
  ...
}
```

The `error` field at this level is a 0/1 boolean (not a code). Inspect `error_description` to understand the failure. Common categories:

### Source download failed
**Symptoms:** error_description mentions "source", "download", "fetch", or "http".
**Likely causes:**
- Source URL is private (S3 bucket policy, presigned URL expired, password-protected HTTP).
- DNS / TLS issues on the customer's hosting.
- HTTP 4xx/5xx from the source server.
**How to fix:** verify the source URL is reachable from a clean network (`curl -I <url>`). For S3, use embedded credentials (`s3://KEY:SECRET@bucket/path`) or a presigned URL with a long expiry. For TUS uploads, ensure the upload completed successfully before submitting the job.

### Source format unsupported / corrupt
**Symptoms:** error_description mentions "decode", "demux", "invalid input", "unsupported codec", "no streams".
**Likely cause:** the source file is corrupted, partially uploaded, or uses an exotic codec.
**How to fix:** re-encode the source locally with `ffmpeg -i <source> -c copy fixed.mp4` to validate. If ffmpeg can read it, Qencode should too — share the source with support if it still fails.

### Destination upload failed
**Symptoms:** error_description mentions "upload", "destination", "S3", "permission denied", "403".
**Likely causes:**
- Wrong `key`/`secret` on the destination object.
- Bucket doesn't exist or the IAM/key lacks `s3:PutObject`.
- `permissions` value rejected by the target provider (see `storage.md` — Qencode S3 and Cloudflare R2 don't accept `permissions`).
- Path conflicts (HLS output where `url` points to a file instead of a folder).
**How to fix:** check `assets/storage.md` for the per-provider compatibility matrix. Use `aws s3 cp` (or equivalent) with the same credentials to verify the destination is writable.

### Out of disk / memory
**Symptoms:** error_description mentions "no space", "out of memory", "killed".
**Likely cause:** the input is unusually large or the requested output ladder is unusually wide; the encoder ran out of resources.
**How to fix:** narrow the ladder, lower the resolution cap, or split the work across multiple jobs (e.g. one HLS output + one MP4 output separately, not in one job).

### Stitch sources don't match
**Symptoms:** for jobs using the `stitch` array — error_description mentions "stitch", "incompatible", "different framerate", "different size".
**Likely cause:** the inputs in the stitch list have mismatched properties (framerate, resolution, codec) that prevent concat-style stitching.
**How to fix:** pre-process the inputs to share the same framerate and resolution, or use a re-encoded stitch path (set per-output encoding params instead of `repack`).

### DRM key fetch failed
**Symptoms:** error_description mentions "DRM", "Widevine", "PlayReady", "Fairplay", "key server", "license".
**Likely cause:** wrong `key_id` / `key` / `iv` in the `cenc_drm` or `fps_drm` block, or a key-server URL that's unreachable from Qencode encoders.
**How to fix:** verify keys are correct hex strings (no `0x` prefix, no whitespace). For external key servers, confirm they accept connections from Qencode's IP ranges.

## Generic fallback: unknown error code

If the error code isn't in this list, do this:

1. **Check the response body** — Qencode usually includes a `message` or `error_description` alongside the code. That's often more informative than the code itself.
2. **Match category by code range:**
   - 1–10: auth / project / access
   - 11–14: request validation
   - 15–29 (sparse): request shape / wrapping issues
   - 30+ (sparse): encoding / runtime issues
3. **Hand it to support** — copy the full request body (with credentials redacted) and the full response. Email support@qencode.com or open an issue at the project portal.
4. **Open a PR against this file** — if you've root-caused it and want to share, add the code here.
