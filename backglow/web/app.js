const $ = (id) => document.getElementById(id);
const presets = ["#ff5900", "#ff0000", "#ff0080", "#a000ff", "#0040ff", "#00c8ff", "#00ff60", "#ffffff"];
let api = null;
let st = null;
let lastOn = 3;
let colourTimer = {};

function toast(text, kind = "") {
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.textContent = text;
  $("toasts").appendChild(el);
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 250); }, 2400);
}

function seg(el, options, current, onPick) {
  el.replaceChildren();
  options.forEach((name, i) => {
    const b = document.createElement("button");
    b.textContent = name;
    if (i === current) b.className = "on";
    b.addEventListener("click", () => onPick(i));
    el.appendChild(b);
  });
}

function kv(rows) {
  const box = $("devInfo");
  box.replaceChildren();
  rows.forEach(([k, v]) => {
    const row = document.createElement("div");
    row.className = "kv";
    const a = document.createElement("span"), b = document.createElement("span");
    a.textContent = k;
    b.textContent = v;
    row.append(a, b);
    box.appendChild(row);
  });
}

function setSwatch(which, value) {
  $(which + "Color").value = value;
  $(which + "Hex").textContent = value;
  $(which + "Sw").style.setProperty("--c", value);
}

function render() {
  const m = st && st.monitor;
  $("conn").textContent = m ? "Connected" : "Offline";
  $("conn").className = "conn " + (m ? "ok" : "bad");
  $("connSub").textContent = m ? m.model : (st && st.error) || "No monitor";
  $("fxSub").textContent = m ? m.model : (st && st.error) || "No monitor";
  $("devSub").textContent = m ? m.model : "—";
  $("permPill").textContent = st && st.error === "No access" ? "Denied" : m ? "OK" : "—";
  $("permPill").className = "pill " + (m ? "ok" : "bad");
  if (!m) {
    $("modes").replaceChildren();
    $("strength").replaceChildren();
    $("pattern").replaceChildren();
    kv([]);
    return;
  }
  if (m.strength) lastOn = m.strength;
  $("powerLabel").textContent = m.strength ? "Turn off" : "Turn on";
  const modes = $("modes");
  modes.replaceChildren();
  m.modes.forEach((name, i) => {
    const b = document.createElement("button");
    b.className = "mode" + (i === m.mode ? " on" : "");
    b.textContent = name;
    b.addEventListener("click", () => setField("mode", i));
    modes.appendChild(b);
  });
  seg($("strength"), m.strengths, m.strength, (i) => setField("strength", i));
  seg($("pattern"), m.patterns, m.pattern, (i) => setField("pattern", i));
  $("custom").classList.toggle("disabled", m.patterns[m.pattern] !== "Custom");
  setSwatch("bg", m.bg);
  setSwatch("fg", m.fg);
  kv([["Model", m.model], ["Bus", "/dev/i2c-" + m.bus], ["Effect", m.modes[m.mode]], ["Colour", m.patterns[m.pattern]], ["Brightness", m.strengths[m.strength]]]);
}

async function load() {
  st = await api.state();
  $("version").textContent = "v" + st.version;
  render();
}

function setField(key, value) {
  if (!st || !st.monitor) return;
  st.monitor[key] = value;
  render();
  api.set(key, value);
}

window.onWriteError = (text) => { toast(text, "bad"); load(); };

function sendColour(which, value) {
  clearTimeout(colourTimer[which]);
  setSwatch(which, value);
  if (!st || !st.monitor) return;
  const m = st.monitor;
  const custom = m.patterns.indexOf("Custom");
  if (m.pattern !== custom) setField("pattern", custom);
  api.colour(which, value);
  m[which] = value;
}

function settleColour(which, value) {
  setSwatch(which, value);
  clearTimeout(colourTimer[which]);
  colourTimer[which] = setTimeout(() => sendColour(which, value), 1000);
}

function init() {
  api = window.pywebview.api;
  document.querySelectorAll(".nav-item").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((x) => x.classList.toggle("active", x === b));
    document.querySelectorAll(".page").forEach((p) => p.classList.toggle("active", p.id === "page-" + b.dataset.page));
  }));
  const box = $("presets");
  presets.forEach((c) => {
    const b = document.createElement("button");
    b.className = "sw";
    b.style.setProperty("--c", c);
    b.title = c;
    b.addEventListener("click", () => sendColour("bg", c));
    box.appendChild(b);
  });
  ["bg", "fg"].forEach((w) => {
    $(w + "Color").addEventListener("input", (e) => settleColour(w, e.target.value));
  });
  $("reloadBtn").addEventListener("click", load);
  $("powerBtn").addEventListener("click", () => st && st.monitor && setField("strength", st.monitor.strength ? 0 : lastOn));
  $("copyRule").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText($("rule").textContent); toast("Copied"); } catch { toast("Can't copy", "bad"); }
  });
  load();
}

if (window.pywebview && window.pywebview.api) init();
else window.addEventListener("pywebviewready", init);
