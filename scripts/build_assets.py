#!/usr/bin/env python3
"""Generate schema-digest.md and schema-index.json from the docs repo's transcoding.json.

Reads <docs>/src/data/api/transcoding.json and emits:
  - assets/schema-digest.md  — compact, LLM-friendly per-endpoint markdown
  - assets/schema-index.json — path-keyed JSON index for attribute lookup

Path resolution order for the docs repo:
  1. --docs-path CLI argument
  2. QENCODE_DOCS_PATH environment variable
  3. fail with a clear message
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
SCHEMA_REL_PATH = Path("src/data/api/transcoding.json")

TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def resolve_docs_path(cli_path: str | None) -> Path:
    raw = cli_path or os.environ.get("QENCODE_DOCS_PATH")
    if not raw:
        sys.exit(
            "error: docs path not provided.\n"
            "  pass --docs-path /path/to/docs_getsby5\n"
            "  or set QENCODE_DOCS_PATH=/path/to/docs_getsby5"
        )
    docs = Path(raw).expanduser().resolve()
    schema = docs / SCHEMA_REL_PATH
    if not schema.is_file():
        sys.exit(f"error: schema not found at {schema}")
    return docs


def short_desc(attr: dict) -> str:
    return strip_html(attr.get("short_description") or attr.get("description"))


def full_desc(attr: dict) -> str:
    return strip_html(attr.get("description") or attr.get("short_description"))


def is_array_of_objects(dt: str | None) -> bool:
    """True only for strict 'array of objects'. Polymorphic types like
    'object or array of objects' are addressed without the [] suffix
    because the children paths are the same in both shapes and users
    expect e.g. `destination.permissions`, not `destination[].permissions`."""
    if not dt:
        return False
    dl = dt.lower().strip()
    return dl.startswith("array of object")


def child_path(parent: str, attr: dict, parent_is_array: bool) -> str:
    suffix = "[]" if parent_is_array else ""
    return f"{parent}{suffix}.{attr['name']}"


def walk_attributes(parent_path: str, parent_dt: str | None, attrs: list[dict], index: dict) -> list[dict]:
    """Flatten a tree of attributes into a list of {path, type, required, desc, ...}."""
    flat = []
    parent_is_array = is_array_of_objects(parent_dt)
    for a in attrs or []:
        path = child_path(parent_path, a, parent_is_array)
        entry = {
            "path": path,
            "type": a.get("data_type") or "",
            "required": bool(a.get("required")),
            "short": short_desc(a),
            "full": full_desc(a),
            "parent": parent_path,
        }
        flat.append(entry)
        index[path] = {
            "type": entry["type"],
            "required": entry["required"],
            "description": entry["full"],
            "parent": entry["parent"],
        }
        if a.get("attributes"):
            flat.extend(walk_attributes(path, a.get("data_type"), a["attributes"], index))
    return flat


def render_attr_table(rows: list[dict], show_parent: bool = False) -> str:
    if not rows:
        return "_(no attributes)_\n"
    if show_parent:
        out = ["| Path | Type | Req | Description |", "|---|---|---|---|"]
        for r in rows:
            out.append(
                f"| `{r['path']}` | {r['type'] or '—'} | "
                f"{'yes' if r['required'] else 'no'} | "
                f"{r['short'] or '—'} |"
            )
    else:
        out = ["| Name | Type | Req | Description |", "|---|---|---|---|"]
        for r in rows:
            name = r["path"].rsplit(".", 1)[-1]
            out.append(
                f"| `{name}` | {r['type'] or '—'} | "
                f"{'yes' if r['required'] else 'no'} | "
                f"{r['short'] or '—'} |"
            )
    return "\n".join(out) + "\n"


def render_endpoint_args(
    args: list[dict],
    parent_path: str,
    index: dict,
    input_objects: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Returns (markdown, deferred_subtrees).

    For json-typed args whose nested schema lives in `input_objects` rather than
    on the arg itself, we merge the matching input_object's attributes into the
    deferred subtree so the digest renders the full nested schema.
    """
    input_by_name = {io["name"]: io for io in (input_objects or [])}
    rows = []
    deferred = []
    for a in args or []:
        path = f"{parent_path}.{a['name']}"
        # If a matching input_object exists, treat its attributes as the arg's nested schema
        merged = dict(a)
        io = input_by_name.get(a["name"])
        if io and io.get("attributes") and not merged.get("attributes"):
            merged["attributes"] = io["attributes"]
            if not merged.get("description") and io.get("description"):
                merged["description"] = io["description"]
        index[path] = {
            "type": merged.get("data_type") or "",
            "required": bool(merged.get("required")),
            "description": full_desc(merged),
            "parent": parent_path,
        }
        rows.append({
            "path": path,
            "type": merged.get("data_type") or "",
            "required": bool(merged.get("required")),
            "short": short_desc(merged),
            "full": full_desc(merged),
        })
        if merged.get("attributes"):
            deferred.append({"path": path, "attr": merged})
    return render_attr_table(rows), deferred


