---
recipe: drm_aes128
title: AES-128 encryption for HLS
when_to_use: User wants AES-128 encryption on HLS output — the basic content protection HLS spec supports natively. Lower friction than full DRM (Widevine/PlayReady/Fairplay); the key is fetched from a URL the player can resolve.
output_count: 1 advanced_hls format block
needs_destination: required (segments + playlists land in your bucket)
based_on: content/tutorials/transcoding/drm/aes-128.md
---

# Recipe — AES-128 encryption (HLS)

AES-128 is the simplest content protection scheme for HLS. Qencode encrypts each segment with a single 128-bit key; the player retrieves the key from a URL you control and decrypts on the fly. Good enough for casual content protection; not full DRM — anyone with the key URL and a copy of the key can decrypt.

For real DRM (Widevine, PlayReady, Fairplay), see the other `drm_*` recipes.

## Generate key + IV first

Run these locally (output goes into your `encryption` block):

```bash
# 1. Generate the 128-bit key in binary
openssl rand -out key.bin 16

# 2. Convert it to hex (this goes into the "key" field)
xxd -p key.bin > key.hex

# 3. Generate a 128-bit IV in hex (this goes into the "iv" field)
openssl rand -hex -out iv.hex 16
```

Then put `key.bin` (the binary, not the hex) on a web server reachable by your players. The URL to that file goes in `key_url`.

## query JSON

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
        "encryption": {
          "key": "<paste the contents of key.hex here, 32 hex chars>",
          "iv": "<paste the contents of iv.hex here, 32 hex chars>",
          "key_url": "https://your-server.com/aes-128/encryption.key"
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

The three encryption fields:
- `key` — the encryption key as a 32-character hex string (128 bits).
- `iv` — the initialization vector as a 32-character hex string.
- `key_url` — public URL where players can fetch the **binary** key file. Qencode bakes this URL into the master playlist via `EXT-X-KEY`.

## How playback works

1. Player loads `master.m3u8` from your destination.
2. Master playlist contains `EXT-X-KEY` lines pointing at `key_url`.
3. Player fetches the key file from `key_url`.
4. Player uses the key + IV to decrypt each segment as it plays.

For real-world deployments, gate `key_url` behind auth (session cookie, signed URL, IP allowlist) so unauthorized clients can't fetch the key. AES-128 is only as secure as your key delivery.

## Customization notes

- **Keys are global per output**: AES-128 in HLS uses one key for the entire ladder. You can't rotate keys per segment in this basic mode (use Widevine/PlayReady for that).
- **DASH support**: AES-128 in this `encryption` shape is HLS-specific. For DASH encryption, use Common Encryption (`cenc_drm`) — see `drm_widevine_ezdrm.md` or `drm_playready_ezdrm.md`.
- **Key rotation**: to rotate keys, re-encode the content with a new key and update `key_url` on your CDN.
- **No real DRM features**: AES-128 doesn't include device binding, license expiry, output restriction (HDCP), or any other DRM control. If you need any of those, use Widevine/PlayReady/Fairplay.

## Schema pointers

- `start_encode2.query.format[].encryption` — AES-128 params (`key`, `iv`, `key_url`)
- `start_encode2.query.format[].cenc_drm` — Common Encryption for Widevine/PlayReady (different scheme; see other DRM recipes)
- `start_encode2.query.format[].fps_drm` — FairPlay Streaming (different scheme; see `drm_fairplay_ezdrm.md`)

See also: `assets/recipes/hls_abr.md` (base HLS ladder), `assets/recipes/drm_widevine_ezdrm.md` / `drm_playready_ezdrm.md` / `drm_fairplay_ezdrm.md` (full DRM), `assets/best-practices.md` (§1, §7 — stream-level params).

## Gotchas

- `key` and `iv` must be **hex strings**, 32 characters each (128 bits). Don't send base64 or raw bytes.
- `key_url` must serve the **binary** key file (the `.bin`, not the hex). Players use the bytes directly.
- AES-128 is metadata-light protection — anyone with network access to `key_url` can decrypt. Gate the URL.
- Fairplay players cannot consume AES-128 encryption; for iOS/macOS native playback use Fairplay (see `drm_fairplay_ezdrm.md`).
