// 模型识别验证服务 前端逻辑

// 左侧配置字段：大模型服务登录使用 AppKey/AppSecret（即 AK/SK）
const FIELDS = [
  ["app_key", "大模型服务 AppKey (AK)", "text"],
  ["app_secret", "大模型服务 AppSecret (SK)", "password"],
  ["api_base", "API Base (登录/WS域名, 不含路径)", "text"],
  ["ws_base", "WebSocket Base (不含 /apiWs)", "text"],
  ["minio_endpoint", "MinIO Endpoint", "text"],
  ["minio_access_key", "MinIO AccessKey", "text"],
  ["minio_secret_key", "MinIO SecretKey", "password"],
  ["minio_bucket", "MinIO Bucket", "text"],
  ["minio_secure", "MinIO Secure (true/false)", "text"],
  ["minio_public_base_url", "MinIO 公网 Base URL", "text"],
  ["directory", "MinIO 目录 (如 /vehicle/sichuan)", "text"],
  ["kafka_bootstrap_servers", "Kafka BootstrapServers", "text"],
  ["topic_receive_image", "接图 Topic", "text"],
  ["device_id", "设备ID", "text"],
  ["device_name", "设备名称", "text"],
  ["concurrency", "并发数", "number"],
  ["timeout_seconds", "超时秒数", "number"],
];

const LS_KEY = "verify_cfg_v1";
let currentId = null;
let pollTimer = null;

// ---------- 配置表单 ----------
function buildForm() {
  const form = document.getElementById("cfgForm");
  const saved = JSON.parse(localStorage.getItem(LS_KEY) || "{}");
  form.innerHTML = "";
  FIELDS.forEach(([key, label, type]) => {
    const div = document.createElement("div");
    div.className = "field";
    const lab = document.createElement("label");
    lab.textContent = label;
    const inp = document.createElement("input");
    inp.name = key;
    inp.type = type;
    inp.value = saved[key] ?? "";
    div.appendChild(lab);
    div.appendChild(inp);
    form.appendChild(div);
  });
}

async function loadServerConfig() {
  try {
    const r = await fetch("/api/config");
    const cfg = await r.json();
    const form = document.getElementById("cfgForm");
    FIELDS.forEach(([key]) => {
      const inp = form.elements[key];
      if (inp && cfg[key] != null && inp.value === "") {
        inp.value = cfg[key];
      }
    });
  } catch (e) {
    console.warn("读取服务端配置失败", e);
  }
}

function collectForm() {
  const form = document.getElementById("cfgForm");
  const cfg = {};
  FIELDS.forEach(([key]) => {
    cfg[key] = form.elements[key].value.trim();
  });
  localStorage.setItem(LS_KEY, JSON.stringify(cfg));
  return cfg;
}

// ---------- 列表与详情 ----------
function statusBadge(status) {
  const map = {
    "已完成": "b-done",
    "有预警": "b-alarm",
    "超时": "b-timeout",
    "已发送": "b-sent",
  };
  const cls = map[status] || "b-sent";
  return `<span class="badge ${cls}">${status}</span>`;
}

async function refreshList() {
  const r = await fetch("/api/results");
  const d = await r.json();
  const list = document.getElementById("imgList");
  list.innerHTML = "";
  d.items.forEach((it) => {
    const div = document.createElement("div");
    div.className = "list-item" + (it.id === currentId ? " active" : "");
    div.innerHTML = `${it.filename || it.id}${statusBadge(it.status)}`;
    div.onclick = () => { currentId = it.id; renderDetail(it); refreshList(); };
    list.appendChild(div);
  });
  if (currentId) {
    const cur = d.items.find((x) => x.id === currentId);
    if (cur) renderDetail(cur);
  }
}

