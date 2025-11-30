#!/bin/bash

# DocsHub - Run Script
# This script helps you set up and run the DocsHub application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           DocsHub - Collaborative Editor Setup              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the DocsHub root directory.${NC}"
    exit 1
fi

# Menu
show_menu() {
    echo ""
    echo -e "${YELLOW}What would you like to do?${NC}"
    echo ""
    echo "  1) Install dependencies (first time setup)"
    echo "  2) Start Redis server"
    echo "  3) Start Django development server"
    echo "  4) Start Celery worker (optional)"
    echo "  5) Run database migrations"
    echo "  6) Create superuser"
    echo "  7) View project status"
    echo "  8) Full setup guide"
    echo "  0) Exit"
    echo ""
    read -p "Select an option (0-8): " choice
}

# Install dependencies
install_deps() {
    echo ""
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    echo ""
    
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
    echo ""
    
    echo -e "${YELLOW}Installing Node dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Node dependencies installed${NC}"
    echo ""
    
    echo -e "${YELLOW}Building React frontend...${NC}"
    npm run build
    echo -e "${GREEN}✓ Frontend built${NC}"
    echo ""
    
    echo -e "${YELLOW}Running database migrations...${NC}"
    python manage.py migrate
    echo -e "${GREEN}✓ Database migrations complete${NC}"
    echo ""
    
    echo -e "${GREEN}✓ All dependencies installed!${NC}"
}

# Start Redis
start_redis() {
    echo ""
    echo -e "${BLUE}🔴 Starting Redis Server...${NC}"
    echo -e "${YELLOW}Make sure Redis is installed. If not, install it:${NC}"
    echo "  - macOS: brew install redis"
    echo "  - Ubuntu/Debian: sudo apt-get install redis-server"
    echo "  - Windows: Download from https://github.com/microsoftarchive/redis/releases"
    echo ""
    echo -e "${YELLOW}Starting Redis (press Ctrl+C to stop)...${NC}"
    echo ""
    redis-server
}

# Start Django
start_django() {
    echo ""
    echo -e "${BLUE}🐍 Starting Django Development Server...${NC}"
    echo -e "${YELLOW}The app will be available at http://localhost:8000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    python manage.py runserver
}

# Start Celery
start_celery() {
    echo ""
    echo -e "${BLUE}👷 Starting Celery Worker...${NC}"
    echo -e "${YELLOW}This handles background tasks (optional)${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    celery -A docshub worker -l info
}

# Run migrations
run_migrations() {
    echo ""
    echo -e "${BLUE}🗄️  Running Database Migrations...${NC}"
    echo ""
    python manage.py migrate
    echo ""
    echo -e "${GREEN}✓ Migrations complete${NC}"
}

# Create superuser
create_superuser() {
    echo ""
    echo -e "${BLUE}👤 Creating Superuser...${NC}"
    echo -e "${YELLOW}You'll be prompted to create an admin account${NC}"
    echo ""
    python manage.py createsuperuser
    echo ""
    echo -e "${GREEN}✓ Superuser created${NC}"
    echo -e "${YELLOW}Access admin at http://localhost:8000/admin${NC}"
}

# Project status
project_status() {
    echo ""
    echo -e "${BLUE}📊 Project Status${NC}"
    echo ""
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo -e "${GREEN}✓${NC} Python: $PYTHON_VERSION"
    else
        echo -e "${RED}✗${NC} Python: Not found"
    fi
    
    # Check Node
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓${NC} Node: $NODE_VERSION"
    else
        echo -e "${RED}✗${NC} Node: Not found"
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✓${NC} npm: $NPM_VERSION"
    else
        echo -e "${RED}✗${NC} npm: Not found"
    fi
    
    # Check Redis
    if command -v redis-server &> /dev/null; then
        REDIS_VERSION=$(redis-server --version 2>&1 | head -1)
        echo -e "${GREEN}✓${NC} Redis: $REDIS_VERSION"
    else
        echo -e "${RED}✗${NC} Redis: Not found (needed for real-time features)"
    fi
    
    # Check if dependencies are installed
    if [ -d "node_modules" ]; then
        echo -e "${GREEN}✓${NC} Node modules: Installed"
    else
        echo -e "${RED}✗${NC} Node modules: Not installed"
    fi
    
    if [ -d "venv" ]; then
        echo -e "${GREEN}✓${NC} Virtual environment: Found"
    elif python3 -c "import django" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Django: Installed"
    else
        echo -e "${RED}✗${NC} Django: Not installed"
    fi
    
    # Check if build exists
    if [ -d "static/dist" ]; then
        echo -e "${GREEN}✓${NC} React build: Ready"
    else
        echo -e "${YELLOW}⚠${NC} React build: Not found (run 'npm run build')"
    fi
    
    echo ""
}

# Full setup guide
full_setup_guide() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                 Full Setup Guide                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${YELLOW}Step 1: Install Dependencies${NC}"
    echo "  Run option 1 from the menu to install all dependencies"
    echo ""
    
    echo -e "${YELLOW}Step 2: Prepare 4 Terminal Windows${NC}"
    echo ""
    echo "  ${BLUE}Terminal 1: Redis${NC}"
    echo "  $ redis-server"
    echo ""
    echo "  ${BLUE}Terminal 2: Django${NC}"
    echo "  $ python manage.py runserver"
    echo ""
    echo "  ${BLUE}Terminal 3: Celery (Optional - for background tasks)${NC}"
    echo "  $ celery -A docshub worker -l info"
    echo ""
    echo "  ${BLUE}Terminal 4: Use for other commands${NC}"
    echo ""
    
    echo -e "${YELLOW}Step 3: Create Superuser${NC}"
    echo "  Run option 6 from the menu"
    echo ""
    
    echo -e "${YELLOW}Step 4: Start Services${NC}"
    echo "  You can use options 2 and 3 from the menu to start Redis and Django"
    echo ""
    
    echo -e "${YELLOW}Step 5: Access the Application${NC}"
    echo "  🌐 Main App: http://localhost:8000"
    echo "  🔐 Admin:    http://localhost:8000/admin"
    echo ""
    
    echo -e "${YELLOW}Features:${NC}"
    echo "  ✓ Real-time collaborative editing"
    echo "  ✓ User authentication"
    echo "  ✓ Document & Spreadsheet management"
    echo "  ✓ WebSocket sync"
    echo "  ✓ Version history & Comments"
    echo ""
    
    echo -e "${YELLOW}Tech Stack:${NC}"
    echo "  Backend: Django 4.2 + Channels + Redis"
    echo "  Frontend: React 18 + TypeScript + Vite"
    echo ""
    
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  • If Redis won't start: Install Redis first"
    echo "  • If Django has migration errors: Run 'python manage.py migrate'"
    echo "  • If frontend won't load: Run 'npm run build'"
    echo ""
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1)
            install_deps
            ;;
        2)
            start_redis
            ;;
        3)
            start_django
            ;;
        4)
            start_celery
            ;;
        5)
            run_migrations
            ;;
        6)
            create_superuser
            ;;
        7)
            project_status
            ;;
        8)
            full_setup_guide
            ;;
        0)
            echo ""
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please select 0-8.${NC}"
            ;;
    esac
done
