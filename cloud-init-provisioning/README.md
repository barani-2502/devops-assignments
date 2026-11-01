# Assignment 1: Server Provisioning with cloud-init

A new Ubuntu 24.04 VM sets itself up from one file, `cloud-init.yaml`. After the first boot it has
Docker installed, a `testpress` user, and a small web app running in a container. Nothing is
configured by hand on the VM.

The VM is created with Multipass on Windows. The project files are managed from WSL.

## Files

- `cloud-init.yaml`: the configuration the VM reads on first boot
- `commands.md`: the important commands, with what each one does
- `verification.md`: proof that it works, and the problem faced along the way

## What cloud-init.yaml sets up

| Part of the YAML | What it does |
|---|---|
| `timezone` | Sets the clock to India time (`Asia/Kolkata`) |
| `packages` | Installs Docker, Git, curl and FFmpeg |
| `users` | Creates the `testpress` user and adds it to the `docker` group |
| `write_files` | Creates the app, its settings, a Dockerfile and a systemd service file |
| `runcmd` | Starts Docker and the app service |

The app is a tiny Python web server. `/` replies `Hello from Testpress!` and `/health` replies `ok`.
It runs in a Docker container, and systemd (Linux's service manager) restarts it if it stops
and starts it at every boot.

## How cloud-init works

On boot, cloud-init runs through four stages:

1. **Local:** finds the configuration it was given (our YAML).
2. **Network:** after the network is up, creates users and writes the files.
3. **Config:** sets the timezone and installs packages.
4. **Final:** runs the last commands, which start Docker and the app.

## Idempotency

Idempotent means running something again gives the same result, with no duplicates or damage.

Cloud-init does its setup only on a VM's first boot. When the VM reboots, it sees the work is
already done and skips it, so nothing is installed or created twice. The app still comes back
after a reboot because systemd starts it automatically.

One consequence: editing the YAML does not change a VM that already exists. To test a change,
delete the VM and create a new one.
