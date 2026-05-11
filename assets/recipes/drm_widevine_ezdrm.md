---
recipe: drm_widevine_ezdrm
title: Widevine DRM via EZDRM (cenc_drm)
when_to_use: User wants Widevine-protected output for Android, Chromecast, ChromeOS, and Chrome/Firefox/Edge browsers, with EZDRM as the key management service. Output is HLS or DASH with Common Encryption.
output_count: 1 advanced_hls or advanced_dash format block
needs_destination: required
based_on: content/tutorials/transcoding/drm/ezdrm-widevine.md
---

# Recipe — Widevine via EZDRM

Widevine is Google's DRM, used by Android, Chromecast, ChromeOS, and Chrome/Firefox/Edge browsers. This recipe uses **EZDRM** as the key management service. For a different KMS, see `drm_buydrm.md` or `drm_expressplay.md`.

The Qencode-side config uses `cenc_drm` (Common Encryption) — the same field is shared by Widevine and PlayReady. This recipe covers Widevine; for PlayReady at the same time, see `drm_playready_ezdrm.md` and combine both `cenc_drm` blocks if you want dual protection.

## Step 1 — Get keys from EZDRM CPIX API

Build a request URL with your EZDRM credentials:

```
https://cpix.ezdrm.com/KeyGenerator/cpix.aspx?k=<KEY_ID_GUID>&u=<username>&p=<password>&c=<resource_name>&m=1
```

| Param | Value |
|---|---|
| `k=` | A client-generated GUID for this content (e.g. `297f600f-1234-1234-b060-2ac13cc42585`) |
| `u=`, `p=` | Your EZDRM account credentials |
| `c=` | Content/resource ID (a stream name or asset name) |
| `m=` | `1` for Widevine + PlayReady, `2` for Fairplay |

EZDRM returns a CPIX XML response. Extract three values:

| Qencode field | Source in CPIX XML |
|---|---|
| `key_id` | The `k=` value, **with dashes removed** (must be hex, no separators) |
| `key` | The `pskc:PlainValue` content, decoded from base64 to hex |
| `pssh` | The `cpix:PSSH` content from the `cpix:DRMSystem` with `systemId="edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"` (Widevine's system ID) |

Python conversion for `key`:

```python
import base64
hex_key = base64.b64decode("jgE7ws6lbo4GBatA0vEoKQ==").hex()
# → '8e013bc2cea56e8e0605ab40d2f12829'
```

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
          "pssh": "AAAAdnBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAAFYIARIQKX9gD08XTA+wYCrBPMQlhRoIbW92aWRvbmUiMnsia2lkIjoiS1g5Z0QwOFhUQSt3WUNyQlBNUWxoUT09IiwidHJhY2tzIjpbIlNEIl19KgJTRA=="
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

Swap `advanced_dash` → `advanced_hls` if you want HLS instead. The `cenc_drm` config is identical for both.

## Step 3 — Player config

Your player needs to know:
- The manifest URL (master playlist from your destination).
- The Widevine license URL — EZDRM's default is `https://widevine.ezdrm.com/widevine/getlicense.aspx`.

Most DRM-capable players (Shaka Player, dashjs, hls.js with WV-via-EME, Qencode Player) accept these as init params.

## Customization notes

- **Widevine + PlayReady in one job**: pull both PSSH blocks from the CPIX XML response (separate `cpix:DRMSystem` tags with different `systemId` values). The Qencode API supports a single `cenc_drm` block — for dual protection you may need multiple format outputs or contact Qencode support. See also `drm_playready_ezdrm.md`.
- **Key per content**: generate a new `k=` GUID for each asset. Reusing a key across assets weakens security.
- **`key_id` format**: must be **hex with no dashes** in the Qencode API call, even though EZDRM returns it dashed. Remove dashes before submitting.
- **Stream-level encoding params** (`video_codec`, `framerate`, etc.) per `best-practices.md` §7 — apply normally; DRM doesn't change ABR composition rules.

## Schema pointers

- `start_encode2.query.format[].cenc_drm.key_id` — hex, no dashes
- `start_encode2.query.format[].cenc_drm.key` — hex
- `start_encode2.query.format[].cenc_drm.pssh` — base64-encoded Widevine PSSH from CPIX
- `start_encode2.query.format[].cenc_drm.la_url` — optional License Acquisition URL (PlayReady-specific; not used for Widevine-only)

See also: `assets/recipes/hls_abr.md` (base ABR), `assets/recipes/drm_playready_ezdrm.md`, `assets/recipes/drm_fairplay_ezdrm.md`, `assets/best-practices.md`, `assets/error-codes.md` (DRM key fetch failures).

## Gotchas

- **Hex, no dashes** on `key_id`. EZDRM returns dashes; strip them.
- **Right PSSH for the right DRM**: Widevine's systemId is `edef8ba9-79d6-4ace-a3c8-27dcd51d21ed`; PlayReady's is `9a04f079-9840-4286-ab92-e65be0885f95`. Pulling the wrong PSSH produces a stream that can't be decrypted by your target player.
- **`pssh` is base64 in the API request**, even though `key` and `key_id` are hex. They use different encodings.
- **Test with a real Widevine-capable browser** (Chrome). Firefox supports Widevine via EME but with stricter policies; iOS Safari does NOT support Widevine (use Fairplay instead — see `drm_fairplay_ezdrm.md`).
