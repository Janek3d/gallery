# WireGuard VPN Setup Guide

This guide explains how to set up WireGuard VPN to securely connect your local GPU worker to the VPS services without exposing Redis and PostgreSQL to the internet.

## Architecture with WireGuard

```
┌─────────────────────────────────┐
│      VPS (Cloud Server)         │
│  ┌──────────────────────────┐  │
│  │   WireGuard Server        │  │
│  │   IP: 10.0.0.1/24        │  │
│  └──────────────────────────┘  │
│  ┌─────────┐  ┌──────────┐     │
│  │   Web   │  │   Nginx   │     │
│  └─────────┘  └──────────┘     │
│  ┌─────────┐  ┌──────────┐     │
│  │   DB    │  │  Redis   │     │
│  │10.0.0.1 │  │10.0.0.1  │     │
│  └─────────┘  └──────────┘     │
│  ┌─────────┐                   │
│  │ Celery  │                   │
│  │  (CPU)  │                   │
│  └─────────┘                   │
└─────────────────────────────────┘
         ▲
         │ WireGuard VPN
         │ (Encrypted Tunnel)
         │
┌─────────────────────────────────┐
│      Local Laptop (GPU)          │
│  ┌──────────────────────────┐  │
│  │   WireGuard Client       │  │
│  │   IP: 10.0.0.2/24        │  │
│  └──────────────────────────┘  │
│  ┌──────────────┐              │
│  │ Celery-GPU   │              │
│  │  (YOLO/OCR)  │              │
│  └──────────────┘              │
└─────────────────────────────────┘
```

## VPS Setup (WireGuard Server)

### 1. Install WireGuard

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install wireguard wireguard-tools

# CentOS/RHEL
sudo yum install epel-release
sudo yum install wireguard-tools

# Verify installation
wg --version
```

### 2. Enable IP Forwarding

```bash
# Enable IP forwarding
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 3. Generate Server Keys

```bash
# Create WireGuard directory
sudo mkdir -p /etc/wireguard
cd /etc/wireguard

# Generate private key
sudo wg genkey | sudo tee server_private.key | sudo wg pubkey | sudo tee server_public.key

# Set permissions
sudo chmod 600 server_private.key
```

### 4. Create Server Configuration

```bash
sudo nano /etc/wireguard/wg0.conf
```

Add the following configuration:

```ini
[Interface]
# Server private key (from server_private.key)
PrivateKey = YOUR_SERVER_PRIVATE_KEY_HERE

# Server WireGuard IP address
Address = 10.0.0.1/24

# Listen on UDP port 51820
ListenPort = 51820

# Firewall rules - allow forwarding
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Client public key (will be added after generating client keys)
PublicKey = CLIENT_PUBLIC_KEY_WILL_BE_ADDED_HERE
# Client WireGuard IP
AllowedIPs = 10.0.0.2/32
```

**Important:** Replace `eth0` with your actual network interface name (check with `ip addr` or `ifconfig`).

### 5. Start WireGuard Server

```bash
# Enable and start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# Check status
sudo wg show
sudo systemctl status wg-quick@wg0
```

### 6. Configure Firewall

```bash
# Allow WireGuard port (51820/UDP)
sudo ufw allow 51820/udp

# Or with iptables
sudo iptables -A INPUT -p udp --dport 51820 -j ACCEPT
```

## Local Machine Setup (WireGuard Client)

### 1. Install WireGuard

**Windows (WSL2):**
```bash
# In WSL2
sudo apt update
sudo apt install wireguard wireguard-tools

# Or use Windows WireGuard client from: https://www.wireguard.com/install/
```

**Linux:**
```bash
sudo apt update
sudo apt install wireguard wireguard-tools
```

**macOS:**
```bash
brew install wireguard-tools
```

### 2. Generate Client Keys

```bash
# Create WireGuard directory
sudo mkdir -p /etc/wireguard
cd /etc/wireguard

# Generate private key
sudo wg genkey | sudo tee client_private.key | sudo wg pubkey | sudo tee client_public.key

# Set permissions
sudo chmod 600 client_private.key

# Display public key (you'll need this for the server)
sudo cat client_public.key
```

### 3. Add Client Public Key to Server

On the VPS, add the client's public key to the server configuration:

```bash
sudo nano /etc/wireguard/wg0.conf
```

Update the `[Peer]` section with the client's public key:

