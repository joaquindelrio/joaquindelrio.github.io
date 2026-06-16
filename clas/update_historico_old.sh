#!/bin/bash
set -e

BASE="/home/quim/www/clas"
cd "$BASE"

# Descargar Excel
mkdir -p "$BASE/data"
sftp -i ~/.ssh/id_quim_cron -oStrictHostKeyChecking=no -P 49857 quim@dtts.obsea.es <<EOF
get json_data.xlsx $BASE/data/json_data.xlsx
bye
EOF

# Generar HTML (últimas 48h)
mkdir -p "$BASE/historico"
python3 "$BASE/make_historico_html.py" \
  --xlsx "$BASE/data/json_data.xlsx" \
  --out  "$BASE/historico/historico.html" \
  --hours 48
