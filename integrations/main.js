/** Discover Linux (shell-1) product entry: subject pane, then generic v86 runner. */
import { initBundleDownloadLinks } from "./plugins/bundleRelease.js";
import { initScrollFocus } from "./plugins/scrollFocus.js";
import "@runner/app.js";

initScrollFocus();
initBundleDownloadLinks();
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
