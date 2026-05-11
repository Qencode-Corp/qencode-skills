---
recipe: drm_fairplay_ezdrm
title: FairPlay DRM via EZDRM (fps_drm)
when_to_use: User wants Fairplay-protected HLS output for iOS, macOS Safari, and Apple TV. Fairplay is Apple's DRM and is **HLS-only** (no DASH support).
output_count: 1 advanced_hls format block
needs_destination: required
based_on: content/tutorials/transcoding/drm/ezdrm-fairplay.md
---

# Recipe — FairPlay via EZDRM

FairPlay Streaming (FPS) is Apple's DRM, used by iOS, macOS Safari, and Apple TV. It's **HLS-only** — no DASH support. The Qencode-side config uses `fps_drm` (distinct from `cenc_drm` used by Widevine/PlayReady).

## Step 1 — Get keys from EZDRM CPIX API

Use the Fairplay variant (`m=2`):

```
https://cpix.ezdrm.com/KeyGenerator/cpix.aspx?k=<KEY_ID_GUID>&u=<username>&p=<password>&c=<resource_name>&m=2
```

From the CPIX XML response, extract:

| Qencode field | Source in CPIX XML |
|---|---|
| `key` | The `pskc:PlainValue` content, decoded from base64 to hex |
| `iv` | The `explicitIV` attribute of `cpix:ContentKey`, decoded from base64 to hex |
| `key_url` | Construct as `skd://fps.ezdrm.com/;<kid>` where `<kid>` is the original GUID (with dashes — Fairplay's `key_url` keeps them) |

Python conversion helper:

```python
import base64
hex_key = base64.b64decode("aqXCOgIfS78MTFx02XUQhg==").hex()
hex_iv  = base64.b64decode("KX9gDxI0EjSwYCrBPMQlhQ==").hex()
```

## Step 2 — Build the query JSON

`fps_drm` is a direct child of the format object.

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "advanced_hls",
        "segment_duration": 6,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/hls/"
        },
        "fps_drm": {
          "key": "6aa5c23a021f4bbf0c4c5c74d9751086",
          "iv": "297f600f12341234b0602ac13cc42585",
          "key_url": "skd://fps.ezdrm.com/;297f600f-1234-1234-b060-2ac13cc42585"
        },
        "stream": [
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 1080, "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720,  "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 480,  "framerate": "30", "keyframe": "60", "quality": 23, "audio_bitrate": 96  }
        ]
      }
    ]
  }
}
```

## Step 3 — Player config

iOS/macOS native players (AVPlayer in Safari, app-embedded AVKit) handle the rest:

1. Player loads the master `.m3u8`.
2. `EXT-X-KEY` lines reference `skd://fps.ezdrm.com/;<kid>` (your `key_url`).
3. Player sends an SPC (Server Playback Context) request to EZDRM's license server.
4. EZDRM returns a CKC (Content Key Context) response.
5. Player decrypts segments using the CKC.

For web playback in Safari, use the HLS source URL with Safari's native EME — no extra player setup needed beyond Apple's standard FPS flow.

## Combining with Widevine/PlayReady for cross-platform

A typical cross-platform delivery encodes the **same source twice**:
- One pass with `cenc_drm` (Widevine + PlayReady) for DASH/HLS on Chrome/Firefox/Edge/Android.
- One pass with `fps_drm` (Fairplay) for HLS on iOS/macOS Safari.

You can submit both as separate `format[]` entries in the same job, each writing to a different destination prefix.

```json
"format": [
  { "output": "advanced_dash", "cenc_drm": {/* Widevine */}, "destination": {/* dash/ */}, "stream": [/* … */] },
  { "output": "advanced_hls",  "fps_drm":  {/* Fairplay */}, "destination": {/* hls/  */}, "stream": [/* … */] }
]
```

Your player serves the right stream URL based on `Accept`/`User-Agent` detection.

## Customization notes

- **`iv` is 32 hex chars** (16 bytes). Some FPS docs use the term "explicit IV" — same thing.
- **`key_url` keeps dashes** in the kid (unlike `cenc_drm.key_id` which strips them). Subtle inconsistency between the DRM systems.
- **No DASH support**: FairPlay is HLS-only. Use `cenc_drm` for DASH.
- **EZDRM's `skd://fps.ezdrm.com/` is the standard prefix**. Custom key servers would use their own SKD URL prefix.

## Schema pointers

- `start_encode2.query.format[].fps_drm.key` — hex
- `start_encode2.query.format[].fps_drm.iv` — hex
- `start_encode2.query.format[].fps_drm.key_url` — `skd://...` URL with `;<kid>` (kid keeps dashes)

See also: `assets/recipes/drm_widevine_ezdrm.md` (Widevine sibling), `assets/recipes/drm_playready_ezdrm.md` (PlayReady sibling), `assets/recipes/hls_abr.md` (base HLS), `assets/best-practices.md`, `assets/error-codes.md`.

## Gotchas

- **Fairplay is HLS-only**. Don't try to put `fps_drm` on a DASH output.
- **`key_url` format**: `skd://fps.ezdrm.com/;<kid-with-dashes>`. The semicolon separator is required.
- **Test on real Apple devices** — Apple's FPS implementation has subtle bugs in older iOS versions. Validate on iOS 14+ at minimum.
- **`fps_drm` and `cenc_drm` are not interchangeable** — `cenc_drm` uses different field names (`pssh`, `la_url`) and different encryption scheme.
- **No PlayReady or Widevine via `fps_drm`** — use `cenc_drm` for those.
