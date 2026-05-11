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

   **Output-format recipes:**

   | User said | Recipe |
   |---|---|
   | "HLS", "adaptive bitrate", "stream to browser/iOS", `.m3u8` | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/hls_abr.md` |
   | "DASH", `.mpd` | adapt `hls_abr.md` — swap `output: "advanced_hls"` → `"advanced_dash"`; same stream-level rules |
   | "MP4 ladder", "multiple resolutions as MP4", "download links" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/mp4_ladder.md` |
   | "MP3", "FLAC", "HLS audio", "extract audio", "audio-only" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/audio_outputs.md` |
   | "thumbnail", "poster", "sprite sheet", "scrub preview" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/thumbnails.md` |
   | "subtitles", "captions", "add .srt", "copy CEA-608/708" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/subtitles.md` |
   | "transcribe", "speech-to-text", "auto-subtitles", "translate audio" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/speech_to_text.md` |
   | "metadata", "ffprobe", "inspect source", "get width/height/duration" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/video_metadata.md` |

   **Codec-specific recipes:**

   | User said | Recipe |
   |---|---|
   | "AV1", `libsvtav1`, "smallest files" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/codec_av1.md` |
   | "LCEVC", `lcevc_h264`, `lcevc_hevc`, "V-Nova" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/codec_lcevc.md` |

   **Workflow/feature recipes:**

   | User said | Recipe |
   |---|---|
   | "per-title encoding", "CRF tuning", `optimize_bitrate` | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/per_title_encoding.md` |
   | "stitch", "concatenate", "combine clips", "compilation" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/stitching.md` |
   | "webhook", "callback", "notify when done" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/callbacks.md` |
   | "retry on error", "soft fail", "reliability", "production-ready" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/reliability.md` |
   | "incremental ABR", "add a 1080p rung later", `incremental_tag` | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/incremental_abr.md` |
   | "refresh playlist", "playable while encoding", "rolling availability" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/refresh_abr_playlist.md` |

   **DRM recipes:**

   | User said | Recipe |
   |---|---|
   | "AES-128", "simple HLS encryption" | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/drm_aes128.md` |
   | "Widevine", "EZDRM Widevine", `cenc_drm` for Android/Chrome | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/drm_widevine_ezdrm.md` |
   | "PlayReady", "EZDRM PlayReady", `cenc_drm` for Windows/Xbox | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/drm_playready_ezdrm.md` |
   | "FairPlay", "EZDRM Fairplay", `fps_drm` for iOS/macOS | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/drm_fairplay_ezdrm.md` |
   | "BuyDRM", "KeyOS", CPIX request | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/drm_buydrm.md` |
   | "ExpressPlay", multi-DRM via ExpressPlay | `${CLAUDE_PLUGIN_ROOT}/assets/recipes/drm_expressplay.md` |

   **Combined outputs** ("HLS + a poster + extract audio") → one `format[]` entry per output, all in the same job. Mix recipes as needed.

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
