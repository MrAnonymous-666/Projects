# NetScan — Network Discovery, Vulnerability Scan & PDF Reporting

A local network security auditing tool built for a college security practical.
It discovers live hosts on your network, runs an nmap-based vulnerability
sweep on each one, and generates a PDF report with plain-English risk
explanations and remediation steps. Includes both a CLI and a simple web
frontend.

> **Legal/ethical note:** Only run this against networks and devices you own
> or have explicit written permission to test (e.g. your home network, or a
> lab network your college has approved for this practical). Scanning
> networks you don't control without permission can be illegal even when
> using detection-only tools like this one.

---

## How it works

```
 [1] Discovery          [2] Vulnerability scan       [3] Report
 netscan/discovery.py   netscan/vuln_scanner.py      netscan/report_generator.py
 (ping sweep)     -->   (nmap -sV --script vuln) --> (PDF with remediation)
```

1. **Discovery** — pings every address in the target subnet in parallel and
   records which hosts respond.
2. **Vulnerability scan** — runs `nmap -sV --script vuln` against each live
   host to detect open services, versions, and known weaknesses (nmap's
   vuln scripts detect/report only — nothing here exploits anything).
3. **Report** — maps each finding to a plain-English risk + fix via a small
   local knowledge base (`netscan/remediation.py`), then renders everything
   into a formatted PDF with `reportlab`.

---

## Project structure

```
netscan-project/
├── cli.py                     # Command-line entry point (runs full pipeline)
├── requirements.txt
├── .gitignore
├── netscan/                   # Core package
│   ├── __init__.py
│   ├── discovery.py           # Step 1: host discovery (ping sweep)
│   ├── vuln_scanner.py        # Step 2: nmap service + vulnerability scan
│   ├── remediation.py         # Knowledge base: findings -> risk/fix text
│   └── report_generator.py    # Step 3: PDF report generation
├── web/                        # Flask web frontend
│   ├── app.py                 # Flask app: /scan, /status/<id>, /report/<id>
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── app.js
└── reports/                    # Generated PDF reports land here (gitignored)
```

---

## Step-by-step setup

### 1. Prerequisites

- Python 3.9+
- **nmap** installed on your system (this is the actual scan engine; the
  Python code just orchestrates it):
  - **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install nmap`
  - **macOS:** `brew install nmap`
  - **Windows:** download the installer from https://nmap.org/download.html
    (this also installs Npcap, which nmap needs on Windows)

Verify it's installed:
```bash
nmap --version
```

### 2. Get the code into VS Code

If you're starting from the files given to you:
```bash
cd path/to/netscan-project
code .
```

Or if you're pushing this to GitHub first and cloning it back down, see the
**Publishing to GitHub** section below.

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the CLI pipeline

Auto-detect and scan your current local network:
```bash
python cli.py
```

Or scan a specific network/host:
```bash
python cli.py 192.168.1.0/24
python cli.py 192.168.1.0/24 -o my_report.pdf
```

This runs discovery → vulnerability scan → PDF report generation in one go
and prints progress as it works. The final PDF is saved to the path you
specified (default: `network_report.pdf`).

**Note on permissions:** nmap normally uses a SYN scan, which needs elevated
privileges. Without them, it automatically falls back to a slower TCP
connect scan, which still works fine for this practical. For best results:
- Linux/macOS: `sudo python cli.py 192.168.1.0/24`
- Windows: run your terminal/VS Code as Administrator

### 6. Run the web frontend

```bash
python web/app.py
```

Then open **http://127.0.0.1:5000** in your browser. Enter a network (or
leave blank to auto-detect), click **Start scan**, and watch the live
progress. When it finishes, a **Download PDF report** button appears.

This is a local single-user demo app (no login/auth) — perfect for your
practical, but don't expose it to the public internet as-is.

---

## Testing individual modules

Each module also works standalone, which is useful for debugging in VS Code:

```bash
# Just discovery
python -m netscan.discovery 192.168.1.0/24

# Just the vuln scanner against specific IPs (writes scan_results.json)
python -m netscan.vuln_scanner 192.168.1.1 192.168.1.10

# Just the report generator, from an existing results file
python -m netscan.report_generator scan_results.json my_report.pdf
```

---

## Extending it further (ideas for your practical writeup)

- **Wireshark/tshark integration**: run a short `tshark` capture during the
  scan and flag unencrypted protocols or unusual traffic patterns as an
  extra "network hygiene" section in the report.
- **Expand `remediation.py`**: add more services/CVE patterns as you
  encounter them during testing on your own lab network.
- **Authentication for the web app**: if you want to demo it to more than
  just yourself, add a simple login before exposing it beyond localhost.
- **Historical comparison**: store past `scan_results.json` files and diff
  them to show "what changed since last scan" — a nice addition for a
  security-monitoring angle in your report.

---

## Publishing to GitHub

From inside the `netscan-project` folder:

```bash
git init
git add .
git commit -m "Initial commit: NetScan pipeline + web frontend"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

The `.gitignore` already excludes virtual environments, `__pycache__`, and
generated scan reports/JSON, so you won't accidentally commit scan data
from a real network.
