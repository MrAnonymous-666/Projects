const form = document.getElementById("scan-form");
const scanBtn = document.getElementById("scan-btn");
const statusPanel = document.getElementById("status-panel");
const statusStage = document.getElementById("status-stage");
const statusNetwork = document.getElementById("status-network");
const statusHosts = document.getElementById("status-hosts");
const statusProgress = document.getElementById("status-progress");
const progressFill = document.getElementById("progress-fill");
const statusMessage = document.getElementById("status-message");
const downloadLink = document.getElementById("download-link");

const STAGE_LABELS = {
  queued: "Queued",
  parsing_network: "Parsing network",
  discovering_hosts: "Discovering live hosts",
  scanning_vulnerabilities: "Running vulnerability scan",
  generating_report: "Generating PDF report",
  done: "Done",
  error: "Error",
};

let pollTimer = null;

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const network = document.getElementById("network").value.trim();

  scanBtn.disabled = true;
  scanBtn.textContent = "Starting...";
  statusPanel.hidden = false;
  downloadLink.hidden = true;
  statusMessage.textContent = "";
  progressFill.style.width = "0%";

  try {
    const res = await fetch("/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ network }),
    });
    const data = await res.json();
    pollStatus(data.job_id);
  } catch (err) {
    statusMessage.textContent = "Failed to start scan: " + err;
    scanBtn.disabled = false;
    scanBtn.textContent = "Start scan";
  }
});

function pollStatus(jobId) {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`/status/${jobId}`);
      if (!res.ok) return;
      const job = await res.json();
      renderStatus(job, jobId);

      if (job.status === "done" || job.status === "error") {
        clearInterval(pollTimer);
        scanBtn.disabled = false;
        scanBtn.textContent = "Start scan";
      }
    } catch (err) {
      // transient network hiccup, keep polling
    }
  }, 1000);
}

function renderStatus(job, jobId) {
  statusStage.textContent = STAGE_LABELS[job.status] || job.status;
  statusNetwork.textContent = job.network || "—";
  statusHosts.textContent = job.hosts ? job.hosts.length : "—";

  let progressText = "—";
  let pct = 0;

  if (job.status === "discovering_hosts" && job.discovery_progress) {
    progressText = `discovery ${job.discovery_progress}`;
    const [done, total] = job.discovery_progress.split("/").map(Number);
    pct = total ? (done / total) * 40 : 0; // discovery = first 40% of bar
  } else if (job.status === "scanning_vulnerabilities" && job.scan_progress) {
    progressText = `host scan ${job.scan_progress}` + (job.current_host ? ` (${job.current_host})` : "");
    const [done, total] = job.scan_progress.split("/").map(Number);
    pct = 40 + (total ? (done / total) * 50 : 0); // vuln scan = next 50%
  } else if (job.status === "generating_report") {
    progressText = "compiling PDF";
    pct = 95;
  } else if (job.status === "done") {
    progressText = "complete";
    pct = 100;
  }

  statusProgress.textContent = progressText;
  progressFill.style.width = pct + "%";

  if (job.status === "done") {
    if (job.report_path) {
      downloadLink.href = `/report/${jobId}`;
      downloadLink.hidden = false;
    }
    if (job.message) {
      statusMessage.textContent = job.message;
    }
  }

  if (job.status === "error") {
    statusMessage.textContent = "Error: " + (job.error || "unknown error");
  }
}
