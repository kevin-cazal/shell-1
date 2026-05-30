/** Official release bundle URL (download only — no in-browser fetch). */
const DEFAULT_OFFICIAL_BUNDLE_URL =
  "https://github.com/kevin-cazal/vm-image-discover-linux-1/releases/latest/download/shell-1-256M.v86b";

export function initOfficialBundleDownloadLink() {
  const anchor = document.getElementById("official-bundle-download");
  if (!anchor) return;
  const url =
    import.meta.env.VITE_OFFICIAL_BUNDLE_URL || DEFAULT_OFFICIAL_BUNDLE_URL;
  anchor.href = url;
  anchor.setAttribute("download", "shell-1-256M.v86b");
}
