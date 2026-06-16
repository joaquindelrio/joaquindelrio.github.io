<?php
// --- Config ---
$API_URL = "http://91.186.8.97:55060/estado";
$TIMEOUT_S = 10;

// --- Fetch JSON server-side (evita mixed content) ---
$ctx = stream_context_create([
  "http" => [
    "timeout" => $TIMEOUT_S,
    "header"  => "User-Agent: quim.obsea.es telit-dashboard\r\n"
  ]
]);

$json = @file_get_contents($API_URL, false, $ctx);
if ($json === false) {
  http_response_code(502);
  $err = error_get_last();
  $msg = $err ? $err["message"] : "Error desconocido";
  ?>
  <!doctype html><html lang="es"><meta charset="utf-8">
  <title>Estado Telit - Error</title>
  <h2>Error leyendo API</h2>
  <p>No he podido leer: <code><?= htmlspecialchars($API_URL) ?></code></p>
  <pre><?= htmlspecialchars($msg) ?></pre>
  </html>
  <?php
  exit;
}

$data = json_decode($json, true);
if (!$data || !isset($data["rows"])) {
  http_response_code(502);
  ?>
  <!doctype html><html lang="es"><meta charset="utf-8">
  <title>Estado Telit - Error</title>
  <h2>Respuesta JSON inválida</h2>
  <p>URL: <code><?= htmlspecialchars($API_URL) ?></code></p>
  <pre><?= htmlspecialchars(substr($json, 0, 2000)) ?></pre>
  </html>
  <?php
  exit;
}

$rows = $data["rows"];
$generated_at = $data["generated_at"] ?? "";
$count = $data["count"] ?? count($rows);

// Pasamos datos a JS
$rows_json = json_encode($rows, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);


// --- IMEI filter (multi) desde URL: ?imei=389,344,5532 ---
$raw_filter = isset($_GET["imei"]) ? (string)$_GET["imei"] : "";
$imei_filters = array_values(array_filter(array_map("trim", preg_split('/[,\s]+/', $raw_filter))));
$imei_filters_json = json_encode($imei_filters, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);


?>


