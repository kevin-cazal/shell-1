import DOMPurify from "dompurify";
import { marked } from "marked";
import subjectMd from "../../subject/Linux.md?raw";

const SUBJECT_IMAGE_BASE = `${import.meta.env.BASE_URL}subject/images/`;

function preprocessMarkdown(md) {
  return md
    .replace(/\{width=[^}]+\}/g, "")
    .replace(/!\[([^\]]*)\]\(images\//g, "![$1](subject/images/");
}

function transformHintsAndSolutions(container) {
  container.querySelectorAll(".solution").forEach((el) => el.remove());
  container.querySelectorAll('[class*="solution"]').forEach((el) => {
    if (el.classList.contains("hint")) return;
    if (el.classList.contains("solution") || el.hasAttribute("hidden")) {
      el.remove();
    }
  });

  container.querySelectorAll(".hint").forEach((hint) => {
    const details = document.createElement("details");
    details.className = "hint-block";
    const summary = document.createElement("summary");
    summary.textContent = "Indice";
    const body = document.createElement("div");
    body.innerHTML = hint.innerHTML;
    details.append(summary, body);
    hint.replaceWith(details);
  });
}

function fixImageSources(container) {
  container.querySelectorAll("img").forEach((img) => {
    const src = img.getAttribute("src");
    if (!src) return;
    if (src.startsWith("subject/images/")) {
      img.src = import.meta.env.BASE_URL + src;
    } else if (src.startsWith("images/")) {
      img.src = SUBJECT_IMAGE_BASE + src.slice("images/".length);
    }
  });
}

/** Show subject pane only after the guest VM is ready; hide on pick screen / reset. */
export function initSubjectPanelVisibility() {
  const panel = document.getElementById("subject-panel");
  const workbench = document.getElementById("workbench");
  const pickOverlay = document.getElementById("pick-overlay");
  if (!panel) return;

  const hide = () => {
    panel.hidden = true;
    workbench?.classList.remove("vm-ready");
  };

  const show = () => {
    if (pickOverlay && !pickOverlay.hidden) return;
    panel.hidden = false;
    workbench?.classList.add("vm-ready");
  };

  hide();

  window.addEventListener("vm-guest-ready", show);

  if (pickOverlay) {
    new MutationObserver(() => {
      if (!pickOverlay.hidden) hide();
    }).observe(pickOverlay, {
      attributes: true,
      attributeFilter: ["hidden"],
    });
  }
}

export function initSubjectPanel() {
  const root = document.getElementById("subject-content");
  if (!root) return;

  marked.setOptions({ gfm: true, breaks: false });

  const html = marked.parse(preprocessMarkdown(subjectMd));
  root.innerHTML = DOMPurify.sanitize(html, {
    ADD_ATTR: ["target", "rel"],
  });

  transformHintsAndSolutions(root);
  fixImageSources(root);
}
