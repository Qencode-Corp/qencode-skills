---
recipe: audio_outputs
title: Audio-only outputs (MP3, HLS audio, FLAC)
when_to_use: User wants to extract or transcode an audio track — standalone MP3 file, HLS-audio playlist for streaming, or lossless FLAC. Input can be a video or an audio-only source.
output_count: 1 format block per audio output requested
needs_destination: optional (defaults to 24-hour temp storage — warn the user)
based_on: content/tutorials/transcoding/audio-outputs.md
---

# Recipe — Audio-only outputs

Three common shapes:

1. **MP3** — single progressive audio file for download/playback.
2. **HLS audio** — single audio rendition packaged as HLS; usable as the audio track in a multi-rendition stream or as a standalone audio playlist.
3. **FLAC** — lossless audio archival.

Input can be a video (audio track is extracted) or an audio-only source.

## MP3 (variable bitrate, fine-tunable)

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "mp3",
        "audio_codec": "mp3",
        "audio_bitrate": 192,
        "audio_sample_rate": 44100,
        "audio_channels_number": 2,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/audio.mp3"
        }
      }
    ]
  }
}
```

> For MP3 outputs, set `audio_codec: "mp3"` — this is the exception to the project's `libfdk_aac` default (which applies to AAC outputs like `hls_audio` and AAC streams inside MP4/HLS/DASH containers).

## HLS audio (single audio rendition)

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "hls_audio",
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/audio_hls/"
        },
        "stream": [
          {
            "audio_codec": "libfdk_aac",
            "audio_bitrate": 128
          }
        ]
      }
    ]
  }
}
```

`hls_audio` is an ABR-style output — per `best-practices.md` §7, audio params (`audio_codec`, `audio_bitrate`) belong on each `stream[]` entry. `destination.url` is a folder.

## FLAC (lossless, up to 320 kbps)

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "flac",
        "audio_bitrate": 320,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/audio.flac"
        }
      }
    ]
  }
}
```

FLAC is lossless, so the audio codec cannot be changed (omit `audio_codec`). `audio_bitrate` is treated as a target rather than a hard cap.

## Trim audio with `start_time` + `duration`

```json
{
  "output": "mp3",
  "start_time": 30,
  "duration": 60,
  "audio_bitrate": 192,
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/clip.mp3"
  }
}
```

`start_time` is in seconds; `duration` is the segment length in seconds.

## Customization notes

- **Audio codec**: the schema accepts `libfdk_aac`, `aac`, `mp3`, `opus`, `libvorbis`. Use `mp3` for `mp3` outputs, `libfdk_aac` for `hls_audio` and any AAC streams (project default).
- **Sample rate**: defaults to 44100. Common alternates: 48000 (broadcast), 22050 (low-bandwidth voice).
- **Channels**: defaults to 2 (stereo). Use 1 for mono (voice/podcast).
- **Bitrate**: defaults to 64 kbps — way too low for music. For voice 96–128 is fine, for music 192–320, for FLAC archival 320.
- **No destination**: outputs land in 24-hour temp storage. Warn the user.

## Other storage backends

See **`assets/storage.md`** for AWS S3, Cloudflare R2, Backblaze B2, Azure Blob, FTP/SFTP destination variants and the per-provider compatibility matrix.

## Schema pointers

- `start_encode2.query.format[].output` — `mp3`, `hls_audio`, `flac`
- `start_encode2.query.format[].audio_codec`, `.audio_bitrate`, `.audio_sample_rate`, `.audio_channels_number`
- `start_encode2.query.format[].start_time`, `.duration` — trimming

See also: `assets/best-practices.md` (§1, §3, §6) and `assets/storage.md`.

## Gotchas

- Don't put `video_codec` or video-sizing params on an audio-only output — they're ignored at best, error at worst.
- `hls_audio` is its own output type — don't use `advanced_hls` with audio-only `stream[]` entries; it's not the same packaging path.
- For multi-language audio tracks alongside video, use `separate_audio: 1` on an `advanced_hls` output (see `assets/recipes/hls_abr.md`), not multiple `hls_audio` outputs.
