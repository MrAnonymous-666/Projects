"""
netscan/discovery.py
---------------------
Finds live hosts on a network via ICMP ping sweep. This is step 1 of the
pipeline: discovery.py -> vuln_scanner.py -> report_generator.py
"""

import sys
import socket
import ipaddress
import concurrent.futures
import platform
import subprocess
import re


# =================================================================================================================
def get_local_ip():
    """
    Reliably gets the machine's real outbound-facing IP by asking the OS
    which local interface would be used to reach a public address.
    Avoids accidentally picking loopback or virtual adapters.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
# =================================================================================================================


# =================================================================================================================
def cidr_to_mask(cidr):
    """Converts a CIDR prefix length (e.g. 24) to dotted-decimal mask (e.g. 255.255.255.0)."""
    cidr = int(cidr)
    mask_int = (0xffffffff << (32 - cidr)) & 0xffffffff
    return socket.inet_ntoa(mask_int.to_bytes(4, "big"))
# =================================================================================================================


# =================================================================================================================
def get_subnet_mask(ip):
    """
    Finds the subnet mask belonging specifically to the given IP (not just
    the first interface found), trying modern tools first and never
    crashing if a command is missing.
    """
    system = platform.system().lower()
    try:
        if system == 'windows':
            output = subprocess.check_output("ipconfig", universal_newlines=True)
            for block in output.split("\n\n"):
                if ip in block:
                    mask_match = re.search(r'Subnet Mask[. ]*: ([\d.]+)', block)
                    if mask_match:
                        return mask_match.group(1)
        else:
            try:
                output = subprocess.check_output(
                    ['ip', '-o', '-f', 'inet', 'addr', 'show'],
                    universal_newlines=True
                )
                for line in output.splitlines():
                    if f"inet {ip}/" in line:
                        cidr_match = re.search(r'inet ' + re.escape(ip) + r'/(\d+)', line)
                        if cidr_match:
                            return cidr_to_mask(cidr_match.group(1))
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass

            try:
                output = subprocess.check_output("ifconfig", shell=True, universal_newlines=True)
                for block in output.split("\n\n"):
                    if ip in block:
                        mask_match = re.search(r'netmask (0x[\da-f]+|[\d.]+)', block)
                        if mask_match:
                            mask = mask_match.group(1)
                            if mask.startswith("0x"):
                                mask = socket.inet_ntoa(int(mask, 16).to_bytes(4, "big"))
                            return mask
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass
    except Exception:
        pass

    return '255.255.255.0'
# =================================================================================================================


# =================================================================================================================
def mask_to_cidr(mask):
    """Converts a dotted-decimal subnet mask to CIDR notation. Falls back to /24 if malformed."""
    try:
        return sum(bin(int(x)).count('1') for x in mask.split('.'))
    except Exception:
        return 24
# =================================================================================================================


# =================================================================================================================
def parse_network(arg=None):
    """
    Parses a network argument into an ipaddress.ip_network object.
    No argument -> auto-detects the local network.
    """
    if not arg:
        ip = get_local_ip()
        mask = get_subnet_mask(ip)
        cidr = mask_to_cidr(mask)
        return ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
    if '/' in arg:
        return ipaddress.ip_network(arg, strict=False)
    elif re.match(r'^\d+\.\d+\.\d+$', arg):
        return ipaddress.ip_network(arg + '.0/24', strict=False)
    elif re.match(r'^\d+\.\d+\.\d+\.\d+$', arg):
        return ipaddress.ip_network(arg + '/24', strict=False)
    else:
        raise ValueError("Invalid network format")
# =================================================================================================================


# =================================================================================================================
def ping(ip):
    """Pings a single IP. Returns the IP string if it responds, otherwise None."""
    ip = str(ip)
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", "1000", ip]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", ip]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        if re.search(r"ttl", result.stdout, re.IGNORECASE):
            return ip
    except Exception:
        return None
    return None
# =================================================================================================================


# =================================================================================================================
def scan_network(network, progress_callback=None):
    """
    Pings every host in the network in parallel. Returns a sorted list of
    IP strings that responded. Optionally calls progress_callback(done, total)
    after each ping completes, useful for a web UI progress bar.
    """
    online = []
    hosts = list(network.hosts())
    total = len(hosts)
    done = 0
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(ping, ip): ip for ip in hosts}
            for future in concurrent.futures.as_completed(futures):
                done += 1
                try:
                    result = future.result()
                    if result:
                        online.append(result)
                except Exception:
                    pass
                if progress_callback:
                    progress_callback(done, total)
    except KeyboardInterrupt:
        print("\nScan interrupted by user. Showing results so far...")

    return sorted(online, key=lambda x: tuple(map(int, x.split('.'))))
# =================================================================================================================


def show_help():
    print(
        "Usage: python -m netscan.discovery [network]\n"
        "Examples:\n"
        "  python -m netscan.discovery                 # Scan current local network\n"
        "  python -m netscan.discovery 192.168.1.0/24   # Scan specific network"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] in ['-h', '--help']:
        show_help()
        sys.exit(0)
    try:
        network = parse_network(args[0] if args else None)
    except Exception as e:
        print(f"Error: {e}")
        show_help()
        sys.exit(1)

    print(f"Scanning network: {network}")
    hosts = scan_network(network)
    print("\nOnline hosts:")
    for host in hosts:
        print(host)
