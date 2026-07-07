"""Compare an extractor output against a ground-truth label, field by field.

Lightweight P1-era eval (stdlib only) — the full harness lands in Phase 5.

Scoring rules (v2, after the 2026-07-06 real-photo run):
- Free-text transcription fields (label_text, description) are scored FUZZY:
  token-set Jaccard >= 0.8 counts as a match — word order and spacing of a
  faithful transcription must not read as an extraction error.
- Color words are compared through small equivalence classes (navy~blue,
  gold~yellow, wine~maroon~burgundy): shade naming is not an extraction error.
- Ground-truth null = unscored (GT convention: labels encode image-visible
  truth; see data/README.md).

Usage:
    python eval/compare.py extracted.json data/labels/<card_id>.json
"""

import json
import re
import sys
from pathlib import Path

IGNORED = {"per_field_confidence", "provenance", "raw_output"}
FUZZY_FIELDS = {"graded.label_text", "graded.description", "graded.grade_label"}
FUZZY_THRESHOLD = 0.8
COLOR_CLASSES = [
    {"navy", "blue", "dark blue"},
    {"gold", "yellow"},
    {"wine", "maroon", "burgundy", "dark red"},
    {"grey", "gray", "silver"},
    {"red", "crimson", "scarlet"},
]


def flatten(obj, prefix=""):
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


def colors_equivalent(a, b) -> bool:
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    a, b = norm(a), norm(b)
    return any(a in cls and b in cls for cls in COLOR_CLASSES)


def token_set_similarity(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-z0-9']+", a.lower()))
    tb = set(re.findall(r"[a-z0-9']+", b.lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def values_match(key: str, got, want) -> bool:
    if norm(got) == norm(want):
        return True
    if key in FUZZY_FIELDS and isinstance(got, str) and isinstance(want, str):
        return token_set_similarity(got, want) >= FUZZY_THRESHOLD
    if ".colors." in key or key.endswith("jersey_colors") or ".jersey_colors." in key:
        return colors_equivalent(got, want)
    return False


def main(extracted_path: str, label_path: str) -> int:
    extracted = flatten(json.loads(Path(extracted_path).read_text()))
    label = flatten(json.loads(Path(label_path).read_text()))

    keys = sorted(set(extracted) | set(label))
    matches, mismatches, label_nulls = [], [], 0
    for key in keys:
        got, want = extracted.get(key), label.get(key)
        if want is None:
            label_nulls += 1
            continue
        if values_match(key, got, want):
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
