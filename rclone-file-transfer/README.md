# Assignment 2: File Transfers with rclone

Moving files between local folders and S3-compatible storage (MinIO in Docker) using rclone.

## Files

- `docker-compose.yml`: starts two MinIO servers (ports 9100 and 9200, the second one is for the two-endpoint bonus)
- `transfer.sh`: reusable copy/sync script
- `scheduled-sync.sh`: wrapper that cron runs every minute
- `run_rclone.py`: runs rclone from Python
- `commands.md`: the important commands, with what each one does
- `results.md`: what happened in each experiment, and answers to the demo questions

## Setup

**1. Install rclone**

```bash
curl https://rclone.org/install.sh | sudo bash
```

**2. Start MinIO** (Docker Desktop must be running)

```bash
# create a file named .env with MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, SECOND_USER and SECOND_PASSWORD
docker compose up -d
```


**3. Give rclone the connection through environment variables**

```bash
set -a; source .env; set +a
export RCLONE_S3_PROVIDER=Minio
export RCLONE_S3_ENDPOINT=http://localhost:9100
export RCLONE_S3_ACCESS_KEY_ID=$MINIO_ROOT_USER
export RCLONE_S3_SECRET_ACCESS_KEY=$MINIO_ROOT_PASSWORD
```

These only exist in the current terminal. After this, `:s3:` works as a remote.

## Using transfer.sh

```bash
./transfer.sh <copy|sync> <source> <destination> [extra rclone flags]
./transfer.sh copy ~/rclone-lab/source :s3:bucket-b/backup
```

The script shows progress, writes `transfer.log`, and exits with 0 on success, 2 for wrong
arguments, 127 if rclone is missing, and rclone's own code otherwise.

