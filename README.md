# shell-1

Discover Linux — Shell 101–102 atelier in the browser (Alpine guest + [v86-runner](https://github.com/kevin-cazal/v86-runner)).

Split view: subject markdown on the left, terminal on the right. Livrables go in the guest at **`/mnt/host`** (virtio 9p).

## Prerequisites

- git, Node.js 20+, Linux root for disk build
- Docker (to build guest static binaries in vm-image)

## First-time setup

```sh
git clone --recursive https://github.com/kevin-cazal/shell-1.git
cd shell-1
git submodule update --init --recursive
```

## Build disk image (default 512 MiB)

```sh
doas ./build.sh
```

Produces `alpine-bios-512M.img` in the repo root (via `submodules/vm-image`).

## Web UI

```sh
npm install
cd submodules/v86-runner && npm install && cd ../..
npm run prepare
npm run dev
```

Open the URL shown, then pick **`shell-1-512M.v86b`** or **`alpine-bios-512M.img`**.

Guest RAM defaults to **512 MiB** (`VITE_VM_MEMORY_MB=512` in `.env`).

## Subject

Course text lives in [`subject/Linux.md`](subject/Linux.md) (editable in this repo). Images in [`subject/images/`](subject/images/). No PDF build step.

## V86B bundle

```sh
npm run prepare
VITE_VM_MEMORY_MB=512 npm run build-bundle -- \
  --disk submodules/vm-image/alpine-bios-512M.img \
  -o shell-1-512M.v86b
```

Official bundle: [vm-image-discover-linux-1 releases](https://github.com/kevin-cazal/vm-image-discover-linux-1/releases/latest).

## Host file share (`/mnt/host`)

- Guest path: **`/mnt/host`**
- Host path: 9p root (e.g. `/delivery_101.tar` on the host ↔ `/mnt/host/delivery_101.tar` in the guest)

## Play online (GitHub Pages)

After enabling **GitHub Pages** (Actions source) on `main`, the app is published at:

**https://kevin-cazal.github.io/shell-1/**

1. Use **Download official bundle (.v86b)** on the home screen (from [vm-image releases](https://github.com/kevin-cazal/vm-image-discover-linux-1/releases/latest)).
2. Choose the downloaded file with **Choose disk or bundle…**.

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

Regenerate challenge files from `subject/Linux.md`:

```sh
python3 scripts/split_linux_subject.py
python3 scripts/generate_flags_and_writeups.py
cd challenges && export GPG_PASSPHRASE='…' && ./encrypt.sh
```

## Follow-ups

- Automated grading of livrables under `/mnt/host` — see [`IDEA.md`](IDEA.md)
