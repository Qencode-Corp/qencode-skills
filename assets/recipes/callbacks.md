---
recipe: callbacks
title: Webhook callbacks — receive notifications when a job finishes
when_to_use: User wants to be notified when a transcoding job moves through queue/save/error events instead of polling. Standard for production pipelines that ingest, transcode, and publish on a schedule.
output_count: configuration only (top-level on query)
needs_destination: n/a
based_on: content/tutorials/transcoding/receiving-callbacks.md
---

# Recipe — Webhook callbacks

Set `callback_url` on the `query` and Qencode POSTs status updates to your endpoint as the job progresses. Three lifecycle events:

| Event | When | Conditions |
|---|---|---|
| `queued` | Just after `/v1/start_encode2` accepts the job | All jobs |
| `saved` | The job has either completed or errored, and its final state is persisted in Qencode's DB | All jobs |
| `error` | An error occurred during processing | Only on errors |

The `saved` event is the most useful — it's the "the job is over, do whatever you do next" trigger. `error` fires only when something went wrong.

## query JSON

```json
{
  "query": {
    "source": "https://example.com/input.mp4",
    "encoder_version": 2,
    "retry_on_error": 1,
    "callback_url": "https://yourserver.com/qencode_callback",
    "format": [
      {
        "output": "mp4",
        "video_codec": "libx264",
        "audio_codec": "libfdk_aac",
        "resolution": 720,
        "quality": 22,
        "optimize_bitrate": 1,
        "min_crf": 18,
        "max_crf": 28,
        "audio_bitrate": 128,
        "destination": {
          "url": "s3://us-west.s3.qencode.com/yourbucket/output.mp4"
        }
      }
    ]
  }
}
```

## What you receive at `callback_url`

POST request with `Content-Type: application/x-www-form-urlencoded`. Fields:

| Field | Description |
|---|---|
| `task_token` | The job's task token (unique ID) |
| `event` | `queued`, `saved`, or `error` |
| `payload` | Whatever string you passed in the top-level `payload` field of `/v1/start_encode2` |
| `error_code` | (error event only) Numeric Qencode error code |
| `error_message` | (error event only) Human-readable error description |
| `callback_type` | `task` for whole-job events, `stream` for per-rendition events (only when `refresh_playlist` or `use_subtask_callback` is on) |
| `status` | **URL-encoded JSON** containing the full status object (same shape as `/v1/status` response) |

The body is form-encoded — your handler needs to parse it as form data, then `JSON.parse` the `status` field, then `JSON.parse` the `payload` field if you passed JSON-shaped payload data.

### Multi-line example of a decoded `saved` callback

```
status={"status": "completed", "videos": [...], "audios": [...], "duration": "30.017", "error": 0, ...}
callback_type=task
task_token=e2079274fc1c4d12af5cf14affc9ba4e
event=saved
payload={"fileName": "bbb_30s.mp4"}
```

## Use the user-defined `payload` to correlate back to your domain

Pass any string in the top-level `payload` field on `/v1/start_encode2` — it travels with the job and comes back verbatim in every callback. Typical use: a JSON-encoded reference to your own internal job ID, user ID, or upload ID:

```json
{
  "query": {
    "source": "...",
    "callback_url": "https://yourserver.com/qencode_callback",
    "format": [/* ... */]
  },
  "payload": "{\"my_job_id\": 42, \"user_id\": 'alice'}"
}
```

(Note `payload` is at the top of the request body, **not** inside `query`.)

## Per-rendition callbacks (`use_subtask_callback`)

For ABR ladders or multi-output jobs, you may want a callback for each output as it lands, not just one at the very end. Set `use_subtask_callback: 1` on the `query`:

```json
"callback_url": "https://yourserver.com/qencode_callback",
"use_subtask_callback": 1
```

Each rendition firing a callback has `callback_type: "stream"`. The whole-job `saved` callback still fires at the end with `callback_type: "task"`.

This works hand-in-hand with `refresh_playlist: 1` (see `assets/recipes/refresh_abr_playlist.md`) — together they give viewers playback as soon as a single rendition lands, AND notify your backend of each rendition completion.

## Handler examples

### Python (Flask)

```python
from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/qencode_callback', methods=['POST'])
def handle_callback():
    data = request.form.to_dict()
    event = data.get('event')
    task_token = data.get('task_token')
    status = json.loads(data.get('status', '{}'))
    payload = json.loads(data.get('payload', '{}')) if data.get('payload') else {}

    if event == 'saved':
        if status.get('error') == 0:
            # Success — videos, audios, images, texts in the status object
            video_urls = [v['url'] for v in status.get('videos', [])]
            print(f"Job {task_token} done: {video_urls} (your payload: {payload})")
        else:
            print(f"Job {task_token} failed: {status.get('error_description')}")
    elif event == 'queued':
        print(f"Job {task_token} queued")
    elif event == 'error':
        print(f"Job {task_token} error {data.get('error_code')}: {data.get('error_message')}")

    return 'OK', 200
```

### Node.js (Express)

```js
const express = require('express');
const app = express();
app.use(express.urlencoded({ extended: true }));

app.post('/qencode_callback', (req, res) => {
  const event = req.body.event;
  const task_token = req.body.task_token;
  const status = req.body.status ? JSON.parse(req.body.status) : {};
  const payload = req.body.payload ? JSON.parse(req.body.payload) : null;

  if (event === 'saved' && status.error === 0) {
    const urls = (status.videos || []).map(v => v.url);
    console.log(`Job ${task_token} done:`, urls, 'payload:', payload);
  }
  res.send('OK');
});

app.listen(3000);
```

## Callback delivery reliability

If your endpoint is unreachable or returns non-2xx, the job adds a **warning** (see `assets/recipes/reliability.md`):

```json
"warnings": [
  {
    "message": "Callback delivery error",
    "details": "Error sending callback to https://yourserver.com/qencode_callback 500: Internal Server Error."
  }
]
```

The job itself still completes; you can recover by polling `/v1/status` with the task_token. Treat callbacks as a fast-path notification, not the only source of truth — keep a polling fallback for missed webhooks.

## Schema pointers

- `start_encode2.query.callback_url` — top-level webhook URL
- `start_encode2.query.use_subtask_callback` — top-level, 0/1; per-rendition events
- `start_encode2.payload` — top-level (not inside `query`); opaque user data echoed back in callbacks
- `status.returns.status` — the full status object inside the callback's `status` field (after URL-decoding and JSON-parsing)

See also: `assets/recipes/reliability.md` (callback delivery warnings, `retry_on_error` restart events), `assets/recipes/refresh_abr_playlist.md` (per-rendition callbacks during ABR encoding), `assets/recipes/incremental_abr.md` (multi-job chains).

## Gotchas

- **`Content-Type` is form-encoded**, not JSON. Use your framework's form parser, then `JSON.parse` the `status` and `payload` fields.
- **`payload` is at the top of the request body**, not inside `query`. Easy to miss.
- **Callback errors don't fail the job** — they show up as warnings. Always keep a polling fallback.
- **Idempotency**: Qencode may resend the same event. Use `task_token` + `event` as a dedup key in your handler.
- **HTTP/HTTPS**: either works. HTTPS strongly recommended in production.
- **Endpoint visibility**: Qencode must be able to reach your URL from the public internet. Localhost / private VPC endpoints won't receive callbacks — use a public ingress (e.g., your edge load balancer, ngrok for dev).
