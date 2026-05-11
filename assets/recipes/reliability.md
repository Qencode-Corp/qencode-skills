---
recipe: reliability
title: Reliability — retry on error, soft-fail, and warning surfacing
when_to_use: User wants jobs to survive transient failures or wants non-critical outputs to fail without aborting the whole job. Production workloads should default to these settings.
output_count: configuration only; can be added to any recipe
needs_destination: n/a (these are workflow knobs, not outputs)
based_on: content/tutorials/transcoding/improve-reliability.md
---

# Recipe — Reliability

Three independent knobs that together raise success rate on production workloads:

1. **`retry_on_error`** (top-level) — auto-retry the whole job once if it fails for a non-persistent reason.
2. **`allow_soft_fail`** (per-format) — let non-critical outputs fail without aborting the job.
3. **`warnings[]`** (read-side) — surface non-fatal issues for proactive monitoring.

None of these change the *encoding* — they change error handling and observability.

## 1. retry_on_error — auto-retry on transient failure

Set at the top level of `query`. Retries the whole job once if a non-persistent error occurs.

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "retry_on_error": 1,
    "format": [ /* … your outputs … */ ]
  }
}
```

**What triggers a retry:** transient encoding-side issues — temporary network blips, intermittent worker errors, capacity-related restarts.

**What does NOT trigger a retry:**
- **Source download errors** (404, expired presigned URL, DNS, TLS) — persistent by definition.
- **Destination upload errors** (403, bucket missing, wrong key/secret) — persistent.
- **Source-corruption errors** ("Source media decode error" warning) — won't help to retry.

**Retry workflow when triggered:**
1. A warning is added to the failed job: *"An error occurred while processing your job. It will be automatically retried with the same parameters in a new job."*
2. A new job is started with the same parameters.
3. A second warning is added to the failed job pointing at the new job ID: *"Retry on error triggered."*
4. A callback with `event: "restarted"` is sent for the failed job, including all warnings.
5. If the restart itself fails to start: callback with `event: "restart_failed"` + warning *"Retry on error failed."*

**Recommendation:** enable `retry_on_error: 1` on **every** production job. It's not on by default.

## 2. allow_soft_fail — let non-critical outputs fail without aborting

Set on **individual outputs** in `format[]`. When `allow_soft_fail: 1`, an error in that specific output:
- Doesn't abort the job.
- Doesn't abort other outputs in the same job.
- Appears as a warning in the final status response.

```json
{
  "query": {
    "source": "https://example.com/lecture.mp4",
    "encoder_version": 2,
    "retry_on_error": 1,
    "format": [
      {
        "output": "advanced_hls",
        "segment_duration": 6,
        "stream": [
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 1080, "framerate": "30", "keyframe": "60", "quality": 22 },
          { "video_codec": "libx264", "audio_codec": "libfdk_aac", "resolution": 720,  "framerate": "30", "keyframe": "60", "quality": 22 }
        ],
        "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/hls/" }
      },
      {
        "output": "speech_to_text",
        "allow_soft_fail": 1,
        "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/stt/" }
      },
      {
        "output": "mp3",
        "allow_soft_fail": 1,
        "audio_bitrate": 192,
        "destination": { "url": "s3://us-west.s3.qencode.com/yourbucket/audio.mp3" }
      }
    ]
  }
}
```

In this example, the HLS rendition is critical; STT and MP3 are nice-to-haves. If the source has no/silent audio, STT and MP3 fail gracefully and the job still completes with the HLS output.

**Recommended use cases:**
- **STT and audio-only outputs** when the source may have no/silent audio.
- **Optional thumbnail sprites** when the primary thumbnail is what matters.
- **Lower-priority device profiles** in a wide ladder.
- **Anything supplementary** the user can live without.

## 3. warnings[] — surface non-fatal issues

Every `/v1/status` response (and callback payload) includes a `warnings[]` array. Warnings don't fail the job but indicate something worth investigating.

```json
"warnings": [
  {
    "message": "Callback delivery error",
    "details": "Error sending callback to https://yourserver.com/qencode_callback 500: Internal Server Error."
  },
  {
    "message": "Source media decode error"
  }
]
```

Common warning categories:
- **Source video decoding errors** — source media may be corrupted; verify by playing locally.
- **Callback endpoint errors** — your webhook returned non-2xx; fix your endpoint to avoid silent loss of completion notifications.
- **Low audio bitrate** — source audio is too low to encode meaningfully; raise it upstream.
- **Errors ignored by `allow_soft_fail`** — outputs that failed quietly because they had `allow_soft_fail: 1`.
- **`retry_on_error` activity** — the messages above.

**Recommendation:** scan `warnings[]` on every completion callback or status fetch. Log to a structured store; alert on patterns (recurring callback failures, increasing decode errors on a source provider, etc.).

## Combined production-ready preamble

Most production jobs should start with this skeleton:

```json
{
  "query": {
    "source": "...",
    "encoder_version": 2,
    "retry_on_error": 1,
    "callback_url": "https://yourserver.com/qencode_callback",
    "format": [
      /* critical outputs (no allow_soft_fail) */
      /* optional outputs with allow_soft_fail: 1 */
    ]
  }
}
```

## Schema pointers

- `start_encode2.query.retry_on_error` — top-level, 0/1
- `start_encode2.query.format[].allow_soft_fail` — per-output, 0/1
- `status.returns.status.warnings` — array of warning objects

See also: `assets/recipes/callbacks.md` (callback delivery + restart events), `assets/best-practices.md` (§1, §6), `assets/error-codes.md` (when a warning escalates to an error).

## Gotchas

- `retry_on_error` retries **the whole job once**, not output-by-output. For per-output resilience, use `allow_soft_fail`.
- A retried job gets a **new** task_token. Subscribers to the original token won't see completion — listen on the callback or query the original token's status for the `restarted` event with the new job ID.
- Persistent errors (404 on source, wrong credentials) won't be retried even with `retry_on_error: 1`. Fix the root cause upstream.
- `allow_soft_fail` doesn't prevent billing for the failed output — Qencode bills for work attempted.
