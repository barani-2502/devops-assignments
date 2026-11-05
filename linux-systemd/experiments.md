# Experiments

All experiments were run in an Ubuntu 24.04 Multipass VM (`testpress-vm`).

---

## 1. Running process

**Action**

```bash
python3 heartbeat.py > heartbeat.log 2>&1 &
pgrep -a python3
ps -o pid,ppid,stat,etime,cmd -p $(pgrep -f heartbeat.py)
tail -n 3 heartbeat.log
```

**Expectation** A Python process with a PID, running in the background and printing a heartbeat.

**Observation** `pgrep` showed one process, PID 90377. `ps` showed parent PID 89412 (my shell), state `S`, running for 30 seconds. The log got a new line every 5 seconds.

**Explanation** Every process gets a PID from the kernel. `&` runs it in the background. State `S` means "sleeping": the program spends most of its time waiting in `sleep(5)`. The parent PID is my bash shell, which started it.

Screenshot: `evidence/01-running-process.png`

Before this I also tested Ctrl+C on the plain script: Python turned SIGINT into a `KeyboardInterrupt` error and exited with code 130.

---

## 2. Graceful shutdown (SIGTERM)

**Action**

```bash
python3 app.py > app.log 2>&1 &
APP_PID=$!
sleep 12
kill -15 $APP_PID; wait $APP_PID; echo "exit code: $?"
cat app.log
```

**Expectation** SIGTERM is a polite request. Because `app.py` has a handler, it should log a message, finish, and exit normally.

**Observation** The log shows `Received SIGTERM, shutting down gracefully`, then `stopped cleanly after 3 heartbeats`. Exit code was 0. The goodbye line came a few seconds after the signal, because the program finishes its 5-second sleep first.

**Explanation** SIGTERM can be caught. The handler sets a flag, the loop ends, and the program exits with 0. The exit code 0 is the app's own choice. Without a handler, SIGTERM would just kill the process (code 143), as the plain heartbeat script showed.

Screenshot: `evidence/02-graceful-shutdown.png`

---

## 3. Forced termination (SIGKILL)

**Action**

```bash
python3 app.py > app.log 2>&1 &
APP_PID=$!
sleep 12
kill -9 $APP_PID; wait $APP_PID; echo "exit code: $?"
cat app.log
```

**Expectation** SIGKILL cannot be handled, so the process dies at once with no goodbye message.

**Observation** The shell printed `Killed` and the exit code was 137 (PID 92941). The log stops at Heartbeat 3 with no "Received" line and no "stopped cleanly" line.

**Explanation** SIGKILL never reaches the program. The kernel removes the process directly, so no handler runs and nothing is cleaned up. 137 = 128 + 9.

