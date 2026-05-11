---
recipe: drm_playready_ezdrm
title: PlayReady DRM via EZDRM (cenc_drm)
when_to_use: User wants PlayReady-protected output for Windows, Xbox, Edge, Samsung TVs, and other Microsoft-ecosystem devices, with EZDRM as the key management service.
output_count: 1 advanced_hls or advanced_dash format block
needs_destination: required
based_on: content/tutorials/transcoding/drm/ezdrm-playready.md
---

# Recipe — PlayReady via EZDRM

PlayReady is Microsoft's DRM, used by Windows, Xbox, Edge, Samsung TVs, and many smart-TV / STB platforms. Like Widevine, PlayReady uses Common Encryption — Qencode's `cenc_drm` field configures both, distinguished by which `pssh` (and the optional `la_url`) you pass.

For Widevine, see `drm_widevine_ezdrm.md`. The two can coexist on the same output for dual protection — see notes below.

## Step 1 — Get keys from EZDRM CPIX API

Same URL as the Widevine recipe (`m=1` returns both Widevine and PlayReady systems):

```
https://cpix.ezdrm.com/KeyGenerator/cpix.aspx?k=<KEY_ID_GUID>&u=<username>&p=<password>&c=<resource_name>&m=1
```

From the CPIX XML response, extract:

| Qencode field | Source in CPIX XML |
|---|---|
| `key_id` | The `k=` value, **with dashes removed** |
| `key` | The `pskc:PlainValue` content, decoded from base64 to hex |
| `pssh` | The `cpix:PSSH` content from the `cpix:DRMSystem` with `systemId="9a04f079-9840-4286-ab92-e65be0885f95"` (PlayReady's system ID — **not the same** as Widevine's) |
| `la_url` | Construct as `https://playready.ezdrm.com/cency/preauth.aspx?pX=<XXXXXX>` where `XXXXXX` is the last 6 digits of your PlayReady Profile ID in EZDRM |

## Step 2 — Build the query JSON

`cenc_drm` is a direct child of the format object (not on a stream entry).

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "advanced_dash",
        "segment_duration": 6,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/dash/"
        },
        "cenc_drm": {
          "key_id": "297f600f12341234b0602ac13cc42585",
          "key": "8e013bc2cea56e8e0605ab40d2f12829",
          "pssh": "AAADBnBzc2gAAAAAmgTweZhAQoarkuZb4IhflQAAAub...",
          "la_url": "https://playready.ezdrm.com/cency/preauth.aspx?pX=A1FD4D"
        },
        "stream": [
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 1080, "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720,  "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 }
        ]
      }
    ]
  }
}
```

The `la_url` is PlayReady-specific — Widevine doesn't need it (the license URL is set client-side).

## Step 3 — Player config

PlayReady-capable players need:
- The manifest URL from your destination.
- The PlayReady License URL — the same value you set in `la_url` above, or a longer-lived equivalent if EZDRM provides per-token URLs.

Edge browser and Windows native apps have built-in PlayReady support; Xbox, smart TVs, and STBs vary.

## Widevine + PlayReady in one output

If you want both DRMs protecting the same content (typical for cross-browser web playback), the CPIX response from `m=1` gives you both PSSH blocks. The Qencode API has one `cenc_drm` field per format — for true dual protection you typically need to:

1. Encode the content with the Widevine PSSH **or** the PlayReady PSSH in `cenc_drm`.
2. Players choose the DRM they support based on `EXT-X-SESSION-KEY` (HLS) or `ContentProtection` (DASH) entries.

If your players require both protections in one stream, contact Qencode support — the API may not expose a multi-system encoding path in v1.

## Customization notes

- **PSSH selection** is critical: the `systemId` of the `cpix:DRMSystem` tag determines which DRM the PSSH protects. Pulling Widevine's PSSH (`edef8ba9-...`) into a PlayReady-only player won't work.
- **`la_url` formatting**: EZDRM's preauth URL includes a `pX=` query param with the last 6 chars of your PlayReady profile ID. Don't include the full ID — only the suffix.
- **Stream-level encoding params** per `best-practices.md` §7.

## Schema pointers

- `start_encode2.query.format[].cenc_drm.pssh` — PlayReady PSSH from CPIX
- `start_encode2.query.format[].cenc_drm.la_url` — License Acquisition URL (PlayReady-specific)
- `start_encode2.query.format[].cenc_drm.key`, `.key_id` — same shape as Widevine

See also: `assets/recipes/drm_widevine_ezdrm.md`, `assets/recipes/drm_fairplay_ezdrm.md`, `assets/recipes/hls_abr.md`, `assets/error-codes.md` (DRM key fetch failures).

## Gotchas

- **Right PSSH for the right DRM**: PlayReady's systemId is `9a04f079-9840-4286-ab92-e65be0885f95`. Widevine's is `edef8ba9-79d6-4ace-a3c8-27dcd51d21ed`. Don't mix them up.
- **`key_id` in hex with no dashes**, like Widevine.
- **`la_url` is PlayReady-specific** — leaving it off works for Widevine but breaks PlayReady.
- **Testing**: use Microsoft Edge on Windows for native PlayReady playback. Chrome supports PlayReady via EME on Windows but with quirks.
