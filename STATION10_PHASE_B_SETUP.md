# Station10 Phase B Implementation Guide

**Date**: October 13, 2025  
**Goal**: Deploy Station10 multi-user Telegram bot with Phase B (Cloudflare Tunnel + webhook)  
**Subdomains**: `dispatch.station10.media` (bot), `uplink.station10.media` (reserved for upload page)

---

## Prerequisites Checklist

- [ ] Cloudflare account with `station10.media` (✓ confirmed)
- [ ] Linode account (will create)
- [ ] Telegram bot token (will get from @BotFather)
- [ ] API keys: `VOXTRAL_API_KEY`, `XAI_API_KEY` (✓ have these)
- [ ] Local ClipScribe repo with current code

---

## Task 1: Configure Cloudflare Tunnel (CURRENT)

### 1.1 Create Cloudflare Zero Trust Account
1. Go to https://one.dash.cloudflare.com/
2. Sign in with your Cloudflare account
3. If prompted, choose "Free" plan for Zero Trust
4. Accept terms and complete setup

### 1.2 Create Tunnel via Dashboard
1. In Zero Trust dashboard: **Networks** → **Tunnels**
2. Click **Create a tunnel**
3. Choose **Cloudflared** connector
4. Name: `station10-dispatch-tunnel`
5. Click **Save tunnel**
6. **STOP HERE** - Don't run the install command yet (we'll do this on Linode VPS)
7. Note the tunnel token (starts with `eyJ...`) - we'll need this later

### 1.3 Configure Public Hostname Route
1. In the tunnel configuration, go to **Public Hostname** tab
2. Add public hostname:
   - **Subdomain**: `dispatch`
   - **Domain**: `station10.media`
   - **Type**: HTTP
   - **URL**: `localhost:8080`
