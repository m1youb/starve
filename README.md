# DHCP Starvation Attack Simulator

An educational cybersecurity tool that simulates DHCP starvation attacks for authorized security testing and learning purposes.

## ⚠️ Legal Disclaimer

**FOR EDUCATIONAL USE ONLY**

This tool is designed exclusively for:
- Authorized security testing on networks you own or have explicit permission to test
- Educational purposes in controlled laboratory environments
- Cybersecurity training and research

**Unauthorized use of this tool against networks you don't own or have permission to test is illegal and may result in criminal prosecution.**

## Features

- 🔍 **Auto-Discovery**: Automatically detect DHCP servers on the network
- 🎯 **Targeted Attack**: Simulate DHCP starvation by exhausting IP addresses
- 📊 **Real-time Monitoring**: Live table of exhausted IP addresses
- 🌐 **Network Intelligence**: Display router IP, subnet mask, and DHCP pool information
- 🎨 **Modern UI**: Clean interface with light/dark mode (Claude AI color palette)
- 🔄 **Interface Selection**: Choose from available network interfaces
- 💻 **Cross-Platform**: Works on Windows, Linux, and macOS

## How It Works

DHCP starvation is a DoS attack that exhausts all available IP addresses in a DHCP server's pool by:

1. Sending multiple DHCP DISCOVER messages with spoofed MAC addresses
2. Accepting all DHCP OFFER responses
3. Requesting each offered IP address
4. Preventing legitimate clients from obtaining IP addresses

## Requirements

