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

https://kevin-cazal.github.io/shell-1/

Download the official `.v86b` from releases, then open it in the atelier UI.

## Submodule layout

| Path | Repository |
|------|------------|
| `submodules/alpine-make-vm-image` | Image builder |
| `submodules/vm-image` | [vm-image-discover-linux-1](https://github.com/kevin-cazal/vm-image-discover-linux-1) |
| `submodules/v86-runner` | Browser runner |

## Follow-ups

- Automated grading of livrables under `/mnt/host` and `answers.txt`
