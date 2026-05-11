---
recipe: hls_abr
title: HLS adaptive bitrate (ABR) playlist
when_to_use: User wants HLS streaming output — a master `.m3u8` plus per-rendition variant playlists and segments — for browser/iOS playback or CDN delivery.
output_count: 1 (single advanced_hls output with multiple streams)
needs_destination: yes (HLS produces many files; you almost always want your own bucket)
---

# Recipe — HLS adaptive bitrate playlist

Produces a single master HLS playlist with multiple bitrate variants. For ABR, all per-rendition encoding params (`video_codec`, `audio_codec`, `resolution`, `framerate`, `keyframe`, `quality`, `audio_bitrate`) belong on each `stream[]` entry — the format level only carries packaging settings (`segment_duration`, `fmp4`, `separate_audio`, `playlist_name`), the destination, and per-title bounds. This is the schema's documented rule, not a workaround.

## Inputs

- `source` — public URL of the input video.
- `streams` — list of resolution rungs. Defaults below.
- `destination` — required (Qencode S3 or your own). HLS produces many files; temp storage usually isn't viable.

## Default ladder

| `resolution` | `audio_bitrate` |
|---|---|
| 1080 | 128 |
| 720  | 128 |
| 540  |  96 |
| 360  |  96 |

`framerate: "30"` + `keyframe: "60"` per stream + `segment_duration: 6` at format level → 2-second GOPs, 3 GOPs per segment, every segment starts on a keyframe.

## query JSON — Qencode-managed storage

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
        "stream": [
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 1080,
            "framerate": "30",
            "keyframe": "60",
            "quality": 22,
            "optimize_bitrate": 1,
            "audio_bitrate": 128
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 720,
            "framerate": "30",
            "keyframe": "60",
            "quality": 22,
            "optimize_bitrate": 1,
            "audio_bitrate": 128
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 540,
            "framerate": "30",
            "keyframe": "60",
            "quality": 23,
            "optimize_bitrate": 1,
            "audio_bitrate": 96
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 360,
            "framerate": "30",
            "keyframe": "60",
            "quality": 23,
            "optimize_bitrate": 1,
            "audio_bitrate": 96
          }
        ]
      }
    ]
  }
}
```

The master playlist will be at `s3://.../hls/master.m3u8` (override with `playlist_name`). Variant playlists and segments live in subdirectories.

## Other storage backends

For AWS S3, Cloudflare R2, Backblaze B2, Azure Blob, FTP/SFTP, fan-out, or CDN cache headers, see **`assets/storage.md`**. That doc has the per-provider compatibility matrix and ready-to-paste destination snippets. The HLS recipe needs `url` to point at a **folder** prefix (with trailing `/`), not a filename — that constraint is also covered there.

## Frame rate / keyframe alignment

If the source isn't 30fps, set `framerate` + `keyframe` consistently across every `stream[]` entry so `keyframe` divides `framerate × segment_duration` cleanly:

| Source | `framerate` | `keyframe` | `segment_duration` (format) |
|---|---|---|---|
| Most web video | "30" | "60" | 6 |
| Film | "24" | "48" | 6 |
| PAL broadcast | "25" | "50" | 6 |
| High-FPS sports | "60" | "60" | 6 |

Apply the chosen `framerate`/`keyframe` to **every** entry in the `stream[]` array — different values across rungs would make ABR switching unreliable.

> **Schema note:** the `stream` object's `attributes` array only enumerates `chunklist_name`. The authoritative source for what goes on stream is the format-level attribute *descriptions* — most read "For HLS or DASH output specify this parameter on stream object level." See `assets/best-practices.md` §7 for the full list.

## Customization notes

- **fMP4 segments**: add `"fmp4": 1` to use `.m4s` segments instead of `.ts`. Required for low-latency HLS, recommended for CMAF.
- **Audio separation**: add `"separate_audio": 1` to split audio into separate renditions — required for multi-language audio tracks.
- **Single folder layout**: add `"single_folder": 1` to flatten all files into one directory.
- **DRM**: add a `cenc_drm` block for Widevine/PlayReady or `fps_drm` for Fairplay (recipe coming in M4).
- **Custom master filename**: `"playlist_name": "stream.m3u8"` overrides the default `master.m3u8`.
- **Fixed bitrate ladder**: replace `quality` per-stream with `bitrate` values (kbps) and remove `optimize_bitrate` from each stream.
- **Bounded per-title CRF**: add `min_crf` / `max_crf` / `adjust_crf` next to `optimize_bitrate` on each stream entry when you need quality floor/ceiling — see `assets/recipes/per_title_encoding.md` for details.

## Schema pointers

Read in `assets/schema-digest.md`:
- `start_encode2.query.format[].stream` — per-rendition options (digest only lists `chunklist_name`; for ABR, also put `video_codec`, `audio_codec`, `resolution`/`width`/`height`/`size`, `framerate`, `keyframe`, `quality`/`bitrate`, `audio_bitrate`, `rotate`, `aspect_ratio`, `two_pass` here — see `best-practices.md` §7)
- `start_encode2.query.format[].segment_duration` — segment length in seconds (stays at format level)
- `start_encode2.query.format[].fmp4` — fMP4/CMAF toggle
- `start_encode2.query.format[].separate_audio` — split audio

See also: `assets/best-practices.md` (§1, §2, §3, §4, §5, §6, §7) and `assets/storage.md`.

## Gotchas

- HLS output requires `destination` — the master playlist references segment URLs that must be stable.
- Use `output: "advanced_hls"` (modern packager), not the legacy `"hls"`.
- Remember the double-wrapped `query` envelope (see `gotchas.md` §1).
