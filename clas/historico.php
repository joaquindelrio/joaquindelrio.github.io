<?php
$base = __DIR__;
$html = $base . "/historico/historico.html";
$lock = $base . "/historico/update.lock";
$log  = $base . "/historico/update.log";
$script = $base . "/update_historico.sh";

$max_age_seconds = 120; // cache: 2 minutos (ajusta)
$now = time();

function is_stale($file, $max_age, $now) {
  if (!file_exists($file)) return true;
  return (($now - filemtime($file)) > $max_age);
}

// --- 1) Leer filtro IMEI desde GET (ej: 389, 344, 5532, 66434) ---
$raw_filter = isset($_GET['imei']) ? (string)$_GET['imei'] : '';
$filters = array_values(array_filter(array_map('trim', preg_split('/[,\s]+/', $raw_filter))));
$filters_json = json_encode($filters, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

// Si está viejo y no hay lock, lanza actualización
if (is_stale($html, $max_age_seconds, $now)) {
  $fp = @fopen($lock, "x"); // crea solo si no existe
  if ($fp) {
    fwrite($fp, (string)$now);
    fclose($fp);

    // Ejecuta actualización en background para no colgar la web
    $cmd = "bash " . escapeshellarg($script) . " >> " . escapeshellarg($log) . " 2>&1; rm -f " . escapeshellarg($lock);
    exec($cmd . " &");
  }
}

// Sirve el HTML si existe; si no, muestra estado
if (!file_exists($html)) {
  header("Content-Type: text/html; charset=utf-8");
  echo "<h3>Histórico en generación...</h3>";
  echo "<p>Recarga en 10-20 segundos.</p>";
  exit;
}

header("Content-Type: text/html; charset=utf-8");

// --- 2) Cargar HTML para poder inyectar UI + JS ---
$content = file_get_contents($html);
if ($content === false) {
  echo "<h3>Error leyendo histórico</h3>";
  exit;
}

// Barra de filtro (se inserta tras el <h2> si existe; si no, tras <body>)
$filter_bar = '
<div style="padding:10px 12px;margin:10px 0 18px 0;border:1px solid #ddd;border-radius:8px;background:#fafafa">
  <form method="GET" style="margin:0;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <label for="imei" style="font-weight:600">Filtrar por IMEI (parcial):</label>
    <input id="imei" name="imei" type="text" value="'.htmlspecialchars($raw_filter, ENT_QUOTES, "UTF-8").'"
           placeholder="Ej: 389, 344, 5532, 66434"
           style="min-width:320px;padding:6px 8px;border:1px solid #ccc;border-radius:6px">
    <button type="submit" style="padding:7px 10px;border:1px solid #999;border-radius:6px;cursor:pointer">Aplicar</button>
    <a href="'.htmlspecialchars(strtok($_SERVER["REQUEST_URI"], "?"), ENT_QUOTES, "UTF-8").'"
       style="padding:7px 10px;border:1px solid #999;border-radius:6px;text-decoration:none;color:#000;background:#fff">
       Limpiar
    </a>
    <span id="imei_status" style="color:#555"></span>
  </form>
</div>
';

// Inserción “suave”
if (strpos($content, "<h2>") !== false) {
  $content = preg_replace('/(<h2>.*?<\/h2>)/s', '$1'.$filter_bar, $content, 1);
} else {
  $content = preg_replace('/(<body[^>]*>)/i', '$1'.$filter_bar, $content, 1);
}

// --- 3) JS: aplica filtro a TODAS las gráficas Plotly encontradas ---
$filter_js = "<script>
(function(){
  const filters = $filters_json;

  function extractImeiFromName(name){
    if(!name) return '';
    // coge todos los dígitos del nombre (vale para 'Dispositivo 353...' y 'Pila 353...')
    const digits = (String(name).match(/\\d+/g) || []).join('');
    return digits || String(name);
  }

  function applyFilter(){
    const status = document.getElementById('imei_status');
    if(!filters || filters.length === 0){
      if(status) status.textContent = 'Mostrando: todos los dispositivos';
      return;
    }

    const graphs = document.querySelectorAll('.plotly-graph-div');
    let matchedAny = false;

    graphs.forEach((gd) => {
      if(!gd || !gd.data || typeof Plotly === 'undefined') return;

      const visibles = gd.data.map((trace) => {
        const key = extractImeiFromName(trace.name || '');
        const ok = filters.some(f => key.includes(String(f)));
        if(ok) matchedAny = true;
        // true => visible; 'legendonly' => no se dibuja pero queda en leyenda (útil para comparar)
        return ok ? true : 'legendonly';
      });

      try {
        Plotly.restyle(gd, {visible: visibles});
      } catch(e) {}
    });

    if(status){
      status.textContent = matchedAny
        ? ('Filtro activo: ' + filters.join(', '))
        : ('Filtro activo: ' + filters.join(', ') + ' (sin coincidencias)');
    }
  }

  window.addEventListener('load', function(){
    // Asegura que los Plotly.newPlot del HTML ya han corrido
    setTimeout(applyFilter, 0);
  });
})();
</script>";

$content = preg_replace('/<\/body>/i', $filter_js . "\n</body>", $content, 1);

// Escupir HTML final
echo $content;
