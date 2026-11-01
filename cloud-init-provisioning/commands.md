# Commands Used

All commands run in Windows PowerShell. Multipass creates and manages the VM.

`multipass exec testpress-vm -- <command>` runs a Linux command **inside** the VM.
It is used in most commands below.

## 1. Install Multipass

```powershell
winget install Canonical.Multipass
```
Installs Multipass, the tool that creates Ubuntu VMs.

```powershell
multipass get local.driver
```
Shows which virtualization engine Multipass uses. Result: `hyperv`.

## 2. Create the VM

```powershell
multipass launch 24.04 --name testpress-vm --cpus 2 --memory 4G --disk 15G `
  --cloud-init "<path to cloud-init.yaml>"
```
Creates an Ubuntu 24.04 VM named `testpress-vm`. The `--cloud-init` option hands it our YAML,
so the VM configures itself on first boot. Adding `--timeout 1200` gives it more time to finish.

## 3. Check that provisioning worked

```powershell
multipass exec testpress-vm -- cloud-init status --wait
```
Waits until cloud-init finishes and prints the result. We want `status: done`.

```powershell
multipass exec testpress-vm -- cloud-init status --long
```
Same check with details, including any errors and warnings.

## 4. Find out why something failed

```powershell
multipass exec testpress-vm -- sudo cloud-init schema --system
```
Checks the YAML for format mistakes. This is how the permissions warning was found.

```powershell
multipass exec testpress-vm -- sudo tail -n 80 /var/log/cloud-init-output.log
```
Shows the last 80 lines of what cloud-init did. This is where the timezone error was found.

## 5. Verify the server

```powershell
multipass exec testpress-vm -- id testpress
```
Shows the `testpress` user and its groups. We want `docker` in the list.

```powershell
multipass exec testpress-vm -- ls -l /opt/testpress
```
Lists the files cloud-init created, with their permissions. We want `-rw-r--r--` (0644).

```powershell
multipass exec testpress-vm -- systemctl status testpress --no-pager
```
Shows whether the app's systemd service is enabled and running.

```powershell
multipass exec testpress-vm -- curl -s http://localhost:8080
multipass exec testpress-vm -- curl -s http://localhost:8080/health
```
Sends HTTP requests to the app. Results: `Hello from Testpress!` and `ok`.

```powershell
multipass exec testpress-vm -- sudo -u testpress docker ps
```
Lists running containers as the `testpress` user. This proves that user can use Docker.
(Plain `docker ps` is denied because the default `ubuntu` user is not in the `docker` group.)

## 6. Reboot and crash recovery

```powershell
multipass restart testpress-vm
```
Reboots the VM. After a short wait, the `curl` check should work again with no manual steps.

```powershell
multipass exec testpress-vm -- sudo docker kill testpress-app
```
Kills the app container on purpose. systemd should start a new one within seconds.

## 7. Clean up

```powershell
multipass delete testpress-vm
multipass purge
```
Deletes the VM and frees its disk space, so a fresh VM can be created from the YAML.
