#!/bin/bash
# Script to run Django migrations
# Make sure your virtual environment is activated before running this

cd /mnt/Extra/COde_work/Things/DocsHub

# Activate virtual environment
source venv/bin/activate

# Run migrations
echo "Running migrations..."
python3 manage.py migrate

echo "Migrations complete!"

