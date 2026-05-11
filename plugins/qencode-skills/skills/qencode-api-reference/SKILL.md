---
name: qencode-api-reference
description: Use when the user asks what a Qencode Transcoding API attribute means, what values it accepts, where it lives in the query structure, what its default is, or whether it's required. Examples — "what does `resize_mode` do?", "is `keyframe` required?", "what values does `output` accept?", "where do I put `framerate` for HLS?", "what's the difference between `width` and `resolution`?". Reads the generated schema index/digest and applies the project's composition defaults.
version: 0.1.0
---

# qencode-api-reference

You answer lookup questions about the Qencode Transcoding API schema. Concise, factual, with the attribute's full path in the `query` tree and a recommendation if the project has one.

## Sources, in priority order

1. **`${CLAUDE_PLUGIN_ROOT}/assets/schema-index.json`** — flat dictionary keyed by attribute path (e.g. `start_encode2.query.format[].destination.permissions`). Each value has `type`, `required`, `description`, `parent`. **Use this first** for fast lookup, especially when the attribute name is unique.

2. **`${CLAUDE_PLUGIN_ROOT}/assets/schema-digest.md`** — full per-endpoint markdown with hierarchical context. Read the relevant section when you need surrounding context or when the attribute appears under multiple parents (e.g. `destination` exists everywhere).

3. **`${CLAUDE_PLUGIN_ROOT}/assets/best-practices.md`** — composition defaults the project recommends. **Always cross-check.** Several common attributes have project-recommended values that override the schema's default (audio codec, encoder version, etc.).

4. **`${CLAUDE_PLUGIN_ROOT}/assets/gotchas.md`** — non-obvious quirks worth surfacing if the attribute has one.

5. **`${CLAUDE_PLUGIN_ROOT}/assets/storage.md`** — for any `destination.*` attribute, this has per-provider compatibility info beyond what the schema says.

## How to answer

Match this shape:

> **`<full.path>`** — `<type>` · <required: yes/no>
>
> <one-paragraph summary from the schema, paraphrased>
>
> **Default:** <value or "—">
> **Project recommendation:** <if best-practices has one; otherwise omit>
> **Notes:** <gotchas / storage-compat / cross-references as bullets, only if relevant>

Keep it scannable. If the user asked about *multiple* attributes or asked an open-ended question ("what affects HLS chunking?"), produce a short table or a tight bulleted list instead.

## Resolution rules

- **Unique attribute name** (e.g. `pix_format`, `cenc_drm`, `optimize_bitrate`) → one `schema-index.json` lookup is enough.
- **Name appears under multiple parents** (e.g. `destination`, `bitrate`, `framerate`) → list each location separately, because the *applicable* rules differ. For example, `framerate` on a stream entry vs on a format block has different ABR implications — both are valid placements but only one is correct for HLS/DASH.
- **Project recommendation supersedes schema default.** If `best-practices.md` says "always X" but the schema documents the field-level default as "Y", lead with X and mention Y as the bare-schema default.
- **`destination.*` attributes**: always include the per-provider compatibility from `storage.md`. The schema's "For S3 only" wording for `permissions` is misleading — call this out.

## Examples of good answers

### Q: "What does `resize_mode` do?"

> **`start_encode2.query.format[].resize_mode`** — string · not required
>
> Controls how the output frame is fitted to the target dimensions when source and target aspect ratios differ. `scale` (default) stretches the source to fill the target. `crop` preserves the source aspect ratio — either cropping pixels or adding black bars depending on the dimensions.
>
> **Default:** `"scale"`
> **Notes:**
> - Only matters when you've also set `width` AND `height` (or `size`) explicitly. If you only set `resolution`, source aspect is preserved automatically and `resize_mode` is moot.

### Q: "What values does `output` accept?"

> **`start_encode2.query.format[].output`** — string · required
>
> Selects the output media format. Each value drives different packaging, file count, and downstream behavior.
>
> **Accepted values:** `mp4`, `webm`, `advanced_hls`, `advanced_dash`, `webm_dash`, `repack`, `mp3`, `hls_audio`, `flac`, `gif`, `thumbnail`, `thumbnails`, `metadata`, `speech_to_text`, `vmaf`
> **Notes:**
> - Use `advanced_hls` / `advanced_dash`, not the legacy `hls` / `dash` packagers.
> - `thumbnail` (singular) = one image; `thumbnails` (plural) = a series or sprite sheet.
> - `vmaf` requires `encoder_version: 1` — the only common case where the project's default of v2 doesn't apply.

### Q: "Where do I put framerate for HLS?"

> **For ABR outputs (`advanced_hls`, `advanced_dash`), put `framerate` on each `stream[]` entry**, not on the format block. The schema's `format[].framerate` description states explicitly "For HLS or DASH output specify this parameter on stream object level."
>
> **Pair with `keyframe`** on each stream so segments cut on keyframe boundaries — `keyframe` should divide `framerate × segment_duration` cleanly (common: `framerate: "30"`, `keyframe: "60"`, `segment_duration: 6` → 3 GOPs per segment).
>
> See `best-practices.md` §7 for the full list of stream-level vs format-level params.

## What NOT to do

- Don't compose a `query` JSON — that's `qencode-build-query`'s job. If the user wants a working query, hand off.
- Don't invent attributes. If `schema-index.json` doesn't have it, say so — it may be removed, renamed, or never have existed.
- Don't quote raw HTML from the schema source — the digest has already been stripped.
- Don't include endpoint-level boilerplate when answering attribute questions. Keep it tight.
