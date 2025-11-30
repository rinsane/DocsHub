#!/bin/bash
# DocsHub Setup Script

echo "DocsHub Setup Initialization"
echo "============================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "✓ Virtual environment activated"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "✓ Python dependencies installed"

# Install Node dependencies
if command -v npm &> /dev/null; then
    echo "Installing Node dependencies..."
    npm install
    echo "✓ Node dependencies installed"
    
    # Build Tailwind CSS
    echo "Building Tailwind CSS..."
    npm run build:css
    echo "✓ Tailwind CSS built"
else
    echo "⚠ npm not found. Skipping frontend build."
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p static/css static/js media templates/accounts templates/documents templates/spreadsheets templates/notifications
echo "✓ Directories created"

# Run migrations
echo "Running Django migrations..."
python manage.py migrate
echo "✓ Migrations complete"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "✓ Static files collected"

echo ""
echo "============================"
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a superuser: python manage.py createsuperuser"
echo "2. Start Redis: redis-server"
echo "3. Start Django: python manage.py runserver"
echo "4. (Optional) Start Celery: celery -A docshub worker -l info"
echo ""
