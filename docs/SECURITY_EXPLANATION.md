# Security Explanation: How Redis and PostgreSQL are Protected

## Overview

With WireGuard VPN, Redis and PostgreSQL are **NOT exposed to the public internet**. They are only accessible through an encrypted VPN tunnel. Here's how it works:

## Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INTERNET (Public)                     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           VPS (Cloud Server)                    │  │
│  │                                                   │  │
│  │  ┌──────────────────────────────────────────┐   │  │
│  │  │  Firewall / Network Security             │   │  │
│  │  │  ✅ Port 80/443 (HTTP/HTTPS) - OPEN      │   │  │
│  │  │  ✅ Port 51820/UDP (WireGuard) - OPEN    │   │  │
│  │  │  ❌ Port 6379 (Redis) - CLOSED            │   │  │
│  │  │  ❌ Port 5432 (PostgreSQL) - CLOSED       │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  │                                                   │  │
│  │  ┌──────────────────────────────────────────┐   │  │
│  │  │  WireGuard VPN Server                     │   │  │
│  │  │  IP: 10.0.0.1                              │   │  │
│  │  │  🔒 Encrypted Tunnel Entry Point           │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  │              │                                    │  │
│  │              │ 🔒 Encrypted VPN Tunnel            │  │
│  │              │                                    │  │
│  │  ┌──────────▼──────────────────────────────┐     │  │
│  │  │  Docker Network (gallery_network)      │     │  │
│  │  │  ┌──────────┐  ┌──────────┐            │     │  │
│  │  │  │  Redis   │  │PostgreSQL│            │     │  │
│  │  │  │ :6379    │  │ :5432    │            │     │  │
│  │  │  │          │  │          │            │     │  │
│  │  │  │ Only accessible from               │     │  │
│  │  │  │ WireGuard network (10.0.0.0/24)    │     │  │
│  │  │  └──────────┘  └──────────┘            │     │  │
│  │  └────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│              🔒 WireGuard Encrypted Tunnel              │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Local Laptop (Your Machine)                │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────┐   │  │
│  │  │  WireGuard VPN Client                     │   │  │
│  │  │  IP: 10.0.0.2                              │   │  │
│  │  │  🔒 Encrypted Tunnel Exit Point            │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  │              │                                    │  │
│  │  ┌───────────▼──────────────────────────────┐   │  │
│  │  │  Docker Container (celery-gpu)           │   │  │
│  │  │  Connects to:                            │   │  │
│  │  │  - redis://10.0.0.1:6379                 │   │  │
│  │  │  - postgres://10.0.0.1:5432              │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Security Layers

### Layer 1: Network Firewall (VPS)

**What's Exposed:**
- ✅ Port 80/443: HTTP/HTTPS (web traffic) - **Necessary for public access**
- ✅ Port 51820/UDP: WireGuard VPN - **Only way to access databases**

**What's NOT Exposed:**
- ❌ Port 6379 (Redis): **Completely blocked from internet**
- ❌ Port 5432 (PostgreSQL): **Completely blocked from internet**

**Result:** Even if someone knows your VPS IP address, they **cannot** directly connect to Redis or PostgreSQL. These ports are not reachable from the internet.

### Layer 2: WireGuard VPN Authentication

**How WireGuard Protects:**

1. **Cryptographic Authentication:**
   - Each peer (server and client) has a public/private key pair
   - Only devices with the correct private key can join the VPN
   - Keys are cryptographically strong (256-bit)

2. **Encryption:**
   - All traffic through WireGuard is encrypted using modern cryptography
   - Even if someone intercepts the traffic, they can't read it

3. **IP Whitelisting:**
   - Only devices with WireGuard client configured can get a VPN IP (10.0.0.2)
   - The server only accepts connections from authenticated clients

**To Access Redis/PostgreSQL, an Attacker Would Need:**
1. Your VPS IP address ✅ (publicly known)
2. WireGuard server private key ❌ (only on VPS, never shared)
3. WireGuard client private key ❌ (only on your local machine)
4. Your local machine's WireGuard configuration ❌ (encrypted, password-protected)

### Layer 3: Docker Network Isolation

**Internal Network:**
- Redis and PostgreSQL run inside Docker containers
- They're on a private Docker network (`gallery_network`)
- They bind to `0.0.0.0` (all interfaces) but are only accessible through:
  - Other Docker containers on the same network
  - WireGuard VPN clients (10.0.0.1 can route to Docker network)

**Result:** Even if someone gains access to your VPS, they would still need:
- WireGuard VPN access to reach the Docker network
- Or direct shell access to the VPS to access containers

## Comparison: Before vs After WireGuard

### ❌ BEFORE (Insecure - Exposed to Internet)

```
Internet → VPS Firewall → Redis (Port 6379) ← Anyone can try to connect!
Internet → VPS Firewall → PostgreSQL (Port 5432) ← Anyone can try to connect!
```

