# Example 01 — Simple MP4, no destination

## User prompt
> Encode https://cdn.example.com/source.mp4 to a 720p MP4.

## Notes
- One output, no destination mentioned → use 24-hour temp storage and warn.
- 720p as a single MP4 → use the MP4 ladder recipe with one rung.
- `resolution: 720` keeps source aspect ratio for both landscape and portrait sources.
- Per-title encoding (`optimize_bitrate: 1`) alone — no `quality`, no `bitrate`, no `min_crf`/`max_crf`. Per-title picks the CRF; the other quality knobs would be ignored anyway.

## Expected JSON

```json
{
  "query": {
    "source": "https://cdn.example.com/source.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 720,
        "optimize_bitrate": 1,
        "audio_bitrate": 128
      }
    ]
  }
}
```

## Expected summary

> Produces one 720p MP4 from your source using H.264 + libfdk_aac with per-title encoding.
>
> ⚠️ No `destination` was specified, so the output lands in Qencode's 24-hour temporary storage and will be **deleted ~24 hours after the job completes**. Add a `destination` block (see `assets/storage.md`) if you want to keep it.
>
> Hand this JSON to `qencode-transcode` to submit, or pass it as the `query` form field on `POST /v1/start_encode2`.
