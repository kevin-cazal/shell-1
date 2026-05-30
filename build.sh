#!/bin/sh
set -e

ROOT=$(cd "$(dirname "$0")" && pwd)
AMVI="${ALPINE_MAKE_VM_IMAGE:-$ROOT/submodules/alpine-make-vm-image/alpine-make-vm-image}"
VM_BUILD="$ROOT/submodules/vm-image/build.sh"
IMAGE_SIZE="${IMAGE_SIZE:-256M}"
IMAGE="${IMAGE:-$ROOT/alpine-bios-${IMAGE_SIZE}.img}"

if [ ! -d "$ROOT/submodules/vm-image" ]; then
	echo "Missing submodules — run: git submodule update --init --recursive" >&2
	exit 1
fi

export ALPINE_MAKE_VM_IMAGE="$AMVI"
export IMAGE_SIZE="$IMAGE_SIZE"
export IMAGE="$IMAGE"
"$VM_BUILD"

echo "Disk image: $IMAGE"
