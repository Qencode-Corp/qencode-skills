# Qencode Transcoding API — Gotchas

Things that aren't obvious from a quick read of the schema. Skills should consult this list before submitting jobs or interpreting failures.

## 1. The `query` field is double-wrapped

The `query` form field on `POST /v1/start_encode2` expects JSON shaped like `{"query": {...transcoding params...}}`, NOT the inner transcoding params alone.

**Wrong** — returns error 19, "query field is required":
```
query={"source": "...", "format": [...]}
```

**Right:**
```
query={"query": {"source": "...", "format": [...]}}
```

The schema field's `data_type` is `"json"`, which suggests the inner object is enough. It isn't. The cURL example in the public docs shows the wrapping clearly.

## 2. `status_url` points at a master endpoint

`/v1/start_encode2` returns a `status_url` that targets a specific master host (e.g. `https://prod-nyc3-1-api-do.qencode.com/v1/status`). The docs note: "always get job status using the endpoint specified as last value returned in `status_url`."

In practice the public `https://api.qencode.com/v1/status` endpoint also works for basic polling, but for production code you should follow `status_url` — the master is authoritative and avoids a routing hop.

## 3. Submission can drop the connection mid-request

The Qencode edge occasionally drops `/v1/start_encode2` connections without sending a response (`httpx.RemoteProtocolError: Server disconnected without sending a response` / curl `HTTP/2 GOAWAY`). This is transient — a single retry succeeds in nearly all cases. Don't retry indefinitely; one retry is enough.

## 4. Tokens have lifecycles

- `token` (from `/v1/access_token`) — a session token tied to your `api_key`. Reuse it across many `create_task` calls; don't call `/v1/access_token` per job.
- `task_token` (from `/v1/create_task`) — single-use. Every `start_encode2` needs a fresh `task_token`.
- `expire` field on the access token is a UTC datetime string; refresh before it expires.

## 5. Source URI shapes

`query.source` accepts:
- HTTPS URL: `https://example.com/video.mp4`
- S3 URL with embedded credentials: `s3://KEY:SECRET@bucket/path/video.mp4`
- TUS upload reference: `tus:<file_uuid>` after a direct upload via `/v1/upload_file`
- Stitch list: use the top-level `stitch` array instead of `source` to concatenate multiple inputs.

## 6. Output storage — see `assets/storage.md`

Everything about `destination` (per-provider params, omitted-destination behavior, fan-out, cache headers) is in `assets/storage.md`. The two most-common pitfalls to remember:

- Omitting `destination` puts outputs in **24-hour temp storage** — files vanish.
- The `permissions` field is documented as "S3 only" but is **rejected by Qencode S3 and Cloudflare R2**. Don't include it for those backends.

## 7. `encoder_version: 2` is the right default

`query.encoder_version` accepts `1` or `2`. **Always set `2`** unless the user explicitly needs a V1-only feature (notably VMAF). V1 has caused audio-out-of-sync output in production and lacks per-title encoding, AV1, and advanced HLS/DASH packaging. See `best-practices.md` §1.

## 8. Polling cadence

The `/v1/status` endpoint is rate-limited per project. For long jobs, poll at increasing intervals: 5s → 15s → 30s → 60s. The `qencode-mcp` `wait_for_job` tool implements this back-off automatically.

## 9. Callbacks fire on each subtask only if you ask

`callback_url` alone fires once when the whole job finishes. To get per-format-output callbacks (useful for ABR ladders where individual renditions complete at different times), set `use_subtask_callback: 1`.
