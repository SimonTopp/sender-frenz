const DISMISSED_KEY = "sender-frenz-install-dismissed";
const VISITS_KEY = "sender-frenz-visit-count";

let _androidPrompt = null;

function _isIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

function _isStandalone() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    navigator.standalone === true
  );
}

function _isDismissed() {
  return localStorage.getItem(DISMISSED_KEY) === "1";
}

export function incrementVisitCount() {
  const n = parseInt(localStorage.getItem(VISITS_KEY) || "0") + 1;
  localStorage.setItem(VISITS_KEY, String(n));
  return n;
}

function _showBanner(kind) {
  const banner = document.getElementById("install-banner");
  if (!banner) return;
  const msg = document.getElementById("install-banner-msg");
  if (kind === "ios") {
    msg.textContent = 'Install: tap \u2b06 Share \u2192 "Add to Home Screen"';
  } else {
    msg.textContent = "Add sender frenz to your home screen";
    const btn = document.getElementById("btn-install-android");
    if (btn) btn.hidden = false;
  }
  banner.hidden = false;
}

export function bindInstallPrompt() {
  if (_isStandalone() || _isDismissed()) return;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    _androidPrompt = e;
    _showBanner("android");
  });

  const visits = incrementVisitCount();
  if (_isIos() && visits >= 2) {
    _showBanner("ios");
  }

  document.getElementById("btn-dismiss-install")?.addEventListener("click", () => {
    localStorage.setItem(DISMISSED_KEY, "1");
    document.getElementById("install-banner").hidden = true;
  });

  document.getElementById("btn-install-android")?.addEventListener("click", async () => {
    if (!_androidPrompt) return;
    _androidPrompt.prompt();
    const { outcome } = await _androidPrompt.userChoice;
    if (outcome === "accepted") {
      localStorage.setItem(DISMISSED_KEY, "1");
      document.getElementById("install-banner").hidden = true;
    }
    _androidPrompt = null;
  });
}
