#!/bin/bash

# ============================================================
# Local Development with Domain Access (macOS)
# Domain: analysis.turki20.sa
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     منظومة إدارة الأداء الوظيفي - Local Development         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

PROJECT_DIR="/Users/turki/Desktop/hr"
PORT=8080
DOMAIN="analysis.turki20.sa"

# Check if ngrok is installed
check_ngrok() {
    if ! command -v ngrok &> /dev/null; then
        echo -e "${YELLOW}[INFO]${NC} Ngrok not installed. Installing via Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}[ERROR]${NC} Homebrew not found. Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        brew install ngrok
    fi
}

# Install ngrok
install_ngrok() {
    echo -e "${YELLOW}[INFO]${NC} Installing ngrok..."
    if ! command -v brew &> /dev/null; then
        echo "Please install Homebrew first: https://brew.sh"
        exit 1
    fi
    brew install --cask ngrok
}

# Setup Cloudflare Tunnel (alternative)
setup_cloudflared() {
    echo -e "${YELLOW}[INFO]${NC} Setting up Cloudflare Tunnel..."
    
    # Download cloudflared
    cd /tmp
    curl -L -o cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    
    echo -e "${GREEN}[OK]${NC} Cloudflare tunnel installed"
}

# Start Flask server
start_server() {
    echo -e "${YELLOW}[INFO]${NC} Starting Flask server..."
    
    # Install dependencies if needed
    pip3 install flask flask-cors pandas numpy --quiet 2>/dev/null || true
    
    # Start server in background
    cd "$PROJECT_DIR"
    python3 production_server.py --host 0.0.0.0 --port $PORT --debug &
    
    SERVER_PID=$!
    echo $SERVER_PID > /tmp/hr-analytics.pid
    
    echo -e "${GREEN}[OK]${NC} Server started on port $PORT (PID: $SERVER_PID)"
    echo ""
}

# Start ngrok tunnel
start_ngrok_tunnel() {
    echo -e "${YELLOW}[INFO]${NC} Starting ngrok tunnel..."
    
    cd "$PROJECT_DIR"
    
    # Start ngrok
    ngrok http $PORT --log=stdout > /tmp/ngrok.log 2>&1 &
    
    # Wait for tunnel to establish
    sleep 3
    
    # Get the public URL
    if command -v jq &> /dev/null; then
        TUNNEL_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    else
        TUNNEL_URL=$(grep -o 'https://[^ ]*' /tmp/ngrok.log | head -1)
    fi
    
    echo -e "${GREEN}[OK]${NC} Ngrok tunnel established"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                       URLs المتاحة                           ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  🌐 Local:     http://localhost:$PORT"
    echo -e "  🌐 Network:   http://$(ipconfig getifaddr en0):$PORT"
    echo -e "  🌐 Ngrok:     $TUNNEL_URL"
    echo ""
    
    # Save tunnel URL
    echo "$TUNNEL_URL" > /tmp/tunnel-url.txt
}

# Setup cloudflare tunnel with custom domain
start_cloudflare_tunnel() {
    echo -e "${YELLOW}[INFO]${NC} Starting Cloudflare tunnel for $DOMAIN..."
    
    # This requires Cloudflare Zero Trust with a paid plan
    # For free alternative, use ngrok with custom domain (paid feature)
    
    echo -e "${YELLOW}[INFO]${NC} For custom domain $DOMAIN, you have options:"
    echo ""
    echo "  1. Ngrok (Free): Use random URL"
    echo "  2. Ngrok Paid: Use custom domain"
    echo "  3. Cloudflare Tunnel: Requires Cloudflare account"
    echo "  4. Localtunnel: npm install -g localtunnel"
    echo ""
    
    read -p "Choose option (1-4): " choice
    
    case $choice in
        1)
            start_ngrok_tunnel
            ;;
        2)
            echo "Ngrok paid feature. Run: ngrok http $PORT --domain=$DOMAIN"
            ;;
        3)
            echo "Setup Cloudflare Zero Trust tunnel:"
            echo "  cloudflared tunnel --url http://localhost:$PORT"
            ;;
        4)
            localtunnel --port $PORT --subdomain ${DOMAIN%%.*} &
            ;;
    esac
}

# Stop all services
stop_services() {
    echo -e "${YELLOW}[INFO]${NC} Stopping services..."
    
    # Stop Flask server
    if [ -f /tmp/hr-analytics.pid ]; then
        kill $(cat /tmp/hr-analytics.pid) 2>/dev/null || true
        rm /tmp/hr-analytics.pid
    fi
    
    # Stop ngrok
    pkill -f "ngrok" 2>/dev/null || true
    
    echo -e "${GREEN}[OK]${NC} Services stopped"
}

# Status check
status_check() {
    echo -e "${BLUE}[STATUS]${NC} Checking services..."
    
    # Check Flask
    if [ -f /tmp/hr-analytics.pid ]; then
        if kill -0 $(cat /tmp/hr-analytics.pid) 2>/dev/null; then
            echo -e "  ✓ Flask server running (PID: $(cat /tmp/hr-analytics.pid))"
        else
            echo -e "  ✗ Flask server not running"
        fi
    else
        echo -e "  ✗ Flask server not running"
    fi
    
    # Check ngrok
    if pgrep -f "ngrok" > /dev/null; then
        echo -e "  ✓ Ngrok tunnel running"
        if [ -f /tmp/tunnel-url.txt ]; then
            echo -e "  URL: $(cat /tmp/tunnel-url.txt)"
        fi
    else
        echo -e "  ✗ Ngrok tunnel not running"
    fi
    
    # Test local connection
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/ | grep -q "200"; then
        echo -e "  ✓ Local server responding on port $PORT"
    fi
}

# Show logs
show_logs() {
    echo -e "${BLUE}[LOGS]${NC} Application logs:"
    echo ""
    tail -50 /tmp/ngrok.log 2>/dev/null || echo "No logs available"
}

# Help
show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|tunnel}"
    echo ""
    echo "Commands:"
    echo "  start   - Start Flask server only (local access)"
    echo "  tunnel  - Start Flask + ngrok tunnel (public access)"
    echo "  stop    - Stop all services"
    echo "  restart - Restart all services"
    echo "  status  - Check service status"
    echo "  logs    - View tunnel logs"
    echo ""
}

# Main
case "${1:-help}" in
    start)
        check_ngrok
        start_server
        echo ""
        echo -e "${GREEN}[OK]${NC} Open http://localhost:$PORT in your browser"
        ;;
    
    tunnel)
        install_ngrok
        start_server
        start_ngrok_tunnel
        echo ""
        echo -e "${GREEN}[OK]${NC} Your app is now accessible publicly!"
        ;;
    
    stop)
        stop_services
        ;;
    
    restart)
        stop_services
        sleep 1
        $0 tunnel
        ;;
    
    status)
        status_check
        ;;
    
    logs)
        show_logs
        ;;
    
    *)
        show_help
        ;;
esac

