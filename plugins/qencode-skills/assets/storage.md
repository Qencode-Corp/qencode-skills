# Qencode Transcoding API — Output Storage

Canonical reference for where Qencode writes encoded outputs. Recipes and `best-practices.md` defer to this file. When composing a `query`, consult this doc to pick a `destination` shape.

The `destination` field lives on each entry of `query.format[]`. It can be omitted, set to a single object, or set to an array of objects (fan-out).

## Default: 24-hour temporary Qencode storage

If `destination` is **omitted entirely** for a given format, the output lands in Qencode's temporary storage and is **deleted ~24 hours after the job completes**. The download URL appears in the `/v1/status` response under `statuses[token].videos[]`, `audios[]`, `images[]`, `texts[]`.

Use this for:
- Quick conversions where the user just wants a downloadable link
- One-off previews and demos

**Never** use it for production — files vanish. Whenever you emit a recipe without a `destination`, **explicitly tell the user about the 24-hour expiry**.

The schema's `destination.message` field documents this directly: *"If you don't specify destination, your output will be available to download from our servers during 24 hours."*

## Supported storage prefixes

The `destination.url` prefix selects the backend:

| Prefix | Storage type | Notes |
|---|---|---|
| `s3://` | Any S3-compatible (Qencode S3, AWS S3, Google Cloud Storage, Cloudflare R2, DigitalOcean Spaces, Backblaze B2 via S3-compat endpoint, etc.) | Most common |
| `b2://` | Backblaze B2 (native API) | Use `s3://` instead if you want one config for B2 + others |
| `azblob://` | Azure Blob Storage | |
| `ftp://` / `ftps://` | FTP server (TLS optional) | Use `is_passive`, `use_tls`, `tcp_port` |
| `sftp://` | FTP over SSH | Use `tcp_port` |

## Path vs folder semantics by output type

The `url` value is interpreted differently depending on `format[].output`:

| Output type | `url` should be |
|---|---|
| `mp4`, `webm`, `mp3`, `flac`, `gif`, `thumbnail`, `vmaf` | full path **including filename and extension** |
| `advanced_hls`, `advanced_dash`, `webm_dash` | path to a **folder** (master playlist + segments land underneath) |
| `thumbnails` | path to a **folder** (multiple images + `.vtt` land here) |
| `speech_to_text` | path to a **folder** (transcript + subtitles files) |
| `metadata` | full path including filename |

## Per-param compatibility matrix

Not every `destination` param works for every backend. Including unsupported params can fail the upload step.

| Param | Qencode S3 | AWS S3 | Cloudflare R2 | DO Spaces / GCS / other s3:// | Backblaze B2 (b2://) | Azure Blob | FTP / SFTP |
|---|---|---|---|---|---|---|---|
| `key` | omit | required | required | required | required | required (storage account) | required (username) |
| `secret` | omit | required | required | required | required | required | required (password) |
| `permissions` | unsupported | supported | unsupported | supported | unsupported | n/a | n/a |
| `storage_class` | unsupported | AWS-only | unsupported | unsupported | unsupported | n/a | n/a |
| `cache_control` | supported | supported | supported | supported | supported | supported | n/a |
| `is_passive` | n/a | n/a | n/a | n/a | n/a | n/a | FTP only |
| `use_tls` | n/a | n/a | n/a | n/a | n/a | n/a | FTP only |
| `tcp_port` | n/a | n/a | n/a | n/a | n/a | n/a | supported |
| `udp_port` | n/a | n/a | n/a | n/a | n/a | n/a | rare |

> The schema describes `permissions` as "For S3 only" — that wording is misleading. It works on most S3-compatible backends but **not** Qencode S3 or Cloudflare R2.

## Examples per provider

### Qencode-managed S3 (recommended default for Qencode customers)

```json
"destination": {
  "url": "s3://us-west.s3.qencode.com/yourbucket/output.mp4"
}
```

No credentials needed — Qencode S3 is authenticated implicitly via the project that owns the API key. No `permissions`, no `storage_class`.

### AWS S3

