/**
 * Route mouse wheel to the scrollable pane under the pointer.
 * xterm/v86 capture wheel globally; scrollbar dragging still uses native overflow.
 */

function getSubjectScroller() {
  const panel = document.getElementById("subject-panel");
  if (!panel || panel.hidden) return null;
  return panel;
}

function getTerminalScroller() {
  const wrap = document.getElementById("terminal-wrap");
  if (!wrap || wrap.hidden) return null;
  return wrap.querySelector(".xterm-viewport");
}

/** @param {Event} event */
function scrollerUnderPointer(event) {
  const subject = getSubjectScroller();
  if (subject?.contains(/** @type {Node} */ (event.target))) {
    return subject;
  }
  const terminal = getTerminalScroller();
  const termWrap = document.getElementById("terminal-wrap");
  if (terminal && termWrap?.contains(/** @type {Node} */ (event.target))) {
    return terminal;
  }
  return null;
}

/** @param {HTMLElement} el @param {number} deltaY */
function applyWheelScroll(el, deltaY) {
  if (el.scrollHeight <= el.clientHeight) return false;
  const maxTop = el.scrollHeight - el.clientHeight;
  const next = Math.max(0, Math.min(maxTop, el.scrollTop + deltaY));
  if (next === el.scrollTop) return false;
  el.scrollTop = next;
  return true;
}

function focusTerminalInput() {
  document
    .querySelector("#terminal-wrap .xterm-helper-textarea")
    ?.focus({ preventScroll: true });
}

function blurTerminalInput() {
  document.querySelector("#terminal-wrap .xterm-helper-textarea")?.blur();
}

export function initScrollFocus() {
  const workbench = document.getElementById("workbench");
  if (!workbench) return;

  workbench.addEventListener(
    "wheel",
    (ev) => {
      if (!workbench.classList.contains("vm-ready")) return;
      const scroller = scrollerUnderPointer(ev);
      if (!scroller) return;
      if (!applyWheelScroll(scroller, ev.deltaY)) {
        ev.preventDefault();
        ev.stopPropagation();
        return;
      }
      ev.preventDefault();
      ev.stopPropagation();
    },
    { passive: false, capture: true },
  );

  const subject = document.getElementById("subject-panel");
  const termWrap = document.getElementById("terminal-wrap");

  subject?.addEventListener("mouseenter", blurTerminalInput);
  termWrap?.addEventListener("mouseenter", focusTerminalInput);
}
