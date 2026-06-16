#!/bin/bash
set -e
export PATH="/usr/local/bin:/usr/bin:/bin"

BASE="/home/quim/www/clas"
DTTS_USER="quim"
DTTS_HOST="dtts.obsea.es"
DTTS_PORT="49857"
KEY="$BASE/.ssh_web/id_quim_cron"
chmod 600 "$KEY" 2>/dev/null || true

DTTS_CMD="/home/quim/make_historico.sh"
DTTS_XLSX="/home/quim/json_data.xlsx"
DTTS_HTML="/home/quim/historico.html"

LOCAL_XLSX="$BASE/data/json_data.xlsx"
LOCAL_HTML="$BASE/historico/historico.html"

mkdir -p "$BASE/data" "$BASE/historico"

echo "[INFO] Generando Excel+HTML en DTTS..."
ssh -i "$KEY" -p "$DTTS_PORT" -oBatchMode=yes -oStrictHostKeyChecking=no \
  "$DTTS_USER@$DTTS_HOST" \
  "bash '$DTTS_CMD'"

echo "[INFO] Descargando Excel+HTML desde DTTS..."
rm -f "$LOCAL_XLSX" "$LOCAL_HTML"

sftp -i "$KEY" -oBatchMode=yes -oStrictHostKeyChecking=no -P "$DTTS_PORT" \
  "$DTTS_USER@$DTTS_HOST" <<EOF
get $DTTS_XLSX $LOCAL_XLSX
get $DTTS_HTML $LOCAL_HTML
bye
EOF

echo "[OK] Actualizado: $LOCAL_HTML"