**Risks:**
- Port scanners can discover open Redis/PostgreSQL ports
- Brute force attacks on authentication
- Unencrypted connections (unless SSL configured)
- Vulnerabilities in Redis/PostgreSQL exposed to internet
- DDoS attacks possible

### ✅ AFTER (Secure - WireGuard VPN)

```
Internet → VPS Firewall → ❌ Redis (Port 6379) - BLOCKED
Internet → VPS Firewall → ❌ PostgreSQL (Port 5432) - BLOCKED

Your Laptop → WireGuard VPN → VPS WireGuard (10.0.0.1) → Redis/PostgreSQL
                                    ↑
                            Only accessible through
                            encrypted VPN tunnel
```

**Benefits:**
- Ports not visible to internet scanners
- No direct attack surface
- All traffic encrypted
- Authentication required (WireGuard keys)
- Only your authorized device can connect

## What Attackers See

### Port Scan from Internet:
```bash
# Attacker runs: nmap -p 6379,5432 YOUR_VPS_IP
# Result:
6379/tcp  closed  # ✅ Not accessible
5432/tcp  closed  # ✅ Not accessible
51820/udp open    # WireGuard - but requires keys to connect
```

**Attacker cannot:**
- Connect to Redis
- Connect to PostgreSQL
- See what services are running on those ports
- Attempt brute force attacks

**Attacker can:**
- See that WireGuard is running (port 51820)
- But cannot connect without valid keys

## Additional Security Measures (Recommended)

Even with WireGuard, you should still:

### 1. Redis Password Authentication (Optional but Recommended)
```yaml
# In docker-compose.vps.yml
redis:
  command: redis-server --appendonly yes --bind 0.0.0.0 --requirepass YOUR_STRONG_PASSWORD
```

Then in `.env`:
```env
celery.broker_url=redis://:YOUR_STRONG_PASSWORD@10.0.0.1:6379/0
```

**Why:** Defense in depth - even if WireGuard is compromised, Redis still requires a password.

### 2. PostgreSQL Strong Passwords
```env
database.password=your_very_strong_password_here
```

**Why:** Defense in depth - even if WireGuard is compromised, PostgreSQL still requires authentication.

### 3. Firewall Rules
```bash
# Only allow WireGuard port from your IP
sudo ufw allow from YOUR_LOCAL_IP to any port 51820 proto udp
```

**Why:** Limits who can even attempt to connect to WireGuard.

### 4. Regular Updates
- Keep WireGuard updated
- Keep Redis and PostgreSQL updated
- Monitor for security advisories

## Security Summary

| Aspect | Status | Explanation |
|--------|--------|-------------|
| **Redis exposed to internet?** | ❌ NO | Only accessible via WireGuard VPN (10.0.0.1:6379) |
| **PostgreSQL exposed to internet?** | ❌ NO | Only accessible via WireGuard VPN (10.0.0.1:5432) |
| **Traffic encrypted?** | ✅ YES | All traffic through WireGuard is encrypted |
| **Authentication required?** | ✅ YES | WireGuard requires cryptographic keys |
| **Ports visible to scanners?** | ❌ NO | Ports 6379 and 5432 are closed on firewall |
| **Can attackers brute force?** | ❌ NO | They can't even reach the services |
| **Can attackers intercept traffic?** | ❌ NO | Traffic is encrypted through VPN tunnel |

## Real-World Attack Scenarios

### Scenario 1: Port Scanner Attack
```
Attacker: Scans YOUR_VPS_IP for common database ports
Result: Ports 6379 and 5432 show as CLOSED
Outcome: ✅ Attacker gives up, can't find services
```

### Scenario 2: Brute Force Attack
```
Attacker: Tries to brute force Redis password
Result: Can't connect - port is not accessible
Outcome: ✅ Attack fails before it even starts
```

### Scenario 3: Man-in-the-Middle Attack
```
Attacker: Intercepts network traffic between you and VPS
Result: Sees encrypted WireGuard packets
Outcome: ✅ Can't decrypt without WireGuard keys
```

### Scenario 4: WireGuard Key Theft
```
Attacker: Steals your WireGuard private key
Result: Can connect to VPN, but still needs:
  - Redis password (if configured)
  - PostgreSQL password
Outcome: ⚠️ Partial access - but still requires database credentials
```

**Mitigation:** Use strong database passwords even with WireGuard!

## Conclusion

**Redis and PostgreSQL are secure because:**

1. ✅ **They are NOT exposed to the internet** - ports are closed on firewall
2. ✅ **Only accessible through encrypted VPN tunnel** - WireGuard provides encryption
3. ✅ **Authentication required** - WireGuard keys prevent unauthorized access
4. ✅ **Network isolation** - Docker network adds another layer
5. ✅ **Defense in depth** - Multiple security layers work together

**Without WireGuard keys, an attacker cannot:**
- See that Redis/PostgreSQL exist
- Connect to them
- Attempt to exploit them
- Intercept or read traffic

This is **significantly more secure** than exposing these services directly to the internet!
