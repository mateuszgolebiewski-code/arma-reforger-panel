# Arma Reforger Server Management Panel

A lightweight, self-hosted web panel for managing your **Arma Reforger dedicated server** on Linux. Built with Python (Flask) and vanilla JavaScript — no heavy frameworks, no external dependencies at runtime.

> **Live demo:** [demoarma.mateuszgolebiewski.pl](https://demoarma.mateuszgolebiewski.pl) — password: `demo`

---

## Features

- **Server control** — Start, stop and restart your Arma Reforger server from the browser
- **Real-time monitoring** — Live CPU and RAM charts updated every 3 seconds, normalized across CPU cores
- **Live log streaming** — Server console logs polled in real time with colour-coded output (errors, warnings, network events)
- **Mission selector** — 41 built-in missions including vanilla and RHS — Status Quo scenarios
- **Mod management** — Add and remove Workshop mods directly from the panel; changes written to `config.json`
- **Config editor** — Edit server name, scenario, game password and admin password without touching the file system
- **PWA support** — Installable as a native-like app on Android and iOS via any modern browser
- **Session authentication** — Password-protected panel with server-side sessions
- **Single config file** — All settings live in one `config.env` file, no code editing required

---

## Requirements

| Component | Version |
|-----------|---------|
| OS        | Ubuntu 20.04 / 22.04 / 24.04 (or any Debian-based Linux) |
| Python    | 3.10+   |
| pip       | any     |
| Arma Reforger Dedicated Server | installed and configured |

---

## Quick Install

Clone the repository and run the installer as root:

```bash
git clone https://github.com/mateuszgolebiewski/arma-reforger-panel.git
cd arma-reforger-panel
sudo bash install.sh
```

The installer will:
1. Ask you for your server paths and desired panel password
2. Install Python dependencies (`flask`)
3. Copy panel files to `/opt/arma-panel/`
4. Write your `config.env`
5. Create and start a `systemd` service (`arma-panel`)

After installation, open your browser at:
```
http://YOUR_SERVER_IP:8888
```

---

## Manual Install

If you prefer to set things up yourself:

```bash
# 1. Install Flask
pip3 install flask --break-system-packages

# 2. Copy files to your preferred directory
mkdir -p /opt/arma-panel/static
cp app.py index.html login.html /opt/arma-panel/
cp static/* /opt/arma-panel/static/

# 3. Create config
cp config.env /opt/arma-panel/config.env
nano /opt/arma-panel/config.env   # fill in your values

# 4. Create systemd service
sudo nano /etc/systemd/system/arma-panel.service
```

Paste the following into the service file:

```ini
[Unit]
Description=Arma Reforger Management Panel
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/arma-panel
ExecStart=/usr/bin/python3 /opt/arma-panel/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now arma-panel
```

---

## Configuration

All settings are in `config.env`:

```env
# Password for the panel web UI
PANEL_PASSWORD=changeme

# Port the panel listens on
PANEL_PORT=8888

# Path to your Arma Reforger server binary directory
SERVER_DIR=/home/arma/server

# Full path to your server config.json
SERVER_CONFIG=/home/arma/server/config.json

# Arma Reforger log directory
LOG_DIR=/home/arma/.config/ArmaReforger/logs

# Server FPS cap (passed as -maxFPS argument)
MAX_FPS=60
```

After editing `config.env`, restart the panel:
```bash
sudo systemctl restart arma-panel
```

---

## HTTPS / Domain (optional but recommended)

To access the panel over HTTPS with a custom domain, use **nginx as a reverse proxy** with a Let's Encrypt certificate. If you use HestiaCP, you can add a subdomain through its web interface and it will handle SSL automatically.

Nginx location block example:
```nginx
location / {
    proxy_pass http://127.0.0.1:8888;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_read_timeout 3600;
}
```

---

## Useful Commands

```bash
# Check panel status
sudo systemctl status arma-panel

# Restart panel (e.g. after config change)
sudo systemctl restart arma-panel

# View live panel logs
sudo journalctl -u arma-panel -f

# Update panel files
cd arma-reforger-panel
git pull
sudo cp app.py index.html login.html /opt/arma-panel/
sudo systemctl restart arma-panel
```

---

## Project Structure

```
arma-reforger-panel/
├── app.py            # Flask backend — API, server control, metrics
├── index.html        # Main panel UI
├── login.html        # Login screen
├── config.env        # Your local configuration (not committed to git)
├── config.env.example # Configuration template
├── install.sh        # Automated installer
├── static/
│   ├── manifest.json     # PWA manifest
│   ├── service-worker.js # PWA service worker
│   ├── icon-192.png      # App icon
│   └── icon-512.png      # App icon (large)
└── README.md
```

---

## RHS — Status Quo Support

The panel includes mission IDs for all RHS — Status Quo scenarios (requires the [RHS mod](https://reforger.armaplatform.com/workshop/595F2BF2F44836FB-RHS-Status-Quo) to be installed on your server). RHS missions appear automatically in the mission dropdown.

---

## Contributing

Pull requests and issues are welcome. If you run into a problem or want to suggest a feature, open an issue on GitHub.

---

## License

MIT — free to use, modify and distribute.

---

*Built by [Mateusz Gołębiewski](https://mateuszgolebiewski.pl)*
