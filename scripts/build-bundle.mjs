#!/usr/bin/env node
/**
 * Build shell-1-256M.v86b from the vm-image disk.
 * Resolves --disk / -o paths from the repo root (npm runs v86-runner in a subdir).
 */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const V86_RUNNER = join(REPO_ROOT, "submodules/v86-runner");
const DEFAULT_DISK = join(REPO_ROOT, "submodules/vm-image/alpine-bios-256M.img");
const DEFAULT_OUTPUT = join(REPO_ROOT, "shell-1-256M.v86b");

/** @param {string} p */
function resolveFromRepo(p) {
  return isAbsolute(p) ? p : resolve(REPO_ROOT, p);
}

/** @param {string[]} argv */
function buildArgs(argv) {
  const out = [];
  let disk = DEFAULT_DISK;
  let output = DEFAULT_OUTPUT;

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--disk" && argv[i + 1]) {
      disk = resolveFromRepo(argv[++i]);
      continue;
    }
    if (arg.startsWith("--disk=")) {
      disk = resolveFromRepo(arg.slice("--disk=".length));
      continue;
    }
    if ((arg === "-o" || arg === "--output") && argv[i + 1]) {
      output = resolveFromRepo(argv[++i]);
      continue;
    }
    if (arg.startsWith("-o=")) {
      output = resolveFromRepo(arg.slice(3));
      continue;
    }
    if (arg.startsWith("--output=")) {
      output = resolveFromRepo(arg.slice("--output=".length));
      continue;
    }
    out.push(arg);
  }

  if (!existsSync(disk)) {
    console.error(`Disk image not found: ${disk}`);
    console.error("Build it first: cd submodules/vm-image && doas ./build.sh");
    process.exit(1);
  }

  return ["--disk", disk, "-o", output, ...out];
}

const forwarded = buildArgs(process.argv.slice(2));
const script = join(V86_RUNNER, "scripts/build-v86-bundle.mjs");

console.error(`Disk image: ${forwarded[1]}`);
console.error(`Bundle out:  ${forwarded[3]}\n`);

const result = spawnSync(process.execPath, [script, ...forwarded], {
  cwd: V86_RUNNER,
  stdio: "inherit",
  env: process.env,
});

process.exit(result.status ?? 1);
