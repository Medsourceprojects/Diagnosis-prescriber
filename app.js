const state = {
  diagnoses: [],
  filtered: [],
  selected: null,
  category: "All",
  query: "",
  editingPrescription: false,
};

const emergencyOnly = new Set([
  "Acute Cholecystitis",
  "Appendicitis",
  "Diabetic Ketoacidosis",
  "Anaphylactic Shock",
  "Acute Respiratory Failure",
  "Cardiac Arrest",
  "Cardiogenic Shock",
  "Ectopic Pregnancy",
  "Meningitis",
  "Organophosphorus Poisoning",
  "Snake Bite",
  "Tension Pneumothorax",
]);

const el = {
  search: document.querySelector("#searchInput"),
  select: document.querySelector("#diagnosisSelect"),
  list: document.querySelector("#diagnosisList"),
  count: document.querySelector("#resultCount"),
  filters: document.querySelector("#categoryFilters"),
  empty: document.querySelector("#emptyState"),
  card: document.querySelector("#detailCard"),
  title: document.querySelector("#diagnosisTitle"),
  badge: document.querySelector("#categoryBadge"),
  alerts: document.querySelector("#alerts"),
  essentials: document.querySelector("#essentialsList"),
  treatment: document.querySelector("#treatmentList"),
  rxDisplay: document.querySelector("#prescriptionDisplay"),
  rx: document.querySelector("#prescriptionText"),
  editRx: document.querySelector("#editRxBtn"),
  copy: document.querySelector("#copyBtn"),
  print: document.querySelector("#printBtn"),
  printArea: document.querySelector("#printArea"),
  toast: document.querySelector("#toast"),
};

function normalize(value) {
  return (value || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function levenshtein(a, b) {
  if (!a || !b) return Math.max(a.length, b.length);
  const dp = Array.from({ length: a.length + 1 }, (_, i) => [i]);
  for (let j = 1; j <= b.length; j += 1) dp[0][j] = j;
  for (let i = 1; i <= a.length; i += 1) {
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[a.length][b.length];
}

function scoreDiagnosis(diagnosis, query) {
  const name = normalize(diagnosis.diagnosis);
  const q = normalize(query);
  if (!q) return 1;
  if (name.includes(q)) return 100 - name.indexOf(q);
  const words = diagnosis.diagnosis.split(/\s+/).map(normalize);
  if (words.some((word) => word.startsWith(q))) return 85;
  const bestDistance = Math.min(...words.map((word) => levenshtein(word.slice(0, q.length + 1), q)));
  const allowedDistance = q.length <= 4 ? 1 : 2;
  if (bestDistance <= allowedDistance) return 60 - bestDistance;
  if (q.length >= 5) {
    let cursor = 0;
    for (const char of name) {
      if (char === q[cursor]) cursor += 1;
      if (cursor === q.length) return 45;
    }
  }
  return 0;
}

function renderList() {
  const query = state.query;
  state.filtered = state.diagnoses
    .map((item) => ({ item, score: scoreDiagnosis(item, query) }))
    .filter(({ item, score }) => score > 0 && (state.category === "All" || item.category === state.category))
    .sort((a, b) => (query ? b.score - a.score : a.item.diagnosis.localeCompare(b.item.diagnosis)))
    .map(({ item }) => item);

  el.count.textContent = `${state.filtered.length} diagnoses`;
  el.list.innerHTML = "";
  el.select.innerHTML = "";

  if (!state.filtered.length) {
    el.list.innerHTML = `<div class="alert amber">No diagnosis found. Try a shorter spelling fragment.</div>`;
    el.select.innerHTML = `<option>No matches</option>`;
    return;
  }

  if (!state.filtered.some((item) => item.id === state.selected?.id)) {
    const placeholder = document.createElement("option");
    placeholder.textContent = "Choose from matches";
    placeholder.value = "";
    placeholder.selected = true;
    placeholder.disabled = true;
    el.select.append(placeholder);
  }

  for (const diagnosis of state.filtered) {
    const option = document.createElement("option");
    option.value = diagnosis.id;
    option.textContent = diagnosis.diagnosis;
    option.selected = state.selected?.id === diagnosis.id;
    el.select.append(option);

    const button = document.createElement("button");
    button.type = "button";
    button.className = `diagnosis-item${state.selected?.id === diagnosis.id ? " active" : ""}`;
    button.innerHTML = `<span>${diagnosis.diagnosis}</span><span class="mini-badge">${diagnosis.category}</span>`;
    button.addEventListener("click", () => selectDiagnosis(diagnosis.id));
    el.list.append(button);
  }
}

function renderFilters() {
  const categories = ["All", ...Array.from(new Set(state.diagnoses.map((item) => item.category))).sort()];
  el.filters.innerHTML = "";
  for (const category of categories) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `filter-chip${category === state.category ? " active" : ""}`;
    button.textContent = category;
    button.addEventListener("click", () => {
      state.category = category;
      renderFilters();
      renderList();
    });
    el.filters.append(button);
  }
}

function renderBullets(target, items) {
  target.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    target.append(li);
  }
}

function cleanPrescription(text) {
  const lines = [];
  for (const rawLine of (text || "").split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      if (lines.length && lines[lines.length - 1] !== "") lines.push("");
      continue;
    }
    if (/^(Dose|Route|Frequency|Duration|Instructions):\s*$/i.test(line)) continue;
    if (/^[-•]\s*$/.test(line)) continue;
    lines.push(line);
  }
  while (lines[lines.length - 1] === "") lines.pop();
  return lines.join("\n");
}

