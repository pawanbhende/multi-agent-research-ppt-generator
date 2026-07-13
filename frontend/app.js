const API_BASE = "https://research-ppt-backend.onrender.com";

const form = document.querySelector("#generateForm");
const topicInput = document.querySelector("#topic");
const sourceInput = document.querySelector("#maxSources");
const slideInput = document.querySelector("#maxSlides");
const sourceValue = document.querySelector("#sourceValue");
const slideValue = document.querySelector("#slideValue");
const generateButton = document.querySelector("#generateButton");
const downloadButton = document.querySelector("#downloadButton");
const outlineList = document.querySelector("#outlineList");
const logList = document.querySelector("#logList");
const healthBadge = document.querySelector("#healthBadge");
const topicBadge = document.querySelector("#topicBadge");
const pipelineState = document.querySelector("#pipelineState");
const slideCount = document.querySelector("#slideCount");
const logCount = document.querySelector("#logCount");
const agentSteps = [...document.querySelectorAll(".agent-step")];

const agentOrder = ["researcher", "analyst", "designer"];

sourceInput.addEventListener("input", () => {
  sourceValue.textContent = sourceInput.value;
});

slideInput.addEventListener("input", () => {
  slideValue.textContent = slideInput.value;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    topic: topicInput.value.trim(),
    max_sources: Number(sourceInput.value),
    max_slides: Number(slideInput.value),
  };

  if (!payload.topic) return;

  setBusy(true);
  resetRun(payload.topic);
  addLog({ agent: "system", status: "started", message: "Submitted deck generation request." });

  try {
    const response = await fetch(`${API_BASE}/api/v1/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "The backend could not generate this deck.");
    }

    renderLogs(data.logs || []);

    if (!data.success) {
      throw new Error(data.error || "The agent pipeline ended with an error.");
    }

    renderOutline(data.outline || []);
    prepareDownload(data.pptx_path);
    pipelineState.textContent = "Complete";
    markAgentsComplete();
    addLog({ agent: "system", status: "completed", message: "Deck is ready to download." });
  } catch (error) {
    pipelineState.textContent = "Error";
    healthBadge.textContent = "API error";
    healthBadge.style.background = "#fde8ee";
    healthBadge.style.color = "#9a2741";
    addLog({ agent: "system", status: "error", message: error.message });
  } finally {
    setBusy(false);
  }
});

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/health`);
    const data = await response.json();
    if (!response.ok) throw new Error("unhealthy");

    healthBadge.textContent = `${data.status} - ${data.app_env}`;
    healthBadge.style.background = "#e6f7f3";
    healthBadge.style.color = "#0f665d";
    replaceInitialLog(`Backend connected at ${API_BASE}.`);
  } catch {
    healthBadge.textContent = "API offline";
    healthBadge.style.background = "#fff2db";
    healthBadge.style.color = "#8a5200";
    replaceInitialLog("Start the FastAPI backend on port 8000, then generate a deck.");
  }
}

function resetRun(topic) {
  downloadButton.classList.add("is-hidden");
  downloadButton.removeAttribute("href");
  topicBadge.textContent = topic;
  pipelineState.textContent = "Running";
  slideCount.textContent = "0";
  logCount.textContent = "0";
  logList.innerHTML = "";
  outlineList.className = "outline-list empty-state";
  outlineList.innerHTML = `
    <div>
      <strong>Agents are building the deck.</strong>
      <p>Research, analysis, and design results will appear when the backend finishes.</p>
    </div>
  `;
  agentSteps.forEach((step) => step.classList.remove("is-active", "is-complete"));
  setActiveAgent("researcher");
}

function setBusy(isBusy) {
  generateButton.disabled = isBusy;
  generateButton.innerHTML = isBusy
    ? '<span class="button-icon" aria-hidden="true">...</span> Generating'
    : '<span class="button-icon" aria-hidden="true">Go</span> Generate deck';
}

function renderLogs(logs) {
  if (!logs.length) return;
  logList.innerHTML = "";
  logs.forEach(addLog);
}

function addLog(log) {
  const line = document.createElement("div");
  line.className = `log-line ${log.status === "error" ? "error" : ""}`;
  line.innerHTML = `
    <span>${escapeHtml(log.agent)}</span>
    <p>${escapeHtml(log.message)}</p>
  `;
  logList.appendChild(line);
  logCount.textContent = String(logList.children.length);

  if (agentOrder.includes(log.agent)) {
    setActiveAgent(log.agent);
    if (log.status === "completed") {
      const step = document.querySelector(`[data-agent="${log.agent}"]`);
      step?.classList.add("is-complete");
    }
  }
}

function renderOutline(outline) {
  outlineList.className = "outline-list";
  outlineList.innerHTML = "";
  slideCount.textContent = String(outline.length);

  if (!outline.length) {
    outlineList.className = "outline-list empty-state";
    outlineList.innerHTML = `
      <div>
        <strong>No outline returned.</strong>
        <p>The backend completed, but did not provide slide content.</p>
      </div>
    `;
    return;
  }

  outline.forEach((slide) => {
    const card = document.createElement("article");
    card.className = "outline-card";
    const bullets = (slide.bullets || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    const citations = (slide.citations || []).slice(0, 3).map(escapeHtml).join(" - ");

    card.innerHTML = `
      <div class="outline-top">
        <span class="slide-number">${slide.slide_number}</span>
        <div>
          <span class="layout-pill">${escapeHtml(String(slide.layout || "content").replace("_", " "))}</span>
          <h4>${escapeHtml(slide.title || "Untitled slide")}</h4>
        </div>
      </div>
      ${slide.key_metric ? `<div class="metric">${escapeHtml(slide.key_metric)}</div>` : ""}
      ${bullets ? `<ul>${bullets}</ul>` : ""}
      ${citations ? `<div class="citations">Citations: ${citations}</div>` : ""}
    `;
    outlineList.appendChild(card);
  });
}

function prepareDownload(pptxPath) {
  if (!pptxPath) return;
  const filename = pptxPath.split(/[\\/]/).pop();
  if (!filename) return;

  downloadButton.href = `${API_BASE}/api/v1/download/${encodeURIComponent(filename)}`;
  downloadButton.classList.remove("is-hidden");
}

function setActiveAgent(agent) {
  agentSteps.forEach((step) => {
    step.classList.toggle("is-active", step.dataset.agent === agent);
  });
}

function markAgentsComplete() {
  agentSteps.forEach((step) => {
    step.classList.remove("is-active");
    step.classList.add("is-complete");
  });
}

function replaceInitialLog(message) {
  logList.innerHTML = `
    <div class="log-line muted">
      <span>system</span>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
  logCount.textContent = "1";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

checkHealth();