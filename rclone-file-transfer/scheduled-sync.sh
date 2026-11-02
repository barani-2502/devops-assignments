#!/usr/bin/env bash
# Run by cron, which has no environment, so the S3 settings are loaded here.
cd "$(dirname "$0")" || exit 1
set -a; source ./.env; set +a
export RCLONE_S3_PROVIDER=Minio
export RCLONE_S3_ENDPOINT=http://localhost:9100
export RCLONE_S3_ACCESS_KEY_ID=$MINIO_ROOT_USER
export RCLONE_S3_SECRET_ACCESS_KEY=$MINIO_ROOT_PASSWORD
./transfer.sh sync "$HOME/rclone-lab/v-src" :s3:bucket-b/scheduled
