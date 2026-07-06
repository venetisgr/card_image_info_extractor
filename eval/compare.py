"""Compare an extractor output against a ground-truth label, field by field.

Lightweight P1-era eval (stdlib only) — the full harness lands in Phase 5.

Usage:
    python eval/compare.py extracted.json data/labels/<card_id>.json
"""

import json
import sys
from pathlib import Path

# Fields not part of extraction accuracy.
IGNORED = {"per_field_confidence", "provenance", "raw_output"}


def flatten(obj, prefix=""):
    """Flatten nested dicts/lists into dot-path -> scalar."""
    out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in IGNORED and not prefix:
                continue
            out.update(flatten(value, f"{prefix}{key}."))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            out.update(flatten(value, f"{prefix}{i}."))
        if not obj:
            out[prefix.rstrip(".")] = []
    else:
        out[prefix.rstrip(".")] = obj
    return out


def norm(value):
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def main(extracted_path: str, label_path: str) -> int:
    extracted = flatten(json.loads(Path(extracted_path).read_text()))
    label = flatten(json.loads(Path(label_path).read_text()))

    keys = sorted(set(extracted) | set(label))
    matches, mismatches, label_nulls = [], [], 0
    for key in keys:
        got, want = extracted.get(key), label.get(key)
        if want is None:
            label_nulls += 1  # ground truth unknown -> not scored
            continue
        if norm(got) == norm(want):
            matches.append(key)
        else:
            mismatches.append((key, got, want))

    scored = len(matches) + len(mismatches)
    print(f"scored fields: {scored}  |  match: {len(matches)}  |  "
          f"mismatch: {len(mismatches)}  |  unscored (GT null): {label_nulls}")
    if scored:
        print(f"field accuracy: {len(matches) / scored:.1%}")
    for key, got, want in mismatches:
        print(f"  MISMATCH {key}: got {got!r}, expected {want!r}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
