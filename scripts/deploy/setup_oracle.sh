#!/bin/bash
# DaivAI — Oracle Cloud Always Free Deployment
# Run on fresh Ubuntu 22.04 ARM VM (4 CPU, 24GB RAM)
# Usage: bash setup_oracle.sh

set -euo pipefail

echo "═══════════════════════════════════════════"
echo "  DaivAI — Oracle Cloud Setup"
echo "  श्री गणेशाय नमः"
echo "═══════════════════════════════════════════"

# ── System packages ──
echo "Installing system dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3.12-dev \
    git build-essential curl

# ── Clone repository ──
echo "Cloning repository..."
if [ ! -d /opt/daivai ]; then
    sudo git clone https://github.com/master12coder/daiv-ai.git /opt/daivai
    sudo chown -R ubuntu:ubuntu /opt/daivai
fi
cd /opt/daivai

# ── Python environment ──
echo "Setting up Python environment..."
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e "engine/"
pip install -e "products/[groq]"
pip install -e "apps/[web]"
pip install gunicorn

# ── Environment file ──
if [ ! -f /opt/daivai/.env ]; then
    echo "Creating .env file..."
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > /opt/daivai/.env << EOF
GOOGLE_CLIENT_ID=REPLACE_ME
GOOGLE_CLIENT_SECRET=REPLACE_ME
SECRET_KEY=${SECRET}
DATABASE_URL=sqlite:////opt/daivai/data/daivai.db
ALLOWED_EMAILS=
GROQ_API_KEY=
EOF
    echo "⚠️  Edit /opt/daivai/.env with your Google OAuth credentials"
fi

# ── Data directory ──
mkdir -p /opt/daivai/data

# ── Caddy (reverse proxy + auto SSL) ──
echo "Installing Caddy..."
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
    sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null || true
echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" | \
    sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy

# ── Systemd service ──
echo "Creating systemd service..."
sudo tee /etc/systemd/system/daivai.service > /dev/null << EOF
[Unit]
Description=DaivAI Web App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/daivai
EnvironmentFile=/opt/daivai/.env
ExecStart=/opt/daivai/.venv/bin/gunicorn \
    "daivai_app.web.app:create_app()" \
    -w 2 -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable daivai

# ── Firewall ──
echo "Opening firewall ports..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
sudo netfilter-persistent save 2>/dev/null || true

echo ""
echo "═══════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit /opt/daivai/.env with Google OAuth credentials"
echo "  2. Edit /etc/caddy/Caddyfile with your domain"
echo "  3. sudo systemctl start daivai"
echo "  4. sudo systemctl start caddy"
echo ""
echo "  शुभम् भवतु"
echo "═══════════════════════════════════════════"
