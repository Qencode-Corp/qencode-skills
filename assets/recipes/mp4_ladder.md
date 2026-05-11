---
recipe: mp4_ladder
title: MP4 multi-resolution ladder
when_to_use: User wants the same source delivered as several standalone MP4 files at different resolutions. Each MP4 is independent — no manifest, no segments. Good for legacy progressive-download players, simple downloads, or as a base for client-side switching.
output_count: variable (one per ladder rung)
needs_destination: optional (defaults to 24-hour temp storage — warn the user)
---

# Recipe — MP4 multi-resolution ladder

Produces N independent MP4 files at different resolutions from a single source. Each rung uses CRF + per-title encoding, libfdk_aac audio, and `resolution` (smaller side) so the recipe works for landscape and portrait sources alike.

## Inputs

- `source` — public URL of the input video (HTTPS or `s3://`).
- `rungs` — list of resolutions the user wants. Defaults below.
- `destination` — optional. **If omitted, files are deleted from Qencode temporary storage after ~24 hours** — tell the user.

## Default ladder

| `resolution` (smaller side) | `audio_bitrate` |
|---|---|
| 1080 | 128 |
| 720  | 128 |
| 480  |  96 |
| 360  |  96 |

Per-title encoding (`optimize_bitrate: 1`) auto-selects the best CRF per rung within `[min_crf, max_crf]`.

## query JSON — Qencode-managed storage (no credentials needed)

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 1080,
        "quality": 22,
        "optimize_bitrate": 1,
        "min_crf": 18,
        "max_crf": 28,
        "audio_bitrate": 128,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/1080p.mp4"
        }
      },
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 720,
        "quality": 22,
        "optimize_bitrate": 1,
        "min_crf": 18,
        "max_crf": 28,
        "audio_bitrate": 128,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/720p.mp4"
        }
      },
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 480,
        "quality": 23,
        "optimize_bitrate": 1,
        "min_crf": 18,
        "max_crf": 30,
        "audio_bitrate": 96,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/480p.mp4"
        }
      },
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 360,
        "quality": 23,
        "optimize_bitrate": 1,
        "min_crf": 18,
        "max_crf": 30,
        "audio_bitrate": 96,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/360p.mp4"
        }
      }
    ]
  }
}
```

## Other storage backends

For AWS S3, Cloudflare R2, Backblaze B2, Azure Blob, FTP/SFTP, fan-out to multiple destinations, or `cache_control` headers, see **`assets/storage.md`**. That doc has the per-provider compatibility matrix and ready-to-paste destination snippets. Substitute the destination block in the recipe above.

## Customization notes

- **Codec**: swap `libx264` → `libx265` for HEVC (smaller files, narrower playback support) or `libsvtav1` for AV1 (smallest, requires `encoder_version: 2`, which is already set).
- **Force exact dimensions**: replace `resolution` with `size: "1920x1080"` and add `resize_mode: "crop"` if you need to force a specific aspect ratio. Otherwise leave `resolution` alone — it preserves source aspect ratio for both landscape and portrait sources.
- **Fixed bitrate target** (CDN/contract): replace `quality` + `optimize_bitrate` block with `"bitrate": 5000` (in kbps). Skip per-title in that case.
- **Skip per-title**: drop `optimize_bitrate`/`min_crf`/`max_crf` and use just `quality: <CRF>` for a fixed-CRF encode.
- **No destination** = 24-hour temp storage. Useful for quick previews; warn the user before submitting.

## Schema pointers

Read in `assets/schema-digest.md`:
- `start_encode2.query.format` — per-output options
- `start_encode2.query.format[].destination` — destination fields
- `start_encode2.query.format[].video_codec_parameters` — fine-grained codec tuning

See also: `assets/best-practices.md` (§1, §2, §3, §4, §5, §6) and `assets/storage.md`.

## Gotchas

- Remember the double-wrapped `query` envelope (see `gotchas.md` §1).
- Ladder rungs run in parallel by default. For per-rung completion callbacks, set `use_subtask_callback: 1` at the top level alongside a `callback_url`.
- `aac` is *not* the default audio codec here — `libfdk_aac` is. Don't downgrade unless the user explicitly forbids libfdk_aac.
