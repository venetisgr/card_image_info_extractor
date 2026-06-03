#!/usr/bin/env bash
# Regenerate the Pydantic (backend) and Kotlin (android) types from the CardInfo
# JSON Schema. The JSON Schema is the single source of truth.
#
# Prerequisites:
#   Python: pip install "datamodel-code-generator[http]" pydantic   (use a venv)
#   Kotlin: Node.js available (npx fetches quicktype on demand)
#
# Usage: bash shared/codegen/generate.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCHEMA="$ROOT/shared/schema/card_info.schema.json"

echo "Source schema: $SCHEMA"

# --- Pydantic v2 (Python / backend) ---
datamodel-codegen \
  --input "$SCHEMA" \
  --input-file-type jsonschema \
  --output "$ROOT/backend/app/models/card_info.py" \
  --output-model-type pydantic_v2.BaseModel \
  --class-name CardInfo \
  --target-python-version 3.11 \
  --use-standard-collections \
  --use-union-operator \
  --use-annotated \
  --field-constraints \
  --use-schema-description \
  --use-field-description \
  --disable-timestamp \
  --collapse-root-models \
  --formatters black isort
echo "  -> backend/app/models/card_info.py"

# --- Kotlin / kotlinx.serialization (Android) ---
mkdir -p "$ROOT/android/app/src/main/java/com/cardextractor/model"
npx --yes quicktype \
  --src "$SCHEMA" \
  --src-lang schema \
  --lang kotlin \
  --framework kotlinx \
  --package com.cardextractor.model \
  --top-level CardInfo \
  --out "$ROOT/android/app/src/main/java/com/cardextractor/model/CardInfo.kt"
echo "  -> android/app/src/main/java/com/cardextractor/model/CardInfo.kt"

echo "Done."
