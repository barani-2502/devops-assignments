# Testpress DevOps Learning Exercises

Hands-on implementation of DevOps exercises focused on infrastructure provisioning, file transfer automation, and Linux service management.

## Assignments

### 1. Automated Server Provisioning with Cloud-Init

Provision and configure an Ubuntu 24.04 virtual machine using cloud-init.

Topics:
- Automated package installation
- Linux user and permission management
- Docker installation and application deployment
- systemd service management
- Health checks and reboot verification
- Idempotency and cloud-init execution stages

### 2. File Transfers and Storage Automation with Rclone

Explore reliable file transfers using rclone and local S3-compatible storage.

Topics:
- Local file operations
- Copy, move and sync
- MinIO and S3-compatible storage
- Configuration-free S3 operations
- Large file transfers and retries
- Data integrity verification
- Bash automation

### 3. Linux Process Management and systemd

Build a Python background service and manage it with systemd, without Docker or other process managers.

Topics:
- Processes and signals (SIGTERM vs SIGKILL)
- Running a service as a dedicated non-root user
- Automatic restarts and restart rate limiting
- Failure investigation with systemctl and journalctl
- CPU and memory limits with cgroups
- Reboot persistence

## Development Environment

- Host OS: Windows 11 Pro
- Development environment: WSL 2 with Ubuntu 22.04
- Target VM: Ubuntu 24.04 (Multipass)
- Version control: Git and GitHub

## Repository Structure

- `cloud-init-provisioning/` - Server provisioning with cloud-init
- `rclone-file-transfer/` - File transfers with rclone
- `linux-systemd/` - Process management and systemd

## Documentation

Each assignment includes setup instructions, commands, verification results, observations and learnings.

