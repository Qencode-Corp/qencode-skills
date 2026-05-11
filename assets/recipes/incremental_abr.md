---
recipe: incremental_abr
title: Incremental ABR — add/remove resolutions without re-encoding the whole ladder
when_to_use: User has an existing HLS/DASH ladder and wants to add a new rung (e.g., adding 1080p later when the video gets popular) or remove a rung without re-encoding everything. Subsequent jobs use the same `incremental_tag` to link to previously-encoded renditions.
output_count: 1 (single advanced_hls or advanced_dash output, updated across multiple jobs)
needs_destination: required (same destination across all jobs in the chain)
based_on: content/tutorials/transcoding/incremental-abr.md
---

# Recipe — Incremental ABR

Sequential ABR-ladder management: encode a low-res rung now, add 720p next month when the video gets traction, add 1080p later if it goes viral. Each job in the chain uses the same `incremental_tag` to reuse already-encoded renditions instead of re-encoding them.

Saves cost and time. Especially useful for catalogs where:
- Most content stays low-traffic — keep them at 360p/480p.
- Some content trends — promote it to 720p+.
- Storage costs matter — only keep high-resolution renditions for popular titles.

## Step 1 — Initial job (one rung)

Encode 360p first. Use a stable `incremental_tag` value you can refer back to:

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "advanced_hls",
        "incremental_tag": "movie_42_ladder",
        "segment_duration": 6,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/movie_42/"
        },
        "stream": [
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 360,
            "framerate": "30",
            "keyframe": "60",
            "quality": 23,
            "audio_bitrate": 96
          }
        ]
      }
    ]
  }
}
```

After this job, your master playlist references one variant: 360p.

### Alternative: let Qencode generate the tag

Set `incremental_tag: "auto"` on the first job. The system generates a unique ID and returns it in the `meta.incremental_tag` field of each video output:

```json
"videos": [
  {
    "meta": {
      "resolution_width": 640,
      "resolution_height": 360,
      "incremental_tag": "9513cab812f0d4003c3ddd2c97bd073a-0"
    }
  }
]
```

Persist that value — you'll need it on every subsequent job in the chain. **Don't parse or rely on its format** — it's opaque.

## Step 2 — Add a rung later

Reuse the same `incremental_tag`. Include the **already-encoded** rung in the `stream[]` list along with the **new** rung you want to add. Qencode only encodes the new one; the previous one is linked from the existing storage:

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "advanced_hls",
        "incremental_tag": "movie_42_ladder",
        "segment_duration": 6,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/movie_42/"
        },
        "stream": [
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 720,
            "framerate": "30",
            "keyframe": "60",
            "quality": 22,
            "audio_bitrate": 128
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 360,
            "framerate": "30",
            "keyframe": "60",
            "quality": 23,
            "audio_bitrate": 96
          }
        ]
      }
    ]
  }
}
```

Qencode encodes the 720p rendition. The 360p variant is reused. The master playlist now references both: 720p and 360p.

## Step 3 — Remove a rung

Run a new job with the same `incremental_tag` and omit the rung you want to drop. Add new rungs if you want:

```json
{
  "output": "advanced_hls",
  "incremental_tag": "movie_42_ladder",
  "segment_duration": 6,
  "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/movie_42/" },
  "stream": [
    { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 1080, "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 },
    { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720,  "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 }
  ]
}
```

Master playlist now references 1080p (newly encoded) + 720p (reused). The 360p entry is **unlinked** from the master playlist.

> ⚠️ **Unlinking ≠ deleting.** The 360p segments remain in your storage bucket — they're just not referenced by the master playlist anymore. If you also want them gone from storage to save cost, delete them with your own S3 tooling.

## Same recipe for DASH

Swap `advanced_hls` → `advanced_dash`. Everything else stays the same.

## Customization notes

- **`incremental_tag` length**: up to 64 characters. Pick something stable and meaningful (`movie_42_ladder`, `live_event_2026_05_11`, etc.) if you'd rather not store auto-generated values.
- **Same source required**: the source URL should match across jobs in the chain. If you encode 720p from `source_v1.mp4` and then try to add 1080p from `source_v2.mp4` with the same tag, the rendition references won't match.
- **Same destination required**: also same. The `incremental_tag` ties together renditions at a specific destination prefix.
- **Same codec / packaging required**: don't mix H.264 and H.265 under one tag; don't mix HLS and DASH.

## Schema pointers

- `start_encode2.query.format[].incremental_tag` — string, max 64 chars, or `"auto"`
- `status.returns.status.videos[].meta.incremental_tag` — auto-generated tag, returned per video output

See also: `assets/recipes/hls_abr.md` (base HLS ladder), `assets/recipes/refresh_abr_playlist.md` (incremental updates *within* a single job).

## Gotchas

- Distinguish from **`refresh_playlist`**: `refresh_playlist` updates the master playlist as renditions finish *within one job*. `incremental_tag` reuses renditions *across multiple jobs over time*. They're different features and can be combined.
- Auto-generated tag format may change. Store the value Qencode gave you, don't try to predict it.
- The unlink-doesn't-delete behavior catches teams who assume removing a rung frees storage. Bake a cleanup step into your pipeline if storage cost matters.
- Be careful with credentials — keep `key`/`secret` on each destination object across all jobs in the chain (Qencode S3 doesn't need them; AWS/R2/etc. do per `storage.md`).
