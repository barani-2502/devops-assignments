# Testpress DevOps Learning Exercises

Hands-on implementation of two DevOps exercises focused on infrastructure provisioning and file transfer automation.

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

## Development Environment

- Host OS: Windows 11 Pro
- Development environment: WSL 2 with Ubuntu 22.04
- Target VM: Ubuntu 24.04
- Version control: Git and GitHub

## Repository Structure

- `cloud-init-provisioning/` - First assignment
- `rclone-file-transfer/` - Second assignment

## Documentation

Each assignment includes setup instructions, commands, verification results, observations and learnings.

## Objective

Build reproducible, automated infrastructure and storage workflows while understanding the underlying concepts.
