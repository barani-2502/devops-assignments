#!/usr/bin/env bash
# Usage: ./transfer.sh <copy|sync> <source> <destination> [extra rclone flags]
# Example: ./transfer.sh copy ./data :s3:my-bucket/data --dry-run
#
# S3 credentials are NOT stored here. Export RCLONE_S3_PROVIDER, RCLONE_S3_ENDPOINT,
# RCLONE_S3_ACCESS_KEY_ID and RCLONE_S3_SECRET_ACCESS_KEY before running.

set -o pipefail

usage() {
  echo "Usage: $0 <copy|sync> <source> <destination> [extra rclone flags]" >&2
  exit 2
}

MODE="${1:-}"
SRC="${2:-}"
DST="${3:-}"
shift 3 2>/dev/null

if [[ "$MODE" != "copy" && "$MODE" != "sync" ]]; then usage; fi
if [[ -z "$SRC" || -z "$DST" ]]; then usage; fi

if ! command -v rclone >/dev/null 2>&1; then
  echo "rclone is not installed" >&2
  exit 127
fi

LOG_FILE="${TRANSFER_LOG:-transfer.log}"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG_FILE"
}

log "START mode=$MODE source=$SRC destination=$DST"

rclone --config /dev/null "$MODE" "$SRC" "$DST" \
  --progress \
  --retries 3 \
  --low-level-retries 5 \
  --log-file "$LOG_FILE" \
  --log-level INFO \
  "$@"
STATUS=$?

if [[ $STATUS -eq 0 ]]; then
  log "SUCCESS mode=$MODE"
else
  log "FAILED mode=$MODE exit_code=$STATUS"
fi

exit $STATUS
