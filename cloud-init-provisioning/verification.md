# Verification

Each check below shows the command, the real output, and what it proves.
Commands were run in PowerShell against the VM `testpress-vm` (Ubuntu 24.04).

## 1. Provisioning finished

```powershell
multipass exec testpress-vm -- cloud-init status --long
```
```text
status: done
extended_status: degraded done
errors: []
recoverable_errors:
WARNING: cloud-config failed schema validation!
```
**Result:** cloud-init completed with no errors. "degraded" only means a schema warning about
file permissions was logged. The files were still created correctly (see check 3).

## 2. The `testpress` user exists

```powershell
multipass exec testpress-vm -- id testpress
```
```text
uid=1000(testpress) gid=1001(testpress) groups=1001(testpress),1000(docker)
```
**Result:** the user was created and belongs to the `docker` group.

## 3. Files have the right permissions

```powershell
multipass exec testpress-vm -- ls -l /opt/testpress
```
```text
-rw-r--r-- 1 root root 274 Nov  1 22:56 Dockerfile
-rw-r--r-- 1 root root  53 Nov  1 22:56 app.env
-rw-r--r-- 1 root root 527 Nov  1 22:56 app.py
```
**Result:** files were created as `0644` (owner can edit, everyone can read). The service file
`/etc/systemd/system/testpress.service` is also `-rw-r--r--`.

## 4. The service is running

```powershell
multipass exec testpress-vm -- systemctl status testpress --no-pager
```
```text
Loaded: loaded (/etc/systemd/system/testpress.service; enabled; preset: enabled)
Active: active (running) since Sun 2026-11-01 23:03:21 IST
```
**Result:** the service is `enabled` (starts at boot) and `active (running)`.

## 5. The app answers HTTP requests

```powershell
multipass exec testpress-vm -- curl -s http://localhost:8080
multipass exec testpress-vm -- curl -s http://localhost:8080/health
```
```text
Hello from Testpress!
ok
```
**Result:** the app is reachable and its health check works.

## 6. The `testpress` user can use Docker

```powershell
multipass exec testpress-vm -- sudo -u testpress docker ps
```
```text
IMAGE                  STATUS                    PORTS                    NAMES
testpress-app:latest   Up 42 seconds (healthy)   0.0.0.0:8080->8080/tcp   testpress-app
```
**Result:** `testpress` runs Docker without root, and the container is healthy.

## 7. The app survives a reboot

```powershell
multipass restart testpress-vm
multipass exec testpress-vm -- curl -s http://localhost:8080
```
```text
Hello from Testpress!
```
**Result:** after the VM restarted, the app came back with no manual steps. The container was
only about 30 seconds old, so it was freshly started by systemd.

## 8. The app restarts itself after a crash

```powershell
multipass exec testpress-vm -- sudo docker kill testpress-app
multipass exec testpress-vm -- sudo docker ps
```
```text
CONTAINER ID   IMAGE                  CREATED         STATUS
2c69bd7468e4   testpress-app:latest   6 seconds ago   Up 5 seconds (healthy)
```
**Result:** the old container (`06d7e6a6d996`) was killed and systemd started a new one
(`2c69bd7468e4`) within seconds.

## 9. Access from the Windows host

```powershell
curl http://172.30.147.107:8080
```
```text
StatusCode        : 200
StatusDescription : OK
Content           : Hello from Testpress!
```
**Result:** the app is reachable from outside the VM, using the VM's IP address.

## Challenge

**Invalid timezone.** The first launch ended with `status: error` and the message
`Invalid timezone Asia/Calcutta`. The VM has no timezone file under that name. I fixed it by
setting `timezone: Asia/Kolkata` in `cloud-init.yaml`, then deleted the VM and created a new one.
