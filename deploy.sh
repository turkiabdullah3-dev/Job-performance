#!/bin/bash

# ============================================================
# HR Analytics System - Deployment Script
# Domain: analysis.turki20.sa
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     منظومة إدارة الأداء الوظيفي - Deployment Script          ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║  Domain: analysis.turki20.sa                                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# Configuration
# ============================================================
PROJECT_DIR="/var/www/hr-analytics"
APP_DIR="/var/www/hr-analytics/app"
LOG_DIR="/var/log/hr-analytics"
SERVICE_NAME="hr-analytics"
DOMAIN="analysis.turki20.sa"

# ============================================================
# Functions
# ============================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Create directories
create_directories() {
    log_step "Creating directories..."
    
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$APP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "/var/www/letsencrypt"
    
    log_info "Directories created successfully"
}

# Install dependencies
install_dependencies() {
    log_step "Installing Python dependencies..."
    
    # Update pip
    python3 -m pip install --upgrade pip
    
    # Install required packages
    pip3 install flask flask-cors pandas numpy gunicorn
    
    log_info "Dependencies installed successfully"
}

# Copy application files
copy_app_files() {
    log_step "Copying application files..."
    
    # Copy from current directory
    cp -r /Users/turki/Desktop/hr/* "$PROJECT_DIR/"
    
    # Set permissions
    chmod -R 755 "$PROJECT_DIR"
    chmod 644 "$PROJECT_DIR"/*.py
    chmod 644 "$PROJECT_DIR"/*.html
    chmod 644 "$PROJECT_DIR"/*.css
    chmod 644 "$PROJECT_DIR"/*.js
    
    log_info "Application files copied successfully"
}

# Create systemd service
create_systemd_service() {
    log_step "Creating systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=HR Analytics System - Ministry of Education
After=network.target
Wants=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/production_server.py \\
    --host 127.0.0.1 \\
    --port 8080 \\
    --workers 2

Restart=always
RestartSec=10

# Resource limits
MemoryMax=512M
CPUQuota=80%

# Logging
StandardOutput=append:$LOG_DIR/app.log
StandardError=append:$LOG_DIR/error.log

# Environment
Environment=PYTHONPATH=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    log_info "Systemd service created successfully"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    log_step "Setting up SSL certificate..."
    
    # Install certbot
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    
    # Get certificate (non-interactive)
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN
    
    if [ $? -eq 0 ]; then
        log_info "SSL certificate obtained successfully"
        
        # Setup auto-renewal
        echo "0 0,12 * * * root certbot renew --quiet" >> /etc/crontab
        log_info "Auto-renewal configured"
    else
        log_warn "SSL certificate setup failed. Will use HTTP only."
    fi
}

# Configure firewall
configure_firewall() {
    log_step "Configuring firewall..."
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    echo "y" | ufw enable
    
    log_info "Firewall configured successfully"
}

# Start services
start_services() {
    log_step "Starting services..."
    
    # Start the app
    systemctl start $SERVICE_NAME
    systemctl enable $SERVICE_NAME
    
    # Check status
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Service started successfully"
    else
        log_error "Service failed to start"
        systemctl status $SERVICE_NAME
        exit 1
    fi
    
    # Restart nginx
    systemctl restart nginx
    
    log_info "All services started successfully"
}

# Test deployment
test_deployment() {
    log_step "Testing deployment..."
    
    # Test local connection
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/ | grep -q "200"; then
        log_info "App is responding on port 8080"
    else
        log_warn "App may not be responding yet"
    fi
    
    # Test domain
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        log_info "Domain is responding: https://$DOMAIN/"
    elif [ "$HTTP_CODE" = "000" ]; then
        log_warn "Domain not accessible yet (DNS may need time)"
    else
        log_warn "Domain returned HTTP code: $HTTP_CODE"
    fi
}

# Show deployment info
show_info() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   Deployment Complete!                       ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  🌐  URL:          https://$DOMAIN"
    echo -e "  📡 API Endpoint:  https://$DOMAIN/api"
    echo -e "  📁 Project:       $PROJECT_DIR"
    echo -e "  📄 Logs:          $LOG_DIR"
    echo ""
    echo -e "  ${YELLOW}Useful Commands:${NC}"
    echo -e "    View logs:      journalctl -u $SERVICE_NAME -f"
    echo -e "    Restart:        systemctl restart $SERVICE_NAME"
    echo -e "    Status:         systemctl status $SERVICE_NAME"
    echo -e "    Stop:           systemctl stop $SERVICE_NAME"
    echo ""
    echo -e "  ${YELLOW}Quick Test:${NC}"
    echo -e "    curl https://$DOMAIN/status"
    echo ""
}

# ============================================================
# Main Execution
# ============================================================

case "${1:-deploy}" in
    deploy)
        check_root
        create_directories
        install_dependencies
        copy_app_files
        create_systemd_service
        configure_firewall
        start_services
        test_deployment
        show_info
        ;;
    
    ssl)
        check_root
        setup_ssl
        ;;
    
    restart)
        systemctl restart $SERVICE_NAME
        log_info "Service restarted"
        ;;
    
    stop)
        systemctl stop $SERVICE_NAME
        log_info "Service stopped"
        ;;
    
    status)
        systemctl status $SERVICE_NAME
        ;;
    
    logs)
        journalctl -u $SERVICE_NAME -f
        ;;
    
    update)
        check_root
        log_step "Updating application..."
        copy_app_files
        systemctl restart $SERVICE_NAME
        log_info "Application updated and restarted"
        ;;
    
    *)
        echo "Usage: $0 {deploy|ssl|restart|stop|status|logs|update}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  ssl      - Setup SSL certificate only"
        echo "  restart  - Restart the application"
        echo "  stop     - Stop the application"
        echo "  status   - Show service status"
        echo "  logs     - View application logs"
        echo "  update   - Update application files"
        exit 1
        ;;
esac