function renderDetail(it) {
  const el = document.getElementById("detail");
  const drawUrl = it.minio_url || (it.stream[0] && it.stream[0].sceneImgUrl);
  let html = `<div class="meta">文件: ${it.filename || "-"} | 状态: ${statusBadge(it.status)} | 流水: ${it.stream_count} 条 | 预警: ${it.alarm_count} 条</div>`;
  if (it.minio_url) html += `<div class="meta">MinIO: ${it.minio_url}</div>`;
  html += `<div class="row"><div>`;
  if (drawUrl) {
    html += `<img id="srcImg" src="${drawUrl}" style="max-width:100%;border:1px solid #eee;border-radius:4px;" onload="drawBoxes()" />`;
    html += `<canvas id="boxCanvas" style="position:relative;"></canvas>`;
  } else {
    html += `<div class="detail-empty">无图片地址</div>`;
  }
  html += `</div><div>`;
  html += `<div style="font-size:13px;font-weight:600;margin-bottom:6px;">流水信息</div><pre id="streamPre">${formatJson(it.stream)}</pre>`;
  html += `<div style="font-size:13px;font-weight:600;margin:10px 0 6px;">预警信息</div><pre id="alarmPre">${formatJson(it.alarms)}</pre>`;
  html += `</div></div>`;
  el.innerHTML = html;
}

function formatJson(v) {
  try { return JSON.stringify(v, null, 2); } catch (e) { return String(v); }
}

window.drawBoxes = function () {
  const img = document.getElementById("srcImg");
  const canvas = document.getElementById("boxCanvas");
  if (!img || !canvas) return;
  const w = img.naturalWidth, h = img.naturalHeight;
  if (!w || !h) return;
  // 画布按原图像素尺寸绘制，再用 CSS 缩放到显示尺寸，保证绝对像素坐标对齐
  canvas.width = w; canvas.height = h;
  canvas.style.width = img.clientWidth + "px";
  canvas.style.height = img.clientHeight + "px";
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, w, h);
  const alarmBoxs = (currentAlarms() || []).flatMap((a) => a.alarmBoxs || []);
  alarmBoxs.forEach((b) => {
    const x = Number(b.x), y = Number(b.y), bw = Number(b.width), bh = Number(b.height);
    if ([x, y, bw, bh].some((n) => Number.isNaN(n))) return;
    ctx.strokeStyle = "#e74c3c";
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, bw, bh);
    if (b.tag) {
      ctx.fillStyle = "#e74c3c";
      ctx.font = "12px sans-serif";
      ctx.fillText(`${b.tag}${b.conf != null ? " " + b.conf : ""}`, x, y > 12 ? y - 4 : y + 12);
    }
  });
};

let _lastAlarms = [];
function currentAlarms() { return _lastAlarms; }

// 轮询结果，并在拿到新数据时记录预警用于画框
async function poll() {
  const r = await fetch("/api/results");
  const d = await r.json();
  _lastAlarms = [];
  d.items.forEach((it) => { if (it.alarms) _lastAlarms.push(...it.alarms); });
  await refreshList();
  if (currentId) {
    const cur = d.items.find((x) => x.id === currentId);
    if (cur) renderDetail(cur);
  }
}

// ---------- 调试日志面板 ----------
const logPanel = document.getElementById("logPanel");
const logBody = document.getElementById("logBody");
let logOpen = false, logTimer = null;

document.getElementById("logBtn").onclick = () => {
  logOpen = !logOpen;
  logPanel.classList.toggle("show", logOpen);
  if (logOpen) { fetchLogs(); logTimer = setInterval(fetchLogs, 2000); }
  else { clearInterval(logTimer); }
};
document.getElementById("logClose").onclick = () => {
  logOpen = false; logPanel.classList.remove("show"); clearInterval(logTimer);
};
document.getElementById("logRefresh").onclick = fetchLogs;

async function fetchLogs() {
  if (!logOpen) return;
  try {
    const r = await fetch("/api/logs?limit=200");
    const d = await r.json();
    logBody.textContent = (d.logs || []).join("\n");
    logBody.scrollTop = logBody.scrollHeight;
  } catch (e) { /* 忽略 */ }
}

// ---------- 操作 ----------
document.getElementById("startBtn").onclick = async () => {
  const cfg = collectForm();
  document.getElementById("status").textContent = "正在启动...";
  const r = await fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  });
  const d = await r.json();
  if (d.ok) {
    document.getElementById("status").textContent = `已发起 ${d.count} 张图片，正在接收...`;
    if (!pollTimer) pollTimer = setInterval(poll, 2000);
    poll();
  } else {
    document.getElementById("status").textContent = "启动失败: " + d.error;
  }
};

document.getElementById("stopBtn").onclick = async () => {
  await fetch("/api/stop", { method: "POST" });
  document.getElementById("status").textContent = "已停止";
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
};

// ---------- 初始化 ----------
buildForm();
loadServerConfig();
