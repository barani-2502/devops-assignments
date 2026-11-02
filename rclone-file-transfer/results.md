# Results

## 1. Copy twice

```bash
rclone copy source dest-a --progress
rclone copy source dest-a --progress
```
```text
First run:   Transferred: 5 / 5, 100 MiB
Second run:  Transferred: 0 B / 0 B     Checks: 5 / 5
```
**Result:** the second run sends nothing. rclone checks each file and skips it.

## 2. copy, move and sync

| Command | File already at the destination | File only at the destination | Source afterwards |
|---|---|---|---|
| `copy` | Skipped if identical | Left alone | Unchanged |
| `move` | Skipped if identical | Left alone | Files are removed |
| `sync` | Skipped if identical | **Deleted** | Unchanged |

**Result for `move`:** on a throwaway copy, both files arrived in `dest-b` and the source folder
was gone afterwards (listing it gave `directory not found`).

## 3. Sync deletes extra files

`dest-b` had three files that were not in `source`.

```bash
rclone sync source dest-b --dry-run
```
```text
NOTICE: extra.txt: Skipped delete as --dry-run is set
NOTICE: file2.txt: Skipped delete as --dry-run is set
NOTICE: subfolder/file3.txt: Skipped delete as --dry-run is set
Deleted: 3 (files), 1 (dirs)
```
**Result:** the dry run listed the deletions and changed nothing. The real `sync` then removed
those files, and `rclone check` reported `0 differences found`.

**Why sync is dangerous:** it deletes anything in the destination that the source does not
have. If the two folders are typed in the wrong order, it deletes from the folder you meant to
keep. Always run `--dry-run` first.

## 4. How rclone decides what to send

```bash
rclone check v-src v-dst
rclone sync v-src v-dst --dry-run --size-only
```
```text
a.txt: md5 differ        (a.txt has new content, same size)
--size-only: a.txt was not copied
```
**Result:** by default rclone compares size and modification time, which noticed the change.
`--size-only` compares only the size, so it missed it. `rclone check` compares content and found it.

## 5. S3 on MinIO

```text
Upload to demo-bucket:       5 / 5 files, 0.7 s
Download + rclone check:     0 differences found, 5 matching files
Bucket to bucket copy:       Server Side Copies: 5 @ 100.000 MiB
Delete folder2/ in bucket-b: bucket-b has 4 files, demo-bucket still has 5
```
**Result:** upload, download, listing, copy and delete all work. The bucket-to-bucket copy
happened inside MinIO, so the data never came down to this machine.

## 6. Between two different S3 servers

A second MinIO ran on port 9200 with its own login.

```text
Transferred: 1 GiB / 1 GiB, 66.999 MiB/s, 15.4 s
check: 0 differences found
```
**Result:** the 1 GB file arrived intact. The output had no `Server Side Copies` line, unlike the
copy between two buckets on one server, so the data passed through this machine.

## 7. No config file

| Method | Result |
|---|---|
| Environment variables | Worked |
| Inline `:s3,...:` | Worked |
| Command-line flags | Worked |
| Wrong key on one command | `403 InvalidAccessKeyId`. The next command worked again |

```bash
ps auxww | grep "[r]clone"     # while an inline-credentials upload was running
```
**Result:** the secret key was visible in the process list.

**Recommendation: environment variables.** Flags and inline settings put the secret on the
command line, where `ps` shows it. Variables stay out of the command line.

## 8. Large file and speed limit

```text
1 GB upload:          6.9 s at about 141 MiB/s, check: 0 differences found
100 MB, --bwlimit 20M: 5.5 s at 20 MiB/s  (without a limit: 0.6 s)
```
**Result:** the limit holds the speed at exactly 20 MiB/s.

## 9. Retries and interrupted upload

```text
Dead port, --low-level-retries 2:
  connection refused ... exceeded maximum number of attempts, 2
```
**Result:** rclone gave up with an error and did not hang.

Five 200 MB files were uploaded and stopped with Ctrl + C while `part3.bin` was at 16%.

```text
Bucket after the interruption:   part1.bin, part2.bin
After running the same command:  Checks: 2 / 2 (skipped), Transferred: 3 / 3 (part3, 4, 5)
Final check:                     0 differences found, 5 matching files
```
**Result:** finished files were skipped. The file that was cut off was not visible in the bucket
and was sent again from the beginning.

## 10. rclone mount

```text
ls mnt        ->  big  file1.txt  folder1  folder2 ...
cat mnt/file1.txt  ->  This text belongs to source/file1.txt
echo ... > mnt/mount-test.txt   ->  mount-test.txt (40 bytes) appeared in the bucket
```
**Result:** the bucket worked as a normal folder, for reading and writing. Writes needed
`--vfs-cache-mode writes`. It is not a real disk, so it depends on rclone staying running and on FUSE.

## 11. Encryption (crypt)

```text
ls :s3:bucket-b/encrypted   ->  104 naj4u7u2agvovupc3fnbh10m9k/4c0mvhqdl3bjj9q488ni3om9no
                                 94 sog6020bv4hurivalrhd4aoja0
ls secret:                  ->  56 subfolder/file3.txt
                                46 file2.txt
cat secret:file2.txt        ->  This text belongs to source/folder1/file2.txt
```
**Result:** the storage holds scrambled names and content, and each file is 48 bytes bigger than
the original. Through `secret:` the files read back normally.

## 12. Scheduled sync with cron

```text
07:00:07 START mode=sync ... destination=:s3:bucket-b/scheduled
07:00:07 SUCCESS mode=sync
ls :s3:bucket-b/scheduled  ->  a.txt, c.txt, d.txt, e.txt
```
**Result:** cron ran `transfer.sh` by itself within a minute, and the files were in the bucket.
The cron line was removed afterwards.

## Answers to the demo questions

1. **`copy` run twice?** The second run sends nothing, because the files are already the same.
2. **A file only at the destination during `sync`?** It is deleted.
3. **How does rclone decide to transfer?** By size and modification time by default. `--size-only`
   uses only size, and `rclone check` compares content.
4. **Between two S3 providers without downloading?** On the same server, yes: a server-side copy,
   as seen in the bucket-to-bucket copy. Between different servers the data normally passes
   through the machine running rclone. The two-server test confirmed this.
5. **Connection drops halfway through a 1 GB upload?** The unfinished object does not appear in
   the bucket. Running the same command again sends it from the beginning and skips files that
   were already complete.
6. **rclone from a Celery worker without `rclone.conf`?** Pass the S3 settings to the subprocess as
   environment variables, use `:s3:` with `--config /dev/null`, and call rclone with a list of
   arguments. Never put the secret in the command line.
