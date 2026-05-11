---
recipe: drm_expressplay
title: Widevine + PlayReady + Fairplay DRM via ExpressPlay
when_to_use: User has an ExpressPlay API key and wants any combination of Widevine, PlayReady, or Fairplay protection. ExpressPlay's key management API is simpler than BuyDRM's CPIX flow — fetch a kid and key, plug into Qencode's standard `cenc_drm`/`fps_drm` shape.
output_count: 1+ advanced_hls / advanced_dash format blocks
needs_destination: required
based_on: content/tutorials/transcoding/drm/expressplay.md
---

# Recipe — Widevine + PlayReady + Fairplay via ExpressPlay

ExpressPlay is a multi-DRM key management and license service that supports Widevine, PlayReady, and Fairplay from one account. Integration with Qencode uses the same `cenc_drm` / `fps_drm` shapes as EZDRM — only the key-management step differs.

## Prerequisites

- **ExpressPlay API key** — see [ExpressPlay docs](https://www.expressplay.com/developer/restapi/) for setup.
- Format: `<customer_id>,<key>` (a comma-separated pair).

## Step 1 — Generate kid + content encryption key

Use ExpressPlay's REST API to provision a new key:

```bash
export API_KEY="123456789,23bc012e34de56e7a8bd6b05e7f0aaa1"
curl -X POST "https://api.service.expressplay.com/keystore/keys?customerAuthenticator=$API_KEY&kek=11111111111111111111111111111111"
```

The `kek` (Key Encryption Key) is a 32-character hex string used by ExpressPlay to encrypt the stored key. You can use any 16-byte value formatted as 32 hex chars — but remember it; you'll need the same `kek` later when generating playback tokens.

Response:
```json
{
  "kid": "6B6801FE59DA030104702C69F1A7D46A",
  "kekId": "#1.952241B0259652B68A8CAE2BE819DFA3390CDB35",
  "ek": "61A9D3B082AAB5A918EBB86461DA475BD80CA4A83CEA16B6",
  "k": "F1234560F6A7DE822574BF2F8190F6CD",
  "lastUpdate": "2021-09-22T22:42:48Z"
}
```

You'll use:
- `kid` → Qencode's `key_id`
- `k`   → Qencode's `key`

## Step 2 — Build the query JSON (Widevine + PlayReady)

Use `cenc_drm` with ExpressPlay's standard PSSH and license URL:

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
          "key": "F1234560F6A7DE822574BF2F8190F6CD",
          "key_id": "6B6801FE59DA030104702C69F1A7D46A",
          "pssh": "CAESEAABAgMEBQYHCAkKCwwNDg8aCmludGVydHJ1c3QiASo=",
          "la_url": "https://pr.service.expressplay.com/playready/RightsManager.asmx"
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

The `pssh` and `la_url` values shown above are **standard ExpressPlay values** — use them as-is. Only `key` and `key_id` change per content asset.

## Step 3 — Build the Fairplay variant

Fairplay needs a separate `format[]` entry (HLS-only) with `fps_drm`:

```json
{
  "output": "advanced_hls",
  "segment_duration": 6,
  "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/hls/" },
  "fps_drm": {
    "key": "F1234560F6A7DE822574BF2F8190F6CD",
    "iv": "00000000000000000000000000000000",
    "key_url": "skd://6B6801FE59DA030104702C69F1A7D46A"
  },
  "stream": [
    { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 1080, "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 },
    { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720,  "framerate": "30", "keyframe": "60", "quality": 22, "audio_bitrate": 128 }
  ]
}
```

- `iv` can be any 32-character hex string (16 bytes). Remember it — you'll need it when generating Fairplay tokens.
- `key_url` format is `skd://<kid>` (no host, just the kid). Different from EZDRM's `skd://fps.ezdrm.com/;<kid>`.

## Cross-platform full job

Combine both DRM systems in one job:

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "advanced_dash",
        "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/dash/" },
        "cenc_drm": { "key": "...", "key_id": "...", "pssh": "CAESE...", "la_url": "https://pr.service.expressplay.com/playready/RightsManager.asmx" },
        "stream": [/* … */]
      },
      {
        "output": "advanced_hls",
        "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/hls/" },
        "fps_drm": { "key": "...", "iv": "0000...0000", "key_url": "skd://..." },
        "stream": [/* … */]
      }
    ]
  }
}
```

## Step 4 — Generate playback tokens

ExpressPlay tokens are per-session, per-DRM. Generate them server-side when a viewer requests playback:

**Widevine:**
```bash
curl -X GET "https://wv-gen.service.expressplay.com/hms/wv/token?customerAuthenticator=$API_KEY&errorFormat=json&kid=$KID&contentKey=$KEY&useHttps=true"
```

Response includes a license URL with embedded token:
```
https://wv.service.expressplay.com/hms/wv/rights/?ExpressPlayToken=BQAdp7z9Kdo...
```

**Fairplay:**
```bash
curl -X GET "https://fp-gen.service.expressplay.com/hms/fp/token?customerAuthenticator=$API_KEY&errorFormat=json&kid=$KID&kek=$KEK&iv=$IV&useHttps=true"
```

Response includes a Fairplay license URL similarly.

**PlayReady:**
ExpressPlay's PlayReady license URL is in the `la_url` you baked into `cenc_drm` — no per-session token needed.

## Step 5 — Player config

Pass the per-session license URL to your player:

```javascript
const params = {
  videoSources: {
    src: "https://yourserver.com/content/playlist.mpd",
    keySystems: {
      'com.widevine.alpha': "https://wv.service.expressplay.com/hms/wv/rights/?ExpressPlayToken=<token>"
    }
  }
};
qPlayer('my_player', params);
```

## Customization notes

- **Static PSSH + la_url for ExpressPlay**: the values shown for `pssh` and `la_url` are constant across ExpressPlay customers — they're ExpressPlay's well-known service endpoints. Don't generate them per content.
- **kek persistence**: pick a `kek` and reuse it consistently for assets that share a key. Rotating `kek` makes existing keys un-retrievable.
- **Customer authenticator format**: ExpressPlay's `API_KEY` is `<customer_id>,<key>`. Both parts go in the `customerAuthenticator` query param URL-encoded.
- **Tokens are short-lived**: ExpressPlay tokens typically expire within hours. Generate per-session, not per-content.

## Schema pointers

- `start_encode2.query.format[].cenc_drm.{key, key_id, pssh, la_url}` — Widevine + PlayReady via ExpressPlay
- `start_encode2.query.format[].fps_drm.{key, iv, key_url}` — Fairplay via ExpressPlay

See also: `assets/recipes/drm_widevine_ezdrm.md`, `assets/recipes/drm_playready_ezdrm.md`, `assets/recipes/drm_fairplay_ezdrm.md` (EZDRM alternatives — different KMS, same Qencode API shape), `assets/recipes/drm_buydrm.md` (BuyDRM, signed CPIX request flow).

## Gotchas

- **ExpressPlay's PSSH is shared, not per-content**: use the well-known `CAESE...intertrust...` value. EZDRM's PSSH is per-content; ExpressPlay's is the service-wide identifier.
- **Fairplay `key_url`**: `skd://<kid>` for ExpressPlay (no host), vs `skd://fps.ezdrm.com/;<kid-with-dashes>` for EZDRM. Don't paste one provider's URL into the other.
- **PlayReady `la_url`**: ExpressPlay's RightsManager URL is fixed. Don't change it.
- **`kid` and `key` are returned as uppercase hex from ExpressPlay's API** — Qencode accepts either case but consistency matters when generating tokens that reference the same values.
