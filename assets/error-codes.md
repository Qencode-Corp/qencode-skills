# Qencode Transcoding API — Error Codes

> **Stub** — populated in M4. The `qencode-troubleshoot` skill reads this file to map error codes returned in `/v1/status` responses (or in the `error` / `error_description` fields) to likely causes and fixes.

## Format

Each entry follows this shape:

```
### Error N — short title
**Returned by:** /v1/<endpoint> (where it appears)
**Likely cause:** ...
**How to fix:** ...
**Related:** other error codes that often appear together
```

## Known codes (seed list — expand in M4)

### Error 19 — query field is required
**Returned by:** `/v1/start_encode2`
**Likely cause:** the `query` form field was sent as `{...inner...}` instead of `{"query": {...inner...}}`. See `gotchas.md` §1.
**How to fix:** wrap the transcoding parameters in an outer `{"query": ...}` object before submitting.

### Error 1 — invalid api_key
**Returned by:** `/v1/access_token`
**Likely cause:** API key is wrong, revoked, or belongs to a project that's been deleted.
**How to fix:** confirm the key in https://portal.qencode.com/project/my_projects ; rotate if needed.

### Error 2 — token expired
**Returned by:** any endpoint that takes `token`
**Likely cause:** the session token from `/v1/access_token` aged out (default ~24h).
**How to fix:** call `/v1/access_token` again with your `api_key` and retry.

<!-- Add more codes as they're observed in the wild. -->
