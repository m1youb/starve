#!/usr/bin/env python3
"""
Quick test script to verify cross-platform functionality
Tests the main platform-specific functions without requiring root/admin
"""

import platform
import sys
import os

# Add the parent directory to path to import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from flask import Flask
        print("  ✓ Flask imported successfully")
    except ImportError as e:
        print(f"  ✗ Flask import failed: {e}")
        return False
    
    try:
        import netifaces
        print("  ✓ netifaces imported successfully")
    except ImportError as e:
        print(f"  ✗ netifaces import failed: {e}")
        return False
    
    try:
        import scapy
        from scapy.layers.dhcp import DHCP, BOOTP
        from scapy.layers.inet import IP, UDP
        from scapy.layers.l2 import Ether
        print("  ✓ Scapy imported successfully")
    except ImportError as e:
        print(f"  ✗ Scapy import failed: {e}")
        print("    Note: On Windows, ensure Npcap is installed")
        return False
    
    return True

def test_platform_detection():
    """Test platform detection"""
    print("\nTesting platform detection...")
    detected_os = platform.system()
    print(f"  Detected OS: {detected_os}")
    print(f"  Platform: {platform.platform()}")
    print(f"  Python version: {platform.python_version()}")
    return True

def test_admin_check():
    """Test admin/root privilege detection"""
    print("\nTesting privilege detection...")
    
    if platform.system() == 'Windows':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            print(f"  Running as Administrator: {is_admin}")
        except:
            print("  Unable to check administrator status")
            return False
    else:
        try:
            is_root = os.geteuid() == 0
            print(f"  Running as root: {is_root}")
        except AttributeError:
            print("  Unable to check root status (not Unix)")
            return False
    
    return True

def test_network_interfaces():
    """Test network interface detection"""
    print("\nTesting network interface detection...")
    try:
        import netifaces
        interfaces = netifaces.interfaces()
        print(f"  Found {len(interfaces)} network interfaces:")
        
        for iface in interfaces[:5]:  # Show first 5
            # Check if loopback
            is_loopback = (iface in ['lo', 'lo0', 'Loopback Pseudo-Interface 1'] or 
                          'loopback' in iface.lower())
            loopback_marker = " (loopback)" if is_loopback else ""
            
            try:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    print(f"    - {iface}: {ip}{loopback_marker}")
                else:
                    print(f"    - {iface}: No IPv4{loopback_marker}")
            except:
                print(f"    - {iface}: Unable to get address{loopback_marker}")
        
        if len(interfaces) > 5:
            print(f"    ... and {len(interfaces) - 5} more")
        
        return True
    except Exception as e:
        print(f"  ✗ Network interface test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Cross-Platform Compatibility Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Import Test", test_imports()))
    results.append(("Platform Detection", test_platform_detection()))
    results.append(("Privilege Check", test_admin_check()))
    results.append(("Network Interfaces", test_network_interfaces()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
        print("\nThe application should work on this platform.")
        if platform.system() == 'Windows':
            print("Remember to run as Administrator when using the actual app!")
        else:
            print("Remember to run with sudo when using the actual app!")
    else:
        print("Some tests failed! ✗")
        print("\nPlease check the error messages above and install missing dependencies.")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