```ini
[Peer]
PublicKey = YOUR_CLIENT_PUBLIC_KEY_HERE
AllowedIPs = 10.0.0.2/32
```

Then restart WireGuard on the server:
```bash
sudo systemctl restart wg-quick@wg0
```

### 4. Create Client Configuration

On the local machine:

```bash
sudo nano /etc/wireguard/wg0.conf
```

Add the following configuration:

```ini
[Interface]
# Client private key
PrivateKey = YOUR_CLIENT_PRIVATE_KEY_HERE

# Client WireGuard IP address
Address = 10.0.0.2/24

[Peer]
# Server public key (from server_public.key on VPS)
PublicKey = YOUR_SERVER_PUBLIC_KEY_HERE

# VPS public IP address and WireGuard port
Endpoint = YOUR_VPS_PUBLIC_IP:51820

# Routes all traffic through VPN (or use 10.0.0.0/24 for only WireGuard network)
AllowedIPs = 10.0.0.0/24

# Keep connection alive
PersistentKeepalive = 25
```

### 5. Start WireGuard Client

```bash
# Start WireGuard
sudo wg-quick up wg0

# Check status
sudo wg show

# To stop
sudo wg-quick down wg0

# Enable on boot (Linux)
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

**Windows:** Use the WireGuard GUI application and import the configuration file.

### 6. Test Connection

```bash
# From local machine, ping the VPS WireGuard IP
ping 10.0.0.1

# Test Redis connection
redis-cli -h 10.0.0.1 -p 6379 ping

# Test PostgreSQL connection
psql -h 10.0.0.1 -p 5432 -U postgres -d gallery
```

## Update Application Configuration

### VPS Configuration

Update `docker-compose.vps.yml` to bind services to WireGuard IP:

```yaml
redis:
  command: redis-server --appendonly yes --bind 0.0.0.0
  # Redis will be accessible via WireGuard IP (10.0.0.1)

db:
  # PostgreSQL will be accessible via WireGuard IP (10.0.0.1)
```

### Local GPU Worker Configuration

Update `.env` on local machine:

```env
# Use WireGuard IP instead of public IP
celery.broker_url=redis://10.0.0.1:6379/0
celery.result_backend=redis://10.0.0.1:6379/0

# Database connection via WireGuard
database.host=10.0.0.1
database.port=5432
```

## Security Best Practices

1. **Use Strong Keys:** WireGuard keys are already cryptographically strong, but keep them secure.

2. **Firewall Rules:** Only allow WireGuard port (51820/UDP) from trusted IPs if possible.

3. **Regular Updates:** Keep WireGuard updated:
   ```bash
   sudo apt update && sudo apt upgrade wireguard
   ```

4. **Backup Keys:** Securely backup your private keys (encrypted).

5. **Monitor Connections:**
   ```bash
   # Check active connections
   sudo wg show
   
   # Monitor traffic
   sudo watch -n 1 'wg show wg0 dump'
   ```

## Troubleshooting

### Connection Issues

1. **Check WireGuard status:**
   ```bash
   sudo wg show
   sudo systemctl status wg-quick@wg0
   ```

2. **Verify firewall rules:**
   ```bash
   sudo ufw status
   sudo iptables -L -n
   ```

3. **Check routing:**
   ```bash
   ip route show
   ```

4. **Test connectivity:**
   ```bash
   ping 10.0.0.1  # From client to server
   ping 10.0.0.2  # From server to client
   ```

### Docker Network Issues

If Docker containers can't reach WireGuard IPs:

1. **Enable IP forwarding in Docker:**
   ```bash
   # Check Docker network settings
   docker network inspect gallery_network
   ```

2. **Use host network mode (if needed):**
   ```yaml
   # In docker-compose, for services that need WireGuard access
   network_mode: host
   ```

3. **Or configure Docker to use WireGuard interface:**
   ```bash
   # Add route in Docker network
   docker network create --subnet=172.20.0.0/16 gallery_network
   ```

## Quick Reference

**Server IP:** 10.0.0.1  
**Client IP:** 10.0.0.2  
**Network:** 10.0.0.0/24  
**Port:** 51820/UDP  

**Server commands:**
```bash
sudo systemctl start wg-quick@wg0
sudo systemctl stop wg-quick@wg0
sudo wg show
```

**Client commands:**
```bash
sudo wg-quick up wg0
sudo wg-quick down wg0
sudo wg show
```
