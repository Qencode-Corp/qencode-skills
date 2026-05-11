---
recipe: codec_av1
title: AV1 encoding (libsvtav1)
when_to_use: User wants AV1 output — 30–40% bitrate savings vs H.264 for the same visual quality. Best for modern web streaming, premium VOD, and long-term archival. Supported by Chrome/Firefox/Edge and modern devices.
output_count: 1+ MP4 or WebM format blocks with video_codec = libsvtav1
needs_destination: optional (defaults to 24-hour temp storage)
based_on: content/tutorials/transcoding/codecs/using-av1-codec.md
---

# Recipe — AV1 encoding (`libsvtav1`)

`libsvtav1` is the SVT-AV1 encoder — significantly better compression than H.264/H.265/VP9 with configurable speed/efficiency presets. Use when client/CDN/storage savings outweigh the slower encode and narrower playback compatibility.

**Output containers supported:** `mp4`, `webm`.

**Important pricing-vs-quality note:** AV1 doesn't support Per-Title Encoding (`optimize_bitrate`). Use CRF (`quality`) with codec-specific tuning instead. See `best-practices.md` §5 — per-title is H.264/H.265 only.

## Basic AV1 (balanced)

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "mp4",
        "video_codec": "libsvtav1",
        "audio_codec": "libfdk_aac",
        "resolution": 1080,
        "quality": 32,
        "audio_bitrate": 128,
        "video_codec_parameters": {
          "preset": 5
        },
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/output.mp4"
        }
      }
    ]
  }
}
```

| Field | What it does |
|---|---|
| `video_codec: "libsvtav1"` | Use AV1. |
| `quality` (CRF) | Lower = better quality + larger file. AV1 typical range: **20–40**. `32` is a balanced default; `28` is high quality; `36+` is bandwidth-conscious. |
| `video_codec_parameters.preset` | 0–13. Lower = slower + smaller files; higher = faster + larger files. `5` is balanced. |

## Preset cheat sheet

| Preset | Use case | Encode speed | File size |
|---|---|---|---|
| 0–3 | Archival, mastering, premium VOD | Slowest | Smallest |
| 4–6 | Balanced — most workflows | Medium | Medium |
| 7–9 | Fast turnaround, near-live VOD | Faster | Larger |
| 10–13 | Live or near-live | Fastest | Largest |

Default is `5`.

## High-quality VOD / archival

Prioritize efficiency and visual fidelity over speed. Suitable for 4K HDR, cinematic masters.

```json
{
  "output": "mp4",
  "video_codec": "libsvtav1",
  "audio_codec": "libfdk_aac",
  "resolution": 2160,
  "quality": 28,
  "audio_bitrate": 192,
  "video_codec_parameters": {
    "preset": 3,
    "tune": 1,
    "aq_mode": 3,
    "film_grain": 0,
    "fast_decode": 0,
    "enable_dlf": 1,
    "enable_restoration": 1,
    "hierarchical_levels": 3,
    "pred_struct": 2
  },
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/premium.mp4"
  }
}
```

## Web delivery (balanced)

General-purpose streaming, browser playback.

```json
{
  "output": "mp4",
  "video_codec": "libsvtav1",
  "audio_codec": "libfdk_aac",
  "resolution": 1080,
  "quality": 32,
  "audio_bitrate": 128,
  "video_codec_parameters": {
    "preset": 5,
    "tune": 1,
    "aq_mode": 1,
    "fast_decode": 0,
    "enable_dlf": 1,
    "enable_restoration": 1,
    "hierarchical_levels": 2,
    "pred_struct": 2
  },
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/web.mp4"
  }
}
```

## Fast turnaround (UGC, near-live)

Speed first, compression second. Targets weaker decoders too.

```json
{
  "output": "webm",
  "video_codec": "libsvtav1",
  "audio_codec": "libopus",
  "resolution": 720,
  "quality": 35,
  "audio_bitrate": 96,
  "video_codec_parameters": {
    "preset": 8,
    "tune": 2,
    "aq_mode": 0,
    "fast_decode": 1,
    "enable_dlf": 0,
    "enable_restoration": 0,
    "hierarchical_levels": 1,
    "pred_struct": 0
  },
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/quick.webm"
  }
}
```

> WebM + AV1 + Opus is the modern royalty-free combo. Don't use `libfdk_aac` with `webm` containers — pair WebM with Opus.

## All AV1 codec parameters

Under `video_codec_parameters`:

| Param | Purpose |
|---|---|
| `preset` | 0–13 speed vs compression. Default 5. |
| `tune` | Perceptual quality vs PSNR optimization. |
| `aq_mode` | Adaptive quantization — improves texture quality at low bitrates. |
| `film_grain` | Synthesize grain back into the output (cinematic content). |
| `fast_decode` | Lower decoding complexity for weaker devices. |
| `enable_dlf` | Deblocking loop filter — reduces blocking artifacts. |
| `enable_restoration` | Restoration filter — reduces ringing/noise artifacts. |
| `hierarchical_levels` | Prediction hierarchy depth. |
| `pred_struct` | Prediction structure — affects latency vs quality. |

## Customization notes

- **No per-title encoding**: AV1 doesn't work with `optimize_bitrate: 1`. Use `quality` (CRF) alone.
- **CRF starting point**: AV1's CRF scale shifts higher than H.264. Use 28 for premium, 32 for web, 35 for bandwidth-conscious. Don't reflexively apply H.264 numbers (which would be very wasteful at AV1 quality).
- **Audio**: `libfdk_aac` works for MP4. For WebM containers, prefer `libopus` (`audio_codec: "libopus"`).
- **Playback compatibility**: AV1 works on Chrome 70+, Firefox 67+, Edge 79+, Android 10+, iOS/Safari 17+. Older devices need an H.264 fallback — consider ABR ladders with mixed codec rungs (AV1 primary, H.264 backup).
- **No destination**: outputs land in 24-hour temp storage. Warn the user.

## Schema pointers

- `start_encode2.query.format[].video_codec` — `libsvtav1`
- `start_encode2.query.format[].video_codec_parameters` — object with `preset`, `tune`, `aq_mode`, `film_grain`, `fast_decode`, `enable_dlf`, `enable_restoration`, `hierarchical_levels`, `pred_struct`
- `start_encode2.query.format[].quality` — CRF, 20–40 typical for AV1

See also: `assets/best-practices.md` (§4 — `quality` over `bitrate`; §5 — AV1 doesn't support per-title), `assets/storage.md`.

## Gotchas

- **`encoder_version: 2` is required** for `libsvtav1`. Setting v1 will reject the codec.
- **AV1 encoding is slow** — even preset 8 is ~2–4× slower than H.264. Budget time and capacity accordingly.
- **Pair container + codec carefully**: AV1 in MP4 is well-supported but newer than AV1 in WebM. Validate against your target players.
- **Don't combine `optimize_bitrate: 1` with AV1** — it's a no-op at best, error at worst.
