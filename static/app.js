const LS_KEY = "verify_cfg";
const FIELDS = [
  ["app_key", "平台 AppKey", "text"],
  ["app_secret", "平台 AppSecret", "password"],
  ["api_base", "平台地址 api_base (http://ip:port)", "text"],
  ["ws_base", "WebSocket 地址 ws_base (ws://ip:port)", "text"],
  ["minio_endpoint", "MinIO endpoint (minio-host:9000)", "text"],
  ["minio_access_key", "MinIO AccessKey", "text"],
  ["minio_secret_key", "MinIO SecretKey", "password"],
  ["minio_bucket", "MinIO Bucket", "text"],
  ["minio_secure", "MinIO secure (true/false)", "text"],
  ["minio_public_base_url", "MinIO 公开基址 (http://host:9000/bucket)", "text"],
  ["directory", "目录名", "text"],
  ["kafka_bootstrap_servers", "Kafka broker (ip:9092)", "text"],
  ["concurrency", "并发数 (默认5)", "text"],
  ["timeout_seconds", "超时秒数 (默认300)", "text"],
];

const form = document.getElementById("cfgForm");
FIELDS.forEach(([k, label, type]) => {
  const wrap = document.createElement("label");
  wrap.className = "field";
  const span = document.createElement("span");
  span.textContent = label;
  const inp = document.createElement("input");
  inp.name = k; inp.id = "f_" + k; inp.type = type || "text"; inp.autocomplete = "off";
  wrap.appendChild(span);
  wrap.appendChild(inp);
  form.appendChild(wrap);
});

function loadSaved() {
  try {
    const s = JSON.parse(localStorage.getItem(LS_KEY) || "{}");
    Object.keys(s).forEach(k => {
      const el = document.getElementById("f_" + k);
      if (el) el.value = s[k];
    });
  } catch (e) {}
}
async function loadServerConfig() {
  try {
    const r = await fetch("/api/config");
    const d = await r.json();
    Object.keys(d).forEach(k => {
      const el = document.getElementById("f_" + k);
      if (el) el.value = d[k];
    });
  } catch (e) {}
}
loadSaved();
loadServerConfig();

let polling = false;
let selectedId = null;
let lastData = null;

function setMsg(t) { document.getElementById("statusMsg").textContent = t; }

document.getElementById("startBtn").onclick = async () => {
  const cfg = {};
  FIELDS.forEach(([k]) => {
    const el = document.getElementById("f_" + k);
    cfg[k] = el.value;
  });
  localStorage.setItem(LS_KEY, JSON.stringify(cfg));
  setMsg("正在启动…");
  try {
    const r = await fetch("/api/start", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cfg),
    });
    const d = await r.json();
    if (d.ok) { setMsg("已启动，正在接收结果…"); startPolling(); }
    else setMsg("启动失败: " + JSON.stringify(d));
  } catch (e) { setMsg("启动异常: " + e); }
};

document.getElementById("stopBtn").onclick = async () => {
  try { await fetch("/api/stop", { method: "POST" }); } catch (e) {}
  stopPolling();
  setMsg("已停止");
};

function startPolling() { if (polling) return; polling = true; tick(); }
function stopPolling() { polling = false; }
async function tick() {
  if (!polling) return;
  try {
    const r = await fetch("/api/results");
    const d = await r.json();
    render(d);
  } catch (e) {}
  setTimeout(tick, 2000);
}

function render(d) {
  lastData = d;
  const list = document.getElementById("imgList");
  list.innerHTML = "";
  d.items.forEach(it => {
    const div = document.createElement("div");
    div.className = "item" + (it.id === selectedId ? " active" : "");
    div.innerHTML = `<span class="badge b_${it.status}">${it.status}</span>` +
      `<span class="fname">${esc(it.filename || it.id)}</span>`;
    div.onclick = () => { selectedId = it.id; render(d); };
    list.appendChild(div);
  });
  if (!selectedId && d.items.length) selectedId = d.items[0].id;
  const cur = d.items.find(x => x.id === selectedId);
  const detail = document.getElementById("detail");
  if (!cur) { detail.innerHTML = '<p class="hint">从左侧选择一张图片查看识别结果</p>'; return; }
  detail.innerHTML = renderDetail(cur);
  const canvas = detail.querySelector("canvas");
  drawCanvas(canvas, cur.minio_url, cur.alarms);
}

function renderDetail(it) {
  const streamHtml = it.stream.length
    ? it.stream.map(s => `<div class="kv"><b>themeLabel:</b> ${esc(s.themeLabel)} ` +
        `<b>ocrMessage:</b> ${esc(s.ocrMessage)} <b>sourceName:</b> ${esc(s.sourceName)} ` +
        `<b>耗时:</b> ${dur(s)} <b>isError:</b> ${esc(s.isError)}</div>`).join("")
    : '<div class="muted">无流水记录</div>';
  const alarmHtml = it.alarms.length
    ? it.alarms.map(a => {
        let boxes = [];
        try { boxes = JSON.parse(a.alarmBoxs || "[]"); } catch (e) {}
        return `<div class="kv"><b>themeLabel:</b> ${esc(a.themeLabel)} ` +
          `<b>alarmLevel:</b> ${esc(a.alarmLevel)} <b>框数:</b> ${boxes.length}</div>`;
      }).join("")
    : '<div class="muted">无预警记录</div>';
  return `
    <h3>${esc(it.filename || it.id)} <span class="badge b_${it.status}">${it.status}</span></h3>
    <div class="imgs">
      <div><div class="cap">原图</div><img src="${it.minio_url}" onerror="this.alt='图片加载失败(确认MinIO可达)'"></div>
      <div><div class="cap">检测框</div><canvas></canvas></div>
    </div>
    <div class="cols">
      <div class="col"><h4>流水信息 (${it.stream_count})</h4>${streamHtml}</div>
      <div class="col"><h4>预警信息 (${it.alarm_count})</h4>${alarmHtml}</div>
    </div>`;
}

function drawCanvas(canvas, url, alarms) {
  const img = new Image();
  img.onload = () => {
    const MAXW = 560;
    const scale = Math.min(MAXW / img.naturalWidth, 1) || 1;
    canvas.width = img.naturalWidth * scale;
    canvas.height = img.naturalHeight * scale;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const boxes = [];
    (alarms || []).forEach(a => {
      try { JSON.parse(a.alarmBoxs || "[]").forEach(b => boxes.push(b)); } catch (e) {}
    });
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#ff3b30";
    ctx.font = "14px sans-serif";
    boxes.forEach(b => {
      const [x1, y1, x2, y2] = b.box;
      const X = x1 * scale, Y = y1 * scale, W = (x2 - x1) * scale, H = (y2 - y1) * scale;
      ctx.strokeRect(X, Y, W, H);
      const label = (b.tag || "") + (b.conf != null ? " " + (b.conf * 100).toFixed(1) + "%" : "");
      ctx.fillStyle = "rgba(255,59,48,0.9)";
      ctx.fillText(label, X, Y > 14 ? Y - 3 : Y + 14);
    });
    if (!boxes.length) { ctx.fillStyle = "#888"; ctx.fillText("无检测框", 10, 20); }
  };
  img.src = url;
}

function dur(s) {
  if (!s.inTime || !s.outTime) return "-";
  try { return ((Number(s.outTime) - Number(s.inTime)) / 1000).toFixed(2) + "s"; } catch (e) { return "-"; }
}
function esc(v) {
  if (v == null) return "";
  return String(v).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}
