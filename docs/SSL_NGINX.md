# SSL/TLS for Nginx

This guide explains how to obtain an SSL certificate and configure nginx to serve the gallery over HTTPS.

## Overview

- **HTTP (port 80)** is always enabled via `nginx/nginx.conf`.
- **HTTPS (port 443)** is optional: enable it by adding certificates and an SSL server block.
- Certificates live in `nginx/ssl/`; the HTTPS server block is in `nginx/conf.d/ssl.conf` (copy from `ssl.conf.example`).

Docker Compose already mounts `nginx/conf.d` and `nginx/ssl` into the nginx container. Enable HTTPS only when you have placed valid certs and created `ssl.conf`.

---

## 1. Generate an SSL certificate

### Option A: Let’s Encrypt (production, free)

Use Certbot on the host (or in a container) to get a certificate for your domain. The server must be reachable at your domain on port 80 (and optionally 443) for HTTP-01 challenge.

**On the server (e.g. Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

Certbot will write files under `/etc/letsencrypt/live/your-domain.com/`:

- `fullchain.pem` – certificate + chain
- `privkey.pem` – private key

**Copy them into the project so nginx in Docker can read them:**

```bash
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown "$(whoami):" nginx/ssl/*.pem
```

**Renewal:** Certbot can renew via cron or systemd timer. After renewal, copy the new files into `nginx/ssl/` again (or use a bind mount from `/etc/letsencrypt` into the nginx container and point nginx at those paths).

**Using Certbot in Docker (alternative):** You can run Certbot in a container and use a volume for `nginx/ssl` so the nginx container and Certbot share the same cert directory. See [Certbot docs](https://certbot.eff.org/instructions) for Docker examples.

### Option B: Self-signed certificate (development / testing)

For local or internal use only:

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

Browsers will show a security warning; accept the exception for testing. Do not use this cert for production.

---

## 2. Enable HTTPS in nginx

1. **Ensure certs are in place:**

   - `nginx/ssl/fullchain.pem`
   - `nginx/ssl/privkey.pem`

2. **Create the SSL server config:**

   ```bash
   cp nginx/conf.d/ssl.conf.example nginx/conf.d/ssl.conf
   ```

3. **Edit `nginx/conf.d/ssl.conf`:**
   - Set `server_name` to your domain (e.g. `gallery.example.com`) or leave `_` for default.
   - If your media signed-URL secret is not the placeholder, set `secure_link_secret` to match Django’s `GALLERY_SIGNED_URL_SECRET` (or the value used in `nginx/nginx.conf`).

4. **Restart nginx:**

   ```bash
   docker compose restart nginx
   ```

   Or, with the VPS compose file:

   ```bash
   docker compose -f docker-compose.vps.yml restart nginx
   ```

5. **Check:** Open `https://your-domain.com` (or `https://localhost` with a self-signed cert). Confirm the padlock and that static/media and the app load correctly.

---

## 3. Redirect HTTP to HTTPS (optional)

To send all HTTP traffic to HTTPS:

1. **Edit `nginx/nginx.conf`.**  
   In the existing `server { listen 80; ... }` block, replace the `location / { ... }` (and other locations) with a redirect, or add at the top of that server block:

   ```nginx
   return 301 https://$host$request_uri;
   ```

   So the block looks like:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # or _
       return 301 https://$host$request_uri;
   }
   ```

2. **Reload nginx:**  
   `docker compose restart nginx` (or your compose file).

---

## 4. File layout summary

| Path | Purpose |
|------|--------|
| `nginx/nginx.conf` | Main config; HTTP (80) and `include /etc/nginx/conf.d/*.conf` |
| `nginx/conf.d/ssl.conf.example` | Template HTTPS server; copy to `ssl.conf` and edit |
| `nginx/conf.d/ssl.conf` | Your HTTPS server block (created by you; not committed) |
| `nginx/ssl/fullchain.pem` | Certificate (or full chain) |
| `nginx/ssl/privkey.pem` | Private key |

`nginx/ssl/` and `nginx/conf.d/ssl.conf` are listed in `.gitignore` so certificates and your SSL config are not committed.

---

## 5. Troubleshooting

- **nginx won’t start:** Ensure `nginx/ssl/fullchain.pem` and `nginx/ssl/privkey.pem` exist and are readable by the container. If HTTPS is not needed yet, remove or rename `nginx/conf.d/ssl.conf` so only `nginx.conf` is used.
- **Certificate not trusted (self-signed):** Expected for dev certs; add a browser exception.
- **Mixed content / redirect loops:** Set Django’s `SECURE_PROXY_SSL_HEADER` and use `https` in `STATIC_URL`/`MEDIA_URL` if you serve the app only over HTTPS. Ensure `X-Forwarded-Proto` is set (already in the provided `ssl.conf.example`).
