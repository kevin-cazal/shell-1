# Shell 101 E2E tests

Headless v86 + CTFd API end-to-end test for the full Shell 101 workshop path.

One VM session (resume from `.v86b` by default), `su - user42` after root on serial0, all 18 challenges in order without resetting the guest.

## Prerequisites

- Node.js 20+
- **V86B bundle** `shell-1-512M.v86b` (repo root or `submodules/vm-image/`) — build with [`npm run build-bundle`](../../README.md#v86b-bundle) after `doas ./build.sh` in vm-image, or download from [vm-image releases](https://github.com/kevin-cazal/vm-image-discover-linux-1/releases/latest)
- CTFd running with challenges deployed
- `npm ci` at repo root and `npm ci --prefix submodules/v86-runner`

## Start CTFd and deploy challenges

```sh
cd submodules/ctfd && docker compose --profile shell-1 up -d

export CTFD_ADMIN_TOKEN='ctfd_0cb2ccac1f05fd0d545f187bb21bed7a7a630eb974a47e6d2c76ce69f7736afa'
export GPG_PASSPHRASE='TESTING42'

python3 submodules/deploy_challenges/deploy_challenges.py \
  --no-clone . \
  --subdir challenges \
  --url http://localhost:9042/ctfd/default \
  --token "$CTFD_ADMIN_TOKEN" \
  --force
```

## Run

```sh
npm run test:e2e:shell101
```

Serial output from the guest is streamed to stdout. Progress logs go to stderr.

## Environment

| Variable | Default |
|----------|---------|
| `CTFD_URL` | `http://localhost:9042/ctfd/default` |
| `CTFD_ADMIN_TOKEN` | compose `PRESET_ADMIN_TOKEN` |
| `VM_BUNDLE` | auto-detect `shell-1-512M.v86b` |
| `E2E_COLD_BOOT` | unset — set to `1` to boot raw `.img` instead of `.v86b` |
| `VM_DISK` | used only when `E2E_COLD_BOOT=1` |
| `E2E_RESUME_TIMEOUT_MS` | `120000` (wait for root after resume) |
| `E2E_BOOT_TIMEOUT_MS` | `1500000` (cold boot only) |
| `VITE_VM_MEMORY_MB` | `512` (cold boot only; bundle carries its own RAM size) |

## Serial prompts

| Phase | Prompt |
|-------|--------|
| Root (ttyS0 autologin) | `localhost:~# ` |
| user42 after `su - user42` | `localhost:~$ ` |

## Notes

- Creates a fresh CTFd user `e2e-<timestamp>` per run; submissions use that user's token.
- Resumes from a saved state (post–`splash-ready` bundle); disk mutations persist for the run. Set `E2E_COLD_BOOT=1` for a full boot from `.img`. No VM reset between challenges.
- Command completion uses a hex-encoded sentinel (`echo <hex>|xxd -r -p`) so the marker string is not visible in the echoed command line before it runs.
- `xxd` is listed in [`submodules/vm-image/packages`](../../submodules/vm-image/packages) for new image builds; older disks fall back to `printf` if `xxd` is missing.
- Full run is much faster with `.v86b` (resume + challenge steps); cold boot adds ~15–25 min. Not wired into default CI.
