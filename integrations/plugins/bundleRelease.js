/** Official release bundle URL (CDN) and GitHub mirror (download only). */
const DEFAULT_OFFICIAL_BUNDLE_URL =
  "https://cdn.cazal.eu/shell-1-256M.v86b";
const DEFAULT_MIRROR_BUNDLE_URL =
  "https://github.com/kevin-cazal/vm-image-discover-linux-1/releases/latest/download/shell-1-256M.v86b";
const BUNDLE_FILENAME = "shell-1-256M.v86b";

export function initBundleDownloadLinks() {
  const primary = document.getElementById("official-bundle-download");
  const mirror = document.getElementById("mirror-bundle-download");
  const cdnUrl =
    import.meta.env.VITE_OFFICIAL_BUNDLE_URL || DEFAULT_OFFICIAL_BUNDLE_URL;
  const mirrorUrl =
    import.meta.env.VITE_MIRROR_BUNDLE_URL || DEFAULT_MIRROR_BUNDLE_URL;

  if (primary) {
    primary.href = cdnUrl;
    primary.setAttribute("download", BUNDLE_FILENAME);
  }
  if (mirror) {
    mirror.href = mirrorUrl;
    mirror.setAttribute("download", BUNDLE_FILENAME);
  }
}

/** @deprecated Use initBundleDownloadLinks */
export const initOfficialBundleDownloadLink = initBundleDownloadLinks;
