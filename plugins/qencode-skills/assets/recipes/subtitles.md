---
recipe: subtitles
title: Add, copy, or remove subtitles on a video output
when_to_use: User wants to attach external subtitle files (.srt/.ass) to a video output, preserve EIA-608/708 closed captions baked into the source, or strip existing subtitles. For *auto-generated* subtitles from speech, see `speech_to_text.md` instead.
output_count: subtitles are configured on a video format block (not a separate output)
needs_destination: required for the video output the subtitles attach to
based_on: content/tutorials/transcoding/subtitles.md
---

# Recipe — Subtitles

Subtitles are configured **on a video format block** (MP4, HLS, DASH, etc.), not as a separate output. Three common operations:

1. **Add** new subtitles from external `.srt` or `.ass` files (one per language).
2. **Copy** existing EIA-608 or EIA-708 closed captions from the source's video stream.
3. **Remove** all subtitles from the output.

Currently supported subtitle formats: `.srt`, `.ass`.

## Add external subtitles (multi-language)

```json
{
  "query": {
    "source": "https://example.com/movie.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 720,
        "optimize_bitrate": 1,
        "subtitles": {
          "sources": [
            {
              "source": "https://example.com/subs/movie.eng.srt",
              "language": "eng"
            },
            {
              "source": "https://example.com/subs/movie.fra.srt",
              "language": "fra"
            }
          ]
        },
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/movie.mp4"
        }
      }
    ]
  }
}
```

Each entry in `subtitles.sources[]` needs:
- `source` — public URL of the `.srt` or `.ass` file
- `language` — 3-letter language tag (`eng`, `fra`, `deu`, `spa`, …)

## Copy EIA-608 / EIA-708 closed captions from source

When the source has CEA-608 or CEA-708 captions baked into the video stream (common in broadcast content), you can carry them through to the output:

```json
{
  "output": "mp4",
  "video_codec": "libx264",
  "audio_codec": "libfdk_aac",
  "resolution": 720,
  "subtitles": {
    "copy": 1
  },
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/movie.mp4"
  }
}
```

`subtitles.copy: 1` copies CEA-608/708 closed captions into the output's video stream. Default is `0`.

## Remove subtitles from the output

External subtitle streams in the source are **copied by default**. To strip them:

```json
{
  "output": "mp4",
  "video_codec": "libx264",
  "audio_codec": "libfdk_aac",
  "resolution": 720,
  "subtitles_copy": 0,
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/movie.mp4"
  }
}
```

`subtitles_copy: 0` (note: not nested under `subtitles`) disables passthrough of existing subtitle streams.

## Subtitles on HLS / DASH ABR outputs

Subtitle configuration belongs on the format block for ABR outputs too, not on individual streams:

```json
{
  "output": "advanced_hls",
  "segment_duration": 6,
  "subtitles": {
    "sources": [
      { "source": "https://example.com/subs/movie.eng.srt", "language": "eng" }
    ]
  },
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/hls/"
  },
  "stream": [
    { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 1080, "framerate": "30", "keyframe": "60", "optimize_bitrate": 1 },
    { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720, "framerate": "30", "keyframe": "60", "optimize_bitrate": 1 }
  ]
}
```

The subtitles get packaged as their own HLS/DASH playlist variant.

## Customization notes

- **Language tags**: the tutorial uses 3-letter ISO 639-2 codes (`eng`, `fra`, `deu`, `spa`, `por`, `ita`, `jpn`, `kor`, `zho`). Most players prefer 3-letter codes for subtitle tracks.
- **Subtitle file format**: `.srt` is universally supported; `.ass` adds styling but not every player honors it.
- **External + copy**: you can combine — `subtitles.sources[]` for new external subs *and* `subtitles.copy: 1` for CEA-608/708 from the source, in the same job.

## For auto-generated subtitles from audio

Use the `speech_to_text` recipe (`assets/recipes/speech_to_text.md`) instead. STT produces `.srt` and `.vtt` files that you can then feed into a follow-up `subtitles` job, or chain them in the same workflow.

## Schema pointers

- `start_encode2.query.format[].subtitles.sources[].source` — URL of the subtitle file
- `start_encode2.query.format[].subtitles.sources[].language` — language tag
- `start_encode2.query.format[].subtitles.copy` — 0/1, copy CEA-608/708 from source
- `start_encode2.query.format[].subtitles_copy` — 0/1 (note flat, not nested), passthrough of existing subtitle streams

See also: `assets/best-practices.md` (§1, §6) and `assets/storage.md`.

## Gotchas

- Two different "copy" knobs: `subtitles.copy` (nested, for CEA-608/708) vs `subtitles_copy` (flat, for existing subtitle streams). Don't confuse them.
- `subtitles_copy` defaults to `1` — existing subtitle streams are kept unless you explicitly set `0`.
- Not all output containers support all subtitle formats. MP4 + WebVTT is well-supported; HLS subtitles use WebVTT in their own variant playlist; DASH supports TTML/IMSC1.
- Subtitle source URLs must be publicly reachable from Qencode — same auth model as the video source.
