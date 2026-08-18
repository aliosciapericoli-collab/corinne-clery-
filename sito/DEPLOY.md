# Deploy su Hetzner (65.21.237.152)

Build statica pre-renderizzata di corinneclery.it, generata dal progetto Lovable
(repo sorgente: `corinne-clery-tribute`). Per rigenerarla: build TanStack Start
con preset nitro `node-server`, avvio locale e mirror delle 17 rotte + asset.

## Setup iniziale sul server (una volta sola)

```bash
sudo mkdir -p /var/www/corinneclery.it
sudo git clone https://github.com/aliosciapericoli-collab/corinne-clery-.git /var/www/corinneclery.it/repo
sudo ln -s /var/www/corinneclery.it/repo/sito /var/www/corinneclery.it/html

sudo tee /etc/nginx/sites-available/corinneclery.it <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name corinneclery.it www.corinneclery.it;
    root /var/www/corinneclery.it/html;
    index index.html;
    error_page 404 /404.html;
    location / {
        try_files $uri $uri/index.html $uri/ =404;
    }
    location /assets/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    location /__l5e/ {
        expires 30d;
        add_header Cache-Control "public";
    }
}
NGINX
sudo ln -s /etc/nginx/sites-available/corinneclery.it /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# SSL (dopo che i DNS puntano al server — già fatto)
sudo certbot --nginx -d corinneclery.it -d www.corinneclery.it --redirect
```

## Aggiornamenti successivi

```bash
cd /var/www/corinneclery.it/repo && sudo git pull
```
