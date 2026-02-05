# Cross-Platform Compatibility Guide

This document outlines the changes made to ensure the DHCP Starvation Attack Simulator works on Windows, Linux, and macOS.

## Changes Made

### 1. **app.py** - Core Application
- Added `import os`, `import sys`, and `import platform` for cross-platform support
- Replaced Unix-specific `os.geteuid()` with cross-platform `check_admin_privileges()` function
- Updated loopback interface detection to handle multiple OS naming conventions:
  - Linux: `lo`
  - macOS: `lo0`
  - Windows: `Loopback Pseudo-Interface 1`
- Added Windows administrator privilege detection using `ctypes.windll.shell32.IsUserAnAdmin()`

### 2. **Directory Structure**
- Organized files into proper Flask structure:
  ```
  ├── app.py
  ├── requirements.txt
  ├── setup.sh          # Linux/macOS
  ├── setup.ps1         # Windows
  ├── templates/
  │   └── index.html
  └── static/
      ├── css/
      │   └── styles.css
      └── js/
          └── app.js
  ```

### 3. **Setup Scripts**
- **setup.sh**: Automated setup for Linux/macOS
  - Python version check
  - Virtual environment creation (optional)
  - Dependency installation
- **setup.ps1**: Automated setup for Windows
  - Python version check
  - Virtual environment creation (optional)
  - Dependency installation
  - Npcap installation reminder

### 4. **README.md**
- Updated requirements section with Windows, Linux, and macOS
- Added platform-specific installation instructions
- Updated usage section with OS-specific commands
- Enhanced troubleshooting with Windows-specific issues
- Added Npcap installation guide for Windows users

## Platform-Specific Requirements

### Windows
- **Npcap**: Required for packet capture (replaces WinPcap)
  - Download: https://npcap.com/#download
  - Must enable "WinPcap API-compatible Mode" during installation
- **Administrator privileges**: Required to run the application
- **PowerShell**: Recommended for command execution

### Linux
- **sudo/root access**: Required for packet manipulation
- **libpcap**: Usually pre-installed on most distributions
- **Network interfaces**: Standard naming (eth0, wlan0, etc.)

### macOS
- **sudo/root access**: Required for packet manipulation
- **libpcap**: May need installation via Homebrew
- **Security permissions**: May require granting terminal network access

## Known Platform Differences

### Network Interface Names
- **Windows**: Long descriptive names (e.g., "Ethernet", "Wi-Fi")
- **Linux**: Short names (e.g., "eth0", "wlan0", "ens33")
- **macOS**: BSD-style names (e.g., "en0", "en1")

### Privilege Elevation
- **Windows**: Right-click → "Run as Administrator"
- **Linux/macOS**: Use `sudo` command

### Packet Capture
- **Windows**: Requires Npcap driver
- **Linux**: Uses built-in libpcap
- **macOS**: Uses built-in libpcap/BPF

## Testing Recommendations

### Windows
1. Test on Windows 10 and Windows 11
2. Verify Npcap installation and compatibility
3. Test with Windows Firewall enabled/disabled
4. Test on different network types (Ethernet, Wi-Fi)

### Linux
1. Test on Ubuntu, Debian, Kali Linux
2. Verify permissions with different user configurations
3. Test network interface detection
4. Test on VirtualBox/VMware virtual networks

### macOS
1. Test on recent macOS versions (10.15+)
2. Verify security permissions for network access
3. Test with Homebrew-installed dependencies
4. Test on both Intel and Apple Silicon if possible

## Troubleshooting by Platform

### Windows Issues
1. **"Npcap not found"**: Install Npcap with WinPcap compatibility
2. **Permission denied**: Run PowerShell as Administrator
3. **No interfaces found**: Check network adapter status in Device Manager
4. **Firewall blocks**: Temporarily disable Windows Firewall for testing

### Linux Issues
1. **Permission denied**: Use `sudo` to run the application
2. **Module not found**: Install system packages via apt/yum
3. **Interface not available**: Bring up interface with `ip link set up`

### macOS Issues
1. **Permission denied**: Use `sudo` and grant Security & Privacy permissions
2. **libpcap errors**: Install via Homebrew: `brew install libpcap`
3. **Interface detection**: macOS uses unique BSD naming (en0, en1)

## Development Notes

### Cross-Platform Code Patterns

**Privilege Detection:**
```python
def check_admin_privileges():
    if platform.system() == 'Windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0
```

**Interface Filtering:**
```python
# Skip loopback (cross-platform)
if iface in ['lo', 'lo0', 'Loopback Pseudo-Interface 1'] or 'loopback' in iface.lower():
    continue
```

**Path Handling:**
Flask automatically handles path separators correctly on all platforms.

## Future Improvements

1. **Auto-detect Npcap on Windows** and provide installation prompts
2. **Add interface validation** specific to each platform
3. **Create installers** for each platform (MSI for Windows, DEB/RPM for Linux)
4. **Add Docker support** for consistent cross-platform deployment
5. **Implement platform-specific logging** for better debugging

## Resources

- **Scapy on Windows**: https://scapy.readthedocs.io/en/latest/installation.html#windows
- **Npcap Documentation**: https://npcap.com/guide/
- **Python platform module**: https://docs.python.org/3/library/platform.html
- **netifaces documentation**: https://pypi.org/project/netifaces/
