<?php
// Muestra el HTML estático generado por python
$path = __DIR__ . "/historico/historico.html";

if (!file_exists($path)) {
  header("Content-Type: text/plain; charset=utf-8");
  echo "historico.html no existe todavía. Ejecuta el script de actualización.\n";
  exit;
}

header("Content-Type: text/html; charset=utf-8");
readfile($path);