- **OS**: Windows 10/11, Linux (Ubuntu, Kali, Debian, etc.), or macOS
- **Python**: 3.8+
- **Privileges**: Administrator (Windows) or Root/sudo (Linux/macOS) access (required for Scapy)
- **Network**: Active network interface
- **Windows Only**: Npcap driver (download from https://npcap.com/)
- **Note**: Uses `psutil` on Windows (no C++ compiler needed) or `netifaces` on Linux/macOS

## Installation

### 1. Clone or Download Files

Ensure you have all files in the same directory:
```
dhcp-starvation-simulator/
├── app.py
├── requirements.txt
├── setup.sh          # Linux/macOS setup script
├── setup.ps1         # Windows setup script
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── styles.css
    └── js/
        └── app.js
```

### 2. Install Dependencies

#### Option A: Automated Setup (Recommended)

**On Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**On Windows PowerShell:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

#### Option B: Manual Installation

**On Linux:**
```bash
# Update package list
sudo apt update

# Install Python dependencies
pip3 install -r requirements.txt

# If you encounter issues, install system packages
sudo apt install python3-scapy python3-flask python3-netifaces
```

**On Windows:**
```powershell
# Install Python dependencies
pip install -r requirements.txt

# IMPORTANT: Install Npcap for Scapy to work on Windows
# Download from: https://npcap.com/#download
# Install with "WinPcap API-compatible Mode" enabled
```

**On macOS:**
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install libpcap if needed
brew install libpcap
```

## Usage

### 1. Start the Application

**IMPORTANT**: Must run with administrator/root privileges for network packet manipulation:

**On Linux/macOS:**
```bash
sudo python3 app.py
```

**On Windows:**
```powershell
# Right-click PowerShell and select "Run as Administrator", then:
python app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
 * Restarting with stat
```
```

### 2. Access the Web Interface

Open your browser and navigate to:
```
http://localhost:5000
```

Or from another device on the network:
```
http://<your-kali-ip>:5000
```

### 3. Configure Attack

1. **Select Network Interface**: Choose from the dropdown (e.g., `eth0`, `wlan0`)
2. **DHCP Server IP**: 
   - Click "Discover" to auto-detect the DHCP server
   - Or manually enter the IP address
3. **Start Attack**: Click "Start Attack" button

### 4. Monitor Results

- **Network Information**: View router IP, subnet mask, and pool range
- **Exhausted IPs Table**: Real-time list of exhausted IP addresses
- **Status Indicator**: Shows current attack state

### 5. Stop Attack

Click "Stop Attack" button to terminate the simulation.

## UI Features

### Light/Dark Mode
- Toggle between light and dark themes using the sun/moon icon
- Automatically saves preference
- Uses Claude AI's color palette for a professional look

### Network Discovery
- Auto-discovers DHCP server on selected interface
- Retrieves network configuration details
- Displays pool information

## Testing in a Safe Environment

### Recommended Lab Setup

1. **Virtual Network**: Use VirtualBox/VMware with isolated network
2. **Test Router**: Configure a dedicated router/DHCP server
3. **No Production Networks**: Never test on production environments

### Sample Virtual Lab

```
[Kali Linux VM] ← Virtual Network → [DHCP Server VM]
   (Attacker)                         (Target)
```

### Setting Up Virtual DHCP Server

Using `dnsmasq` on Ubuntu:

```bash
# Install dnsmasq
sudo apt install dnsmasq

# Configure DHCP
sudo nano /etc/dnsmasq.conf

# Add:
interface=eth0
dhcp-range=192.168.100.50,192.168.100.150,12h

# Start service
sudo systemctl start dnsmasq
```

## Troubleshooting

### "Must run as administrator/root" Error

**On Linux/macOS:**
```bash
# Use sudo
sudo python3 app.py
```

**On Windows:**
```powershell
# Right-click PowerShell and select "Run as Administrator"
# Then run: python app.py
```

### No Interfaces Found

**On Linux:**
```bash
# Check network interfaces
ip addr show

# Ensure interface is up
sudo ip link set eth0 up
```

**On Windows:**
```powershell
# Check network interfaces
ipconfig /all

# Or
Get-NetAdapter
```

### Windows: Npcap Not Installed
If Scapy fails on Windows with WinPcap errors:
1. Download Npcap from https://npcap.com/#download
2. Run installer with **"Install Npcap in WinPcap API-compatible Mode"** checked
3. Restart your computer
4. Reinstall Scapy: `pip install --force-reinstall scapy`

### DHCP Server Not Found
- Verify network connectivity
- Check if DHCP server is active
- Ensure no firewall blocking DHCP traffic (ports 67/68)
- Try different interface
- **Windows**: Disable Windows Firewall temporarily for testing

### Port 5000 Already in Use
```bash
# Change port in app.py (last line)
app.run(host='0.0.0.0', port=8080, debug=True)
```

### Scapy Permission Errors

**On Linux/macOS:**
```bash
# Ensure running with sudo
sudo python3 app.py

# Or install with proper permissions
sudo pip3 install scapy
```

**On Windows:**
```powershell
# Run PowerShell as Administrator
# Reinstall Scapy with Npcap support
pip install --force-reinstall scapy
```

## Technical Details

### Attack Mechanism

1. **DHCP Discovery**: Sends broadcast DISCOVER packets
2. **Spoofed MACs**: Uses random MAC addresses for each request
3. **IP Reservation**: Requests all offered IPs
4. **Pool Exhaustion**: Continues until pool is depleted

### Network Packet Flow

```
Attacker → DHCP DISCOVER (Spoofed MAC) → DHCP Server
Attacker ← DHCP OFFER (IP Address)     ← DHCP Server
Attacker → DHCP REQUEST (Accept IP)    → DHCP Server
Attacker ← DHCP ACK (Confirm)          ← DHCP Server
```

## Security Implications

### Attack Impact
- Denial of Service (DoS) for legitimate clients
- Network unavailability
- Service disruption

### Detection Methods
- Monitor abnormal DHCP request rates
- Track unique MAC addresses
- Analyze network traffic patterns
- Use IDS/IPS systems

### Prevention Measures
- Enable DHCP snooping on switches
- Implement port security
- Limit DHCP requests per port
- Use static IP assignments for critical devices
- Enable 802.1X authentication

## Project Structure

```
.
├── app.py                 # Flask backend with Scapy logic
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main UI template
└── static/
    ├── css/
    │   └── styles.css    # Claude AI color palette
    └── js/
        └── app.js        # Frontend logic
```

## Academic Context

This tool is designed for:
- Cybersecurity coursework
- Network security labs
- Penetration testing training
- Understanding DHCP protocol vulnerabilities
- Learning defensive security measures

## Assignment Integration

### Demonstration Points
1. Show DHCP protocol understanding
2. Explain attack mechanism
3. Demonstrate tool functionality
4. Discuss mitigation strategies
5. Present ethical considerations

### Report Suggestions
- Document attack methodology
- Analyze captured packets (Wireshark)
- Compare with other DoS attacks
- Propose defense mechanisms
- Discuss legal/ethical implications

## License

Educational use only. See legal disclaimer above.

## Credits

Created for cybersecurity education. Interface inspired by Claude AI design system.

## Support

For issues or questions related to:
- **Technical**: Check troubleshooting section
- **Academic**: Consult your course instructor
- **Security**: Report vulnerabilities responsibly

---

**Remember**: With great power comes great responsibility. Use this tool ethically and legally.