| | SIGTERM (15) | SIGKILL (9) |
|---|---|---|
| Can the app catch it? | Yes | No |
| Cleanup runs? | Yes | No |
| Exit code here | 0 (app's choice) | 137 |

Screenshot: `evidence/03-forced-termination.png`

---

## 4. systemd service

**Action**

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin testpress-worker
# install app.py, the .env file and the .service file (see README)
systemd-analyze verify /etc/systemd/system/testpress-worker.service
sudo systemctl daemon-reload
sudo systemctl enable --now testpress-worker
systemctl status testpress-worker --no-pager
ps -o user,pid,ppid,cmd -u testpress-worker
journalctl -u testpress-worker -n 6 --no-pager
```

**Expectation** The service runs as the new non-root user, starts at boot, and its logs appear in journald.

**Observation** Status showed `enabled` and `active (running)`, Main PID 93467. `ps` showed the process owned by `testpress-worker` (the name is cut to `testpre+` by `ps`), with parent PID 1. Heartbeats appeared in the journal. The CGroup line was `/system.slice/testpress-worker.service`.

**Explanation** `enable` links the service into `multi-user.target`. `User=` makes systemd drop root before starting the program. The parent is PID 1 (systemd), so systemd sees when it dies. Each service gets its own cgroup, which is used later for resource limits.

Screenshot: `evidence/04-systemd-service.png`

---

## 5. Automatic restart after SIGKILL

**Action**

```bash
OLD=$(systemctl show -p MainPID --value testpress-worker)
sudo kill -9 $OLD
sleep 7
NEW=$(systemctl show -p MainPID --value testpress-worker)
journalctl -u testpress-worker -n 12 --no-pager
```

**Expectation** systemd notices the process died and starts a new one with a different PID.

**Observation** PID before: 93467. PID after: 93632. The journal showed:

- `Main process exited, code=killed, status=9/KILL` at 06:08:02
- `Failed with result 'signal'`
- `Scheduled restart job, restart counter is at 1` at 06:08:07
- `Started testpress-worker.service`

**Explanation** Being killed by a signal counts as a failure, so `Restart=on-failure` applies. systemd waited `RestartSec` (5 seconds at that time: 06:08:02 to 06:08:07) and started a new process. The new PID proves it is a new process.

Screenshot: `evidence/05-automatic-restart.png`

---

## 6. Crash investigation (non-zero exit)

**Action**

```bash
sudo sed -i 's/^CRASH_AFTER_BEATS=.*/CRASH_AFTER_BEATS=3/; s/^CRASH_EXIT_CODE=.*/CRASH_EXIT_CODE=3/' /etc/testpress-worker.env
sudo systemctl restart testpress-worker
journalctl -u testpress-worker -n 20 --no-pager
systemctl show testpress-worker -p NRestarts -p Result -p ExecMainStatus
journalctl -u testpress-worker -p err --no-pager
```

**Expectation** The app exits with code 3 after 3 heartbeats, and systemd restarts it again and again.

**Observation** The journal showed `[ERROR] Simulated crash after 3 heartbeats, exit code 3`, then `Main process exited, code=exited, status=3/NOTIMPLEMENTED`, then `Failed with result 'exit-code'`, then `Scheduled restart job` with the counter going 1, 2, and so on. This repeated about every 15 seconds. `NRestarts` showed 8, because it also counted the restart from Experiment 5. `Result=success` and `ExecMainStatus=0` were shown because a fresh process was running at that moment. `journalctl -p err` printed `-- No entries --`.

**Explanation** This time the app chose to exit, so the journal says `code=exited`. In Experiment 5 it said `code=killed`. That is how to tell a crash from a kill. `NOTIMPLEMENTED` is only systemd's label for the number 3. `-p err` found nothing because the app's lines are logged at normal priority, so the plain journal (`journalctl -u ...`) is the right place to look. When investigating a crash loop: read the journal, check the exit code, check `NRestarts`, then look at the settings.

Screenshot: `evidence/06-crash-investigation.png`

---

## 7. Invalid executable path

**Action**

```bash
sudo sed -i 's|^ExecStart=.*|ExecStart=/usr/bin/python3-wrong /opt/testpress-worker/app.py|' /etc/systemd/system/testpress-worker.service
sudo systemctl daemon-reload
sudo systemctl start testpress-worker
systemctl status testpress-worker --no-pager -l
journalctl -u testpress-worker -n 10 --no-pager
```

**Expectation** The program cannot start, so no heartbeats appear and the service fails.

**Observation** Status showed `activating (auto-restart)` and `ExecStart=/usr/bin/python3-wrong ... (code=exited, status=203/EXEC)`. The journal repeated `Failed to start ...` and there were no heartbeat lines. The restart counter was already high (19, 20) because the crash loop from Experiment 6 was never reset.

**Explanation** Code 203/EXEC means systemd could not run the program at all, so the app never started. With `Type=exec`, systemd reports this failure immediately. A failed start still counts as a failure, so `Restart=on-failure` kept retrying.

Screenshot: `evidence/07-invalid-configuration.png`

---

## 8. Repeated crashes and restart rate limiting

**Action**

```bash
# added to [Unit]: StartLimitIntervalSec=60 and StartLimitBurst=3
# changed RestartSec to 2, set CRASH_AFTER_BEATS=1
sudo systemctl daemon-reload
sudo systemctl reset-failed testpress-worker
sudo systemctl start testpress-worker
systemctl status testpress-worker --no-pager -l
journalctl -u testpress-worker -n 20 --no-pager
```

**Expectation** After a few quick crashes systemd should give up and not retry forever.

**Observation** The app started and crashed three times (06:24:43, 06:24:46, 06:24:48). Then the journal said `Start request repeated too quickly.` and `Failed to start`. The restart counter stopped at 3 and the status was `Active: failed`. The status said `Result: exit-code` and not `start-limit-hit`.

**Explanation** systemd allows 3 starts in 60 seconds (`StartLimitBurst=3`, `StartLimitIntervalSec=60`). The next request is refused. The service stays failed until a person fixes the problem and runs `systemctl reset-failed`. This is the opposite of an infinite retry loop: failures stay visible. The message `Start request repeated too quickly` is the proof of rate limiting.

Screenshot: `evidence/08-repeated-crashes.png`

---

## 9. Resource limits

**Action**

```bash
# added to [Service]: MemoryMax=50M, MemorySwapMax=0, CPUQuota=50%
# set LEAK_MB_PER_BEAT=20 in the env file
sudo systemctl daemon-reload
sudo systemctl restart testpress-worker
systemctl show testpress-worker -p MemoryMax -p MemorySwapMax -p CPUQuotaPerSecUSec
journalctl -u testpress-worker -n 15 --no-pager
```

**Expectation** Each heartbeat the app holds 20 MB more. With a 50 MB limit it should be killed on the third heartbeat (60 MB).

**Observation** `MemoryMax=52428800` (50 MB), `MemorySwapMax=0`, `CPUQuotaPerSecUSec=500ms`. The log showed `Holding 20 MB`, then `Holding 40 MB`, then Heartbeat 3. Then the process was killed: `Main process exited, code=killed, status=9/KILL`, `Failed with result 'signal'`. The log ends with no shutdown message. After that, the start limit from Experiment 8 stopped further restarts (`Start request repeated too quickly`).

**Explanation** systemd turns `MemoryMax` into a cgroup memory limit. When the service goes over it, the kernel kills the process with SIGKILL, so the app's handler never runs. `CPUQuota=50%` does not kill anything: it only slows the process down.

<!-- OOM-KILLER LINE: if the check below printed a kernel line like
"Memory cgroup out of memory: Killed process ... (python3)", paste it here and add it to the screenshot.
If it printed nothing, delete this comment and leave the paragraph above as it is.
Command: journalctl -b -1 -k --no-pager | grep -i -E "oom|killed process" -->

Screenshot: `evidence/09-resource-limits.png`

---

## 10. Reboot persistence

**Action**

```bash
systemctl is-enabled testpress-worker
uptime -s
sudo reboot
# reconnect after about a minute
uptime -s; who -b; uptime -p
systemctl status testpress-worker --no-pager
systemctl show testpress-worker -p ActiveEnterTimestamp -p NRestarts
```

**Expectation** The service starts by itself after the reboot, without `systemctl start`.

**Observation** `who -b` showed boot at 2026-11-05 06:34 and `uptime -p` showed "up 0 minutes". The service was `active (running)` since 06:34:08 with a new PID (747) and `NRestarts=0`. The status also showed `Memory: ... (max: 50.0M swap max: 0B ...)`, so the limits survived the reboot. The leak setting was back at 0.

**Explanation** `systemctl enable` created a symlink in `multi-user.target`. At boot, systemd starts everything linked there. `NRestarts=0` means it was a fresh start, not a crash restart.

Screenshot: `evidence/10-reboot-persistence.png`

---

## Answers to the Questions

### What is the difference between SIGTERM and SIGKILL?
- **SIGTERM** asks a program to stop. The program can catch it, save its work and exit cleanly.
- **SIGKILL** forces the program to stop. It cannot be caught, so no cleanup happens.
- `systemctl stop` sends SIGTERM first. If the program is still running after 90 seconds (the default `TimeoutStopSec`), systemd sends SIGKILL.

### Why doesn't nohup provide the same reliability as systemd?
- `nohup` only keeps a program running after the terminal is closed.
- It does not restart the program if it crashes, start it after a reboot, limit its resources, or keep its logs.
- systemd does all of these.

### What happens when a service crashes repeatedly?
- systemd restarts it after the `RestartSec` delay.
- If it crashes more than `StartLimitBurst` times within `StartLimitIntervalSec`, systemd stops trying and shows `Start request repeated too quickly`.
- The service stays failed until someone fixes the problem and runs `systemctl reset-failed`.

### What is the difference between restarting a process and restarting a service?
- Restarting a process means running the program again by hand.
- Restarting a service (`systemctl restart`) stops it properly, then starts it again with the same user, settings and limits, and records everything in the logs.

### What happens to child processes when a systemd service is stopped?
- systemd keeps all processes of a service together in one group (a cgroup).
- When the service stops, systemd signals every process in the group, not just the main one. This is the default `KillMode=control-group`.

### How would you ensure a Celery worker finishes its current task before shutting down?
- Celery finishes its running tasks when it receives SIGTERM (called a "warm shutdown").
- systemd sends SIGTERM by default when stopping a service.
- Set `TimeoutStopSec` long enough for the longest task. Otherwise systemd sends SIGKILL and the task is cut off.
