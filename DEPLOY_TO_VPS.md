# Station10 Bot Deployment Steps

**Run these commands on the VPS (as station10 user)**

## Step 1: Redeploy Updated Code

The bot code has been completely rewritten with:
- ✅ Proper aiohttp webhook server
- ✅ Secret token verification
- ✅ Non-blocking async processing
- ✅ File upload handlers (≤1.5GB via Telegram)
- ✅ Health check endpoint

Transfer new code from your Mac:

```bash
# On Mac:
cd /Users/base/Projects/clipscribe
./create_deployment.sh
scp clipscribe-deploy.tar.gz root@173.230.150.96:/tmp/
rm clipscribe-deploy.tar.gz

# On VPS (as station10):
cd ~
rm -rf src/ tests/ scripts/ examples/ docs/ pyproject.toml poetry.lock
sudo mv /tmp/clipscribe-deploy.tar.gz ~/
sudo chown station10:station10 ~/clipscribe-deploy.tar.gz
tar xzf clipscribe-deploy.tar.gz
poetry install --without dev --extras enterprise
```

## Step 2: Configure Cloudflare Tunnel

```bash
# Authenticate cloudflared with your Cloudflare account
cloudflared tunnel login
```

This will print a URL - open it in browser, select `station10.media`, authorize.

```bash
# Create tunnel config directory
mkdir -p ~/.cloudflared

# Create config file
cat > ~/.cloudflared/config.yml << 'CFEOF'
tunnel: station10-dispatch-tunnel
credentials-file: /home/station10/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: dispatch.station10.media
    service: http://localhost:8080
  - service: http_status:404
CFEOF
```

**IMPORTANT**: You need the tunnel credentials file. Get it from Cloudflare:

1. Go to Zero Trust dashboard: https://one.dash.cloudflare.com/
2. Navigate to **Networks** → **Tunnels**
3. Click on **station10-dispatch-tunnel**
4. Look for the connector token or credentials JSON

OR use the install command from the dashboard to get credentials automatically.

## Step 3: Install and Start Tunnel

```bash
# Install tunnel as system service
sudo cloudflared service install

# Start tunnel
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f
```

## Step 4: Install Bot as System Service

```bash
# Copy service file
sudo cp ~/scripts/station10-bot.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable bot service
sudo systemctl enable station10-bot

# Start bot
sudo systemctl start station10-bot

# Check status
sudo systemctl status station10-bot

# View logs
sudo journalctl -u station10-bot -f
```

## Step 5: Verify Everything Works

```bash
# Check tunnel is healthy
sudo systemctl status cloudflared

# Check bot is running
sudo systemctl status station10-bot

# Check bot logs for webhook setup message
sudo journalctl -u station10-bot -n 50

# You should see:
# "Starting Station10 Dispatch Bot on port 8080"
# "Webhook URL: https://dispatch.station10.media/webhook"
# "✓ Webhook configured successfully"
```

## Step 6: Test the Bot

1. Open Telegram
2. Search for your bot: `@station10dispatch_bot`
3. Send: `/start`
4. You should get a welcome message

If it works: ✅ Bot is live!

## Troubleshooting

### Tunnel not connecting
```bash
# Check cloudflared logs
sudo journalctl -u cloudflared -f

# Manually test tunnel
cloudflared tunnel run station10-dispatch-tunnel
```

### Bot not starting
```bash
# Check bot logs
sudo journalctl -u station10-bot -f

# Test bot manually
cd ~
source env.production
poetry run python -m src.clipscribe.bot.station10_bot
```

### Webhook not receiving updates
```bash
# Check webhook info
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo

# Should show:
# - url: https://dispatch.station10.media/webhook
# - has_custom_certificate: false
# - pending_update_count: 0
```

## Next Steps After Bot is Running

1. Test video processing: `/process https://youtube.com/watch?v=...`
2. Test file upload: Send a video file to the bot
3. Check database: `sqlite3 ~/station10.db "SELECT * FROM users;"`
4. Monitor costs: Send `/stats` to the bot

