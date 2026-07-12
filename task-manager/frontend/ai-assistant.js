// ===== AI ASSISTANT MODULE =====
// All AI features (natural language task add, chat assistant, smart
// category/priority suggestions, weekly insights) go through this file.
//
// This now calls YOUR OWN proxy server (ai-proxy/) instead of Google's
// Gemini API directly. The real Gemini API key lives only on that
// server - this file and the app it's part of never see it, which is
// what keeps the key safe even if someone extracts/inspects the APK.

async function callAI(prompt, wantJSON){
  const res = await fetch(`${AI_CONFIG.PROXY_URL}/api/ai/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, wantJSON: !!wantJSON })
  });

  if(!res.ok){
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.message || `AI proxy request failed (${res.status})`);
  }

  const data = await res.json();
  const raw = data.result;

  if(!raw) throw new Error("AI returned an empty response");

  return wantJSON ? JSON.parse(raw) : raw;
}

function summarizeTasksForAI(taskList){
  if(!taskList.length) return "(no tasks yet)";
  return taskList.map(t =>
    `- [${t.completed ? "done" : "pending"}] ${t.text} (category: ${t.category}, priority: ${t.priority}, due: ${t.dueDate || "none"})`
  ).join("\n");
}

// ===== FEATURE: natural language task add + chat Q&A (combined) =====
async function aiProcessAssistantMessage(userText, currentTasks){
  const today = new Date().toISOString().split("T")[0];

  const prompt = `
You are a task management assistant inside a to-do list app. Today's date is ${today}.

The user's current tasks:
${summarizeTasksForAI(currentTasks)}

The user said: "${userText}"

Decide if the user wants to ADD one or more new tasks, or is ASKING a question / wants information.

Respond with ONLY valid JSON in exactly one of these two shapes:

Adding tasks:
{"action":"add_tasks","tasks":[{"text":"...","category":"Personal|Study|Work|Health","priority":"high|medium|low","dueDate":"YYYY-MM-DD or empty string"}]}

Answering a question:
{"action":"answer","message":"your helpful natural language answer"}

Rules:
- Infer category and priority sensibly from wording if not stated explicitly.
- Convert relative dates ("friday", "tomorrow", "next monday") into real YYYY-MM-DD dates based on today's date.
- If no date is mentioned for a new task, use an empty string.
- Keep "message" concise and friendly, plain text, no markdown.
`;

  return await callAI(prompt, true);
}

// ===== FEATURE: smart category + priority suggestion =====
async function aiSuggestCategoryPriority(taskText){
  const prompt = `
Task: "${taskText}"
Suggest the best-fitting category and priority for this task.
Respond with ONLY valid JSON: {"category":"Personal|Study|Work|Health","priority":"high|medium|low"}
`;
  return await callAI(prompt, true);
}

// ===== FEATURE: AI weekly insights/summary =====
async function aiGenerateWeeklySummary(taskList){
  const today = new Date().toISOString().split("T")[0];

  const prompt = `
Today's date is ${today}. Here is the user's full task list:
${summarizeTasksForAI(taskList)}

Write a short, friendly productivity summary in 4-6 sentences. Mention:
how many tasks are completed vs pending, which category they're focusing
on most, any overdue tasks (due date before today and not completed),
and end with one encouraging, specific tip. Plain text only, no markdown.
`;
  return await callAI(prompt, false);
}
