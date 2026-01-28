# HR Analytics System - Deployment Guide
# Domain: analysis.turki20.sa

## Quick Start (Local Development)

### 1. Run Locally
```bash
cd /Users/turki/Desktop/hr
python3 app.py
```
Then open: http://127.0.0.1:8080

---

## Production Deployment (VPS/Server)

### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- Nginx web server
- Domain pointing to server IP
- SSH access with sudo privileges

### Step 1: Upload Files to Server

**Option A: Using SCP**
```bash
scp -r /Users/turki/Desktop/hr/* user@your-server-ip:/tmp/
```

**Option B: Using Git**
```bash
git clone your-repo-url
cd hr-analytics
```

### Step 2: Run Deployment Script

```bash
# Make executable
chmod +x deploy.sh

# Run full deployment
sudo ./deploy.sh deploy
```

This will:
- Create necessary directories
- Install Python dependencies
- Copy application files
- Create systemd service
- Configure firewall
- Start services

### Step 3: Setup SSL Certificate

```bash
sudo ./deploy.sh ssl
```

This uses Let's Encrypt to get free SSL certificate.

### Step 4: Verify

Open: https://analysis.turki20.sa

---

## Manual Deployment Steps

If you prefer manual setup:

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install python3-pip nginx software-properties-common certbot python3-certbot-nginx
pip3 install flask flask-cors pandas numpy gunicorn
```

### 2. Create Directory
```bash
sudo mkdir -p /var/www/hr-analytics
sudo mkdir -p /var/log/hr-analytics
sudo mkdir -p /var/www/letsencrypt
```

### 3. Copy Files
```bash
sudo cp -r /Users/turki/Desktop/hr/* /var/www/hr-analytics/
sudo chmod -R 755 /var/www/hr-analytics
```

### 4. Configure Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/analysis.turki20.sa
sudo ln -s /etc/nginx/sites-available/analysis.turki20.sa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Create Systemd Service
```bash
sudo cp hr-analytics.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hr-analytics
sudo systemctl start hr-analytics
```

### 6. Setup SSL
```bash
sudo certbot --nginx -d analysis.turki20.sa -d www.analysis.turki20.sa
```

---

## Service Management

```bash
# View status
sudo systemctl status hr-analytics

# Restart service
sudo systemctl restart hr-analytics

# View logs
sudo journalctl -u hr-analytics -f

# Stop service
sudo systemctl stop hr-analytics
```

---

## File Structure

```
/var/www/hr-analytics/
├── app.py                    # Original Flask app (development)
├── production_server.py      # Production Flask app (use this)
├── index.html               # Main HTML page
├── styles.css               # Styling
├── script.js                # Frontend JavaScript
├── nginx.conf               # Nginx configuration
├── deploy.sh                # Deployment script
└── README.md               # This file

/var/log/hr-analytics/
├── app.log                  # Application logs
└── error.log               # Error logs
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main page |
| `/init-session` | GET | Initialize session |
| `/upload` | POST | Upload Excel file |
| `/progress` | GET | Get processing progress |
| `/analytics` | POST | Get analytics results |
| `/get-columns` | POST | Get file columns |
| `/analyze-custom` | POST | Custom analysis |
| `/clear` | POST | Clear data |
| `/status` | GET | Health check |
| `/health` | GET | Load balancer health |

---

## Troubleshooting

### App not starting
```bash
# Check logs
sudo journalctl -u hr-analytics -e

# Check port
sudo lsof -i :8080
```

### Nginx errors
```bash
# Test config
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### SSL certificate issues
```bash
# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Domain not resolving
- Wait 24-48 hours for DNS propagation
- Check domain DNS settings
- Verify A record points to server IP

---

## Security Notes

1. **Keep SSL certificates renewed** - Auto-renewal is set up
2. **Firewall** - UFW is configured to allow only needed ports
3. **Sessions** - Automatically expire after 2 hours
4. **Rate limiting** - Built into the application

---

## Support

For issues:
1. Check application logs: `sudo journalctl -u hr-analytics -f`
2. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Verify service status: `sudo systemctl status hr-analytics`

---

## Ministry of Education - KSA

This system is configured for the Ministry of Education's Performance Management department.
All data processing is done locally on the server.

