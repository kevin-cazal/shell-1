/** Discover Linux (shell-1) product entry: subject pane, then generic v86 runner. */
import { initOfficialBundleDownloadLink } from "./plugins/bundleRelease.js";
import { initSubjectPanel } from "./plugins/subjectPanel.js";
import "@runner/app.js";

initSubjectPanel();
initOfficialBundleDownloadLink();
initFrenchAtelierPickStatus();

function initFrenchAtelierPickStatus() {
  const statusEl = document.getElementById("status");
  const pickOverlay = document.getElementById("pick-overlay");
  if (!statusEl || !pickOverlay) return;
  const label = "En attente du fichier de l'atelier";
  const apply = () => {
    if (!pickOverlay.hidden) statusEl.textContent = label;
  };
  apply();
  new MutationObserver(apply).observe(pickOverlay, {
    attributes: true,
    attributeFilter: ["hidden"],
  });
}
