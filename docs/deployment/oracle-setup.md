# Oracle Cloud Always Free Deployment

## What You Get (Free Forever)

- 4 ARM Ampere CPU cores
- 24 GB RAM
- 200 GB block storage
- Always Free (no credit card charges)

## Step 1: Create Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Click "Start for Free"
3. Sign up with email (credit card required but never charged for Always Free)
4. Select region closest to you (Mumbai for India)

## Step 2: Create VM

1. Go to Compute → Instances → Create Instance
2. Name: "jyotish"
3. Image: Ubuntu 22.04 (Canonical)
4. Shape: VM.Standard.A1.Flex (ARM)
5. CPUs: 4, Memory: 24 GB
6. Add SSH key (create one or paste existing)
7. Click "Create"
8. Wait for RUNNING status
9. Copy the Public IP address

## Step 3: DNS Setup

Option A — Custom domain:
- Add A record: `jyotish.yourdomain.com` → Oracle VM IP
- Caddy handles SSL automatically

Option B — Free DuckDNS:
1. Go to [duckdns.org](https://duckdns.org)
2. Sign in with Google
3. Create subdomain: `jyotish.duckdns.org`
4. Point to Oracle VM IP

## Step 4: Deploy

```bash
# SSH into your VM
ssh ubuntu@YOUR_VM_IP

# Run the setup script
curl -sSL https://raw.githubusercontent.com/master12coder/vedic-ai-framework/main/scripts/deploy/setup_oracle.sh | bash

# Edit environment
nano /opt/jyotish/.env
# Add Google OAuth credentials (see google-oauth-setup.md)

# Configure Caddy
sudo nano /etc/caddy/Caddyfile
# Content:
# jyotish.yourdomain.com {
#     reverse_proxy localhost:8000
# }

# Start services
sudo systemctl start caddy
sudo systemctl start jyotish

# Verify
curl -s http://localhost:8000/health
```

## Step 5: Daily Backup (Optional)

```bash
# Add backup cron job
chmod +x /opt/jyotish/scripts/deploy/backup.sh
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/jyotish/scripts/deploy/backup.sh") | crontab -
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 443 not accessible | Oracle Cloud → Networking → Security Lists → Add Ingress Rule for 443 |
| Caddy can't get SSL | Ensure DNS points to VM IP, port 80 + 443 open |
| App not starting | `sudo journalctl -u jyotish -f` to see logs |
| OAuth redirect error | Check redirect URI matches exactly in Google Console |
