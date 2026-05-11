---
recipe: stitching
title: Stitch multiple source videos into one output
when_to_use: User wants to concatenate two or more input videos into a single output (compilation, clip stitching, intro+main+outro). Inputs can be full videos or clipped segments by `start_time` + `duration`.
output_count: 1+ format blocks; the `stitch` source replaces the singular `source`
needs_destination: optional (defaults to 24-hour temp storage)
based_on: content/tutorials/transcoding/stitch-videos-together.md
---

# Recipe — Stitch videos together

Replace the top-level `source` with a `stitch` array of input URLs (or input objects with `url` + optional `start_time` + `duration`). Qencode concatenates them in order and produces the requested outputs.

> ⚠️ **Encoder version exception:** the public docs state stitching is currently only supported under **`encoder_version: 1`**. This overrides our usual default (`encoder_version: 2` — see `best-practices.md` §1). Set `encoder_version: 1` explicitly on stitch jobs until support is added to v2.

## Basic stitch — three full videos

```json
{
  "query": {
    "encoder_version": 1,
    "stitch": [
      "https://example.com/intro.mp4",
      "https://example.com/main.mp4",
      "https://example.com/outro.mp4"
    ],
    "format": [
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 720,
        "bitrate": 2800,
        "framerate": "30",
        "keyframe": "60",
        "audio_bitrate": 128,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/compilation.mp4"
        }
      }
    ]
  }
}
```

Note: omit `source` when using `stitch` — they're mutually exclusive top-level fields.

## Stitch with clips (mixing whole videos and segments)

```json
{
  "query": {
    "encoder_version": 1,
    "stitch": [
      "https://example.com/clip_a.mp4",
      {
        "url": "https://example.com/clip_b.mp4",
        "start_time": 100.0,
        "duration": 60.0
      },
      {
        "url": "https://example.com/clip_c.mp4",
        "start_time": 30.0,
        "duration": 15.0
      }
    ],
    "format": [
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 720,
        "bitrate": 2800,
        "framerate": "30",
        "keyframe": "60",
        "audio_bitrate": 128,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/compilation.mp4"
        }
      }
    ]
  }
}
```

`start_time` and `duration` are both in seconds and apply to each individual input. You can repeat the same `url` across multiple entries to stitch different clips from the same source.

## Stitch into HLS

```json
{
  "query": {
    "encoder_version": 1,
    "stitch": [
      "https://example.com/intro.mp4",
      "https://example.com/main.mp4"
    ],
    "format": [
      {
        "output": "advanced_hls",
        "segment_duration": 6,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/hls/"
        },
        "stream": [
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720, "framerate": "30", "keyframe": "60", "bitrate": 2800, "audio_bitrate": 128 },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 480, "framerate": "30", "keyframe": "60", "bitrate": 1400, "audio_bitrate": 96  }
        ]
      }
    ]
  }
}
```

## Why explicit `bitrate` / `framerate` / `keyframe`

The tutorial recommends explicitly specifying these on every stitch job. Reason: input videos can have **different** framerates, resolutions, or codecs, and the output's behavior becomes hard to predict otherwise:

- If `framerate` isn't set on the output, it inherits the framerate of the **first** video in the list — which may not match the others.
- If `bitrate` isn't set, the output bitrate is derived per-input, leading to inconsistent perceived quality across clip boundaries.
- For HLS/DASH, keyframe alignment depends on a stable `keyframe` setting; otherwise segments won't cut cleanly at clip boundaries.

> Note: stitching with `encoder_version: 1` doesn't support per-title encoding (`optimize_bitrate`), so we use explicit `bitrate` rather than `quality` + per-title. This is one of the few cases where CBR-style `bitrate` is the right choice. See `best-practices.md` §4.

## Input video compatibility — what to harmonize

For best results, pre-process your inputs so they share:

- **Resolution / aspect ratio**: mixing landscape and portrait clips without `resize_mode: "crop"` will produce wonky output.
- **Frame rate**: 30 fps clips stitched with 24 fps clips will visibly judder at boundaries.
- **Audio sample rate / channels**: 48 kHz stereo + 44.1 kHz mono may cause audio glitches at seams.

If you can't preprocess, set `resize_mode: "crop"`, `framerate: "30"` (or whatever target), `audio_channels_number: 2` to force normalization at encode time.

## Customization notes

- **Encoder v2 isn't supported for stitch yet** — keep an eye on the docs; this may change.
- **Per-title encoding (`optimize_bitrate`)** doesn't work under v1 — use `bitrate` for stitch jobs.
- **No destination**: outputs land in 24-hour temp storage. Warn the user.
- **Same audio language across inputs** is recommended; multi-language stitching produces unpredictable audio mapping.
- For trimming a single video without concatenation, use `start_time` + `duration` on a single `format[]` entry with a normal `source` (no `stitch` needed) — see `assets/recipes/mp4_ladder.md` for that pattern.

## Schema pointers

- `start_encode2.query.stitch` — replaces `source`; array of URL strings or `{url, start_time?, duration?}` objects
- `start_encode2.query.encoder_version` — must be `1` for stitch jobs (currently)
- `start_encode2.query.format[].framerate` / `.keyframe` / `.bitrate` — recommend explicit values for predictability

See also: `assets/recipes/mp4_ladder.md` (single-source MP4 ladder), `assets/recipes/hls_abr.md` (single-source HLS), `assets/best-practices.md` (§1 — stitching is the exception to "encoder_version: 2 always").

## Gotchas

- **Don't set both `source` and `stitch`** — they're mutually exclusive top-level fields.
- **Hard requirement: `encoder_version: 1`** for stitch jobs as of the current docs. Trying to use v2 will fail or silently produce wrong output.
- **Audio glitches at clip boundaries** are common when inputs have different sample rates; pre-normalize or accept brief glitches.
- **Total duration** is the sum of all input durations (minus any clipped portions). Long stitch jobs run long and bill accordingly.
- **Source URLs all need to be reachable** by Qencode. A single 404 fails the whole stitch.
