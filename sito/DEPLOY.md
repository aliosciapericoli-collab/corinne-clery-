# Deploy corinneclery.it — Hetzner (65.21.237.152)

Build statica pre-renderizzata del sito, generata dal progetto Lovable
(repo sorgente: `corinne-clery-tribute`). Serve **Caddy** (non nginx):
config in `/etc/caddy/conf.d/corinneclery.caddy`, sito in `/home/work/corinneclery/sito`.

Setup iniziale già fatto il 18/08/2026 con `deploy/setup-caddy.sh` (rieseguibile, è idempotente).

## Aggiornare il sito online

1. Rigenerare la build statica dal progetto Lovable (vedi sotto) e pusharla in `sito/` di questa repo.
2. Sul server:
   ```bash
   git -C /home/work/corinneclery pull
   ```
   Niente reload: Caddy serve i file direttamente.

## Come si rigenera la build statica

Dal repo `corinne-clery-tribute` (clone locale):
1. In `vite.config.ts` aggiungere temporaneamente (NON committare):
   `nitro: { preset: "node-server" }` e `vite: { preview: { host: "127.0.0.1" } }`.
2. `bun install && bun run build`
3. `PORT=4173 node .output/server/index.mjs` e scaricare le 17 rotte con curl
   (8 pagine + 9 storie + /404.html) in cartelle `<rotta>/index.html`,
   sopra una copia di `.output/public/`.
4. Scaricare gli asset `/__l5e/...` referenziati (immagini caricate su Lovable)
   dalla preview `https://id-preview--053acdb3-755c-4385-88c1-08a1a43cc1b7.lovable.app`
   negli stessi percorsi.
5. Verificare che nessun riferimento `src/href` punti a file mancanti, poi push in `sito/`.

I DNS (IONOS) puntano a 65.21.237.152 (A per `@` e `www`); il dominio NON deve essere
configurato come custom domain su Lovable, altrimenti il domain-connect IONOS riscrive i DNS.
