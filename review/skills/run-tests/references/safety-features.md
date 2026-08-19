## Safety Features

Guarantees the runner enforces. Read the caveats — several controls are
best-effort and OS-dependent, not hard sandboxing.

### Enforced
- ✅ **Wall-clock timeout** — each run wrapped in `timeout` (10 min tests,
  5 min dependency install); process killed when it expires.
- ✅ **Isolated workspace** — code checked out into a fresh `mktemp -d`
  dir; cleaned up after the run.
- ✅ **Dangerous-pattern denylist** — test command grepped for a small set
  of destructive patterns (`rm -rf`, `dd if=`, `mkfs`, `ssh`, privileged Docker,
  production URLs). **Defense-in-depth only**, not a real sandbox: a
  denylist cannot catch every dangerous command, so never rely on it alone.

### Best-effort (OS-dependent, not guaranteed)
- ⚠️ **Memory limit (`ulimit -v`, ~2GB)** — soft per-process address-space
  cap. Varies by platform, does not bound child processes reliably.
- ⚠️ **Single-file size limit (`ulimit -f`, ~1GB)** — limits size of any one
  file written, **not** total disk usage. No portable total-disk cap exists.

### Not enforced
- ❌ **Network isolation** — attempted via `unshare --net` on Linux (needs
  privileges/namespaces), **skipped entirely on macOS**. Do not assume tests
  run without network access; only production-URL patterns in the command are
  blocked, and the workload may still make outbound connections.
- ❌ **CPU-core / CPU-seconds limit** — not set; wall-clock `timeout` is the only
  time bound.
