#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/dist"
PACKAGE_DIR="$ARTIFACT_DIR/lambda_package"

rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

pip install -r "$ROOT_DIR/requirements.txt" -t "$PACKAGE_DIR"
cp -r "$ROOT_DIR/src/otimizador" "$PACKAGE_DIR/"

(cd "$PACKAGE_DIR" && zip -r "$ARTIFACT_DIR/otimizador-lambda.zip" .)

echo "Artifact: $ARTIFACT_DIR/otimizador-lambda.zip"
