---
recipe: per_title_encoding
title: Per-Title Encoding (CRF bands tuned per source)
when_to_use: User wants optimal quality-per-byte. Per-title analyzes the source and picks the best CRF per scene within bounds you set. Strongly recommended for H.264/H.265 outputs. Replaces `two_pass: 1` in all cases.
output_count: 1+ format blocks; per-title is a per-format toggle
needs_destination: optional (defaults to 24-hour temp storage)
based_on: content/tutorials/transcoding/per-title-encoding.md
---

# Recipe — Per-Title Encoding

Per-Title Encoding analyzes the source video and chooses the best CRF per scene within your specified bounds. Produces **better quality at smaller file size** than fixed-CRF or two-pass encoding, with one-pass wall-clock time.

**This is the default approach used in every other recipe in this set** — `mp4_ladder`, `hls_abr`, etc., already enable it. This recipe documents the knobs in detail for cases where you want to tune them.

**Codec support:** H.264 (`libx264`) and H.265 (`libx265`) only. AV1 / VP9 / LCEVC don't support per-title in v1 of the API.

**Pricing note:** enabling `optimize_bitrate: 1` multiplies the per-output price by **1.5×** (the analysis pass costs extra). Worth it for production deliverables.

## Minimum config

Just turn it on:

```json
{
  "output": "mp4",
  "optimize_bitrate": 1,
  "video_codec": "libx264"
}
```

Qencode picks a CRF for each scene from the full range `[0, 51]`. You'll usually want to constrain that range.

## Production config — bounded CRF range

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
        "optimize_bitrate": 1,
        "min_crf": 18,
        "max_crf": 28,
        "adjust_crf": 0,
        "audio_bitrate": 128,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/output.mp4"
        }
      }
    ]
  }
}
```

| Parameter | Range | Purpose |
|---|---|---|
| `optimize_bitrate` | 0 / 1 | Enable per-title. Default 0. |
| `min_crf` | 0–51 | Lowest (highest quality) CRF the picker may select. Defaults to 0. |
| `max_crf` | 0–51 | Highest (lowest quality) CRF the picker may select. Defaults to 51. |
| `adjust_crf` | -10 to +10 | Shift the picked CRF in either direction. Negative = better quality, positive = smaller file. Default 0. |

CRF is inverse: lower = better quality + larger file. A "subjectively sane" range is **18–28** for H.264 (per the docs). `18` is visually lossless or near-it; `23` is the default in many tools; `28` is noticeable but acceptable for low-bitrate streaming.

## Per-source tuning recommendations

| Source type | `min_crf` | `max_crf` | Notes |
|---|---|---|---|
| Premium content (films, premium UGC) | 18 | 24 | Stay sharp; bandwidth is secondary. |
| Standard web video | 20 | 28 | Balanced. |
| Bandwidth-constrained delivery | 24 | 32 | Acceptable on small screens; saves bytes. |
| Low-resolution rungs (≤480p) in an ABR ladder | 21 | 30 | Lower rungs tolerate more compression because they're scaled down anyway. |

For ABR ladders (`advanced_hls`, `advanced_dash`), put `optimize_bitrate` (and the optional `min_crf`/`max_crf`/`adjust_crf` bounds) **on each `stream[]` entry**, not at the format level — per `best-practices.md` §7. The picker chooses an appropriate CRF per scene per rendition.

```json
"stream": [
  {
    "video_codec": "libx264",
    "audio_codec": "libfdk_aac",
    "resolution": 1080,
    "framerate": "30",
    "keyframe": "60",
    "quality": 22,
    "optimize_bitrate": 1,
    "min_crf": 18,
    "max_crf": 28,
    "audio_bitrate": 128
  },
  /* … other rungs … */
]
```

## When NOT to use per-title

- **Fixed bitrate contracts** — broadcasters, CDN slot sales, or any case where the output must hit a specific bitrate. Use `bitrate: <kbps>` (CBR) instead, without `optimize_bitrate`.
- **AV1 or VP9 outputs** — not supported. Use the codec's own quality controls.
- **Speed-critical workflows** where the 1.5× cost or the extra analysis pass is unacceptable. Drop to fixed CRF (`quality: 22`) without `optimize_bitrate`.

## When to bias quality vs file size

If your average output is too soft or too sharp, use `adjust_crf`:

```json
"optimize_bitrate": 1,
"min_crf": 18,
"max_crf": 28,
"adjust_crf": -2   // shift CRF 2 points lower → noticeably sharper, larger files
```

`adjust_crf` is clamped within `[min_crf, max_crf]`. If the picker chose 26 and you set `adjust_crf: -2`, the effective CRF is `max(min_crf, 26-2) = 24`.

## Schema pointers

- `start_encode2.query.format[].optimize_bitrate` — enable per-title (0/1). For ABR outputs, put this on each `stream[]` entry instead.
- `start_encode2.query.format[].min_crf` — lowest CRF the picker may select (optional)
- `start_encode2.query.format[].max_crf` — highest CRF the picker may select (optional)
- `start_encode2.query.format[].adjust_crf` — shift in either direction, -10…+10 (optional)

See also: `assets/best-practices.md` (§5 explicitly forbids `two_pass: 1` — use per-title instead), `assets/recipes/mp4_ladder.md` and `assets/recipes/hls_abr.md` (both have per-title pre-wired).

## Gotchas

- **Don't combine with `two_pass: 1`** — per-title supersedes two-pass and produces better results.
- **Don't combine with `bitrate`** — `optimize_bitrate` is CRF-based; setting an explicit `bitrate` constrains it in a confusing way. Pick one.
- The 1.5× pricing is per-output, not per-job. A 4-rung ladder with per-title costs 4 × 1.5× = 6× one fixed-rate rung.
- For AV1 outputs that need ABR-style adaptive quality, use `quality` with `min_crf`/`max_crf` *without* `optimize_bitrate` — the codec's internal logic handles complexity adaptation.
