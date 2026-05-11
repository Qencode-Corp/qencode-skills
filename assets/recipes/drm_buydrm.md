---
recipe: drm_buydrm
title: Widevine + PlayReady DRM via BuyDRM (CPIX request)
when_to_use: User has a BuyDRM (KeyOS) account and wants Widevine and/or PlayReady protection. BuyDRM uses signed CPIX requests rather than raw key params, so the API surface differs from EZDRM.
output_count: 1 advanced_dash or advanced_hls format block
needs_destination: required
based_on: content/tutorials/transcoding/drm/buydrm.md
---

# Recipe — Widevine + PlayReady via BuyDRM (KeyOS)

BuyDRM's KeyOS service uses a different integration model than EZDRM: instead of passing raw key/PSSH/IV values, you generate a **signed CPIX request** with your BuyDRM x509 certificate and pass the base64-encoded request to Qencode. Qencode forwards it to BuyDRM's KeyOS service and receives the keys.

**SDK requirement (as of the tutorial):** Currently you should use the python2 Qencode SDK to generate the CPIX request. If you need BuyDRM with a different SDK or language, contact Qencode support.

## Prerequisites

1. **BuyDRM x509 End User's certificate** — two `.pem` files (private key + public cert). Get from BuyDRM support if you don't have them yet.
2. **Qencode python SDK**: `pip install qencode`

## Step 1 — Generate signed CPIX request

```python
import uuid
import base64
from qencode import create_cpix_user_request

# Paths to your BuyDRM cert files
USER_PVT_KEY_PATH = './keys/user_private_key.pem'
USER_PUB_CERT_PATH = './keys/user_public_cert.pem'

# One key per track type (SD, HD, UHD)
key_ids = [
    { 'kid': str(uuid.uuid4()), 'track_type': 'SD' },
    { 'kid': str(uuid.uuid4()), 'track_type': 'HD' }
]

media_id = 'my_first_stream'
content_id = 'my_movies_group'
common_encryption = 'cenc'

cpix_request = create_cpix_user_request(
    key_ids,
    media_id,
    content_id,
    common_encryption,
    USER_PVT_KEY_PATH,
    USER_PUB_CERT_PATH,
    use_playready=True,
    use_widevine=True,
    use_fairplay=False,
)

cpix_b64 = base64.b64encode(cpix_request).decode('ascii')
```

`cpix_b64` is the value you'll pass to Qencode in the next step.

## Step 2 — Build the query JSON

BuyDRM uses `buydrm_drm` (not `cenc_drm`) on the format object. The single `request` field holds the base64-encoded CPIX request — Qencode forwards it to BuyDRM and uses the returned keys for encryption.

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
        "buydrm_drm": {
          "request": "<base64-encoded CPIX request from step 1>"
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

Swap `advanced_dash` → `advanced_hls` for HLS instead.

## Step 3 — Submit (Python SDK shape)

```python
import qencode

API_KEY = "your-qencode-api-key"
client = qencode.client(API_KEY)
task = client.create_task()
query = QUERY.replace('{cpix_request}', cpix_b64)
task.custom_start(query)
```

A full example lives at: https://github.com/qencode-dev/qencode-api-python-client/blob/master/sample-code/drm/buydrm/buydrm_widevine_playready.py

## Step 4 — Player config

For browsers using Widevine:

- **License URL**: `https://widevine.keyos.com/api/v4/getLicense`
- **Custom Data header**: base64-encoded BuyDRM Authentication XML. Generate one at https://console.keyos.com/#authxml/generate (requires BuyDRM login).

Qencode Player example:

```javascript
const params = {
  videoSources: {
    src: "https://yourserver.com/content/playlist.mpd",
    emeHeaders: {
      'CustomData': '<base64-encoded auth XML>'
    },
    keySystems: {
      'com.widevine.alpha': "https://widevine.keyos.com/api/v4/getLicense"
    }
  }
};
qPlayer('my_player', params);
```

## Customization notes

- **Track-type keys**: BuyDRM expects separate kids per track type (SD, HD, UHD). For a typical 4-rung ABR ladder you'd usually use SD (≤720p) and HD (≥1080p) kids.
- **CPIX request signing**: only the python2 SDK ships with this helper as of the tutorial. If you need to call it from Node/Java/PHP, contact Qencode support — they can advise on porting or generating CPIX requests directly.
- **No raw key/PSSH/IV**: unlike `cenc_drm` and `fps_drm`, you don't pass keys directly. The CPIX request encapsulates everything BuyDRM needs.
- **Fairplay too**: set `use_fairplay=True` in `create_cpix_user_request` and BuyDRM returns Fairplay keys alongside Widevine/PlayReady. Submit those via a separate `format[]` entry with `output: "advanced_hls"` and the same `buydrm_drm.request`.

## Schema pointers

- `start_encode2.query.format[].buydrm_drm.request` — base64-encoded signed CPIX request
- Compare to `start_encode2.query.format[].cenc_drm` (raw-key DRM integration via EZDRM, ExpressPlay)
- Compare to `start_encode2.query.format[].fps_drm` (raw-key Fairplay)

See also: `assets/recipes/drm_widevine_ezdrm.md` (raw-key Widevine alternative), `assets/recipes/drm_playready_ezdrm.md`, `assets/recipes/drm_fairplay_ezdrm.md`, `assets/best-practices.md`, `assets/error-codes.md`.

## Gotchas

- **python2 SDK requirement** is unusual in 2026 — confirm with Qencode support whether a python3 helper has shipped. If not, run the python2 CPIX-request step in a sidecar service.
- **Private key handling**: the BuyDRM `.pem` private key must NOT be exposed to clients. Keep it server-side; never bake it into a mobile app or front-end bundle.
- **Authentication XML on the player side** is signed with a separate BuyDRM signing key. Sign server-side and pass the base64 result to the client to use as the `CustomData` header.
- **License URL for Widevine** is BuyDRM's `widevine.keyos.com`, not Google's. Don't accidentally configure the player against Google's default Widevine endpoint.
