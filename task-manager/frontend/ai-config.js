// ===== AI CONFIGURATION =====
// This file used to hold your real Gemini API key directly - that was
// the security issue. Now it only holds the ADDRESS of your own proxy
// server, which is not a secret (same idea as API_URL in the other
// version of this project).
//
// While testing locally, leave this as localhost. Once you deploy
// ai-proxy/ (see README.md), change this to your deployed URL, e.g.
// "https://your-ai-proxy.onrender.com"

const AI_CONFIG = {
  PROXY_URL: "http://localhost:6000"
};
