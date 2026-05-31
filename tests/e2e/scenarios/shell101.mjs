import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { HOME42_ROOT } from "../lib/paths.mjs";
import { ensureHost9pMounted } from "../lib/vm-runner.mjs";
import {
  extractFirstNumber,
  extractLastLine,
  extractTrailingCount,
} from "../lib/serial-session.mjs";
import { CHECKER_MS, CMD_MS, SLOW_CMD_MS } from "../lib/timeouts.mjs";

/** @typedef {{ serial: import("../lib/serial-session.mjs").SerialSession extends infer S ? S : never, ctfd: import("../lib/ctfd.mjs").CtfdClient }} StepContext */

/** @typedef {{ slug: string, ctfdName: string, run: (ctx: StepContext) => Promise<string> }} Shell101Step */

function homeStats() {
  const all = readdirSync(HOME42_ROOT).filter((n) => n !== "." && n !== "..");
  const visible = all.filter((n) => !n.startsWith("."));
  const hidden = all.filter((n) => n.startsWith("."));
  const memo1Size = statSync(join(HOME42_ROOT, "memo1.txt")).size;
  const dirCount = all.filter((n) =>
    statSync(join(HOME42_ROOT, n)).isDirectory(),
  ).length;
  return {
    visibleCount: visible.length,
    hiddenCount: hidden.length,
    memo1Size,
    dirCount,
  };
}

const STATS = homeStats();

function flag(inner) {
  return `shell1{${inner}}`;
}

