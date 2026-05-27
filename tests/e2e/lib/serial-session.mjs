import { SERIAL_MS } from "./timeouts.mjs";

/** @typedef {{ send: (cmd: string) => void, waitFor: (re: RegExp, opts?: { timeout?: number }) => Promise<string>, getTail: (lines?: number) => string }} SerialSession */

export const ROOT_PROMPT = /localhost:~#\s*$/;
export const USER42_PROMPT = /localhost:~[$]\s*$/;

const FLAG_RE = /shell1\{[^}]+\}/;
const BUFFER_MAX = 256 * 1024;

/** Unique marker; alphanumeric only (safe in shell and RegExp). */
function makeSentinelTag() {
  return `E2EEND${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`;
}

/**
 * Print sentinel after cmd via hex → xxd so the tag text is not in the echoed
 * command line (only appears once decoded at runtime).
 * @param {string} tag
 */
function sentinelEchoCmd(tag) {
  const hex = Buffer.from(tag, "utf8").toString("hex");
  return `echo ${hex}|xxd -r -p||printf $(echo ${hex}|sed 's/../\\\\x& /g')`;
}

/** @param {string} tag */
function tagRegex(tag) {
  return new RegExp(tag.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
}

/** @param {string} text */
function stripAnsi(text) {
  return text
    .replace(/\x1b\[[0-9;?]*[a-zA-Z]/g, "")
    .replace(/\x1b\([A-Z0-9]/g, "")
    .replace(/\r/g, "");
}

/**
 * @param {import("v86").V86} emulator
 * @returns {SerialSession}
 */
export function createSerialSession(emulator) {
  let buffer = "";
  /** @type {RegExp | null} */
  let activePrompt = ROOT_PROMPT;

  emulator.add_listener("serial0-output-byte", (byte) => {
    buffer += String.fromCharCode(byte);
    if (buffer.length > BUFFER_MAX) {
      buffer = buffer.slice(-BUFFER_MAX);
    }
  });

  function tailPlain(chars = 4096) {
    return stripAnsi(buffer.slice(-chars));
  }

  /**
   * @param {RegExp} re
   * @param {{ timeout?: number }} [opts]
   */
  function waitFor(re, opts = {}) {
    const timeout = opts.timeout ?? SERIAL_MS;
    const start = Date.now();
    return new Promise((resolve, reject) => {
      const tick = () => {
        if (re.test(tailPlain())) {
          resolve(buffer);
          return;
        }
        if (Date.now() - start >= timeout) {
          reject(
            new Error(
              `Timed out after ${timeout}ms waiting for ${re}\n--- serial tail ---\n${getTail(50)}`,
            ),
          );
          return;
        }
        setTimeout(tick, 50);
      };
      tick();
    });
  }

  function getTail(lines = 50) {
    return buffer.split("\n").slice(-lines).join("\n");
  }

  function send(cmd) {
    emulator.serial0_send(`${cmd}\n`);
  }

  return {
    send,
    waitFor,
    getTail,

    /** @param {RegExp} prompt */
    setPrompt(prompt) {
      activePrompt = prompt;
    },

    get prompt() {
      return activePrompt;
    },

    /**
     * Run one shell command and wait for a unique sentinel echoed after it.
     * @param {string} cmd
     * @param {{ prompt?: RegExp, timeout?: number }} [opts]
     * @returns {Promise<string>} command stdout/stderr (ANSI stripped)
     */
    async run(cmd, opts = {}) {
      const timeout = opts.timeout ?? SERIAL_MS;
      const tag = makeSentinelTag();
      const marker = buffer.length;
      send(`${cmd}; ${sentinelEchoCmd(tag)}`);
      await waitFor(tagRegex(tag), { timeout });
      const out = stripAnsi(buffer.slice(marker));
      const before = out.split(tag)[0] ?? out;
      return before.trimStart();
    },

    /**
     * @param {string} cmd
     * @param {{ timeout?: number }} [opts]
     */
    async runAndExtractFlag(cmd, opts = {}) {
      const out = await this.run(cmd, opts);
      const flag = extractFlag(out);
      if (!flag) {
        throw new Error(
          `No shell1{…} flag in output of: ${cmd}\n--- output ---\n${out.slice(-2000)}`,
        );
      }
      return flag;
    },
  };
}

/** @param {string} text */
export function extractFlag(text) {
  const m = text.match(FLAG_RE);
  return m ? m[0] : null;
}

/** @param {string} text */
export function extractLastLine(text) {
  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  return lines.at(-1) ?? "";
}

/** Last line that is only digits (typical wc -l output). */
export function extractTrailingCount(text) {
  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i--) {
    if (/^\d+$/.test(lines[i])) {
      return lines[i];
    }
  }
  return extractFirstNumber(text);
}

/** @param {string} text */
export function extractFirstNumber(text) {
  const m = text.match(/\b(\d+)\b/);
  return m ? m[1] : null;
}
