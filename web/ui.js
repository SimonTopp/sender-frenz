/** Switch to named view, hiding all others. */
export function showView(id) {
  document.querySelectorAll(".view").forEach((v) =>
    v.classList.add("view--hidden")
  );
  document.getElementById(id).classList.remove("view--hidden");
}
