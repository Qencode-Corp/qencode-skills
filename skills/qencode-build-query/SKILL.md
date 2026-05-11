---
name: qencode-build-query
description: Use when the user asks to transcode, encode, convert, re-encode, or process a video — or to produce HLS, DASH, MP4, MP3, thumbnails, or any other Qencode output. Composes a validated `query` JSON payload for `POST /v1/start_encode2`. Pure composition; does not submit the job. Hand the JSON to `qencode-transcode` (or paste into the user's own tooling) to actually run it.
version: 0.1.0
---

# qencode-build-query

You compose the `query` JSON for the Qencode Transcoding API. You do not submit jobs — that's `qencode-transcode`'s job.

## What "compose" means here

Produce a single JSON block of the exact shape `POST /v1/start_encode2` expects:

```json
{
  "query": {
    "source": "...",
    "encoder_version": 2,
    "format": [ /* one entry per output */ ]
  }
}
```

The outer `{"query": ...}` wrapper is **required** — submitting just the inner object returns error 19 "query field is required". Never strip the wrapper.

## Workflow

1. **Read `${CLAUDE_PLUGIN_ROOT}/assets/best-practices.md` first.** It has the eight composition defaults (encoder v2, `resolution` over `height`, `libfdk_aac`, `quality` over `bitrate`, per-title instead of `two_pass`, no `permissions` on Qencode S3, omitted-destination = 24h temp, ABR per-rendition params on `stream[]`). These override what the schema's defaults suggest.

2. **Pick the matching recipe(s)** based on what the user asked for. Read each picked recipe's full markdown before writing JSON.

   | User said | Recipe |
   |---|---|
   | "HLS", "adaptive bitrate", "stream to browser/iOS", `.m3u8` | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/hls_abr.md` |
   | "MP4 ladder", "multiple resolutions as MP4", "download links" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/mp4_ladder.md` |
   | "thumbnail", "poster", "sprite sheet", "scrub preview" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/thumbnails.md` |
   | "DASH", `.mpd` | adapt `hls_abr.md` — replace `output: "advanced_hls"` with `"advanced_dash"`, keep the same stream-level rules |
   | "extract audio", `.mp3`, `.flac` | use `output: "mp3"` or `"flac"` with `audio_codec`, `audio_bitrate` (see schema digest) |
   | "transcribe", "captions", "subtitles" | use `output: "speech_to_text"` (see schema digest) |
   | Combined ("HLS + a poster + extract audio") | one `format[]` entry per output, all in the same job |

   If no recipe matches, fall back to the schema digest at `${CLAUDE_PLUGIN_ROOT}/assets/schema-digest.md`.

3. **Pick the destination shape.** Read `${CLAUDE_PLUGIN_ROOT}/assets/storage.md` whenever the user mentions:
   - a specific provider (AWS, R2, Backblaze, Azure, FTP, …)
   - public/private access, ACLs, storage class
   - multiple destinations (fan-out)
   - cache headers / CDN settings

   If the user names no destination at all, omit `destination` and **explicitly tell them outputs will be deleted after ~24 hours**.

4. **Fill in user-supplied values** (source URL, custom ladder, bucket, etc.). For missing details:
   - Apply the recipe's defaults (don't ask).
   - For ambiguous things that materially affect output (e.g. "what ladder do you want?", "AWS S3 or Qencode S3?"), ask one short question with a recommended default, not a barrage.

5. **Sanity check before emitting:**
   - Outer `{"query": ...}` wrapper present.
   - `encoder_version: 2` at the top.
   - For HLS/DASH outputs: `video_codec`, `audio_codec`, `resolution` (or sizing equivalent), `framerate`, `keyframe`, `quality`, `audio_bitrate` live on each `stream[]` entry — NOT at the format level.
   - For Qencode S3 destinations (`*.s3.qencode.com`): no `key`, no `secret`, no `permissions`, no `storage_class`.
   - For Cloudflare R2: no `permissions`, no `storage_class`.
   - No `two_pass: 1` — use `optimize_bitrate: 1` with `min_crf`/`max_crf` instead.
   - Audio codec is `libfdk_aac` unless the user said otherwise.

6. **Emit the JSON in a single fenced block.** Then add a short, scannable summary covering:
   - What this job produces (e.g. "4-rung HLS ladder at 1080/720/540/360, written to s3://…")
   - Any caveats — especially the 24-hour expiry if `destination` was omitted
   - The next step ("Hand this to `qencode-transcode` to submit, or pass it as the `query` form field to `POST /v1/start_encode2`.")

   Do not narrate the composition process — just the JSON and the summary.

## Examples

Self-study examples live in `${CLAUDE_PLUGIN_ROOT}/skills/qencode-build-query/examples/`. Each is a `.md` file with the user prompt and the expected output. Read one or two if you're unsure of the conventions.

## What NOT to do

- Do **not** call any HTTP endpoint or MCP tool — composition only.
- Do **not** invent fields not in the schema digest.
- Do **not** ask the user for an `api_key` or `task_token` — those belong to the submission step.
- Do **not** strip the outer `{"query": ...}` wrapper, ever.
- Do **not** override the eight defaults from `best-practices.md` silently; if you must, surface why in the summary.

## Cross-references

- `${CLAUDE_PLUGIN_ROOT}/assets/best-practices.md` — composition defaults
- `${CLAUDE_PLUGIN_ROOT}/assets/storage.md` — destinations
- `${CLAUDE_PLUGIN_ROOT}/assets/gotchas.md` — non-obvious quirks
- `${CLAUDE_PLUGIN_ROOT}/assets/recipes/*.md` — named recipes
- `${CLAUDE_PLUGIN_ROOT}/assets/schema-digest.md` — every attribute
- `${CLAUDE_PLUGIN_ROOT}/assets/schema-index.json` — fast attribute lookup (for `qencode-api-reference`)
