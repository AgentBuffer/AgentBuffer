#!/usr/bin/env bash
set -euo pipefail

# Generate TypeScript types from Pydantic models
# Requires: pip install datamodel-code-generator

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_FILE="$ROOT_DIR/services/shared/models.py"
OUTPUT_DIR="$ROOT_DIR/apps/web/lib/types"

mkdir -p "$OUTPUT_DIR"

datamodel-codegen \
  --input "$MODELS_FILE" \
  --input-file-type python \
  --output "$OUTPUT_DIR/models.ts" \
  --output-model-type typescript \
  --target-python-version 3.12

echo "Generated TypeScript types at $OUTPUT_DIR/models.ts"
