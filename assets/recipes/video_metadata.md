---
recipe: video_metadata
title: Extract source video metadata (ffprobe JSON)
when_to_use: User needs source video info (width, height, duration, codecs, streams) before deciding how to transcode — gating logic, automatic ladder sizing, content classification, or just sanity-checking inputs.
output_count: 1
needs_destination: optional (defaults to 24-hour temp storage)
based_on: content/tutorials/transcoding/video-metadata.md
---

# Recipe — Source video metadata

Produces a JSON file containing ffprobe-style metadata for the source: format info, streams (video + audio + subtitles), codecs, durations, bitrates, frame rates, pixel formats, channel layouts, tags. Use this when you need to inspect the source before transcoding (or in addition to transcoding).

## query JSON

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "metadata",
        "metadata_version": "4.1.5",
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/metadata.json"
        }
      }
    ]
  }
}
```

`destination.url` points at the **full JSON file path** (not a folder). The output is a single `.json` file.

## What you get back

The JSON has the same shape as `ffprobe -of json -show_format -show_streams`. Top-level keys:

- `format.duration` (seconds), `format.bit_rate`, `format.size`, `format.format_name`
- `format.tags` — title, artist, encoder, etc. (if present in source)
- `streams[]` — one entry per stream:
  - Video streams: `codec_type: "video"`, `codec_name` (`h264`, `hevc`, `vp9`, `av1`, …), `width`, `height`, `display_aspect_ratio`, `r_frame_rate`, `avg_frame_rate`, `pix_fmt`, `level`, `profile`, `has_b_frames`, `bits_per_raw_sample`
  - Audio streams: `codec_type: "audio"`, `codec_name`, `channels`, `channel_layout`, `sample_rate`, `bit_rate`
  - Subtitle streams: `codec_type: "subtitle"`, `codec_name`, language tags

## Customization notes

- **`metadata_version`**: pin to a specific FFPROBE util version (e.g. `"4.1.5"`). Recommended for production workflows so the JSON shape doesn't shift when Qencode upgrades ffprobe. Omit to get the current default.
- **No destination**: the JSON file lands in 24-hour temp storage. Fine for one-off inspection; warn the user if they're building a pipeline.

## Why use metadata output instead of running ffprobe yourself

- The source file may live behind credentials Qencode already has (TUS upload, S3 with `s3://KEY:SECRET@…`).
- You're already calling Qencode for transcoding — bundling a metadata output adds no API overhead and finishes in seconds (much faster than a transcode).
- The output is structured, dated, and can be persisted to your storage.

## Schema pointers

- `start_encode2.query.format[].output` — `metadata`
- `start_encode2.query.format[].metadata_version` — pin a specific ffprobe version

See also: `assets/storage.md` and `assets/best-practices.md` (§1, §6).

## Gotchas

- Don't put encoding params (`video_codec`, `quality`, `resolution`, etc.) on a `metadata` output — they're meaningless.
- The metadata output is **fast and cheap** but still bills as a job. For high-frequency probing, consider caching the JSON.
- For very large sources, the metadata output may still take a few seconds because Qencode has to fetch enough of the file to read indexes.
