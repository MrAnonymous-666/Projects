"""
netscan/remediation.py
------------------------
Step 2.5 of the pipeline. A small local knowledge base that maps common
services/findings to plain-English risk explanations and remediation
steps. Used by report_generator.py to turn raw nmap findings into
something a non-expert can act on.
"""

SERVICE_ADVICE = {
    "ftp": {
        "risk": "FTP transmits credentials and data in plain text, making it easy to intercept on the network.",
        "fix": "Disable FTP if not required. If file transfer is needed, use SFTP or FTPS instead.",
    },
    "telnet": {
        "risk": "Telnet sends everything, including passwords, unencrypted. It is one of the most commonly abused legacy services.",
        "fix": "Disable Telnet entirely and use SSH for remote administration instead.",
    },
    "ssh": {
        "risk": "SSH is generally secure, but outdated versions or weak configurations (password auth, weak ciphers, default port) increase brute-force risk.",
        "fix": "Keep SSH updated, disable password authentication in favor of key-based auth, disable root login, and consider changing the default port or adding rate-limiting/fail2ban.",
    },
    "http": {
        "risk": "Unencrypted HTTP traffic (including any login forms) can be read or modified in transit.",
        "fix": "Redirect all HTTP traffic to HTTPS with a valid TLS certificate. Disable plaintext HTTP where possible.",
    },
    "https": {
        "risk": "HTTPS is good practice, but outdated TLS versions, weak ciphers, or expired/self-signed certificates undermine it.",
        "fix": "Ensure TLS 1.2+ only, disable weak ciphers, and use a certificate from a trusted CA (or properly deployed internal CA).",
    },
    "microsoft-ds": {
        "risk": "SMB (file sharing) has a long history of critical vulnerabilities (e.g. EternalBlue) and is a common ransomware entry point.",
        "fix": "Disable SMBv1 entirely, restrict SMB to trusted internal segments only, and keep the OS patched.",
    },
    "netbios-ssn": {
        "risk": "NetBIOS exposes host/share information and has known exploitation history.",
        "fix": "Disable NetBIOS over TCP/IP if not required, or restrict it to trusted internal segments.",
    },
    "mysql": {
        "risk": "An exposed database service increases the attack surface for data theft or unauthorized access, especially with default/weak credentials.",
        "fix": "Do not expose database ports to the wider network; bind to localhost or a private subnet, enforce strong credentials, and use a firewall to restrict access to known application servers.",
    },
    "ms-wbt-server": {
        "risk": "RDP is a very common target for brute-force attacks and has had several critical remote-code-execution vulnerabilities (e.g. BlueKeep).",
        "fix": "Avoid exposing RDP directly to the internet; use a VPN, enable Network Level Authentication, enforce strong passwords/MFA, and keep it patched.",
    },
    "domain": {
        "risk": "An exposed/misconfigured DNS service can be abused for cache poisoning, zone transfers, or DDoS amplification.",
        "fix": "Restrict zone transfers to trusted secondary servers, disable recursion for external clients, and keep the DNS software patched.",
    },
    "pop3": {
        "risk": "POP3 without encryption transmits mailbox credentials and content in plain text.",
        "fix": "Disable plain POP3 and use POP3S (encrypted) instead, or migrate to a modern mail protocol.",
    },
    "imap": {
        "risk": "IMAP without encryption transmits mailbox credentials and content in plain text.",
        "fix": "Disable plain IMAP and use IMAPS (encrypted) instead.",
    },
}

SEVERITY_GENERIC_ADVICE = {
    "critical": "This finding indicates a serious, potentially remotely exploitable weakness. Treat it as top priority: patch, reconfigure, or isolate the affected service immediately.",
    "high": "This finding suggests a real, likely exploitable weakness. Prioritize a fix soon and consider restricting network access to this service in the meantime.",
    "medium": "This finding indicates a configuration or version weakness that should be addressed as part of regular maintenance.",
    "low": "This finding is lower risk but still worth reviewing, as it may reveal information useful to an attacker during reconnaissance.",
    "info": "This is informational (e.g. an open port/service) and not a vulnerability by itself, but every unnecessary open port increases attack surface.",
}


# =================================================================================================================
def get_remediation(finding):
    """
    Given a single finding dict (as produced by vuln_scanner.scan_host),
    returns (risk_text, fix_text) - falling back to generic severity-based
    advice if the service isn't in the knowledge base.
    """
    service = (finding.get("service") or "").lower()
    if service in SERVICE_ADVICE:
        advice = SERVICE_ADVICE[service]
        return advice["risk"], advice["fix"]

    severity = finding.get("severity", "info")
    generic = SEVERITY_GENERIC_ADVICE.get(severity, SEVERITY_GENERIC_ADVICE["info"])
    return generic, "Review the finding details, verify whether the service is needed, keep software patched, and restrict network access to only what is necessary."
# =================================================================================================================