def render_subtree(path: str, attr: dict, index: dict, depth: int = 3) -> str:
    """Recursively render a section for an attribute that has nested attributes."""
    out = []
    heading = "#" * depth
    dt = attr.get("data_type") or ""
    out.append(f"{heading} `{path}`  \n_type: {dt or '—'}_\n")
    if attr.get("short_description"):
        out.append(f"{short_desc(attr)}\n")
    flat = walk_attributes(path, dt, attr.get("attributes", []), index)
    direct = [r for r in flat if r["parent"] == path or r["parent"] == path + ("[]" if is_array_of_objects(dt) else "")]
    out.append(render_attr_table(direct))
    further = [r for r in flat if r not in direct]
    seen = set()
    for r in further:
        if r["parent"] in seen:
            continue
        seen.add(r["parent"])
    nested_attrs = [a for a in attr.get("attributes", []) if a.get("attributes")]
    for child in nested_attrs:
        cpath = child_path(path, child, is_array_of_objects(dt))
        out.append("\n" + render_subtree(cpath, child, index, depth=depth + 1))
    return "\n".join(out)


def render_returns(
    returns: list[dict],
    parent_path: str,
    index: dict,
    output_objects: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Returns (markdown, deferred_subtrees) for return fields, mirroring args."""
    if not returns:
        return "_(no return fields documented)_\n", []
    output_by_name = {oo["name"]: oo for oo in (output_objects or [])}
    rows = []
    deferred = []
    for r in returns:
        path = f"{parent_path}.{r['name']}"
        merged = dict(r)
        oo = output_by_name.get(r["name"])
        if oo and oo.get("attributes") and not merged.get("attributes"):
            merged["attributes"] = oo["attributes"]
        index[path] = {
            "type": merged.get("data_type") or "",
            "required": False,
            "description": full_desc(merged),
            "parent": parent_path,
        }
        rows.append({
            "path": path,
            "type": merged.get("data_type") or "",
            "required": False,
            "short": short_desc(merged),
            "full": full_desc(merged),
        })
        if merged.get("attributes"):
            deferred.append({"path": path, "attr": merged})
    return render_attr_table(rows), deferred


def build(docs_path: Path) -> tuple[str, dict]:
    schema_raw = (docs_path / SCHEMA_REL_PATH).read_bytes()
    schema = json.loads(schema_raw)
    source_hash = hashlib.sha256(schema_raw).hexdigest()[:12]
    index: dict = {}
    out = []
    out.append("# Qencode Transcoding API — Schema Digest")
    out.append("")
    out.append(f"_Generated from `{SCHEMA_REL_PATH}` (source sha256 prefix `{source_hash}`). Do not edit by hand — run `scripts/build_assets.py`._")
    out.append("")
    out.append("Endpoints (in call order):")
    out.append("")
    for ep in schema["content"]:
        method = ep.get("method", "")
        ver = ep.get("version", "")
        name = ep["name"]
        out.append(f"- [`{method} /{ver}/{name}`](#{name}) — {strip_html(ep.get('description',''))[:120].rstrip()}…")
    out.append("")
    out.append("---")
    out.append("")

    for ep in schema["content"]:
        method = ep.get("method", "")
        ver = ep.get("version", "")
        name = ep["name"]
        out.append(f"## `{method} /{ver}/{name}` <a id=\"{name}\"></a>")
        out.append("")
        out.append(strip_html(ep.get("description", "")))
        out.append("")
        out.append("**Arguments:**\n")
        ep_path = f"{name}"
        args_md, deferred = render_endpoint_args(
            ep.get("method_arguments", []),
            ep_path,
            index,
            input_objects=ep.get("input_objects", []),
        )
        out.append(args_md)

        # Special-case start_encode2: render full query subtree
        for d in deferred:
            out.append("")
            out.append(render_subtree(d["path"], d["attr"], index, depth=3))

        # Returns
        if ep.get("return_object"):
            out.append("")
            out.append("**Returns:**\n")
            ret_md, ret_deferred = render_returns(
                ep["return_object"],
                ep_path + ".returns",
                index,
                output_objects=ep.get("output_objects", []),
            )
            out.append(ret_md)
            for d in ret_deferred:
                out.append("")
                out.append(render_subtree(d["path"], d["attr"], index, depth=3))

            # Render any output_objects whose name didn't match a return field
            matched = {r["name"] for r in ep["return_object"]}
            for oo in ep.get("output_objects", []):
                if oo["name"] in matched:
                    continue
                if not oo.get("attributes"):
                    continue
                oo_path = ep_path + f".returns.{oo['name']}"
                out.append("")
                out.append(f"**`{oo['name']}` object** (referenced by returns above):\n")
                out.append(render_subtree(oo_path, oo, index, depth=3))

        out.append("")
        out.append("---")
        out.append("")

    return "\n".join(out), index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-path", help="path to docs_getsby5 checkout (overrides QENCODE_DOCS_PATH)")
    ap.add_argument("--check", action="store_true", help="exit non-zero if regeneration would change committed assets")
    args = ap.parse_args()

    docs_path = resolve_docs_path(args.docs_path)
    digest_md, index = build(docs_path)

    ASSETS_DIR.mkdir(exist_ok=True)
    digest_file = ASSETS_DIR / "schema-digest.md"
    index_file = ASSETS_DIR / "schema-index.json"

    if args.check:
        cur_md = digest_file.read_text() if digest_file.exists() else ""
        cur_idx = index_file.read_text() if index_file.exists() else ""
        new_idx = json.dumps(index, indent=2, sort_keys=True) + "\n"
        if cur_md != digest_md or cur_idx != new_idx:
            sys.exit("schema assets are stale — re-run scripts/build_assets.py and commit")
        print("schema assets are up to date")
        return

    digest_file.write_text(digest_md)
    index_file.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(f"wrote {digest_file.relative_to(REPO_ROOT)} ({len(digest_md):,} bytes)")
    print(f"wrote {index_file.relative_to(REPO_ROOT)} ({len(index):,} entries)")


if __name__ == "__main__":
    main()
