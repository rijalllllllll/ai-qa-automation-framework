const form = document.getElementById("storyForm");
const btn = document.getElementById("generateBtn");
const regenBtn = document.getElementById("regenerateBtn");
const errorBox = document.getElementById("errorBox");
const loading = document.getElementById("loading");
const storyView = document.getElementById("storyView");
const history = document.getElementById("history");
const historyList = document.getElementById("historyList");

const HISTORY_KEY = "story_history";

function readForm() {
  return {
    child_name: document.getElementById("childName").value.trim(),
    age: Number(document.getElementById("age").value),
    mood: document.getElementById("mood").value,
    character: document.getElementById("character").value.trim(),
    moral: document.getElementById("moral").value.trim(),
    length: document.getElementById("length").value,
  };
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.textContent = "";
  errorBox.hidden = true;
}

function renderStory(data) {
  document.getElementById("storyTitle").textContent = data.title;
  document.getElementById("storyMeta").textContent =
    `${data.word_count} words · ${data.request.length} · v${data.meta.provider}`;
  document.getElementById("sections").innerHTML = data.sections
    .map((s) => `<h4>${s.heading}</h4><p>${s.text}</p>`)
    .join("");
  document.getElementById("moralLine").textContent = `🌟 ${data.moral}`;
  storyView.hidden = false;
  regenBtn.hidden = false;
  addHistory(data.title);
}

function addHistory(title) {
  let items = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  items.unshift({ title, at: new Date().toISOString() });
  items = items.slice(0, 5);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items));
  renderHistory(items);
}

function renderHistory(items) {
  if (!items.length) return;
  historyList.innerHTML = items
    .map((i) => `<li>${i.title} <span class="muted">${new Date(i.at).toLocaleTimeString()}</span></li>`)
    .join("");
  history.hidden = false;
}

async function generate() {
  clearError();
  btn.disabled = true;
  loading.hidden = false;
  try {
    const res = await fetch("/api/generate-story", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readForm()),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = body.detail && Array.isArray(body.detail)
        ? body.detail.map((d) => d.msg).join("; ")
        : "Something went wrong. Try again.";
      throw new Error(msg);
    }
    renderStory(body);
  } catch (err) {
    showError(err.message || "Unexpected error");
  } finally {
    btn.disabled = false;
    loading.hidden = true;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  generate();
});
regenBtn.addEventListener("click", generate);

renderHistory(JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"));