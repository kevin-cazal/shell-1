#!/usr/bin/env node
/**
 * Shell 101 headless E2E: one VM session (resume .v86b by default) + CTFd submissions.
 */
import { CtfdClient } from "./lib/ctfd.mjs";
import { bootVmAsUser42 } from "./lib/vm-runner.mjs";
import {
  SHELL101_CHALLENGE_NAMES,
  SHELL101_STEPS,
} from "./scenarios/shell101.mjs";

async function main() {
  const ctfd = new CtfdClient();
  console.error("[e2e] Checking CTFd…");
  await ctfd.ping();
  await ctfd.loadChallenges(SHELL101_CHALLENGE_NAMES);

  const user = await ctfd.createE2eUser();
  console.error(`[e2e] CTFd user: ${user.name}`);

  let vm;
  try {
    vm = await bootVmAsUser42({
      onSerial: (byte) => process.stdout.write(String.fromCharCode(byte)),
    });
  } catch (e) {
    console.error("[e2e] VM boot failed:", e instanceof Error ? e.message : e);
    process.exit(1);
  }

  const { serial, destroy } = vm;
  let passed = 0;
  let failed = false;

  for (const step of SHELL101_STEPS) {
    const label = `${step.slug} (${step.ctfdName})`;
    process.stderr.write(`\n[e2e] ▶ ${label}\n`);
    try {
      const submission = await step.run({ serial, ctfd });
      await ctfd.submit(step.ctfdName, submission);
      console.error(`[e2e] ✓ ${label} → ${submission}`);
      passed += 1;
    } catch (e) {
      failed = true;
      console.error(`[e2e] ✗ ${label}`);
      console.error(e instanceof Error ? e.message : e);
      if (serial.getTail) {
        console.error("--- serial tail ---\n" + serial.getTail(40));
      }
      break;
    }
  }

  await destroy();

  console.error(`\n[e2e] ${passed}/${SHELL101_STEPS.length} challenges passed`);
  process.exit(failed ? 1 : 0);
}

main().catch((e) => {
  console.error("[e2e] Fatal:", e instanceof Error ? e.message : e);
  process.exit(1);
});
