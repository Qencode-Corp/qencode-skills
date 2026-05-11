#!/usr/bin/env python3
"""Raw-HTTP fallback for the Qencode Transcoding API.

Used by the qencode-transcode and qencode-job-status skills when no MCP server
is connected. Talks to https://api.qencode.com directly using a project API key
loaded from the QENCODE_API_KEY environment variable.

Subcommands:

  submit         Submit a transcoding job. Reads the {"query": ...} JSON from
                 stdin or --query-file. Prints task_token + status_url as JSON.

  status         Fetch status for a task token. Prints the status entry as JSON.

  wait           Poll status until terminal or timeout. Prints the final
                 status entry as JSON. Uses an exponential backoff (5s → 60s).

All subcommands print structured JSON to stdout on success. On failure they
exit non-zero with a one-line error to stderr.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

API_BASE = os.environ.get("QENCODE_API_BASE", "https://api.qencode.com")
TERMINAL_STATUSES = {"completed", "error", "failed"}


def _die(msg: str, code: int = 1) -> "no_return":  # type: ignore[valid-type]
    print(msg, file=sys.stderr)
    sys.exit(code)


def _post(path: str, fields: dict[str, str]) -> dict:
    url = f"{API_BASE}{path}"
    body = urllib.parse.urlencode(fields).encode()
    last_exc: Exception | None = None
    # Single retry — Qencode edge occasionally drops the connection mid-request.
    for attempt in range(2):
        req = urllib.request.Request(url, data=body, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
                break
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode())
            except Exception:
                _die(f"HTTP {e.code} from {path}: {e.reason}")
            break
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            last_exc = e
            if attempt == 1:
                _die(f"connection error calling {path}: {e}")
            time.sleep(0.5)
    code = payload.get("error", 0)
    if code != 0:
        msg = payload.get("message") or payload.get("error_description") or "unknown error"
        _die(f"Qencode error {code} from {path}: {msg}")
    return payload


def _require_api_key() -> str:
    key = os.environ.get("QENCODE_API_KEY")
    if not key:
        _die("QENCODE_API_KEY is not set. Export it or use the MCP path instead.")
    return key


def _session_token() -> str:
    return _post("/v1/access_token", {"api_key": _require_api_key()})["token"]


def _create_task(token: str) -> dict:
    return _post("/v1/create_task", {"token": token})


def _start_encode2(token: str, task_token: str, query: dict, payload: str | None) -> dict:
    # Ensure the double-wrap. start_encode2 requires {"query": {...}}.
    if not (isinstance(query, dict) and "query" in query and isinstance(query["query"], dict)):
        query = {"query": query}
    data = {"task_token": task_token, "query": json.dumps(query)}
    if payload is not None:
        data["payload"] = payload
    return _post("/v1/start_encode2", data)


def cmd_submit(args: argparse.Namespace) -> None:
    raw = sys.stdin.read() if args.query_file is None else open(args.query_file).read()
    if not raw.strip():
        _die("submit: empty query JSON on stdin")
    try:
        query = json.loads(raw)
    except json.JSONDecodeError as e:
        _die(f"submit: invalid JSON: {e}")
    token = _session_token()
    task = _create_task(token)
    started = _start_encode2(token, task["task_token"], query, args.payload)
    print(json.dumps({
        "task_token": task["task_token"],
        "status_url": started.get("status_url"),
        "upload_url": task.get("upload_url"),
    }, indent=2))


def _status_for(task_token: str) -> dict:
    body = _post("/v1/status", {"task_tokens": task_token})
    statuses = body.get("statuses") or {}
    return statuses.get(task_token, body)


def cmd_status(args: argparse.Namespace) -> None:
    # /v1/status accepts the api_key-derived session token but the public docs
    # show task_tokens is enough; we use the token + task_token shape for
    # symmetry with the MCP path.
    print(json.dumps(_status_for(args.task_token), indent=2))


def cmd_wait(args: argparse.Namespace) -> None:
    deadline = time.monotonic() + args.timeout
    interval = 5.0
    last: dict = {}
    while True:
        last = _status_for(args.task_token)
        st = last.get("status")
        if st in TERMINAL_STATUSES or last.get("error"):
            break
        if time.monotonic() >= deadline:
            break
        time.sleep(min(interval, max(0.0, deadline - time.monotonic())))
        # Exponential backoff capped at 60s — see gotchas.md §8.
        interval = min(interval * 1.5, 60.0)
    print(json.dumps(last, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(prog="http_fallback.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_submit = sub.add_parser("submit", help="submit a job (reads query JSON from stdin or --query-file)")
    p_submit.add_argument("--query-file", help="path to a JSON file with the query (otherwise stdin)")
    p_submit.add_argument("--payload", help="optional opaque payload string")
    p_submit.set_defaults(func=cmd_submit)

    p_status = sub.add_parser("status", help="fetch status for a task token")
    p_status.add_argument("task_token")
    p_status.set_defaults(func=cmd_status)

    p_wait = sub.add_parser("wait", help="poll status until terminal or timeout")
    p_wait.add_argument("task_token")
    p_wait.add_argument("--timeout", type=float, default=600.0, help="max seconds to wait (default 600)")
    p_wait.set_defaults(func=cmd_wait)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
