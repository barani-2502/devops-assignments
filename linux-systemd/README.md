# Linux Process Management & systemd

A small Python service that prints a heartbeat every 5 seconds and is managed by systemd.
systemd starts it at boot, restarts it if it crashes, and sends its logs to journald.

Tested on Ubuntu 24.04 (Multipass VM).

## Files

- `app.py`: the Python service
- `testpress-worker.service`: the systemd unit file
- `testpress-worker.env`: settings for the service
- `experiments.md`: all experiments with results and explanations
- `evidence/`: screenshots of the experiments

## Settings

Set in `testpress-worker.env`:

| Name | Default | Meaning |
|---|---|---|
| `WORKER_NAME` | `testpress-worker` | Name shown in logs |
| `HEARTBEAT_INTERVAL` | `5` | Seconds between heartbeats |
| `CRASH_AFTER_BEATS` | `0` | Crash after this many heartbeats (`0` = never) |
| `CRASH_EXIT_CODE` | `1` | Exit code used for the crash |
| `LEAK_MB_PER_BEAT` | `0` | Memory (MB) held per heartbeat, to test the memory limit (`0` = off) |

## Setup

Run these inside the VM, from this folder:

```bash
# 1. Create a user that cannot log in
sudo useradd --system --no-create-home --shell /usr/sbin/nologin testpress-worker

# 2. Install the app
sudo mkdir -p /opt/testpress-worker
sudo cp app.py /opt/testpress-worker/app.py

# 3. Install the settings and the service file
sudo cp testpress-worker.env /etc/testpress-worker.env
sudo cp testpress-worker.service /etc/systemd/system/testpress-worker.service

# 4. Load, start and enable at boot
sudo systemctl daemon-reload
sudo systemctl enable --now testpress-worker
```

## Check it

```bash
systemctl status testpress-worker --no-pager
journalctl -u testpress-worker -n 10 --no-pager
```

## Common commands

```bash
sudo systemctl start testpress-worker
sudo systemctl stop testpress-worker
sudo systemctl restart testpress-worker
sudo systemctl reset-failed testpress-worker   # after systemd gives up restarting
```

After editing the service file, run `sudo systemctl daemon-reload`.

## Experiments

See `experiments.md`.
