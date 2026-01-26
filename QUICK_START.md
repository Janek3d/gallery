# Quick Start - Split Deployment with WireGuard

**⚠️ Prerequisite:** Set up WireGuard VPN first! See [WIREGUARD_SETUP.md](WIREGUARD_SETUP.md)

## VPS Setup (5 minutes)

```bash
# 1. Clone and configure
git clone <your-repo>
cd gallery
cp .env.example .env
# Edit .env with your settings

# 2. Start all services
docker-compose -f docker-compose.vps.yml up -d

# 3. Check status
docker-compose -f docker-compose.vps.yml ps

# 4. Get your VPS IP
hostname -I
```

## Local GPU Worker Setup (5 minutes)

```bash
# 1. Clone and configure
git clone <your-repo>
cd gallery
cp .env.example .env

# 2. Ensure WireGuard is connected (ping 10.0.0.1 should work)

# 3. Edit .env - Use WireGuard IP (10.0.0.1):
#    celery.broker_url=redis://10.0.0.1:6379/0
#    celery.result_backend=redis://10.0.0.1:6379/0
#    database.host=10.0.0.1

# 4. Start GPU worker
docker-compose -f docker-compose.gpu.yml up -d

# 5. Check logs
docker-compose -f docker-compose.gpu.yml logs -f celery-gpu
```

## Verify Everything Works

1. **Check VPS services:**
   - Web: http://YOUR_VPS_IP:8000
   - Flower: http://YOUR_VPS_IP:5555 (should show both workers)

2. **Check GPU worker logs:**
   ```bash
   docker-compose -f docker-compose.gpu.yml logs celery-gpu
   ```

3. **Test task routing:**
   - Send a GPU task and verify it processes on local GPU worker
   - Send a CPU task and verify it processes on VPS CPU worker

## Common Issues

**GPU worker can't connect to Redis:**
- **First check WireGuard:** `sudo wg show` and `ping 10.0.0.1`
- Verify Redis is running: `docker-compose -f docker-compose.vps.yml ps redis`
- Test connection: `redis-cli -h 10.0.0.1 -p 6379 ping`

**GPU worker can't connect to database:**
- Usually not needed if tasks don't access DB directly
- If needed, configure PostgreSQL for remote access (see DEPLOYMENT.md)

**Tasks not processing:**
- Check queue names match: CPU tasks → 'cpu' queue, GPU tasks → 'gpu' queue
- Verify routing in `settings.py` CELERY_TASK_ROUTES
