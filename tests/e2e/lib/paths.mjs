import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const E2E_DIR = dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = join(E2E_DIR, "../../..");
export const V86_RUNNER_ROOT = join(REPO_ROOT, "submodules/v86-runner");
export const HOME42_ROOT = join(
  REPO_ROOT,
  "submodules/vm-image/rootfs/home/user42",
);

/** @returns {string} */
export function resolveVmBundle() {
  const fromEnv = process.env.VM_BUNDLE;
  if (fromEnv) {
    return fromEnv;
  }
  const candidates = [
    join(REPO_ROOT, "shell-1-512M.v86b"),
    join(REPO_ROOT, "submodules/vm-image/shell-1-512M.v86b"),
  ];
  for (const p of candidates) {
    if (existsSync(p)) {
      return p;
    }
  }
  throw new Error(
    `VM bundle not found. Build with:\n` +
      `  cd submodules/vm-image && doas ./build.sh\n` +
      `  VITE_VM_MEMORY_MB=512 npm run build-bundle\n` +
      `Or set VM_BUNDLE to a .v86b path.\nTried:\n${candidates.join("\n")}`,
  );
}

/** @returns {string} */
export function resolveVmDisk() {
  const fromEnv = process.env.VM_DISK;
  if (fromEnv) {
    return fromEnv;
  }
  const candidates = [
    join(REPO_ROOT, "submodules/vm-image/alpine-bios-512M.img"),
    join(REPO_ROOT, "alpine-bios-512M.img"),
  ];
  for (const p of candidates) {
    if (existsSync(p)) {
      return p;
    }
  }
  throw new Error(
    `VM disk not found. Build with: doas ./build.sh\nTried:\n${candidates.join("\n")}`,
  );
}
