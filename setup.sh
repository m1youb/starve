#!/bin/bash
# Setup script for Linux/macOS

echo "Setting up DHCP Starvation Attack Simulator..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Create virtual environment (optional but recommended)
read -p "Create a virtual environment? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the application:"
echo "  sudo python3 app.py"
echo ""
echo "Then open your browser to http://localhost:5000"
