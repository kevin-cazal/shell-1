import { readFileSync } from "node:fs";
import { join } from "node:path";
import { V86 } from "../../../submodules/v86-runner/node_modules/v86/build/libv86.mjs";
import { createHost9p } from "../../../submodules/v86-runner/src/host9p/index.js";
import { resolveBiosPath } from "../../../submodules/v86-runner/scripts/lib/resolve-bios.mjs";
import { loadBundleFromPath } from "./load-bundle.mjs";
import { V86_RUNNER_ROOT, resolveVmBundle, resolveVmDisk } from "./paths.mjs";
import {
  ROOT_PROMPT,
  USER42_PROMPT,
  createSerialSession,
} from "./serial-session.mjs";

const DEFAULT_COLD_BOOT_TIMEOUT_MS = Number(
  process.env.E2E_BOOT_TIMEOUT_MS || 1_500_000,
);
const DEFAULT_RESUME_TIMEOUT_MS = Number(
  process.env.E2E_RESUME_TIMEOUT_MS || 120_000,
);
const memoryMb = Number(process.env.VITE_VM_MEMORY_MB || 512);
const memorySizeFromEnv = memoryMb * 1024 * 1024;

/** @param {ReturnType<typeof createSerialSession>} serial */
export async function ensureHost9pMounted(serial) {
  const out = await serial.run(
    "mkdir -p /mnt/host; modprobe 9pnet_virtio 2>/dev/null; modprobe 9p 2>/dev/null; " +
      "i=0; while [ $i -lt 120 ]; do /usr/local/sbin/mount-host-share 2>/dev/null && mountpoint -q /mnt/host && break; i=$((i+1)); sleep 1; done; " +
      "mountpoint -q /mnt/host && echo HOST_OK || echo HOST_FAIL",
    { timeout: 180_000 },
  );
  if (!out.includes("HOST_OK")) {
    throw new Error(
      `host9p mount failed after 120s:\n${out.slice(-1000)}`,
    );
  }
}

/**
 * @param {{ onSerial?: (byte: number) => void, bootTimeoutMs?: number }} [opts]
 */
export async function bootVmAsUser42(opts = {}) {
  const useColdBoot = process.env.E2E_COLD_BOOT === "1";
  const wasmPath = join(
    V86_RUNNER_ROOT,
    "node_modules/v86/build/v86.wasm",
  );

  /** @type {ArrayBuffer} */
  let diskBuffer;
  /** @type {ArrayBuffer} */
  let biosBuffer;
  /** @type {ArrayBuffer} */
  let vgaBiosBuffer;
  /** @type {ArrayBuffer | undefined} */
  let initialStateBuffer;
  let memorySize = memorySizeFromEnv;

  if (useColdBoot) {
    const diskPath = resolveVmDisk();
    const seabiosPath = resolveBiosPath(undefined, "seabios.bin", V86_RUNNER_ROOT);
    const vgabiosPath = resolveBiosPath(undefined, "vgabios.bin", V86_RUNNER_ROOT);
    const disk = readFileSync(diskPath);
    const seabios = readFileSync(seabiosPath);
    const vgabios = readFileSync(vgabiosPath);
    diskBuffer = disk.buffer;
    biosBuffer = seabios.buffer;
    vgaBiosBuffer = vgabios.buffer;
    console.error(
      `[e2e] Cold boot ${diskPath} (${disk.length} bytes), RAM ${memoryMb}MiB…`,
    );
  } else {
    const bundlePath = resolveVmBundle();
    const bundle = await loadBundleFromPath(bundlePath);
    diskBuffer = bundle.diskBuffer;
    biosBuffer = bundle.biosBuffer;
    vgaBiosBuffer = bundle.vgaBiosBuffer;
    initialStateBuffer = bundle.initialStateBuffer;
    memorySize = bundle.memorySize;
    console.error(
      `[e2e] Resuming ${bundlePath} (${bundle.label}, RAM ${Math.round(memorySize / 1024 / 1024)}MiB)…`,
    );
  }

  const host9p = createHost9p();

  /** @type {import("v86").V86} */
  let emulator;

  const promptTimeoutMs =
    opts.bootTimeoutMs ??
    (useColdBoot ? DEFAULT_COLD_BOOT_TIMEOUT_MS : DEFAULT_RESUME_TIMEOUT_MS);

  emulator = new V86({
    wasm_path: wasmPath,
    bios: { buffer: biosBuffer },
    vga_bios: { buffer: vgaBiosBuffer },
    hda: { buffer: diskBuffer },
    ...(initialStateBuffer
      ? { initial_state: { buffer: initialStateBuffer } }
      : {}),
    memory_size: memorySize,
    virtio_console: true,
    autostart: true,
    disable_keyboard: true,
    filesystem: { handle9p: host9p.handle9p },
  });

  const serial = createSerialSession(emulator);
  if (opts.onSerial) {
    emulator.add_listener("serial0-output-byte", opts.onSerial);
  }

  await new Promise((resolve) => {
    emulator.add_listener("emulator-ready", () => {
      emulator.bus.send("virtio-console0-resize", [24, 132]);
      resolve();
    });
  });

  // Saved state does not replay prior serial bytes into our buffer — nudge the shell.
  if (!useColdBoot) {
    await new Promise((r) => setTimeout(r, 300));
    serial.send("");
  }

  console.error("[e2e] Waiting for root prompt localhost:~# …");
  await serial.waitFor(ROOT_PROMPT, { timeout: promptTimeoutMs });
  console.error("[e2e] Root shell ready, mounting host9p…");
  await ensureHost9pMounted(serial);

  console.error("[e2e] Switching to user42…");
  serial.send("su - user42");
  await serial.waitFor(USER42_PROMPT, { timeout: 60_000 });
  serial.setPrompt(USER42_PROMPT);

  console.error("[e2e] user42 shell ready (localhost:~$)");

  async function destroy() {
    try {
      await emulator.destroy();
    } catch {
      /* ignore */
    }
  }

  return { emulator, serial, host9p, destroy };
}