function currentPrescription() {
  return state.editingPrescription ? cleanPrescription(el.rx.value) : cleanPrescription(el.rxDisplay.textContent);
}

function renderPrescription(text) {
  const cleaned = cleanPrescription(text);
  el.rx.value = cleaned;
  el.rxDisplay.textContent = cleaned;
  el.rx.classList.toggle("is-hidden", !state.editingPrescription);
  el.rxDisplay.classList.toggle("is-hidden", state.editingPrescription);
  el.editRx.textContent = state.editingPrescription ? "Done Editing" : "Edit Prescription";
}

function renderDetail(disease) {
  el.empty.classList.add("hidden");
  el.card.classList.remove("hidden");
  el.title.textContent = disease.diagnosis;
  el.badge.textContent = disease.category;

  el.alerts.innerHTML = "";
  if (emergencyOnly.has(disease.diagnosis)) {
    const alert = document.createElement("div");
    alert.className = "alert red";
    alert.textContent = "Urgent referral/admission advised.";
    el.alerts.append(alert);
  }

  renderBullets(el.essentials, disease.essentialsOfDiagnosis);
  renderBullets(el.treatment, disease.treatmentManagement);
  state.editingPrescription = false;
  renderPrescription(disease.prescription);
}

function selectDiagnosis(key) {
  const diagnosis = state.diagnoses.find((item) => item.id === key || item.diagnosis === key);
  if (!diagnosis) return;
  state.selected = diagnosis;
  el.select.value = diagnosis.id;
  renderList();
  renderDetail(diagnosis);
}

function renderPrintArea() {
  const disease = state.selected;
  const prescription = currentPrescription();
  el.printArea.innerHTML = `
    <h1>Prescription</h1>
    <p class="print-note">Doctor reference only — verify before prescribing.</p>
    <div class="print-grid">
      <div><strong>Patient:</strong> ________________________</div>
      <div><strong>Age/Sex:</strong> __________ / __________</div>
      <div><strong>Diagnosis:</strong> ${escapeHtml(disease?.diagnosis || "")}</div>
      <div><strong>Date:</strong> __________</div>
    </div>
    <div class="print-rx">${escapeHtml(prescription)}</div>
    <div class="signature"><div>Doctor name/signature: ________________________</div></div>
  `;
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

function showToast(message) {
  el.toast.textContent = message;
  el.toast.classList.add("show");
  window.setTimeout(() => el.toast.classList.remove("show"), 1800);
}

async function init() {
  try {
    const response = await fetch("data/diagnoses.json");
    if (!response.ok) throw new Error("Unable to load diagnosis data");
    state.diagnoses = await response.json();
    state.filtered = state.diagnoses;
    renderFilters();
    renderList();
  } catch (error) {
    el.count.textContent = "Data error";
    el.list.innerHTML = `<div class="alert red">${error.message}</div>`;
  }
}

el.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderList();
});

el.select.addEventListener("change", (event) => selectDiagnosis(event.target.value));
el.editRx.addEventListener("click", () => {
  state.editingPrescription = !state.editingPrescription;
  renderPrescription(el.rx.value);
});
el.rx.addEventListener("input", () => {
  if (state.editingPrescription) {
    el.rxDisplay.textContent = cleanPrescription(el.rx.value);
  }
});
el.copy.addEventListener("click", async () => {
  const text = currentPrescription();
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const temp = document.createElement("textarea");
    temp.value = text;
    temp.setAttribute("readonly", "");
    temp.style.position = "fixed";
    temp.style.left = "-9999px";
    document.body.append(temp);
    temp.select();
    document.execCommand("copy");
    temp.remove();
  }
  showToast("Prescription copied");
});
el.print.addEventListener("click", () => {
  const text = currentPrescription();
  el.rx.value = text;
  el.rxDisplay.textContent = text;
  renderPrintArea();
  window.print();
});

init();