```json
"destination": {
  "url": "s3://us-east-1.amazonaws.com/yourbucket/output.mp4",
  "key": "AKIA...",
  "secret": "...",
  "permissions": "public-read",
  "storage_class": "STANDARD"
}
```

`permissions` accepts AWS canned ACLs: `private`, `public-read`, `authenticated-read`, `bucket-owner-read`, etc. `storage_class` accepts `STANDARD`, `REDUCED_REDUNDANCY`, `STANDARD_IA`, `ONEZONE_IA`, `INTELLIGENT_TIERING`, `GLACIER`, `DEEP_ARCHIVE`.

### Cloudflare R2

```json
"destination": {
  "url": "s3://<account-id>.r2.cloudflarestorage.com/yourbucket/output.mp4",
  "key": "...",
  "secret": "..."
}
```

R2 uses the S3-compatible API but rejects `permissions` and `storage_class`. Object visibility is controlled at the bucket level in the Cloudflare dashboard.

### DigitalOcean Spaces (and other generic S3-compatible)

```json
"destination": {
  "url": "s3://nyc3.digitaloceanspaces.com/yourspace/output.mp4",
  "key": "...",
  "secret": "...",
  "permissions": "public-read"
}
```

### Backblaze B2 (native)

```json
"destination": {
  "url": "b2://yourbucket/output.mp4",
  "key": "...",
  "secret": "..."
}
```

You can also use Backblaze via `s3://` with their S3-compatible endpoint — pick whichever your tooling already authenticates against.

### Azure Blob Storage

```json
"destination": {
  "url": "azblob://yourcontainer/output.mp4",
  "key": "yourstorageaccount",
  "secret": "..."
}
```

### FTP

```json
"destination": {
  "url": "ftp://ftp.example.com/path/output.mp4",
  "key": "username",
  "secret": "password",
  "is_passive": 1,
  "use_tls": 0,
  "tcp_port": 21
}
```

### FTPS (FTP over TLS)

```json
"destination": {
  "url": "ftps://ftp.example.com/path/output.mp4",
  "key": "username",
  "secret": "password",
  "is_passive": 1,
  "use_tls": 1,
  "tcp_port": 990
}
```

### SFTP

```json
"destination": {
  "url": "sftp://example.com/path/output.mp4",
  "key": "username",
  "secret": "password",
  "tcp_port": 22
}
```

## Fan-out: multiple destinations for one output

`destination` is `object or array of objects`. Pass an array to copy the encoded asset to several places at once — useful for cross-region replication, primary + backup, or vendor diversification.

```json
"destination": [
  { "url": "s3://us-west.s3.qencode.com/primary/output.mp4" },
  {
    "url": "s3://us-east-1.amazonaws.com/backup/output.mp4",
    "key": "AKIA...",
    "secret": "...",
    "permissions": "private"
  }
]
```

Every destination in the array receives the same bytes. Different destinations can use different providers and different param sets — each is validated independently.

## CDN-friendly headers (`cache_control`)

Set browser/CDN cache TTLs at upload time (avoids a per-object PUT after encoding):

```json
"destination": {
  "url": "s3://us-west.s3.qencode.com/yourbucket/output.mp4",
  "cache_control": "public, max-age=31536000, immutable"
}
```

Common patterns:
- HLS/DASH manifests: `"public, max-age=10"` (short TTL — playlists update)
- HLS/DASH segments and MP4 outputs: `"public, max-age=31536000, immutable"` (segments are content-addressed; never change)
- Private content: `"private, no-store"`

## Schema pointers

Read in `assets/schema-digest.md`:
- `start_encode2.query.format[].destination` — destination object
- `start_encode2.query.format[].destination.url` — prefix list and path-vs-folder rules
- `start_encode2.query.format[].destination.cache_control` — full directive reference

## When to consult this doc

The `qencode-build-query` and `qencode-transcode` skills should read this file (or the relevant per-provider section) any time the user mentions:
- where outputs should land
- a specific cloud provider (AWS, R2, B2, Azure, GCS, DigitalOcean, …)
- public-vs-private access, ACLs, storage class
- cache headers / CDN settings
- copying to multiple buckets / regions
