"""
cli.py
-------
Top-level command-line entry point that runs the full pipeline:
  1. Discover live hosts on the network (netscan.discovery)
  2. Run nmap vulnerability scans on each host (netscan.vuln_scanner)
  3. Generate a PDF report (netscan.report_generator)

Usage:
    python cli.py                     # auto-detect local network
    python cli.py 192.168.1.0/24      # scan a specific network
    python cli.py 192.168.1.0/24 -o my_report.pdf

IMPORTANT: Only run this against networks/hosts you own or have explicit
permission to test.
"""

import sys
import argparse

from netscan import discovery, vuln_scanner, report_generator


def print_banner():
    print("""
  _   _      _    _____
 | \\ | |    | |  / ____|
 |  \\| | ___| |_| (___   ___ __ _ _ __
 | . ` |/ _ \\ __|\\___ \\ / __/ _` | '_ \\
 | |\\  |  __/ |_ ____) | (_| (_| | | | |
 |_| \\_|\\___|\\__|_____/ \\___\\__,_|_| |_|

NetScan - Network discovery, vulnerability scan & PDF reporting
Only scan networks/hosts you own or have explicit permission to test.
    """)


def main():
    parser = argparse.ArgumentParser(description="NetScan: discover hosts, scan for vulnerabilities, generate a PDF report.")
    parser.add_argument("network", nargs="?", default=None,
                         help="Network to scan, e.g. 192.168.1.0/24. Omit to auto-detect your local network.")
    parser.add_argument("-o", "--output", default="network_report.pdf",
                         help="Output PDF path (default: network_report.pdf)")
    args = parser.parse_args()

    print_banner()

    try:
        network = discovery.parse_network(args.network)
    except Exception as e:
        print(f"Error parsing network: {e}")
        sys.exit(1)

    print(f"[1/3] Discovering live hosts on {network} ...")
    hosts = discovery.scan_network(network)
    print(f"      Found {len(hosts)} live host(s): {', '.join(hosts) if hosts else '(none)'}")

    if not hosts:
        print("No live hosts found - nothing to scan. Exiting.")
        sys.exit(0)

    print(f"[2/3] Running nmap vulnerability scans on {len(hosts)} host(s) ...")

    def progress(done, total, ip):
        print(f"      ({done}/{total}) scanned {ip}")

    results = vuln_scanner.scan_hosts(hosts, progress_callback=progress)

    print(f"[3/3] Generating PDF report -> {args.output}")
    report_generator.generate_report(results, network_label=str(network), output_path=args.output)

    print(f"\nDone. Report saved to {args.output}")


if __name__ == "__main__":
    main()
