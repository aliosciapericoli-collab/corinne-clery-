#!/bin/bash
# Attiva il salvataggio dell'archivio: collega /api/ al piccolo server e lo avvia con pm2.
set -e
CF=/etc/caddy/conf.d/gobbocorinne.alioscia.it.caddy
API=/home/work/gobbo-corinne/_api
BK="$API/caddy-prima-$(date +%Y%m%d-%H%M%S).caddy"

echo "1/4 · Copia di sicurezza della configurazione di Caddy"
sudo cp "$CF" "$BK"

echo "2/4 · Collego /api/ al server dell'archivio"
if ! sudo grep -q "reverse_proxy /api/\*" "$CF"; then
  sudo sed -i 's#^    root \* /home/work/gobbo-corinne$#    respond /_api/* 404\n    reverse_proxy /api/* 127.0.0.1:3270\n    root * /home/work/gobbo-corinne#' "$CF"
fi
if ! sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1; then
  echo "Configurazione non valida: rimetto quella di prima. Niente è cambiato."
  sudo cp "$BK" "$CF"
  exit 1
fi
sudo systemctl reload caddy

echo "3/4 · Avvio il server dell'archivio"
if pm2 describe archivio-corinne >/dev/null 2>&1; then
  pm2 restart archivio-corinne
else
  pm2 start "$API/server.js" --name archivio-corinne
fi
pm2 save >/dev/null

echo "4/4 · Controllo"
sleep 1
if curl -sf http://127.0.0.1:3270/api/archivio >/dev/null; then
  echo "FATTO: l'archivio ora si può modificare."
else
  echo "ATTENZIONE: il server non risponde. Manda uno screenshot a Claude."
fi
