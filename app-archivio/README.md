# App archivio

Pagina: https://gobbocorinne.alioscia.it/archivio/ (stessa password del gobbo).

- `index.html`: la pagina. Se il server `/api` risponde, mostra i pulsanti Modifica, Registrata e Allega animazioni; altrimenti è in sola lettura.
- `archivio.json`: dati iniziali. **Da quando il salvataggio è attivo, la versione vera è quella sul server** (`/home/work/gobbo-corinne/archivio/archivio.json`): non sovrascriverla con questa.
- `api/server.js`: server Node senza dipendenze, solo su 127.0.0.1:3270, con pm2 come `archivio-corinne`. Copie di sicurezza in `_api/backup/` (ultime 300). Allegati in `archivio/media/<id-storia>/`.
- `api/installa.sh`: collega `/api/*` in Caddy e avvia il server (si lancia una volta sola).
