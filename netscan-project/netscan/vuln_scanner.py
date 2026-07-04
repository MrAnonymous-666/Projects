"""
netscan/vuln_scanner.py
------------------------
Step 2 of the pipeline. Takes a list of live hosts (from discovery.py) and
runs nmap service/version detection plus nmap's built-in 'vuln' NSE script
category against each one.

Nmap's vuln scripts only ever REPORT known weaknesses (banner/version
fingerprinting, known misconfigurations, publicly disclosed CVE checks) -
they do not exploit anything. This is the standard, safe way to do a
defensive vulnerability sweep of your own network.

IMPORTANT: Only run this against networks/hosts you own or have explicit
permission to test.

Requires: nmap installed on the system, and `pip install python-nmap`
"""

import nmap
import datetime


DEFAULT_PORTS = "21-23,25,53,80,110,139,143,443,445,3306,3389,8080"

SEVERITY_KEYWORDS = {
    "critical": ["remote code execution", "rce", "critical"],
    "high": ["vulnerable", "exploit", "backdoor", "unauthenticated"],
    "medium": ["outdated", "weak", "deprecated", "misconfigur"],
    "low": ["information disclosure", "banner", "version detected"],
}


# =================================================================================================================
def classify_severity(text):
    """Given nmap script output text, guess a severity bucket from common phrasing."""
    text_lower = text.lower()
    for severity in ["critical", "high", "medium", "low"]:
        if any(keyword in text_lower for keyword in SEVERITY_KEYWORDS[severity]):
            return severity
    return "info"
# =================================================================================================================


# =================================================================================================================
def scan_host(ip, ports=DEFAULT_PORTS):
    """
    Runs nmap service/version detection + vuln scripts against a single host.
    Returns {ip, scanned_at, findings: [...], error}
    """
    scanner = nmap.PortScanner()
    result = {
        "ip": ip,
        "scanned_at": datetime.datetime.now().isoformat(),
        "findings": [],
        "error": None,
    }

    try:
        # -sV: service/version detection
        # --script vuln: nmap's vulnerability-detection script category
        # -Pn: skip nmap's own host-alive check (we already confirmed it's up)
        # -T4: faster timing, reasonable for a LAN scan
        scanner.scan(ip, ports, arguments="-sV -Pn --script vuln -T4")
    except Exception as e:
        result["error"] = str(e)
        return result

    if ip not in scanner.all_hosts():
        result["error"] = "Host did not respond to nmap scan (may have gone offline or blocked probes)."
        return result

    host_data = scanner[ip]

    for proto in host_data.all_protocols():
        ports_data = host_data[proto]
        for port, port_info in ports_data.items():
            if port_info.get("state") != "open":
                continue

            service = port_info.get("name", "unknown")
            product = port_info.get("product", "")
            version = port_info.get("version", "")

            result["findings"].append({
                "port": port,
                "protocol": proto,
                "service": service,
                "product": product,
                "version": version,
                "script": None,
                "output": f"Open port running {service} {product} {version}".strip(),
                "severity": "info",
            })

            script_output = port_info.get("script", {})
            for script_name, script_text in script_output.items():
                result["findings"].append({
                    "port": port,
                    "protocol": proto,
                    "service": service,
                    "product": product,
                    "version": version,
                    "script": script_name,
                    "output": script_text.strip(),
                    "severity": classify_severity(script_text),
                })

    return result
# =================================================================================================================


# =================================================================================================================
def scan_hosts(ip_list, ports=DEFAULT_PORTS, progress_callback=None):
    """
    Runs scan_host() against a list of IPs. Returns a list of per-host result dicts.
    Optionally calls progress_callback(done, total, ip) after each host finishes,
    useful for a web UI progress bar.
    """
    all_results = []
    total = len(ip_list)
    for i, ip in enumerate(ip_list, start=1):
        result = scan_host(ip, ports)
        all_results.append(result)
        if progress_callback:
            progress_callback(i, total, ip)
    return all_results
# =================================================================================================================


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m netscan.vuln_scanner <ip1> [ip2] [ip3] ...")
        sys.exit(1)

    ips = sys.argv[1:]
    results = scan_hosts(ips)
    with open("scan_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to scan_results.json")
