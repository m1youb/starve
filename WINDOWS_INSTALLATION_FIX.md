# 🔧 Windows Installation Fix - No C++ Compiler Needed!

## ✅ Problem Solved!

The original `netifaces` package required **Microsoft Visual C++ Build Tools** to compile on Windows, which caused installation failures. 

## 🎯 Solution Applied

I've updated the project to automatically use **`psutil`** instead, which:
- ✅ Has pre-built wheels for Windows (no compilation needed)
- ✅ Works perfectly for network interface detection
- ✅ Is already installed on your system
- ✅ Automatically falls back if `netifaces` is unavailable

## 📦 Updated Dependencies

**New `requirements.txt`:**
```
Flask>=3.0.0
scapy>=2.5.0
psutil>=5.9.0
```

**What Changed:**
- ❌ Removed: `netifaces==0.11.0` (requires C++ compiler on Windows)
- ✅ Added: `psutil>=5.9.0` (pre-built wheels available)

## 🚀 Installation Steps (Windows)

### Step 1: Install Npcap
**REQUIRED** for Scapy to work on Windows:
1. Download from: https://npcap.com/#download
2. Run installer
3. ✅ Check **"Install Npcap in WinPcap API-compatible Mode"**
4. Complete installation
5. **Restart your computer** (important!)

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

This should now work without errors! ✅

### Step 3: Verify Installation
Run the test script:
```powershell
python test_platform.py
```

### Step 4: Run the Application
**Important:** Must run as Administrator for packet capture to work.

1. Right-click **PowerShell** → **"Run as Administrator"**
2. Navigate to project folder:
   ```powershell
   cd "C:\Users\ayoub\OneDrive\Desktop\Python Project"
   ```
3. Run the application:
   ```powershell
   python app.py
   ```
4. Open browser to: **http://localhost:5000**

## 🔍 How It Works

The updated `app.py` now includes smart fallback logic:

```python
# Try to import netifaces, fall back to psutil if not available
try:
    import netifaces
    USE_NETIFACES = True
except ImportError:
    import psutil
    USE_NETIFACES = False
    print("Note: Using psutil for network interface detection")
```

**On Windows:**
- Uses `psutil` (no compilation needed)
- Gets network interfaces via `psutil.net_if_addrs()`
- Works perfectly with Scapy

**On Linux/macOS:**
- Can use either `netifaces` or `psutil`
- Both work well on these platforms

## ⚠️ Common Issues & Solutions

### Issue: Npcap Not Installed
**Error:** `Scapy fails to send packets`
**Solution:** Install Npcap from https://npcap.com/ with WinPcap compatibility mode

### Issue: Not Running as Administrator
**Error:** `ERROR: This script must be run with administrator/root privileges!`
**Solution:** Right-click PowerShell → "Run as Administrator"

### Issue: Windows Firewall Blocking
**Error:** `DHCP server not found`
**Solution:** 
1. Temporarily disable Windows Firewall for testing
2. Or add exception for Python/Scapy

### Issue: Wrong Python Version
**Error:** Version incompatibilities
**Solution:** Ensure Python 3.8+ is installed:
```powershell
python --version
```

## 📊 Testing

### Quick Test (No Admin Required)
```powershell
python test_platform.py
```

Expected output:
```
✓ Flask imported successfully
✓ Scapy imported successfully
✓ psutil imported successfully
✓ Platform Detection: Windows
✓ Network Interfaces found: X interfaces
```

### Full Test (Requires Admin)
```powershell
# Run as Administrator
python app.py
```

Should see:
```
Using psutil for network interface detection
Starting DHCP Starvation Attack Simulator...
Access the web interface at: http://localhost:5000

 * Running on http://0.0.0.0:5000
```

## 🎉 Benefits of This Fix

| Before | After |
|--------|-------|
| ❌ Required Visual C++ Build Tools (1-2 GB download) | ✅ Uses pre-built wheels (instant install) |
| ❌ Complex installation process | ✅ Simple `pip install` |
| ❌ Compilation errors on Windows | ✅ No compilation needed |
| ❌ Platform-specific issues | ✅ Works on all platforms |

## 📝 Summary

You can now install and run the DHCP Starvation Attack Simulator on Windows **without installing Visual Studio Build Tools**!

**Just remember:**
1. ✅ Install Npcap (one-time setup)
2. ✅ Run `pip install -r requirements.txt`
3. ✅ Run PowerShell as Administrator
4. ✅ Execute `python app.py`

The application will automatically use `psutil` for network interface detection, which works perfectly on Windows!
