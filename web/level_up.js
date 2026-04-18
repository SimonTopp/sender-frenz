import { hideLevelUpBadge } from "./avatar.js";
import { showView } from "./ui.js";

let _avatarId = null;
let _selectedSkin = null;
let _selectedRoom = null;

export function bindLevelUp(avatarId) {
  _avatarId = avatarId;
  document
    .getElementById("level-up-badge")
    .addEventListener("click", openPicker);
  document
    .getElementById("btn-confirm-level-up")
    .addEventListener("click", confirmLevelUp);
  document
    .getElementById("btn-cancel-level-up")
    .addEventListener("click", closePicker);
}

async function openPicker() {
  try {
    const res = await fetch(`/avatar/${_avatarId}`);
    if (!res.ok) return;
    const data = await res.json();
    renderOptions("skin-options", data.level.skin_upgrades);
    renderOptions("room-options", data.level.room_upgrades);
  } catch {
    return;
  }
  _selectedSkin = null;
  _selectedRoom = null;
  document.getElementById("btn-confirm-level-up").disabled = true;
  showView("view-level-up");
}

function renderOptions(containerId, slugs) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  for (const slug of slugs) {
    const card = document.createElement("div");
    card.className = "option-card";
    card.dataset.slug = slug;
    card.textContent = slug
      .split("-")
      .map((w) => w[0].toUpperCase() + w.slice(1))
      .join(" ");
    card.addEventListener("click", () => selectOption(containerId, slug, card));
    container.appendChild(card);
  }
}

function selectOption(containerId, slug, card) {
  document
    .querySelectorAll(`#${containerId} .option-card`)
    .forEach((c) => c.classList.remove("option-card--selected"));
  card.classList.add("option-card--selected");
  if (containerId === "skin-options") _selectedSkin = slug;
  else _selectedRoom = slug;
  document.getElementById("btn-confirm-level-up").disabled = !(
    _selectedSkin && _selectedRoom
  );
}

async function confirmLevelUp() {
  try {
    const res = await fetch("/level-up", {
      method: "POST",
      headers: {
        "avatar-id": _avatarId,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        skin_slug: _selectedSkin,
        room_slug: _selectedRoom,
      }),
    });
    if (!res.ok) throw new Error(`${res.status}`);
  } catch {
    document.getElementById("quip").textContent =
      "THE SYSTEM REJECTED YOUR SELECTIONS. RECONSIDER.";
  } finally {
    hideLevelUpBadge();
    _selectedSkin = null;
    _selectedRoom = null;
    showView("view-main");
  }
}

function closePicker() {
  _selectedSkin = null;
  _selectedRoom = null;
  document.getElementById("btn-confirm-level-up").disabled = true;
  showView("view-main");
}