<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Estado Telit</title>

  <!-- Leaflet (mapa) -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;margin:20px}
    .top{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
    .meta{color:#666}
    input{padding:8px;width:320px;max-width:100%}
    button{padding:8px 12px;cursor:pointer}
    .pill{padding:2px 8px;border-radius:999px;border:1px solid #ddd;font-size:12px}
    .right{margin-left:auto}
    .small{font-size:12px;color:#666}

    #map{height:360px;margin-top:12px;border:1px solid #ddd;border-radius:10px;overflow:hidden}

    table{border-collapse:collapse;width:100%;margin-top:12px}
    th,td{border:1px solid #ddd;padding:7px;font-size:13px;white-space:nowrap}
    th{background:#f6f6f6;position:sticky;top:0;z-index:1;cursor:pointer}
    tr:hover{background:#fafafa}
    .wrap{white-space:normal}

    .sort{font-size:11px;color:#666;margin-left:6px}
    .legend{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px}
    .dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;border:1px solid rgba(0,0,0,.2)}
  </style>
</head>
<body>
  <div class="top">
    <h2 style="margin:0;">Estado Telit</h2>
    <span class="meta">Actualizado: <?= htmlspecialchars($generated_at) ?> · <span id="n"></span> / <?= htmlspecialchars((string)$count) ?> dispositivos</span>
    <span class="pill">Fuente: ID16980 :55060</span>
    <span class="right small" id="clock"></span>
  </div>

  <div class="top" style="margin-top:10px;">
<input id="q" name="imei" placeholder="Filtrar IMEI (parcial, coma): 389, 344, 5532" value="<?= htmlspecialchars($raw_filter) ?>" />
      <button onclick="applyFilterReload()">Aplicar</button>
    <button onclick="loadUI(true)">Refrescar</button>
    <button onclick="toggleAuto()">Auto: <span id="auto">OFF</span></button>
  </div>

  <div class="legend">
    <span class="pill"><span class="dot" style="background:#2ecc71;"></span>GPS POS</span>
    <span class="pill"><span class="dot" style="background:#3498db;"></span>GTP POS</span>
    <span class="pill"><span class="dot" style="background:#95a5a6;"></span>Otros / sin pos</span>
  </div>

  <div id="map"></div>

  <table id="tbl">
    <thead>
      <tr>
        <th data-key="idx"># <span class="sort" id="s_idx"></span></th>
        <th data-key="imei">IMEI <span class="sort" id="s_imei"></span></th>
        <th data-key="ultima_conexion">Última conexión <span class="sort" id="s_ultima_conexion"></span></th>
        <th data-key="minutos_desde_conexion">Min <span class="sort" id="s_minutos_desde_conexion"></span></th>
        <th data-key="timestamp_reinicio">Reinicio <span class="sort" id="s_timestamp_reinicio"></span></th>
        <th data-key="pila">Pila <span class="sort" id="s_pila"></span></th>
        <th data-key="result">Result <span class="sort" id="s_result"></span></th>
        <th data-key="longitude">Lon <span class="sort" id="s_longitude"></span></th>
        <th data-key="latitude">Lat <span class="sort" id="s_latitude"></span></th>
        <th data-key="accuracy">Acc <span class="sort" id="s_accuracy"></span></th>
        <th data-key="char3" class="wrap">char3 <span class="sort" id="s_char3"></span></th>
        <th data-key="v4">v4 <span class="sort" id="s_v4"></span></th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

<script>
const RAW = <?= $rows_json ?>;

const IMEI_FILTERS = <?= $imei_filters_json ?>;


// --- Estado UI ---
let timer = null;
let sortKey = "minutos_desde_conexion";
let sortDir = "asc"; // asc = más reciente (menos minutos)
let map, layer;

// --- Helpers ---
function nowTick(){
  document.getElementById("clock").textContent = new Date().toLocaleString();
}
setInterval(nowTick, 1000); nowTick();

function isValidPos(r){
  const lat = Number(r.latitude), lon = Number(r.longitude);
  if (!isFinite(lat) || !isFinite(lon)) return false;
  if (lat === 99 || lon === 99) return false;
  if (lat === 0 || lon === 0) return false;
  return true;
}

function statusColor(r){
  const s = (r.char3 || "").toUpperCase();
  if (s.includes("GPS POS")) return "#2ecc71"; // verde
  if (s.includes("GTP POS")) return "#3498db"; // azul
  return "#95a5a6"; // gris
}

function cmp(a,b,key){
  const va = a?.[key], vb = b?.[key];
  // numérico si se puede
  const na = Number(va), nb = Number(vb);
  const bothNum = isFinite(na) && isFinite(nb) && (va !== "" && vb !== "");
  if (bothNum) return na - nb;
  // string
  return String(va ?? "").localeCompare(String(vb ?? ""), undefined, {numeric:true, sensitivity:"base"});
}

function sortRows(rows){
  const out = [...rows];
  out.sort((a,b)=>{
    const c = cmp(a,b,sortKey);
    return sortDir === "asc" ? c : -c;
  });
  return out;
}

function applyFilterReload(){
  const v = document.getElementById("q").value.trim();
  const base = location.pathname;
  if(!v){
    location.href = base;
    return;
  }
  location.href = base + "?imei=" + encodeURIComponent(v);
}


function filterRows(rows){
  const raw = document.getElementById("q").value.trim().toLowerCase();

  // Si hay filtros desde PHP (?imei=...), esos mandan
  const list = (Array.isArray(IMEI_FILTERS) && IMEI_FILTERS.length)
    ? IMEI_FILTERS.map(s => String(s).trim().toLowerCase()).filter(Boolean)
    : raw
      ? raw.split(/[,\s]+/).map(s => s.trim().toLowerCase()).filter(Boolean)
      : [];

  if (list.length === 0) return rows;

  return rows.filter(r => {
    const imei = String(r.imei ?? "").toLowerCase();
    return list.some(f => imei.includes(f));
  });
}


function filterRowsOLD(rows){
  const q = document.getElementById("q").value.trim().toLowerCase();
  if (!q) return rows;
  return rows.filter(r => String(r.imei ?? "").toLowerCase().includes(q));
}

function setSortIndicators(){
  document.querySelectorAll(".sort").forEach(el => el.textContent = "");
  const el = document.getElementById("s_" + sortKey);
  if (el) el.textContent = sortDir === "asc" ? "▲" : "▼";
}

function renderTable(rows){
  const tb = document.querySelector("#tbl tbody");
  tb.innerHTML = "";
  rows.forEach(r=>{
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.idx ?? ""}</td>
      <td>${r.imei ?? ""}</td>
      <td>${r.ultima_conexion ?? ""}</td>
      <td>${r.minutos_desde_conexion ?? ""}</td>
      <td>${r.timestamp_reinicio ?? ""}</td>
      <td>${r.pila ?? ""}</td>
      <td>${r.result ?? ""}</td>
      <td>${r.longitude ?? ""}</td>
      <td>${r.latitude ?? ""}</td>
      <td>${r.accuracy ?? ""}</td>
      <td class="wrap">${r.char3 ?? ""}</td>
      <td>${r.v4 ?? ""}</td>
    `;
    tb.appendChild(tr);
  });
  document.getElementById("n").textContent = rows.length;
}

function initMap(){
  map = L.map("map", {scrollWheelZoom:true}).setView([41.2236, 1.7360], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap"
  }).addTo(map);

  layer = L.layerGroup().addTo(map);
}

function renderMap(rows){
  if (!map) initMap();
  layer.clearLayers();

  const pts = rows.filter(isValidPos);
  pts.forEach(r=>{
    const lat = Number(r.latitude), lon = Number(r.longitude);
    const color = statusColor(r);

    const marker = L.circleMarker([lat, lon], {
      radius: 7,
      color: color,
      fillColor: color,
      fillOpacity: 0.9,
      weight: 2
    });

    const popup = `
      <b>IMEI:</b> ${r.imei ?? ""}<br>
      <b>Última:</b> ${r.ultima_conexion ?? ""}<br>
      <b>Min:</b> ${r.minutos_desde_conexion ?? ""}<br>
      <b>Pila:</b> ${r.pila ?? ""}<br>
      <b>Acc:</b> ${r.accuracy ?? ""}<br>
      <b>char3:</b> ${r.char3 ?? ""}<br>
      <b>v4:</b> ${r.v4 ?? ""}
    `;
    marker.bindPopup(popup);
    marker.addTo(layer);
  });

  if (pts.length > 0){
    const bounds = L.latLngBounds(pts.map(r => [Number(r.latitude), Number(r.longitude)]));
    map.fitBounds(bounds.pad(0.15));
  }
}

// --- Main UI ---
function loadUI(force=false){
  // Nota: RAW viene del server (PHP). Para refrescar datos, recargamos la página.
  // El botón Refrescar hace reload. Aquí solo re-renderizamos filtros/orden.
  let rows = filterRows(RAW);
  rows = sortRows(rows);
  setSortIndicators();
  renderTable(rows);
  renderMap(rows);
}

function toggleAuto(){
  const el = document.getElementById("auto");
  if (timer){
    clearInterval(timer);
    timer = null;
    el.textContent = "OFF";
    return;
  }
  el.textContent = "ON";
  timer = setInterval(() => location.reload(), 30000); // 30s
}

// Eventos
document.getElementById("q").addEventListener("input", () => loadUI());
document.querySelectorAll("#tbl thead th[data-key]").forEach(th=>{
  th.addEventListener("click", ()=>{
    const k = th.getAttribute("data-key");
    if (sortKey === k) sortDir = (sortDir === "asc") ? "desc" : "asc";
    else { sortKey = k; sortDir = "asc"; }
    loadUI();
  });
});

// Default: más reciente primero (minutos asc)
setSortIndicators();
loadUI();
</script>
</body>
</html>