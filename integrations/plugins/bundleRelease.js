/** Official release bundle URL (CDN) and secondary mirrors (download only). */
const DEFAULT_OFFICIAL_BUNDLE_URL =
  "https://cdn.cazal.eu/shell-1-256M.v86b";
const DEFAULT_MIRROR_BUNDLE_URLS = [
  "https://github.com/kevin-cazal/vm-image-discover-linux-1/releases/latest/download/shell-1-256M.v86b",
  "https://gitlab.com/api/v4/projects/83317930/packages/generic/vm-artifacts/latest/shell-1-256M.v86b",
  "https://lab.epitech.academy/dl/shell-1-256M.v86b",
];
const BUNDLE_FILENAME = "shell-1-256M.v86b";

function parseMirrorUrls() {
  const fromEnv = import.meta.env.VITE_MIRROR_BUNDLE_URLS;
  if (fromEnv) {
    return fromEnv.split(",").map((url) => url.trim()).filter(Boolean);
  }
  return DEFAULT_MIRROR_BUNDLE_URLS;
}

export function initBundleDownloadLinks() {
  const primary = document.getElementById("official-bundle-download");
  const mirrors = document.querySelectorAll(".welcome-link-mirror");
  const cdnUrl =
    import.meta.env.VITE_OFFICIAL_BUNDLE_URL || DEFAULT_OFFICIAL_BUNDLE_URL;
  const mirrorUrls = parseMirrorUrls();

  if (primary) {
    primary.href = cdnUrl;
    primary.setAttribute("download", BUNDLE_FILENAME);
  }
  mirrors.forEach((link, index) => {
    const url = mirrorUrls[index];
    if (!url) return;
    link.href = url;
    link.setAttribute("download", BUNDLE_FILENAME);
  });
}

/** @deprecated Use initBundleDownloadLinks */
export const initOfficialBundleDownloadLink = initBundleDownloadLinks;