3. Under **Additional application settings**:
   - Enable **No TLS Verify** (since we're routing to localhost)
4. Click **Save hostname**

### 1.4 Reserve uplink Subdomain (DNS Only)
1. Go to Cloudflare dashboard → **DNS** → **Records**
2. Add CNAME record:
   - **Type**: CNAME
   - **Name**: `uplink`
   - **Target**: `station10.media` (placeholder; we'll update later)
   - **Proxy status**: Proxied (orange cloud)
   - **TTL**: Auto
3. Save

### 1.5 Verify DNS Propagation
```bash
# Check dispatch subdomain (should show Cloudflare IPs)
dig dispatch.station10.media

# Check uplink subdomain
dig uplink.station10.media
```

Expected: Both should resolve to Cloudflare proxy IPs (104.x.x.x or similar)

---

## Task 2: Provision Linode VPS

### 2.1 Create Linode Account
1. Go to https://www.linode.com/
2. Sign up (use your Station10 email)
3. Add payment method
4. Verify email

### 2.2 Create Linode Instance
1. Click **Create** → **Linode**
2. **Distribution**: Ubuntu 24.04 LTS
3. **Region**: Choose closest to your team (e.g., Newark, NJ for East Coast US)
4. **Linode Plan**: Shared CPU → **Nanode 1GB** ($5/month)
   - 1 CPU, 1GB RAM, 25GB SSD, 1TB transfer
5. **Linode Label**: `station10-bot`
6. **Root Password**: Generate strong password (save in password manager)
7. **SSH Keys**: Add your public key if you have one
8. Click **Create Linode**

### 2.3 Wait for Provisioning
- Status will change from "Provisioning" to "Running" (~30-60 seconds)
- Note the **IP Address** (e.g., `45.79.x.x`)

### 2.4 Initial SSH Connection
```bash
# Connect as root
ssh root@45.79.x.x

# Update system
apt update && apt upgrade -y

# Install basic security tools
apt install -y ufw fail2ban unattended-upgrades
```

### 2.5 Harden Server
```bash
# Configure firewall (allow only outbound; Tunnel handles inbound)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw enable

# Create service user
adduser --disabled-password --gecos "" station10
usermod -aG sudo station10

# Set up sudo without password for service user
echo "station10 ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/station10
```

---

## Task 3: Install Runtime Dependencies

### 3.1 Install Python 3.12
```bash
# Switch to service user
su - station10

# Install Python 3.12
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Set Python 3.12 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

### 3.2 Install Poetry
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
echo 'export PATH="/home/station10/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
poetry --version
```

### 3.3 Install Media Tools
```bash
# Install ffmpeg and yt-dlp
sudo apt install -y ffmpeg curl

# Install yt-dlp
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# Verify
ffmpeg -version
yt-dlp --version
```

### 3.4 Install cloudflared
```bash
# Download cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install
sudo dpkg -i cloudflared.deb

# Verify
cloudflared --version

# Clean up
rm cloudflared.deb
```

---

## Task 4: Deploy ClipScribe Code

### 4.1 Transfer Code to VPS
```bash
# On your LOCAL machine (not VPS):
cd /Users/base/Projects/clipscribe

# Create deployment archive (exclude cache, logs, output, venv)
tar czf clipscribe-deploy.tar.gz \
  --exclude='cache' \
  --exclude='logs' \
  --exclude='output' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  .

# Transfer to VPS
scp clipscribe-deploy.tar.gz station10@45.79.x.x:~/

# Clean up local archive
rm clipscribe-deploy.tar.gz
```

### 4.2 Extract and Set Up on VPS
```bash
# On VPS as station10 user:
cd ~
tar xzf clipscribe-deploy.tar.gz
mv clipscribe-deploy clipscribe  # or extract directly
cd clipscribe

# Install dependencies
poetry install --no-dev

# Verify installation
poetry run python -c "import clipscribe; print('✓ ClipScribe installed')"
```

### 4.3 Create Environment File
```bash
# On VPS:
cd ~/clipscribe

# Create env.production
cat > env.production << 'ENVEOF'
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_SECRET_TOKEN=your_webhook_secret_here

# API Keys
VOXTRAL_API_KEY=your_voxtral_key_here
XAI_API_KEY=your_xai_key_here

# Cloudflare R2 (will add after Task 4)
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=station10-intelligence

# Bot Config
PORT=8080
WEBHOOK_URL=https://dispatch.station10.media
OUTPUT_DIR=/home/station10/clipscribe/output
LOG_LEVEL=INFO
ENVEOF

# Secure the file
chmod 600 env.production
```

**ACTION REQUIRED**: 
1. Get Telegram bot token from @BotFather (see Task 5.1)
2. Generate webhook secret: `openssl rand -hex 32`
3. Update `env.production` with real values

---

## Task 5: Set Up Telegram Bot

### 5.1 Create Bot with @BotFather
1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. **Bot name**: `Station10 Dispatch` (display name)
4. **Bot username**: `station10dispatch_bot` (must end in `_bot`)
5. Save the bot token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
6. Send `/setdescription` → Select your bot → Set description:
   ```
   Station10 intelligence dispatch bot. Process videos, extract entities, build knowledge graphs.
   ```
7. Send `/setabouttext` → Select your bot → Set about:
   ```
   Multi-user intelligence platform for Station10 Media
   ```

### 5.2 Update env.production
```bash
# On VPS:
nano ~/clipscribe/env.production

# Update TELEGRAM_BOT_TOKEN with the token from @BotFather
# Update TELEGRAM_SECRET_TOKEN with output from: openssl rand -hex 32
```

---

## Task 6: Configure Cloudflare Tunnel on VPS

### 6.1 Authenticate cloudflared
```bash
# On VPS as station10 user:
cloudflared tunnel login
```

This will print a URL. Open it in a browser, select `station10.media`, authorize.

### 6.2 Connect Tunnel to VPS
```bash
# Get your tunnel ID from Cloudflare dashboard
# Or list tunnels:
cloudflared tunnel list

# Create tunnel config
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << 'CFEOF'
tunnel: station10-dispatch-tunnel
credentials-file: /home/station10/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: dispatch.station10.media
    service: http://localhost:8080
  - service: http_status:404
CFEOF

# Get tunnel credentials (run this in Cloudflare dashboard or via API)
# The tunnel token from step 1.2 contains the credentials
```

### 6.3 Install Tunnel as systemd Service
```bash
# Install service
sudo cloudflared service install

# Edit service to run as station10 user
sudo systemctl edit cloudflared.service
# Add these lines:
[Service]
User=station10
Group=station10

# Enable and start
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Check status
sudo systemctl status cloudflared
```

---

## Next Steps

Once Task 1-6 are complete, we'll continue with:
- Task 7: Set up R2 bucket, IAM, lifecycle
- Task 8: Implement webhook server with secret verification
- Task 9: Make bot non-blocking, add file handlers
- Task 10: Implement signed upload flow
- Task 11: Create uplink upload page
- Task 12: Testing and validation

---

## Troubleshooting

### Tunnel not connecting
```bash
# Check cloudflared logs
sudo journalctl -u cloudflared -f

# Verify config
cat ~/.cloudflared/config.yml

# Test tunnel manually
cloudflared tunnel run station10-dispatch-tunnel
```

### DNS not resolving
```bash
# Check Cloudflare DNS
dig dispatch.station10.media

# Verify tunnel status in dashboard
# Networks → Tunnels → station10-dispatch-tunnel should show "HEALTHY"
```

### SSH connection issues
```bash
# From local machine, verify SSH access
ssh -v station10@45.79.x.x

# If key auth fails, use password
ssh station10@45.79.x.x -o PreferredAuthentications=password
```

