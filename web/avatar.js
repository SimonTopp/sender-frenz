const avatar = document.getElementById("avatar");

// ---------------------------------------------------------------------------
// Animation engine
// ---------------------------------------------------------------------------

function triggerClass(cls, durationMs) {
  avatar.classList.add(cls);
  setTimeout(() => avatar.classList.remove(cls), durationMs);
}

function triggerStageTransition(direction) {
  const newStage = avatar.dataset.nextStage;
  triggerClass(`anim--vampiric-${direction}`, 1000);
  if (newStage) {
    setTimeout(() => {
      avatar.dataset.stage = newStage;
      delete avatar.dataset.nextStage;
    }, 1000);
  }
}

const ANIMATION_MAP = {
  hunger_warning: () => triggerClass("anim--hunger-warn", 1200),
  hunger_critical: () => triggerClass("anim--hunger-crit", 800),
  hygiene_warning: () => triggerClass("anim--hygiene-warn", 1200),
  hygiene_critical: () => triggerClass("anim--hygiene-crit", 800),
  social_warning: () => triggerClass("anim--social-warn", 1500),
  social_critical: () => triggerClass("anim--social-crit", 1500),
  vampiric_advance: () => triggerStageTransition("advance"),
  vampiric_retreat: () => triggerStageTransition("retreat"),
  level_up_ready: () => showLevelUpBadge(),
};

export function applyEvent(kind) {
  const handler = ANIMATION_MAP[kind];
  if (handler) handler();
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

export function renderAvatar(session) {
  const app = session.appearance;
  const social = session.social_summary;

  avatar.dataset.skin = app.skin_slug || "";
  avatar.dataset.stage = app.vampiric_stage;
  avatar.dataset.hunger = app.hunger_visual;
  avatar.dataset.hygiene = app.hygiene_visual;

  document.getElementById("meter-hunger").style.width =
    `${session.needs.hunger * 100}%`;
  document.getElementById("meter-hygiene").style.width =
    `${session.needs.hygiene * 100}%`;
  document.getElementById("meter-social").style.width =
    `${session.social.score * 100}%`;
  document.getElementById("social-stage-label").textContent =
    social.stage_label;

  const quips = session.quips;
  if (quips && quips.length > 0) {
    document.getElementById("quip").textContent = quips[quips.length - 1];
  }

  if (session.level_up_available) {
    showLevelUpBadge();
  } else {
    hideLevelUpBadge();
  }
}

export function updateFromAction(response) {
  document.getElementById("meter-hunger").style.width =
    `${response.needs.hunger * 100}%`;
  document.getElementById("meter-hygiene").style.width =
    `${response.needs.hygiene * 100}%`;
  document.getElementById("quip").textContent = response.quip;
}

export function showLevelUpBadge() {
  document.getElementById("level-up-badge").classList.remove("level-up-badge--hidden");
}

export function hideLevelUpBadge() {
  document.getElementById("level-up-badge").classList.add("level-up-badge--hidden");
}

// Expose for Playwright tests
window._applyEvent = applyEvent;
