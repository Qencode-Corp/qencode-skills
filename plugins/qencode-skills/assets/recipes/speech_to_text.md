---
recipe: speech_to_text
title: Speech-to-Text — auto-subtitles, transcripts, and translations
when_to_use: User wants automatic transcription (SRT, VTT, TXT, JSON-with-timestamps) of speech in a video or audio file. Optionally translates the transcript into up to 15 target languages within the same job.
output_count: 1 format block; emits 4 file types per target language (each toggleable)
needs_destination: optional but recommended (multiple files; 24-hour temp storage if omitted)
based_on: content/tutorials/transcoding/speech-to-text.md
---

# Recipe — Speech-to-Text (with optional translations)

A single `speech_to_text` format block produces, by default, four files for the source language: `transcript.txt`, `timestamps.json`, `subtitles.srt`, `subtitles.vtt`. If you add `translate_languages`, the same four file types are produced *per target language* with a language-code suffix in the filenames.

## Inputs

- `source` — public URL of a video or audio file (anything with speech in it).
- `destination` — required for reliable production use. The `url` is a **folder** prefix; the four files land underneath it.

## Basic transcription, source language auto-detected

```json
{
  "query": {
    "source": "https://example.com/lecture.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "speech_to_text",
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/stt/"
        }
      }
    ]
  }
}
```

This emits `transcript.txt`, `timestamps.json`, `subtitles.srt`, `subtitles.vtt` in the destination folder. The source language is auto-detected from the audio.

## Force a specific source language

```json
{
  "output": "speech_to_text",
  "language": "uk",
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/stt/"
  }
}
```

Use ISO codes (e.g. `en`, `de`, `es`, `it`, `uk`, `cs`, `zh`). Set `language` only when you want to **force** the source language — otherwise Qencode auto-detects.

## Translate into multiple target languages

```json
{
  "output": "speech_to_text",
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/stt/"
  },
  "translate_languages": ["uk", "cs", "de", "es", "it", "fr"]
}
```

`translate_languages` accepts up to **15** target language codes. Output filenames include the language-code suffix (`subtitles-cs.srt`, `transcript-de.txt`, etc.). If you need more than 15, split across multiple jobs.

## Choose accuracy vs speed

```json
{
  "output": "speech_to_text",
  "mode": "accuracy",
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/stt/"
  }
}
```

`mode` accepts `accuracy` (slowest, best quality), `balanced`, or `speed` (fastest, less accurate). Default is `balanced`.

## Pick which file types to emit + custom filenames

```json
{
  "output": "speech_to_text",
  "mode": "accuracy",
  "translate_languages": ["es", "fr"],
  "transcript": 1,
  "transcript_name": "show_transcript.txt",
  "json": 0,
  "srt": 1,
  "srt_name": "show_captions.srt",
  "vtt": 0,
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/stt/"
  }
}
```

| File type | Toggle | Custom name | Default name |
|---|---|---|---|
| Plain transcript | `transcript: 1` (default) | `transcript_name` | `transcript.txt` |
| JSON with timestamps | `json: 1` (default) | `json_name` | `timestamps.json` |
| SRT subtitles | `srt: 1` (default) | `srt_name` | `subtitles.srt` |
| VTT subtitles | `vtt: 1` (default) | `vtt_name` | `subtitles.vtt` |

Set any to `0` to skip that file type.

## Transcribe only a clip

```json
{
  "output": "speech_to_text",
  "start_time": 60.0,
  "duration": 30.0,
  "destination": {
    "url": "s3://us-west.s3.qencode.com/yourbucket/stt/"
  }
}
```

Use `start_time` + `duration` (both in seconds) to process only a segment. Reduces cost and time on long recordings.

## Reading the result

The `/v1/status` response includes a `texts[]` array. Each entry has:
- `url` / `download_url` — base URL for the output folder
- `storage.names` — the actual filenames (with language suffixes if translations were requested)
- `detected_language` — what language Qencode detected (whether or not you forced `language`)
- `meta` — `mode`, `model`, `entropy_threshold`, `beam_size`, `language`, `translate_languages`
- `cost` — per-job STT cost

## Customization notes

- **Source-language coverage**: ~19 "Stable" languages have WER ≤20%; ~46 more are "Beta" (less accurate). See the full tutorial for the language tables.
- **Translation-language coverage**: ~25 "Stable" target languages plus ~60 "Beta". Stable list includes major European, East Asian, and Middle Eastern languages.
- **Audio quality matters**: noisy backgrounds, overlapping speech, low-quality compression all hurt accuracy. Pre-clean the audio if you can.
- **No destination**: outputs land in 24-hour temp storage. Warn the user — STT outputs are typically things you want to keep.

## Other storage backends

See **`assets/storage.md`** for AWS S3, Cloudflare R2, B2, Azure, FTP/SFTP destination variants.

## Schema pointers

- `start_encode2.query.format[].output` — `speech_to_text`
- `start_encode2.query.format[].mode` — `accuracy` / `balanced` / `speed`
- `start_encode2.query.format[].language` — force source language (ISO code)
- `start_encode2.query.format[].translate_languages` — array of target ISO codes (max 15)
- `start_encode2.query.format[].transcript` / `.json` / `.srt` / `.vtt` — 0/1 toggles
- `start_encode2.query.format[].transcript_name` / `.json_name` / `.srt_name` / `.vtt_name` — custom filenames

See also: `assets/best-practices.md` (§1, §6) and `assets/storage.md`.

## Gotchas

- `destination.url` is a **folder** prefix (trailing `/`), not a file path.
- `translate_languages` is **required-ish**: omit it and you only get source-language outputs (no translations). The schema marks it required only when you want translations; in practice it's omittable.
- Cost scales with audio duration and number of target languages.
- For multi-track audio (e.g. dubbed video), STT typically picks the default audio stream. There's no public per-track selector — pre-extract the target track if needed.
