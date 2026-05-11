# Example 03 — Combined: HLS + poster image + extracted MP3, to AWS S3

## User prompt
> From https://cdn.example.com/lecture.mp4, give me HLS streaming, a poster image at the 30-second mark, and an MP3 audio extract. Put everything in my AWS bucket `lectures-prod` in `us-east-1`, publicly readable. Just need 1080 and 720 for HLS.

## Notes
- Three outputs → three `format[]` entries.
- AWS S3 destinations → include `key`, `secret`, `permissions: "public-read"`. (Placeholders shown; the user fills them in.)
- HLS folder path uses trailing `/`; the poster and MP3 are single files with full filenames.
- "30-second mark" → use `start_time: 30` on a single thumbnail output.
- Only 2 ladder rungs requested → trim the default ladder.
- Audio extraction → `output: "mp3"` with libfdk audio not applicable (use `libmp3lame`/default).

## Expected JSON

```json
{
  "query": {
    "source": "https://cdn.example.com/lecture.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "advanced_hls",
        "segment_duration": 6,
        "destination": {
          "url": "s3://us-east-1.amazonaws.com/lectures-prod/hls/",
          "key": "AKIA_REPLACE",
          "secret": "REPLACE",
          "permissions": "public-read"
        },
        "stream": [
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 1080,
            "framerate": "30",
            "keyframe": "60",
            "optimize_bitrate": 1,
            "audio_bitrate": 128
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 720,
            "framerate": "30",
            "keyframe": "60",
            "optimize_bitrate": 1,
            "audio_bitrate": 128
          }
        ]
      },
      {
        "output": "thumbnail",
        "start_time": 30,
        "image_format": "jpg",
        "resolution": 1080,
        "destination": {
          "url": "s3://us-east-1.amazonaws.com/lectures-prod/poster.jpg",
          "key": "AKIA_REPLACE",
          "secret": "REPLACE",
          "permissions": "public-read"
        }
      },
      {
        "output": "mp3",
        "audio_bitrate": 192,
        "destination": {
          "url": "s3://us-east-1.amazonaws.com/lectures-prod/audio.mp3",
          "key": "AKIA_REPLACE",
          "secret": "REPLACE",
          "permissions": "public-read"
        }
      }
    ]
  }
}
```

## Expected summary

> Single job, three outputs running in parallel:
> 1. **HLS** at 1080p + 720p under `s3://lectures-prod/hls/`
> 2. **Poster JPEG** at 30 s of source, 1080-resolution, at `s3://lectures-prod/poster.jpg`
> 3. **MP3 audio** at 192 kbps at `s3://lectures-prod/audio.mp3`
>
> All three are uploaded as `public-read` (AWS canned ACL). Replace the `AKIA_REPLACE` / `REPLACE` placeholders with your AWS credentials before submitting.
>
> Hand this JSON to `qencode-transcode` to submit.
