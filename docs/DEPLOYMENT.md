# Deployment Guide - Split Architecture with WireGuard VPN

This guide explains how to deploy the gallery application across two machines using WireGuard VPN for secure connections:
- **VPS (Cloud Server)**: Web server, database, Redis, CPU Celery workers
- **Local Laptop**: GPU Celery worker for YOLO and PaddleOCR

**⚠️ Important:** This deployment uses WireGuard VPN to securely connect the local GPU worker to VPS services. Redis and PostgreSQL are NOT exposed to the internet. See [WIREGUARD_SETUP.md](WIREGUARD_SETUP.md) for detailed WireGuard configuration.

## Architecture Overview

```
┌─────────────────────────────────┐
│      VPS (Cloud Server)         │
│  ┌─────────┐  ┌──────────┐     │
│  │   Web   │  │   Nginx   │     │
│  └─────────┘  └──────────┘     │
│  ┌─────────┐  ┌──────────┐     │
│  │   DB    │  │  Redis   │◄────┼──┐
│  └─────────┘  └──────────┘     │  │
│  ┌─────────┐  ┌──────────┐     │  │
│  │ Celery  │  │ Celery   │     │  │
│  │  (CPU)  │  │  Beat    │     │  │
│  └─────────┘  └──────────┘     │  │
│  ┌─────────┐                   │  │
│  │ Flower  │                   │  │
│  └─────────┘                   │  │
└─────────────────────────────────┘  │
                                     │
                                     │ Redis Connection
                                     │ (Port 6380)
                                     │
┌─────────────────────────────────┐  │
│      Local Laptop (GPU)          │  │
│  ┌──────────────┐                │  │
│  │ Celery-GPU   │────────────────┘  │
│  │  (YOLO/OCR)  │                   │
│  └──────────────┘                   │
└─────────────────────────────────┘
```

## Prerequisites

### VPS Requirements
- Docker and Docker Compose installed
- Ports open: 80, 443, 51820 (WireGuard UDP), 8000 (Web)
- WireGuard installed and configured (see [WIREGUARD_SETUP.md](WIREGUARD_SETUP.md))
- For HTTPS: SSL certificate and nginx SSL config (see [SSL_NGINX.md](SSL_NGINX.md))
- Firewall configured to allow WireGuard port (51820/UDP) from your local IP

### Local Laptop Requirements
- Docker and Docker Compose installed
- NVIDIA GPU with drivers installed
- NVIDIA Container Toolkit installed
- WSL2 (if on Windows)
- WireGuard installed and configured (see [WIREGUARD_SETUP.md](WIREGUARD_SETUP.md))
- WireGuard VPN connection to VPS established

## VPS Setup

1. **Clone the repository on VPS:**
   ```bash
   git clone <your-repo-url>
   cd gallery
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Configure `.env` for VPS:**
   ```env
   # Database
   DB_NAME=gallery
   DB_USER=postgres
   DB_PASSWORD=your_secure_password
   DB_HOST=db
   DB_PORT=5432

   # Redis (internal)
   REDIS_PORT=6379
   REDIS_EXTERNAL_PORT=6380

   # Celery
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0

   # Flower (monitoring)
   FLOWER_USERNAME=admin
   FLOWER_PASSWORD=your_secure_password
   FLOWER_PORT=5555
   ```

4. **Start services:**
   ```bash
   docker-compose -f docker-compose.vps.yml up -d
   ```

5. **Verify services are running:**
   ```bash
   docker-compose -f docker-compose.vps.yml ps
   ```

6. **Configure PostgreSQL for remote access (if GPU worker needs DB access):**
   ```bash
   # Note: GPU worker typically only needs Redis connection
   # Database access is usually only needed if tasks directly query DB
   # If needed, configure PostgreSQL to accept remote connections
   ```

7. **Get your VPS IP address:**
   ```bash
   # On Linux
   hostname -I
   # Or check your VPS provider's dashboard
   ```

## Local Laptop Setup

1. **Clone the repository on local machine:**
   ```bash
   git clone <your-repo-url>
   cd gallery
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Configure WireGuard VPN first:**
   - Follow the instructions in [WIREGUARD_SETUP.md](WIREGUARD_SETUP.md)
   - Ensure WireGuard connection is established and tested
   - Verify you can ping `10.0.0.1` from your local machine

