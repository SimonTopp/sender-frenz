import { renderAvatar, applyEvent } from "./avatar.js";
import { bindActions } from "./actions.js";
import { bindLevelUp } from "./level_up.js";
import { showView } from "./ui.js";

const AVATAR_KEY = "sender-frenz-avatar-id";

function getOrCreateAvatarId() {
  let id = localStorage.getItem(AVATAR_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(AVATAR_KEY, id);
  }
  return id;
}

export function connectSSE(avatarId) {
  let delay = 5000;
  const source = new EventSource(`/events/${avatarId}`);

  source.onmessage = (e) => {
    applyEvent(JSON.parse(e.data).kind);
    delay = 5000;
  };

  source.onerror = () => {
    source.close();
    setTimeout(() => connectSSE(avatarId), Math.min(delay, 30000));
    delay = Math.min(delay * 2, 30000);
  };

  return source;
}

async function boot() {
  showView("view-loading");
  const avatarId = getOrCreateAvatarId();
  // Expose for tests and level_up.js
  window._senderFrenzAvatarId = avatarId;

  try {
    const res = await fetch("/session/open", {
      method: "POST",
      headers: { "avatar-id": avatarId },
    });
    if (!res.ok) throw new Error(`${res.status}`);
    const session = await res.json();

    renderAvatar(session);
    bindActions(avatarId);
    bindLevelUp(avatarId);
    connectSSE(avatarId);
    showView("view-main");

    for (const event of session.events) {
      applyEvent(event.kind);
    }
  } catch {
    showView("view-error");
    document.getElementById("btn-retry").onclick = boot;
  }
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}

boot();
