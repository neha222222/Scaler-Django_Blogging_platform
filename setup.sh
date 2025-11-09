#!/bin/bash

# Blogging Platform Setup Script
# This script automates the initial setup process

set -e  # Exit on error

echo "🚀 Starting Blogging Platform Setup..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Run migrations
echo "🗄️  Setting up database..."
python manage.py makemigrations
python manage.py migrate
echo "✅ Database setup complete"
echo ""

# Create superuser prompt
echo "👤 Create admin superuser..."
echo "   (You can skip this and create it later with: python manage.py createsuperuser)"
read -p "   Create superuser now? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi
echo ""

# Run tests
echo "🧪 Running tests..."
python manage.py test blog --verbosity=2
echo ""

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Run server: python manage.py runserver"
echo "   3. Visit API docs: http://127.0.0.1:8000/swagger/"
echo "   4. Visit admin: http://127.0.0.1:8000/admin/"
echo ""
echo "🎉 Happy coding!"

