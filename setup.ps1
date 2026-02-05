# Setup script for Windows

Write-Host "Setting up DHCP Starvation Attack Simulator..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment (optional but recommended)
$createVenv = Read-Host "Create a virtual environment? (y/n)"
if ($createVenv -eq "y") {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    .\venv\Scripts\Activate.ps1
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

# Check for Npcap (required for Scapy on Windows)
Write-Host ""
Write-Host "IMPORTANT: Scapy requires Npcap on Windows" -ForegroundColor Yellow
Write-Host "If you haven't installed it yet:" -ForegroundColor Yellow
Write-Host "  1. Download from: https://npcap.com/#download" -ForegroundColor White
Write-Host "  2. Install with 'WinPcap API-compatible Mode' enabled" -ForegroundColor White
Write-Host ""

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Cyan
Write-Host "  1. Right-click PowerShell and 'Run as Administrator'" -ForegroundColor White
Write-Host "  2. Run: python app.py" -ForegroundColor White
Write-Host ""
Write-Host "Then open your browser to http://localhost:5000" -ForegroundColor White
