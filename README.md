# shell-1

Discover Linux — Shell 101–102 atelier in the browser (Alpine guest + [v86-runner](https://github.com/kevin-cazal/v86-runner)).

Challenge content source-of-truth lives under **`challenges/`**. Livrables go in the guest at **`/mnt/host`** (virtio 9p).

## Prerequisites

- git, Node.js 20+, Linux root for disk build
- Docker (to build guest static binaries in vm-image)

## Full local deploy

One-shot workshop setup (VM, bundle, Vite, CTFd, challenges):

```sh
./deploy-local.sh
```

Runs the disk build as root, uses Docker for CTFd, and defaults from [`.cursor/rules/redeploy-challenges.mdc`](.cursor/rules/redeploy-challenges.mdc). Skip steps with env vars, e.g. `SKIP_VM=1 ./deploy-local.sh` if the disk image is already built.

## First-time setup

```sh
git clone --recursive https://github.com/kevin-cazal/shell-1.git
cd shell-1
git submodule update --init --recursive
npm install
cd submodules/v86-runner && npm install && cd ../..
```

## Build disk image (default 256 MiB)

```sh
./build.sh   # as root
```

Produces `alpine-bios-256M.img` in the repo root (via `submodules/vm-image`).

## Web UI

After [first-time setup](#first-time-setup):

```sh
npm run prepare
npm run dev
```

Open the URL shown, then pick **`shell-1-256M.v86b`** or **`alpine-bios-256M.img`**.

Guest RAM defaults to **256 MiB** (`VITE_VM_MEMORY_MB=256` in `.env`).

## Challenges content

Course/challenge statements live in [`challenges/`](challenges/), with one `challenge.yml` per challenge.

## V86B bundle

```sh
npm run prepare
cd submodules/vm-image
./build.sh   # as root
cd ../..
VITE_VM_MEMORY_MB=256 npm run build-bundle
```

Defaults: disk `submodules/vm-image/alpine-bios-256M.img`, output `shell-1-256M.v86b` at repo root. Override with `--disk` / `-o` (paths relative to repo root).

Official bundle: [cdn.cazal.eu/shell-1-256M.v86b](https://cdn.cazal.eu/shell-1-256M.v86b).

### 512 MiB variant (optional)

Larger disk and guest RAM if you need more headroom.

```sh
export IMAGE_SIZE=512M IMAGE="$PWD/alpine-bios-512M.img"
./build.sh   # as root

VITE_VM_MEMORY_MB=512 npm run build-bundle -- \
  --disk alpine-bios-512M.img \
  -o shell-1-512M.v86b
```

In the UI, pick **`shell-1-512M.v86b`**. When loading the raw disk instead, set `VITE_VM_MEMORY_MB=512` in `.env`.

One-shot local deploy:

```sh
IMAGE_SIZE=512M DISK_IMAGE="$PWD/alpine-bios-512M.img" \
BUNDLE_OUT="$PWD/shell-1-512M.v86b" VITE_VM_MEMORY_MB=512 ./deploy-local.sh
```

## Host file share (`/mnt/host`)

- Guest path: **`/mnt/host`**
- Host path: 9p root (e.g. `/delivery_101.tar` on the host ↔ `/mnt/host/delivery_101.tar` in the guest)

## Play online (GitHub Pages)

After enabling **GitHub Pages** (Actions source) on `main`, the app is published at:

**https://kevin-cazal.github.io/shell-1/**

1. Use **Télécharger le fichier de l'atelier** on the home screen (default: [cdn.cazal.eu/shell-1-256M.v86b](https://cdn.cazal.eu/shell-1-256M.v86b)).
2. Choose the downloaded file with **Choose disk or bundle…**.

## Container image (GHCR)

Workshop UI only (Vite app + embedded `shell-1-256M.v86b`). **No CTFd** — use [CTFd (local scoring)](#ctfd-local-scoring) or `./deploy-local.sh` for scoring.

Published on push to `main` (see [`.github/workflows/docker-ghcr.yml`](.github/workflows/docker-ghcr.yml)):

**https://github.com/kevin-cazal/shell-1/pkgs/container/shell-1**

```sh
docker run --rm -p 8080:80 ghcr.io/kevin-cazal/shell-1:latest
# http://localhost:8080 — download or open the bundled .v86b from the same host
```

Local build:

```sh
docker build -t shell-1:local .
docker run --rm -p 8080:80 shell-1:local
```

## Deploy (GitHub Pages)

Pushes to `main` run `.github/workflows/pages.yml` (Vite build + deploy). Set repository **Pages → Build and deployment → GitHub Actions**.

## Deploy under a path prefix

`npm run build` emits relative asset URLs (`base: ./`) so you can serve `dist/` behind nginx at e.g. `/games/shell-1/`. See `submodules/v86-runner` for `VITE_BASE`.

## Submodule layout

| Path | Repository |
|------|------------|
| `submodules/alpine-make-vm-image` | Image builder |
| `submodules/vm-image` | [vm-image-discover-linux-1](https://github.com/kevin-cazal/vm-image-discover-linux-1) |
| `submodules/v86-runner` | Browser runner |
| `challenges` | [shell-1-challenges](https://github.com/kevin-cazal/shell-1-challenges) |
| `integrations/ctfd_shell1_flags` | [ctfd-shell1-flags](https://github.com/kevin-cazal/ctfd-shell1-flags) |
| `submodules/ctfd` | [shell-1-ctfd](https://github.com/kevin-cazal/shell-1-ctfd) |
| `submodules/deploy_challenges` | [deploy_challenges](https://github.com/kevin-cazal/deploy_challenges) |

## CTFd (local scoring)

```sh
cd submodules/ctfd
docker compose --profile shell-1 up -d
# http://localhost:9042/ctfd/default/  registration code: shell-1-2026
```

Deploy challenges (flags are GPG-encrypted in the challenges submodule):

```sh
export GPG_PASSPHRASE='TESTING42'   # workshop local secret; use your own in production
export CTFD_TOKEN='…'              # PRESET_ADMIN_TOKEN in submodules/ctfd/docker-compose.yml

python3 submodules/deploy_challenges/deploy_challenges.py \
  --no-clone . \
  --subdir challenges \
  --url http://localhost:9042/ctfd/default \
  --token "$CTFD_TOKEN"
```

Export participant ratings/reviews and admin comments to [`TODO_comments.md`](TODO_comments.md):

```sh
export CTFD_TOKEN='…'   # same admin token as above
python3 scripts/export_ctfd_feedback.py
```

Headless E2E (full Shell 101 path, v86 + CTFd): see [`tests/e2e/README.md`](tests/e2e/README.md) — `npm run test:e2e:shell101`.

Refresh encrypted flags after manual updates:

```sh
cd challenges && export GPG_PASSPHRASE='…' && ./encrypt.sh
```

Several challenges use **multiple-choice** flags (`shell1{A}`–`shell1{D}`); hands-on steps stay in the challenge text. See [`challenges/README.md`](challenges/README.md).

## Follow-ups

- Automated grading of livrables under `/mnt/host` — see [`IDEA.md`](IDEA.md)
