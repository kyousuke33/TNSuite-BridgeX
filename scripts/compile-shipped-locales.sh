#!/usr/bin/env bash
set -euo pipefail

if (( $# != 2 )); then
  echo "Usage: compile-shipped-locales.sh <filezilla-source-root> <locale-output-root>" >&2
  exit 64
fi

SRC="$1"
OUT="$2"
MSGFMT_BIN="${MSGFMT_BIN:-/ucrt64/bin/msgfmt}"

[[ -d "$SRC/locales" ]] || { echo "ERROR: Missing FileZilla locales directory: $SRC/locales" >&2; exit 65; }
[[ -x "$MSGFMT_BIN" ]] || { echo "ERROR: msgfmt not executable: $MSGFMT_BIN" >&2; exit 66; }

mkdir -p "$OUT"
count=0
for po in "$SRC"/locales/*.po; do
  [[ -f "$po" ]] || continue
  lang="$(basename "$po" .po)"
  dest="$OUT/$lang/LC_MESSAGES"
  mkdir -p "$dest"
  "$MSGFMT_BIN" -c -o "$dest/filezilla.mo" "$po"
  [[ -s "$dest/filezilla.mo" ]] || { echo "ERROR: msgfmt produced empty catalog for $lang" >&2; exit 67; }
  ((count+=1))
done

if (( count < 1 )); then
  echo "ERROR: No shipped FileZilla .po catalogs were compiled." >&2
  exit 68
fi

echo "FILEZILLA_LOCALES_COMPILED=$count"
