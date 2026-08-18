#!/usr/bin/env bash
# Setup corinneclery.it su Caddy — da eseguire con: sudo bash setup-caddy.sh
set -euo pipefail

SITO_DIR=/home/work/corinneclery
REPO_URL=https://github.com/aliosciapericoli-collab/corinne-clery-.git

echo "== 1/4 Pulizia tentativo nginx precedente (se esiste)"
rm -rf /var/www/corinneclery.it
rm -f /etc/nginx/sites-enabled/corinneclery.it /etc/nginx/sites-available/corinneclery.it 2>/dev/null || true

echo "== 2/4 Clone/aggiornamento del sito in $SITO_DIR"
if [ -d "$SITO_DIR/.git" ]; then
  git -C "$SITO_DIR" pull
else
  git clone "$REPO_URL" "$SITO_DIR"
fi
chown -R work:work "$SITO_DIR" 2>/dev/null || true

echo "== 3/4 Config Caddy"
cat > /etc/caddy/conf.d/corinneclery.caddy <<'EOF'
# Corinne Cléry — www → apex (301)
www.corinneclery.it {
	redir https://corinneclery.it{uri} permanent
}

corinneclery.it {
	encode gzip zstd

	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains"
		X-Content-Type-Options    "nosniff"
		X-Frame-Options           "SAMEORIGIN"
		Referrer-Policy           "strict-origin-when-cross-origin"
		-Server
	}

	root * /home/work/corinneclery/sito
	try_files {path} {path}/index.html
	file_server

	@html path *.html
	header @html Cache-Control "public, max-age=300, must-revalidate"

	@assets path /assets/* /__l5e/*
	header @assets Cache-Control "public, max-age=31536000, immutable"

	handle_errors {
		rewrite * /404.html
		file_server
	}
}
EOF

echo "== 4/4 Validazione e reload Caddy"
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
echo "FATTO. Caddy sta richiedendo il certificato Let's Encrypt (pochi secondi)."