/** @type {Shell101Step[]} */
export const SHELL101_STEPS = [
  {
    slug: "00_intro",
    ctfdName: "Shell 101 — 001 — Introduction",
    run: async () => flag("pret a commencer"),
  },
  {
    slug: "a_execution_commandes",
    ctfdName: "Shell 101 — 002 — Exécution de commandes",
    run: async ({ serial }) => {
      await serial.run("cal", { timeout: CMD_MS });
      return flag("B");
    },
  },
  {
    slug: "b_arguments_commande",
    ctfdName: "Shell 101 — 003 — Arguments de commande",
    run: async ({ serial }) => {
      await serial.run("cal -y", { timeout: CMD_MS });
      return flag("cal -y");
    },
  },
  {
    slug: "c01_ls",
    ctfdName: "Shell 101 — 004 — ls",
    run: async ({ serial }) => {
      const out = await serial.run("ls -1 | wc -l");
      const n = extractTrailingCount(out);
      if (n !== String(STATS.visibleCount)) {
        throw new Error(
          `ls count expected ${STATS.visibleCount}, got ${n}\n${out.slice(-500)}`,
        );
      }
      return flag(n);
    },
  },
  {
    slug: "c01_ls_a",
    ctfdName: "Shell 101 — 005 — ls (fichiers cachés)",
    run: async ({ serial }) => {
      const out = await serial.run(
        "ls -a | grep '^\\.' | grep -v '^\\.$' | grep -v '^\\.\\.$' | wc -l",
      );
      const n = extractTrailingCount(out);
      if (n !== String(STATS.hiddenCount)) {
        throw new Error(
          `hidden count expected ${STATS.hiddenCount}, got ${n}\n${out.slice(-500)}`,
        );
      }
      return flag(n);
    },
  },
  {
    slug: "c01_ls_l",
    ctfdName: "Shell 101 — 006 — ls (taille memo1.txt)",
    run: async ({ serial }) => {
      const out = await serial.run("ls -l memo1.txt | awk '{print $5}'");
      const n = extractTrailingCount(out);
      if (n !== String(STATS.memo1Size)) {
        throw new Error(
          `memo1 size expected ${STATS.memo1Size}, got ${n}\n${out.slice(-500)}`,
        );
      }
      return flag(n);
    },
  },
  {
    slug: "c01_ls_l_dirs",
    ctfdName: "Shell 101 — 007 — ls (répertoires)",
    run: async ({ serial }) => {
      const out = await serial.run("ls -l | grep '^d' | wc -l");
      const n = extractTrailingCount(out);
      if (n !== String(STATS.dirCount)) {
        throw new Error(
          `dir count expected ${STATS.dirCount}, got ${n}\n${out.slice(-500)}`,
        );
      }
      return flag(n);
    },
  },
  {
    slug: "c02_whoami",
    ctfdName: "Shell 101 — 008 — whoami",
    run: async ({ serial }) => {
      const out = await serial.run("whoami");
      const user = extractLastLine(out);
      if (user !== "user42") {
        throw new Error(`whoami expected user42, got ${user}`);
      }
      return flag("user42");
    },
  },
  {
    slug: "c03_pwd",
    ctfdName: "Shell 101 — 009 — pwd",
    run: async ({ serial }) => {
      const out = await serial.run("cd ~ && pwd");
      const path = extractLastLine(out);
      if (path !== "/home/user42") {
        throw new Error(`pwd expected /home/user42, got ${path}`);
      }
      return flag("/home/user42");
    },
  },
  {
    slug: "c04_cd",
    ctfdName: "Shell 101 — 010 — cd",
    run: async () => flag("A"),
  },
  {
    slug: "c05_mkdir",
    ctfdName: "Shell 101 — 011 — mkdir",
    run: async ({ serial }) => {
      const out = await serial.run("cd ~ && mkdir -p 101 && cd 101 && pwd");
      const path = extractLastLine(out);
      if (path !== "/home/user42/101") {
        throw new Error(`mkdir pwd expected /home/user42/101, got ${path}`);
      }
      return flag("/home/user42/101");
    },
  },
  {
    slug: "d01_cp",
    ctfdName: "Shell 101 — 012 — cp",
    run: async ({ serial }) => {
      await serial.run("cd ~", { timeout: CMD_MS });
      await serial.run("mkdir -p 101", { timeout: CMD_MS });
      await serial.run("cp memo1.txt memo2.txt 101/", { timeout: CMD_MS });
      await serial.run("cp -r memos links works code 101/", { timeout: SLOW_CMD_MS });
      await serial.run("cp .secret1.txt .secret2.txt 101/", { timeout: CMD_MS });
      return serial.runAndExtractFlag("check_shell101_cp", { timeout: CHECKER_MS });
    },
  },
  {
    slug: "d01b_compris",
    ctfdName: "Shell 101 — 013 — Compris",
    run: async () => flag("compris"),
  },
  {
    slug: "d02_mv",
    ctfdName: "Shell 101 — 014 — mv",
    run: async ({ serial }) => {
      await serial.run("cd ~/101", { timeout: CMD_MS });
      await serial.run("mv memo1.txt memo2.txt memos/", { timeout: CMD_MS });
      await serial.run("mv links/qrcode1 links/wikipedia_linux", {
        timeout: CMD_MS,
      });
      await serial.run("mv links/qrcode2 links/ubuntu", { timeout: CMD_MS });
      await serial.run("mv .secret1.txt secret1.txt", { timeout: CMD_MS });
      await serial.run("mv .secret2.txt secret2.txt", { timeout: CMD_MS });
      return serial.runAndExtractFlag("check_shell101_mv", { timeout: CHECKER_MS });
    },
  },
  {
    slug: "e01_cat",
    ctfdName: "Shell 101 — 015 — cat",
    run: async ({ serial }) => {
      await serial.run("cat ~/101/secret1.txt", { timeout: CMD_MS });
      return flag("B");
    },
  },
  {
    slug: "e02_nano",
    ctfdName: "Shell 101 — 016 — nano",
    run: async ({ serial }) => {
      await serial.run("cd ~/101/memos", { timeout: CMD_MS });
      await serial.run("awk '!seen[$0]++' memo2.txt > memo2.tmp && mv memo2.tmp memo2.txt", {
        timeout: CMD_MS,
      });
      await serial.run(
        "echo '- Convaincre un chat que je suis le chef' >> memo2.txt",
        { timeout: CMD_MS },
      );
      return serial.runAndExtractFlag("check_shell101_nano", {
        timeout: CHECKER_MS,
      });
    },
  },
  {
    slug: "e03_rm",
    ctfdName: "Shell 101 — 017 — rm et rmdir",
    run: async ({ serial }) => {
      await serial.run("rm ~/101/works/essay1.txt", { timeout: CMD_MS });
      await serial.run("rm -r ~/101/code", { timeout: SLOW_CMD_MS });
      return serial.runAndExtractFlag("check_shell101_rm", { timeout: CHECKER_MS });
    },
  },
  {
    slug: "e04_archivage",
    ctfdName: "Shell 101 — 018 — Archivage (tar)",
    run: async () => flag("tar ok"),
  },
  {
    slug: "livrable_1",
    ctfdName: "Shell 101 — 019 — Livrable 1",
    run: async ({ serial }) => {
      await ensureHost9pMounted(serial);
      await serial.run("cd ~", { timeout: CMD_MS });
      await serial.run(
        "rm -f ~/101/memos/memo2.tmp ~/101/memos/.gitkeep ~/delivery_101.tar 2>/dev/null; " +
          "test -f ~/101/secret1.txt && rm -f ~/101/.secret1.txt ~/101/.secret2.txt; true",
        { timeout: CMD_MS },
      );
      await serial.run("tar -cf delivery_101.tar 101", { timeout: SLOW_CMD_MS });
      const members = await serial.run(
        "tar -tf ~/delivery_101.tar | LC_ALL=C sort | wc -l",
      );
      const memberCount = extractTrailingCount(members);
      if (memberCount !== "11") {
        const listing = await serial.run(
          "tar -tf ~/delivery_101.tar | LC_ALL=C sort",
        );
        throw new Error(
          `delivery_101.tar has ${memberCount} members (expected 11):\n${listing}`,
        );
      }
      await serial.run("cp delivery_101.tar /mnt/host/.delivery_101.tar", {
        timeout: SLOW_CMD_MS,
      });
      return serial.runAndExtractFlag("check_shell101_livrable1", {
        timeout: SLOW_CMD_MS,
      });
    },
  },
];

export const SHELL101_CHALLENGE_NAMES = SHELL101_STEPS.map((s) => s.ctfdName);
