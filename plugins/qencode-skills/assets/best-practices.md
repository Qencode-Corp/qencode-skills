# Qencode Transcoding API — Composition Best Practices

Authoritative defaults for building a `query` JSON. These override the schema's apparent defaults — the schema documents what's *allowed*, this document captures what's *operationally correct*.

When composing a query (manually, via the `qencode-build-query` skill, or in any recipe), apply these unless the user explicitly opts out.

## 1. `encoder_version: 2` at the top of `query`

Always set `"encoder_version": 2`. V1 covers only a small legacy subset of features (notably VMAF) and has caused audio-out-of-sync output in production. Don't pin V1 unless the user explicitly needs a V1-only feature.

## 2. Sizing — prefer `resolution` over `height`

To preserve source aspect ratio, use `resolution` (smaller side of the frame). It works for both landscape and portrait sources:

- `resolution: 1080` → 1920×1080 landscape, 1080×1920 portrait
- `resolution: 360` → 640×360 landscape, 360×640 portrait

Use `width`, `height`, or `size` only when the user explicitly wants an exact dimension or to force a particular aspect ratio (with `resize_mode: "crop"`).

## 3. Audio codec — `libfdk_aac`, not `aac`

Use `"audio_codec": "libfdk_aac"` by default. Only fall back to `"aac"` if the user explicitly forbids libfdk_aac (e.g. licensing constraints).

## 4. Quality vs bitrate — but per-title supersedes both

When per-title is OFF, default to CRF: `"quality": 22` per format/stream. CRF produces better quality per byte than constant-bitrate. Use `"bitrate"` only when the user has a specific target bitrate (CDN contract, broadcast spec, fixed bandwidth budget).

**When `optimize_bitrate: 1` is enabled (next rule), `quality` and `bitrate` are both ignored** — per-title picks the CRF itself. Don't include either alongside `optimize_bitrate: 1`.

## 5. Per-title encoding instead of two-pass

**Never** use `"two_pass": 1`. Use Per-Title Encoding:

```json
"optimize_bitrate": 1
```

That's the whole thing — **don't pair with `quality` or `bitrate`** (per-title overrides them). Better quality than two-pass with one-pass wall-clock time. Per-title picks the optimal CRF per scene/source automatically.

`min_crf` / `max_crf` / `adjust_crf` are optional bounds on the auto-picked CRF — leave them off by default and let per-title pick the full range. Add them only when you need a hard quality floor or ceiling for a specific deliverable (see `assets/recipes/per_title_encoding.md` for tuning details).

## 6. Storage — see `assets/storage.md`

Output destinations have their own canonical reference: `assets/storage.md`. Read it whenever the user mentions where outputs should land, a specific cloud provider, public/private access, ACLs, cache headers, or copying to multiple buckets.

Headline rules to remember at composition time:

- **Omitted `destination` → 24-hour temp storage.** Outputs are deleted ~24h after the job completes. Always warn the user when emitting a recipe without `destination`.
- **Qencode S3 (`*.s3.qencode.com`):** omit `key`, `secret`, `permissions`, and `storage_class`.
- **Cloudflare R2:** include `key`+`secret`; omit `permissions` and `storage_class`.
- **AWS S3:** include `key`+`secret`; `permissions` and `storage_class` are supported.
- **Other backends** (B2 native, Azure Blob, FTP/SFTP, generic S3-compatible): see the per-provider examples and compatibility matrix in `storage.md`.

`destination` also accepts an array for fan-out to multiple destinations — see `storage.md` for the syntax.

## 7. HLS / DASH — per-rendition params go on `stream[]`

For `output: "advanced_hls"` or `"advanced_dash"`, the entire per-rendition encoding spec lives on each `stream[]` entry. The format level only carries packaging settings, the destination, and per-title bounds. The schema's per-attribute descriptions are explicit — most format-level params end with "For HLS or DASH output specify this parameter on stream object level."

**On each `stream[]` entry:**
- `video_codec`, `audio_codec`
- `framerate`, `keyframe`
- `optimize_bitrate` for per-title encoding (and `min_crf` / `max_crf` / `adjust_crf` if you bound it) — **OR** `quality` (CRF) **OR** `bitrate` (CBR); these three are mutually exclusive — pick one quality control per stream
- `audio_bitrate`
- `resolution` (or `size` / `width` / `height`)
- `rotate`, `aspect_ratio`, `two_pass` (rare)

**Stays at the format level:**
- `output`, `destination`
- `segment_duration`, `fmp4`, `separate_audio`, `playlist_name` (packaging)

```json
"output": "advanced_hls",
"segment_duration": 6,
"destination": { /* ... */ },
"stream": [
  {
    "video_codec": "libx264",
    "audio_codec": "libfdk_aac",
    "resolution": 1080,
    "framerate": "30",
    "keyframe": "60",
    "optimize_bitrate": 1,
    "audio_bitrate": 128
  },
  {
    "video_codec": "libx264",
    "audio_codec": "libfdk_aac",
    "resolution": 720,
    "framerate": "30",
    "keyframe": "60",
    "optimize_bitrate": 1,
    "audio_bitrate": 128
  }
]
```

Without explicit `framerate` and `keyframe` per stream, segments may not be cut on keyframe boundaries — players will fail to switch ABR ladders cleanly or will stutter.

> **Schema digest note:** the `stream` object's `attributes` array in `transcoding.json` only enumerates `chunklist_name`. The authoritative source for what goes on the stream object is the format-level attribute *descriptions* — most end with "For HLS or DASH output specify this parameter on stream object level."

The keyframe interval should divide `segment_duration × framerate` cleanly:

| framerate | segment_duration | keyframe | GOPs per segment |
|---|---|---|---|
| 30 | 6 | 60 | 3 |
| 30 | 4 | 60 | 2 |
| 24 | 6 | 48 | 3 |
| 25 | 6 | 50 | 3 |
| 60 | 6 | 60 | 6 |

For source content with non-standard frame rates (film at 24, PAL at 25), match the source rather than forcing 30.

## Quick recap (the skeleton every recipe starts from)

```json
{
  "query": {
    "source": "<URL>",
    "encoder_version": 2,
    "format": [
      {
        "output": "...",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 720,
        "optimize_bitrate": 1,
        "audio_bitrate": 128,
        "destination": { /* see §6/§7 */ }
      }
    ]
  }
}
```

For HLS/DASH, the format block omits all per-rendition params and instead carries a `stream[]` array; each entry holds `video_codec`, `audio_codec`, `resolution`, `framerate`, `keyframe`, `optimize_bitrate`, `audio_bitrate` per rung. See §7.
