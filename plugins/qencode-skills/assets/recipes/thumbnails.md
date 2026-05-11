---
recipe: thumbnails
title: Thumbnail extraction (single, interval, or sprite sheet)
when_to_use: User wants poster images, periodic thumbnails along the timeline, or a sprite sheet for video scrubbing previews.
output_count: 1 format block per thumbnail style requested
needs_destination: optional (defaults to 24-hour temp storage — warn the user)
---

# Recipe — Thumbnails

Three common shapes:
1. **Single thumbnail** at a specific time (poster image)
2. **Periodic thumbnails** every N seconds along the timeline
3. **Sprite sheet** — one image with N×M tiled thumbnails for scrub previews

Thumbnail sizing uses `resolution` (smaller side) so the recipe works for landscape and portrait sources without distorting either.

## Single poster at 50%

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "thumbnail",
        "time": 0.5,
        "image_format": "jpg",
        "resolution": 720,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/poster.jpg"
        }
      }
    ]
  }
}
```

`time` is a fraction of total duration (0.0–1.0). For an exact second, use `start_time` (in seconds); for a specific frame, use `frame_number`.

## Periodic thumbnails every 10 seconds

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "thumbnails",
        "interval": 10,
        "image_format": "jpg",
        "resolution": 240,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/thumbs/"
        }
      }
    ]
  }
}
```

Output files are named like `thumb_0001.jpg`, `thumb_0002.jpg`, … in the destination prefix.

## Sprite sheet (10 columns wide)

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "thumbnails",
        "interval": 10,
        "sprite": 1,
        "columns": 10,
        "image_format": "jpg",
        "resolution": 90,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/sprite.jpg"
        }
      }
    ]
  }
}
```

Each cell is sized so its smaller side equals `resolution`. The result is one big JPEG/WEBP. For player scrubbing UIs that consume a `.vtt` file, you'll typically also want to generate the WebVTT mapping client-side.

## Combining with a transcode in one job

You can submit thumbnails as additional `format` entries alongside a video output. They run in parallel and complete independently:

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      { "output": "advanced_hls", "segment_duration": 6, "stream": [{"video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720, "framerate": "30", "keyframe": "60", "quality": 22}], "destination": {/*...*/} },
      { "output": "thumbnail",  "time": 0.5, "resolution": 720, "destination": {/*...*/} },
      { "output": "thumbnails", "interval": 10, "sprite": 1, "columns": 10, "resolution": 90, "destination": {/*...*/} }
    ]
  }
}
```

## Other storage backends

For AWS S3, Cloudflare R2, Backblaze B2, Azure Blob, FTP/SFTP, or fan-out, see **`assets/storage.md`**. Note: the `thumbnails` (plural) and `speech_to_text` outputs need `url` to be a **folder** path; `thumbnail` (singular) needs a full filename. `storage.md` covers the path-vs-folder rules per output type.

## Customization notes

- **Use `width` instead of `resolution`** when the user wants a fixed thumbnail width regardless of source orientation. `resolution` is the better default; `width` is occasionally what UI layouts need.
- **Format**: `image_format` accepts `jpg`, `png`, `webp`. WEBP is smallest; JPEG has the broadest browser support.
- **No destination** = 24-hour temp storage. Useful for quick previews; warn the user before submitting.

## Schema pointers

Read in `assets/schema-digest.md`:
- `start_encode2.query.format[].output` — `thumbnail` (single) vs `thumbnails` (multi)
- `start_encode2.query.format[].time` / `start_time` / `frame_number` — when to grab
- `start_encode2.query.format[].interval` — period in seconds for `thumbnails`
- `start_encode2.query.format[].sprite` / `columns` — sprite sheet layout
- `start_encode2.query.format[].image_format` — `jpg`, `png`, `webp`

See also: `assets/best-practices.md` (§1, §2, §6) and `assets/storage.md`.

## Gotchas

- `output: "thumbnail"` (singular) emits one image. `output: "thumbnails"` (plural) emits a series.
- `time` is a 0–1 fraction; `start_time` is in seconds. Don't mix them unintentionally.
- `resolution` preserves aspect ratio. Setting both `width` and `height` may stretch unless `resize_mode: "crop"` is also set.
