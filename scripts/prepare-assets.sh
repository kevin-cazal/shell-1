#!/bin/sh
# Stage BIOS, v86.wasm, and COI service worker for the web runner.
set -e

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUNNER="$ROOT/submodules/v86-runner"
ASSETS="$RUNNER/public/assets"
PUBLIC="$RUNNER/public"
V86_RAW="https://raw.githubusercontent.com/copy/v86/master"
V86_RELEASE="https://github.com/copy/v86/releases/download/latest"

mkdir -p "$ASSETS"

fetch() {
	url=$1
	dest=$2
	curl -fsSL -o "$dest" "$url"
}

if [ ! -d "$RUNNER" ]; then
	echo "Missing submodules/v86-runner — run: git submodule update --init" >&2
	exit 1
fi

wasm_src="$RUNNER/node_modules/v86/build/v86.wasm"
if [ -f "$wasm_src" ]; then
	cp -f "$wasm_src" "$PUBLIC/v86.wasm"
else
	fetch "$V86_RELEASE/v86.wasm" "$PUBLIC/v86.wasm"
fi

if [ -f "$RUNNER/node_modules/v86/bios/seabios.bin" ]; then
	cp -f "$RUNNER/node_modules/v86/bios/seabios.bin" \
		"$RUNNER/node_modules/v86/bios/vgabios.bin" \
		"$ASSETS/"
else
	fetch "$V86_RAW/bios/seabios.bin" "$ASSETS/seabios.bin"
	fetch "$V86_RAW/bios/vgabios.bin" "$ASSETS/vgabios.bin"
fi

printf 'Assets ready under %s/public\n' "$RUNNER"

COI_SRC="$ROOT/public/coi-serviceworker.js"
if [ -f "$COI_SRC" ]; then
	cp -f "$COI_SRC" "$PUBLIC/coi-serviceworker.js"
	printf 'COI service worker copied to %s\n' "$PUBLIC"
else
	printf 'warn: missing %s (GitHub Pages cross-origin isolation)\n' "$COI_SRC" >&2
fi
