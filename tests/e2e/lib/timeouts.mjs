/** @param {string} name @param {number} fallback */
function ms(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === "") {
    return fallback;
  }
  const n = Number(raw);
  if (!Number.isFinite(n) || n < 0) {
    throw new Error(`Invalid ${name}=${raw} (expected non-negative number)`);
  }
  return n;
}

/** Default wait for serial.run() and waitFor(). */
export const SERIAL_MS = ms("E2E_SERIAL_TIMEOUT_MS", 30_000);

/** Wait for root prompt after .v86b resume. */
export const RESUME_BOOT_MS = ms("E2E_RESUME_TIMEOUT_MS", 60_000);

/** Wait for root prompt on cold boot from raw .img. */
export const COLD_BOOT_MS = ms("E2E_BOOT_TIMEOUT_MS", 600_000);

/** Total timeout for host9p mount script in the guest. */
export const HOST9P_MS = ms("E2E_HOST9P_TIMEOUT_MS", 60_000);

/** Guest mount loop iterations (1s sleep each). */
export const HOST9P_ATTEMPTS = ms("E2E_HOST9P_MOUNT_ATTEMPTS", 45);

/** Wait for user42 prompt after su. */
export const USER42_SWITCH_MS = ms("E2E_USER42_TIMEOUT_MS", 30_000);

/** Simple one-shot shell commands in scenarios. */
export const CMD_MS = ms("E2E_CMD_TIMEOUT_MS", 15_000);

/** cp -r, tar, and similar slow filesystem work. */
export const SLOW_CMD_MS = ms("E2E_SLOW_CMD_TIMEOUT_MS", 45_000);

/** check_shell101_* invocations. */
export const CHECKER_MS = ms("E2E_CHECKER_TIMEOUT_MS", 30_000);
