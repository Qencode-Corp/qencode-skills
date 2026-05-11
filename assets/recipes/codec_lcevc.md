---
recipe: codec_lcevc
title: LCEVC encoding (enhancement layer on H.264 / HEVC)
when_to_use: User wants LCEVC — V-Nova's MPEG-5 Part 2 enhancement layer that adds bitrate savings on top of a base codec (H.264 or HEVC). Bandwidth-conscious streaming where players support LCEVC decoding.
output_count: 1+ format blocks with video_codec = lcevc_h264 or lcevc_hevc
needs_destination: optional (defaults to 24-hour temp storage)
based_on: content/tutorials/transcoding/lcevc.md
---

# Recipe — LCEVC encoding

LCEVC (MPEG-5 Part 2 Low Complexity Enhancement Video Encoding) is V-Nova's multi-layer codec: a base H.264 or HEVC stream is augmented by a low-bitrate enhancement stream. Players with LCEVC support combine the two for higher visual quality at lower total bitrate; players without LCEVC support fall back to playing just the base stream.

Use when you want the bandwidth/quality win of LCEVC and your target audience is on supported players (web players with V-Nova's JS SDK, certain native apps and STBs — see [V-Nova integrations](https://docs.v-nova.com/v-nova/lcevc/integrations)).

**Codec options:**
- `lcevc_h264` — LCEVC on top of H.264 base (broader compatibility)
- `lcevc_hevc` — LCEVC on top of HEVC base (better base efficiency, narrower playback)

## query JSON

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "stitch": 2,
    "format": [
      {
        "output": "mp4",
        "video_codec": "lcevc_h264",
        "audio_codec": "libfdk_aac",
        "resolution": 1080,
        "quality": 22,
        "audio_bitrate": 128,
        "video_codec_parameters": {
          "lcevc_tune": "vmaf"
        },
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/lcevc.mp4"
        }
      }
    ]
  }
}
```

> ⚠️ **Quirk**: the tutorial states LCEVC jobs require `stitch: 2` at the top level (an integer, not the usual array-of-sources). Treat it as an opaque LCEVC mode flag rather than the stitching feature. Include it as shown.

## LCEVC tuning parameters

All under `video_codec_parameters`:

| Param | Purpose |
|---|---|
| `lcevc_tune` | Optimization target. Common values: `"vmaf"` (perceptual quality), `"psnr"`, `"ssim"`. |
| `scaling_mode_level0` | LCEVC base-layer scaling mode. |
| `dc_dithering_type` | Dithering type for low-bitrate scenarios. |
| `dc_dithering_strength` | Strength of dithering. |
| `dc_dithering_qp_start` | QP threshold where dithering begins. |
| `dc_dithering_qp_saturate` | QP threshold where dithering saturates. |
| `m_ad_mode` | Adaptive deblocking mode. |
| `m_hf_strength` | High-frequency enhancement strength. |
| `m_lf_strength` | Low-frequency enhancement strength. |

The defaults are tuned for typical web streaming. Override only when you've A/B-tested for your specific content and player.

## When to choose LCEVC vs AV1 vs plain H.264/HEVC

| Goal | Best choice |
|---|---|
| Widest playback compatibility, simple stack | `libx264` (H.264) |
| Better quality per byte, modern players | `libsvtav1` (AV1) — see `codec_av1.md` |
| Better quality per byte, transparent fallback to base codec for non-supporting players | `lcevc_h264` or `lcevc_hevc` |
| 4K HDR with the best base codec | `libx265` (HEVC) |

LCEVC's strength: existing video pipelines that already deliver H.264 or HEVC can be augmented without breaking compatibility. Non-LCEVC players play the base stream; LCEVC players get the enhanced quality automatically.

## ABR ladder with LCEVC

LCEVC works in HLS/DASH ladders too. Apply the codec at the `stream[]` level per `best-practices.md` §7:

```json
{
  "output": "advanced_hls",
  "segment_duration": 6,
  "stitch": 2,
  "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/lcevc_hls/" },
  "stream": [
    {
      "video_codec": "lcevc_h264",
      "audio_codec": "libfdk_aac",
      "resolution": 1080,
      "framerate": "30",
      "keyframe": "60",
      "quality": 22,
      "audio_bitrate": 128,
      "video_codec_parameters": { "lcevc_tune": "vmaf" }
    },
    {
      "video_codec": "lcevc_h264",
      "audio_codec": "libfdk_aac",
      "resolution": 720,
      "framerate": "30",
      "keyframe": "60",
      "quality": 22,
      "audio_bitrate": 128,
      "video_codec_parameters": { "lcevc_tune": "vmaf" }
    }
  ]
}
```

## Customization notes

- **`encoder_version: 2` is required** — LCEVC codecs are v2-only.
- **Player support is the gating constraint**: confirm your audience has LCEVC-capable players (V-Nova player SDK, dashJS plugin, etc.) before committing to an LCEVC-primary ladder. Otherwise just use plain H.264/HEVC.
- **Per-title encoding (`optimize_bitrate`) compatibility** with LCEVC isn't documented as supported in the tutorial — omit it unless you've confirmed it works for your codec/version combination.
- **No destination**: outputs land in 24-hour temp storage. Warn the user.

## Schema pointers

- `start_encode2.query.stitch` — set to `2` for LCEVC jobs (LCEVC mode flag, not the stitching feature)
- `start_encode2.query.encoder_version` — must be `2`
- `start_encode2.query.format[].video_codec` — `lcevc_h264` or `lcevc_hevc`
- `start_encode2.query.format[].video_codec_parameters.lcevc_tune` — `vmaf`, `psnr`, `ssim`, etc.

See also: `assets/best-practices.md` (§1 — encoder v2; §7 — ABR stream-level params), `assets/recipes/codec_av1.md` (alternative codec for bandwidth savings), V-Nova's docs at https://docs.v-nova.com/v-nova/lcevc.

## Gotchas

- **The `stitch: 2` requirement is unusual** and doesn't follow the usual `stitch`-is-an-array pattern. Don't confuse this with the actual stitching feature (`assets/recipes/stitching.md`). They share the field name but mean different things.
- **Non-LCEVC players will still play the base stream** — this is the headline feature. Verify with a test player before shipping.
- **LCEVC enhancement adds a small bitrate overhead** but the base stream can be encoded more aggressively because LCEVC compensates. Total bitrate at equivalent perceived quality drops 15–30% in typical content.
