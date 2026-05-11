# Example 02 — HLS ABR to Qencode S3

## User prompt
> Make an HLS stream from s3://input/movie.mp4. Write it to my Qencode bucket at s3://us-west.s3.qencode.com/movies/abc/.

## Notes
- HLS → `hls_abr.md` recipe, default 4-rung ladder.
- Qencode-managed S3 destination → no `key`, no `secret`, no `permissions`, no `storage_class`.
- Trailing `/` on the destination URL because HLS writes to a folder.
- All per-rendition params (`video_codec`, `audio_codec`, `resolution`, `framerate`, `keyframe`, `quality`, `audio_bitrate`) live on each `stream[]` entry — the format level only carries packaging + per-title bounds + destination.

## Expected JSON

```json
{
  "query": {
    "source": "s3://input/movie.mp4",
    "encoder_version": 2,
    "format": [
      {
        "output": "advanced_hls",
        "segment_duration": 6,
        "optimize_bitrate": 1,
        "min_crf": 18,
        "max_crf": 28,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/movies/abc/"
        },
        "stream": [
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 1080,
            "framerate": "30",
            "keyframe": "60",
            "quality": 22,
            "audio_bitrate": 128
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 720,
            "framerate": "30",
            "keyframe": "60",
            "quality": 22,
            "audio_bitrate": 128
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 540,
            "framerate": "30",
            "keyframe": "60",
            "quality": 23,
            "audio_bitrate": 96
          },
          {
            "video_codec": "libx264",
            "audio_codec": "libfdk_aac",
            "resolution": 360,
            "framerate": "30",
            "keyframe": "60",
            "quality": 23,
            "audio_bitrate": 96
          }
        ]
      }
    ]
  }
}
```

## Expected summary

> Produces an HLS master playlist with 4 renditions (1080p/720p/540p/360p) at 6-second segments, written to `s3://us-west.s3.qencode.com/movies/abc/`. Each stream's `framerate: "30"` + `keyframe: "60"` ensures segments align to keyframe boundaries so ABR switching is clean.
>
> The master playlist will be at `master.m3u8` under that prefix (override with `playlist_name` if needed).
>
> Hand this JSON to `qencode-transcode` to submit.
