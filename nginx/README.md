# Nginx deploy qo'llanmasi (production)

`mafia.omadli.uz.conf` — host serverdagi global nginx uchun namuna config. Docker'da emas.

## Talablar
- Ubuntu 22.04+ yoki shunga o'xshash
- nginx (`apt install nginx`)
- certbot (`apt install certbot python3-certbot-nginx`)

## Deploy qadamlari

### 1. Domain DNS
`mafia.omadli.uz` → server IP (A record). DNS tarqalishi uchun ~1 soat kuting.

### 2. Document root
```bash
sudo mkdir -p /var/www/mafia
sudo chown -R www-data:www-data /var/www/mafia
```

### 3. Frontend build (Bosqich 3 da to'liq):
```bash
cd /opt/mafia/frontend
npm install
npm run build
sudo cp -r dist/* /var/www/mafia/
sudo chown -R www-data:www-data /var/www/mafia
```

Yoki: `bash /opt/mafia/scripts/build-frontend.sh`

### 4. Nginx config
```bash
sudo cp /opt/mafia/nginx/mafia.omadli.uz.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/mafia.omadli.uz.conf /etc/nginx/sites-enabled/

# Default site'ni o'chirish (kerak bo'lsa)
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL (LetsEncrypt — config'ga avtomatik qo'shadi)
```bash
sudo certbot --nginx -d mafia.omadli.uz --non-interactive --agree-tos -m admin@omadli.uz
sudo systemctl reload nginx
```

Certbot avtomatik:
- HTTP→HTTPS redirect qo'shadi
- SSL sertifikatlarni `/etc/letsencrypt/live/mafia.omadli.uz/`'ga joylaydi
- Cron orqali avtomatik yangilash sozlaydi

### 6. Backend ishga tushirish
```bash
cd /opt/mafia
cp .env.example .env
# .env'ni to'ldirish (BOT_TOKEN, parollar va h.k.)
docker compose up -d
docker compose logs -f backend
```

### 7. Telegram webhook'ni o'rnatish
```bash
source .env
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -d "url=$WEBHOOK_BASE_URL/webhook/$WEBHOOK_SECRET"
```

## Tekshirish

```bash
# Nginx ishlayapti?
sudo systemctl status nginx

# SSL OK?
curl -I https://mafia.omadli.uz/health

# Backend OK?
curl https://mafia.omadli.uz/health

# Loglar
sudo tail -f /var/log/nginx/mafia.access.log
sudo tail -f /var/log/nginx/mafia.error.log
docker compose logs -f backend
```

## Yangilash (deploy)

```bash
cd /opt/mafia
git pull
docker compose pull
docker compose up -d --build backend
docker compose exec backend aerich upgrade
bash scripts/build-frontend.sh
```
