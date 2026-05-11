---
recipe: refresh_abr_playlist
title: Refresh ABR playlist — make renditions playable as they finish
when_to_use: User wants viewers to start watching the lower-resolution rungs of an HLS/DASH ladder while higher-resolution rungs are still encoding. Cuts time-to-first-frame on long encodes. Different from `incremental_tag` — this is within a single job.
output_count: 1 (single advanced_hls or advanced_dash output, master playlist refreshed during encoding)
needs_destination: required (master playlist is rewritten each time a rendition completes)
based_on: content/tutorials/transcoding/refreshing-abr-playlist.md
---

# Recipe — Refresh ABR playlist

Turn on `refresh_playlist: 1` on an ABR output and Qencode updates the master playlist at your destination **each time a rendition finishes**. The first rendition (usually the lowest resolution, which encodes fastest) becomes playable while the rest are still in flight.

Common use cases:
- **Long-form encodes** (movies, multi-hour lectures) where waiting 20+ minutes for the whole ladder is too slow.
- **Live-event archives** that need to be available ASAP after the event ends.
- **Catalog ingestion pipelines** where time-to-first-play is a key metric.

## query JSON

```json
{
  "query": {
    "source": "https://example.com/source_video.mp4",
    "encoder_version": 2,
    "callback_url": "https://yourserver.com/qencode_callback",
    "format": [
      {
        "output": "advanced_hls",
        "refresh_playlist": 1,
        "segment_duration": 6,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/hls/"
        },
        "stream": [
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 360,  "framerate": "30", "keyframe": "60", "optimize_bitrate": 1, "audio_bitrate": 96  },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 480,  "framerate": "30", "keyframe": "60", "optimize_bitrate": 1, "audio_bitrate": 128 },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720,  "framerate": "30", "keyframe": "60", "optimize_bitrate": 1, "audio_bitrate": 128 },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 1080, "framerate": "30", "keyframe": "60", "optimize_bitrate": 1, "audio_bitrate": 128 }
        ]
      }
    ]
  }
}
```

Two key params:
- `refresh_playlist: 1` — enable incremental playlist updates.
- `callback_url` (optional but recommended) — get notified each time a rendition is added.

## How playback evolves during the job

| Time | Playlist content | What viewers can watch |
|---|---|---|
| t=0 | Empty / not yet present | nothing |
| t=2min | 360p variant listed | 360p only |
| t=5min | 360p + 480p variants | 360p, 480p |
| t=12min | 360p + 480p + 720p variants | 360p, 480p, 720p |
| t=20min | Full ladder | Full ABR ladder |

The actual cadence depends on encoder load and source length. Smaller / shorter / lower-resolution rungs finish first.

## Watching for refresh events

### Via callbacks (preferred)

Set `callback_url` and Qencode POSTs to your endpoint each time the master playlist is updated. The callback body includes:

| Field | Value |
|---|---|
| `task_token` | The job's task token |
| `event` | Lifecycle event (`queued`, `saved`, etc.) |
| `callback_type` | `"stream"` for playlist-refresh events |
| `status` | Encoding status snapshot — `videos[]`, `error`, percent, URLs |

See `assets/recipes/callbacks.md` for the full callback shape.

### Via polling

If you can't expose a callback endpoint, periodically call `mcp__qencode__get_job_status` (or `POST /v1/status`). The same `videos[]` array updates as renditions land.

## DASH variant

Swap `advanced_hls` → `advanced_dash`:

```json
{
  "output": "advanced_dash",
  "refresh_playlist": 1,
  /* … same stream[] … */
}
```

The `.mpd` manifest is rewritten as each rendition finishes.

## Customization notes

- **Resolution order matters for perceived speed**: list smaller resolutions first in `stream[]`. They finish first and unlock playback for low-bandwidth viewers immediately.
- **Don't pair with `incremental_tag` unless intentional**: they're different features. `refresh_playlist` is within-job; `incremental_tag` is across-jobs. Combining them works but rarely needed.
- **CDN caching**: if your CDN caches the master playlist aggressively, refreshes won't reach viewers. Set a short `cache_control` on the master playlist (e.g. `"public, max-age=10"`); segments can stay long-cached. See `assets/storage.md` for cache patterns.
- **No destination**: `refresh_playlist` requires a stable destination prefix — it doesn't work meaningfully with the 24-hour temp storage (no master playlist URL to refresh).

## Schema pointers

- `start_encode2.query.refresh_playlist` — 0/1, **top-level** (not on `format[]`). Default 0.
- `start_encode2.query.callback_url` — top-level webhook URL.
- `start_encode2.query.use_subtask_callback` — for per-format callbacks.

See also: `assets/recipes/hls_abr.md` (base HLS ladder), `assets/recipes/callbacks.md` (callback delivery), `assets/recipes/incremental_abr.md` (the cross-job sibling feature), `assets/storage.md` (CDN cache headers for the master playlist).

## Gotchas

- `refresh_playlist` is **top-level on `query`**, not nested in `format[]`. Easy to get wrong.
- Make sure your CDN doesn't aggressively cache the master playlist — viewers won't see the new rungs.
- For DASH, the `.mpd` is similarly refreshed; the same caching caveat applies.
- The total job time is unchanged — refresh_playlist is about *time-to-first-play*, not total encode time.
