# Commands Used

S3 commands use `:s3:`, a remote built from the environment variables in README.md.
`--config /dev/null` gives rclone an empty config file, so nothing depends on `rclone.conf`.

## 1. Local files

```bash
rclone ls source
```
Lists every file with its size.

```bash
rclone copy source dest-a --progress
```
Copies files that are missing or changed. Running it again sends nothing.

```bash
rclone check source dest-a
```
Compares two locations and reports differences. Changes nothing.

```bash
rclone move move-src dest-b
```
Copies files to the destination, then deletes them from the source.

```bash
rclone sync source dest-b --dry-run
rclone sync source dest-b
```
Makes `dest-b` identical to `source`, including **deleting** extra files. `--dry-run` only prints
what would happen, so it is always run first.

```bash
rclone delete dest-b/folder2
```
Deletes the files inside that folder, in the destination only.

## 2. S3 on MinIO

```bash
rclone --config /dev/null mkdir :s3:bucket-b
rclone --config /dev/null lsd :s3:
```
Creates a bucket, then lists all buckets.

```bash
rclone --config /dev/null copy source :s3:demo-bucket --progress
rclone --config /dev/null ls :s3:demo-bucket
```
Uploads a folder, then lists the objects.

```bash
rclone --config /dev/null copy :s3:demo-bucket downloaded
```
Downloads a bucket into a local folder.

```bash
rclone --config /dev/null copy :s3:demo-bucket :s3:bucket-b
```
Copies from one bucket to another.

```bash
rclone --config /dev/null delete :s3:bucket-b/folder2
```
Deletes objects under `folder2/`.

## 3. Without a config file

```bash
rclone --config /dev/null lsd ":s3,provider=Minio,endpoint='http://localhost:9100',access_key_id=$MINIO_ROOT_USER,secret_access_key=$MINIO_ROOT_PASSWORD:"
```
Defines the whole remote inside the command, between the colons.

```bash
rclone --config /dev/null lsd :s3: --s3-provider Minio --s3-endpoint http://localhost:9100 \
  --s3-access-key-id "$MINIO_ROOT_USER" --s3-secret-access-key "$MINIO_ROOT_PASSWORD"
```
The same settings passed as flags.

```bash
RCLONE_S3_ACCESS_KEY_ID=wrong-user rclone --config /dev/null lsd :s3:
```
Overrides one variable for this single command only.

## 4. Large files and failures

```bash
rclone --config /dev/null copy big :s3:demo-bucket/big --progress --transfers 2 --s3-upload-concurrency 4
```
Uploads a 1 GB file. `--transfers` is how many files go at once, `--s3-upload-concurrency` is how
many parts of one big file go at once.

```bash
rclone --config /dev/null copy source/large-100mb.bin :s3:bucket-b/bw-test --bwlimit 20M --progress
```
Limits the speed to 20 MiB/s.

```bash
RCLONE_S3_ENDPOINT=http://localhost:9999 rclone --config /dev/null lsd :s3: --retries 3 --low-level-retries 2
```
Points at a port where nothing runs, to watch the retries.

```bash
rclone --config /dev/null copy interrupt-test :s3:demo-bucket/interrupt-test --transfers 1 --bwlimit 50M --progress -v
```
A slow upload of five 200 MB files. It was stopped with Ctrl + C halfway and then run again.


## 5. Other features

```bash
rclone --config /dev/null copy enda:demo-bucket/big endb:target-bucket/big -v
```
Copies between two different MinIO servers. `enda:` and `endb:` are remotes defined with
`RCLONE_CONFIG_ENDA_*` and `RCLONE_CONFIG_ENDB_*` environment variables, so no config file is needed.

```bash
rclone --config /dev/null mount :s3:demo-bucket ~/rclone-lab/mnt --vfs-cache-mode writes --daemon
fusermount3 -u ~/rclone-lab/mnt
```
Shows a bucket as a normal folder, then unmounts it.

```bash
read -rs -p "Choose a crypt password: " CRYPT_PASSWORD
export RCLONE_CONFIG_SECRET_TYPE=crypt RCLONE_CONFIG_SECRET_REMOTE=":s3:bucket-b/encrypted"
export RCLONE_CONFIG_SECRET_PASSWORD=$(printf %s "$CRYPT_PASSWORD" | rclone obscure -)
rclone --config /dev/null copy source/folder1 secret:
```
Creates an encrypting remote called `secret:`. `read -rs` keeps the password out of the screen and
history. Files copied to `secret:` are stored encrypted in `bucket-b/encrypted`.

```bash
* * * * * /home/baranitp/practice/devops/rclone-file-transfer/scheduled-sync.sh >> ~/rclone-lab/cron.log 2>&1
```
A cron line that runs the sync every minute. Cron starts with an empty environment, so
`scheduled-sync.sh` loads the S3 settings and then calls `transfer.sh`.

```bash
python3 run_rclone.py ~/rclone-lab/source :s3:bucket-b/python-test
```
Runs rclone from Python with `subprocess`. The command is a list (no shell), and the S3 settings
are passed as environment variables.
