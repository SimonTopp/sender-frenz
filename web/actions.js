import { updateFromAction } from "./avatar.js";

export function bindActions(avatarId) {
  document.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", () =>
      handleAction(btn.dataset.action, avatarId)
    );
  });
}

export async function handleAction(kind, avatarId) {
  const btn = document.querySelector(`[data-action="${kind}"]`);
  if (!btn || btn.disabled) return;

  if ("vibrate" in navigator) navigator.vibrate(30);
  btn.disabled = true;

  try {
    const res = await fetch(`/action/${kind}`, {
      method: "POST",
      headers: { "avatar-id": avatarId },
    });
    if (!res.ok) throw new Error(`${res.status}`);
    updateFromAction(await res.json());
  } catch {
    document.getElementById("quip").textContent =
      "THE SYSTEM ENCOUNTERED AN ISSUE. YOUR CONCERN HAS BEEN LOGGED.";
  } finally {
    btn.disabled = false;
  }
}
