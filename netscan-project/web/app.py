"""
web/app.py
-----------
Flask backend for the NetScan web frontend. Wraps the discovery -> vuln
scan -> PDF report pipeline behind a small job API so the browser can
kick off a scan, poll progress, and download the resulting PDF.

Run with:  python web/app.py
Then open: http://127.0.0.1:5000

IMPORTANT: Only run this against networks/hosts you own or have explicit
permission to test. This app has no authentication - do not expose it
to the public internet as-is; it is intended for local/lab use for a
college practical demo.
"""

import os
import sys
import uuid
import threading

from flask import Flask, request, jsonify, render_template, send_file, abort

# Allow importing the `netscan` package from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from netscan import discovery, vuln_scanner, report_generator

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

app = Flask(__name__)

# In-memory job store. Fine for a single-user local/lab demo (college
# practical). For a real multi-user deployment, replace with a database.
JOBS = {}
JOBS_LOCK = threading.Lock()


def run_pipeline(job_id, network_arg):
    """Runs the full pipeline in a background thread and updates JOBS[job_id]."""
    try:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "parsing_network"
        network = discovery.parse_network(network_arg or None)

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "discovering_hosts"
            JOBS[job_id]["network"] = str(network)

        def discovery_progress(done, total):
            with JOBS_LOCK:
                JOBS[job_id]["discovery_progress"] = f"{done}/{total}"

        hosts = discovery.scan_network(network, progress_callback=discovery_progress)

        with JOBS_LOCK:
            JOBS[job_id]["hosts"] = hosts
            if not hosts:
                JOBS[job_id]["status"] = "done"
                JOBS[job_id]["message"] = "No live hosts found."
                return
            JOBS[job_id]["status"] = "scanning_vulnerabilities"
            JOBS[job_id]["scan_progress"] = f"0/{len(hosts)}"

        def scan_progress(done, total, ip):
            with JOBS_LOCK:
                JOBS[job_id]["scan_progress"] = f"{done}/{total}"
                JOBS[job_id]["current_host"] = ip

        results = vuln_scanner.scan_hosts(hosts, progress_callback=scan_progress)

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "generating_report"

        pdf_path = os.path.join(REPORTS_DIR, f"{job_id}.pdf")
        report_generator.generate_report(results, network_label=str(network), output_path=pdf_path)

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["report_path"] = pdf_path
            JOBS[job_id]["results"] = results

    except Exception as e:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def start_scan():
    data = request.get_json(silent=True) or {}
    network_arg = data.get("network", "").strip()

    job_id = str(uuid.uuid4())
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "queued"}

    thread = threading.Thread(target=run_pipeline, args=(job_id, network_arg), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        abort(404)
    # Don't send the full raw results/report_path over the status endpoint,
    # just enough for the UI to render progress.
    safe_job = {k: v for k, v in job.items() if k != "results"}
    return jsonify(safe_job)


@app.route("/report/<job_id>")
def download_report(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job or job.get("status") != "done" or not job.get("report_path"):
        abort(404)
    return send_file(job["report_path"], as_attachment=True, download_name="network_report.pdf")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