4. **Configure `.env` for local GPU worker:**
   ```env
   # VPS Connection via WireGuard VPN (10.0.0.1 is the VPS WireGuard IP)
   CELERY_BROKER_URL=redis://10.0.0.1:6379/0
   CELERY_RESULT_BACKEND=redis://10.0.0.1:6379/0

   # Database connection to VPS via WireGuard
   DATABASE_HOST=10.0.0.1
   DATABASE_PORT=5432
   DATABASE_NAME=gallery
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your_secure_password

   # Celery GPU Worker
   CELERY_GPU_WORKER_CONCURRENCY=2
   ```

5. **Update `config.yaml` or use environment variables (optional):**
   ```yaml
   celery:
     broker_url: "redis://10.0.0.1:6379/0"
     result_backend: "redis://10.0.0.1:6379/0"
   
   database:
     host: "10.0.0.1"
     port: 5432
     name: "gallery"
     user: "postgres"
     password: "your_secure_password"
   ```

6. **Start GPU worker:**
   ```bash
   docker-compose -f docker-compose.gpu.yml up -d
   ```

7. **Verify GPU worker is running:**
   ```bash
   docker-compose -f docker-compose.gpu.yml ps
   docker-compose -f docker-compose.gpu.yml logs celery-gpu
   ```

## Security Considerations

### WireGuard VPN Security
- **Redis and PostgreSQL are NOT exposed to the internet** - they are only accessible via WireGuard VPN
- WireGuard provides encrypted, authenticated connections
- Only the WireGuard port (51820/UDP) needs to be open on the VPS
- Configure firewall to only allow WireGuard port from your local IP

### Redis Security
- Redis is accessible only via WireGuard VPN (10.0.0.1:6379)
- **Optional but recommended**: Add Redis password authentication
  ```bash
  # In docker-compose.vps.yml, update Redis command:
  command: redis-server --appendonly yes --bind 0.0.0.0 --requirepass YOUR_REDIS_PASSWORD
  ```
- Then update `CELERY_BROKER_URL` to: `redis://:YOUR_REDIS_PASSWORD@10.0.0.1:6379/0`

### Database Security
- PostgreSQL is accessible only via WireGuard VPN (10.0.0.1:5432)
- Use strong passwords
- Consider using SSL connections for database (even within VPN)

### Firewall Rules
On VPS, configure firewall to only allow:
- Port 80/443: From anywhere (web traffic)
- Port 51820/UDP: Only from your local laptop IP (WireGuard VPN)
- Port 8000: Optional, for direct web access (or use nginx reverse proxy)

## Testing the Connection

### Test WireGuard Connection
```bash
# From local machine, ping VPS WireGuard IP
ping 10.0.0.1

# Check WireGuard status
sudo wg show
```

### Test Redis Connection from Local Machine
```bash
# Install redis-cli if needed
# On Ubuntu/Debian:
sudo apt-get install redis-tools

# Test connection via WireGuard
redis-cli -h 10.0.0.1 -p 6379 ping
```

### Test Database Connection
```bash
# From local machine via WireGuard
psql -h 10.0.0.1 -p 5432 -U postgres -d gallery
```

### Monitor Workers
- Access Flower on VPS: `http://YOUR_VPS_IP:5555`
- You should see both CPU and GPU workers listed

## Troubleshooting

### GPU Worker Can't Connect to Redis
- **First, verify WireGuard is connected:** `sudo wg show` and `ping 10.0.0.1`
- Check Redis is running: `docker-compose -f docker-compose.vps.yml ps redis`
- Test connection: `redis-cli -h 10.0.0.1 -p 6379 ping`
- Check WireGuard routing: `ip route show`

### GPU Worker Can't Connect to Database
- **First, verify WireGuard is connected:** `sudo wg show` and `ping 10.0.0.1`
- Check PostgreSQL is running: `docker-compose -f docker-compose.vps.yml ps db`
- Test connection: `psql -h 10.0.0.1 -p 5432 -U postgres -d gallery`
- Verify Docker network allows WireGuard access

### Tasks Not Processing on GPU Worker
- Verify tasks are routed to 'gpu' queue
- Check Celery routing configuration in `settings.py`
- Monitor logs: `docker-compose -f docker-compose.gpu.yml logs -f celery-gpu`

## Maintenance

### Updating Code
1. Pull latest code on both machines
2. Rebuild and restart:
   - VPS: `docker-compose -f docker-compose.vps.yml up -d --build`
   - Local: `docker-compose -f docker-compose.gpu.yml up -d --build`

### Viewing Logs
- VPS: `docker-compose -f docker-compose.vps.yml logs -f`
- Local: `docker-compose -f docker-compose.gpu.yml logs -f celery-gpu`

### Stopping Services
- VPS: `docker-compose -f docker-compose.vps.yml down`
- Local: `docker-compose -f docker-compose.gpu.yml down`
