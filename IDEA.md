# Ideas / follow-ups

Deferred work for the shell-1 workshop and CTFd integration.

## Automated grading of guest livrables

Today, challenges use **static flags** in `challenges/*/private/flag.txt` (format `shell1{…}`), synced to CTFd via [deploy_challenges](submodules/deploy_challenges/README.md).

A later milestone could **verify work in the VM** instead of (or in addition to) typed flags:

| Artifact | Location | Example check |
|----------|----------|----------------|
| Livrable 101 | `/mnt/host/.delivery_101.tar` (hidden copy) | Archive exists, `tar -tf` lists expected paths from `~/101` |
| Livrable 102 | `~/data_102/answers.txt`, derived CSVs | Line counts, grep of expected flight ids |
| Finals | `all_data.csv`, `all_data_valid_ip.csv`, `all_data.tar.gz` | File presence, row counts, IP filter rules |

Possible implementations:

- CTFd plugin or custom challenge type that polls/checks via a sidecar with access to the 9p host share
- Post-submit webhook that runs validation scripts against `/mnt/host`
- Browser runner hook that reports completion to CTFd API

Until then, organizers rely on static flags and [private/writeup.md](challenges/shell_101/00_intro/private/writeup.md) solutions.

## Other ideas

- Load one challenge description at a time in the web UI (sync with CTFd progress).
- GPG-encrypt flags for public challenge repos (`private/flag.txt.gpg`).
- Keep challenge statements updated directly in `challenges/*/challenge.yml`.
