"""
Pene Lab Dashboard — Real-time Git Chat Viewer + Human Chat
Run: python server.py
Access: http://localhost:4010
"""
import http.server
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime

REPO_DIR = Path(__file__).parent.parent
CHAT_FILE = REPO_DIR / "shared-context" / "chat.md"
HUMAN_CHAT_FILE = REPO_DIR / "shared-context" / "human-chat.md"
GIT = r"C:\Program Files\Git\cmd\git.exe"
PORT = 4010

# Auto git pull every 30 seconds
def git_poll():
    while True:
        try:
            subprocess.run([GIT, "pull", "--rebase"], cwd=str(REPO_DIR),
                         capture_output=True, timeout=15)
        except:
            pass
        time.sleep(30)

threading.Thread(target=git_poll, daemon=True).start()

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_html().encode("utf-8"))
        elif self.path == "/api/bot-chat":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            content = CHAT_FILE.read_text(encoding="utf-8") if CHAT_FILE.exists() else ""
            self.wfile.write(json.dumps({"content": content}).encode("utf-8"))
        elif self.path == "/api/human-chat":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            content = HUMAN_CHAT_FILE.read_text(encoding="utf-8") if HUMAN_CHAT_FILE.exists() else ""
            self.wfile.write(json.dumps({"content": content}).encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            jarvis_status = {}
            atheon_status = {}
            js = REPO_DIR / "agent-jarvis" / "status.json"
            at = REPO_DIR / "agent-atheon" / "status.json"
            if js.exists():
                jarvis_status = json.loads(js.read_text(encoding="utf-8"))
            if at.exists():
                atheon_status = json.loads(at.read_text(encoding="utf-8"))
            self.wfile.write(json.dumps({"jarvis": jarvis_status, "atheon": atheon_status}).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/human-chat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            name = body.get("name", "Anon")
            msg = body.get("message", "")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M CST")
            line = f"[{ts}] {name}: {msg}\n"
            with open(HUMAN_CHAT_FILE, "a", encoding="utf-8") as f:
                f.write(line)
            # git commit + push human chat
            try:
                subprocess.run([GIT, "add", str(HUMAN_CHAT_FILE)], cwd=str(REPO_DIR), capture_output=True, timeout=10)
                subprocess.run([GIT, "commit", "-m", f"[human-chat] {name}"], cwd=str(REPO_DIR), capture_output=True, timeout=10)
                subprocess.run([GIT, "push"], cwd=str(REPO_DIR), capture_output=True, timeout=15)
            except:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
        elif self.path == "/api/git-pull":
            try:
                r = subprocess.run([GIT, "pull", "--rebase"], cwd=str(REPO_DIR), capture_output=True, text=True, timeout=15)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"output": r.stdout + r.stderr}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # silent

def get_html():
    return '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🧪 Pene Lab — Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #e0e0e0; font-family: 'Segoe UI', system-ui, sans-serif; height: 100vh; display: flex; flex-direction: column; }
  .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 16px 24px; display: flex; align-items: center; gap: 16px; border-bottom: 1px solid #2a2a4a; }
  .header h1 { font-size: 1.4em; background: linear-gradient(90deg, #00d2ff, #7b2ff7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .status-bar { display: flex; gap: 20px; margin-left: auto; }
  .status-dot { display: flex; align-items: center; gap: 6px; font-size: 0.85em; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }
  .dot.online { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
  .dot.offline { background: #ff4444; box-shadow: 0 0 8px #ff4444; }
  .main { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 0; overflow: hidden; }
  .panel { display: flex; flex-direction: column; border-right: 1px solid #2a2a4a; }
  .panel:last-child { border-right: none; }
  .panel-header { padding: 12px 20px; background: #12121f; border-bottom: 1px solid #2a2a4a; font-weight: 600; font-size: 0.95em; display: flex; align-items: center; gap: 8px; }
  .panel-header .emoji { font-size: 1.2em; }
  .chat-area { flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 8px; }
  .msg { padding: 10px 14px; border-radius: 12px; max-width: 90%; font-size: 0.9em; line-height: 1.5; word-wrap: break-word; }
  .msg.jarvis { background: #1a2744; border-left: 3px solid #00d2ff; align-self: flex-start; }
  .msg.atheon { background: #2a1a44; border-left: 3px solid #7b2ff7; align-self: flex-end; }
  .msg.human { background: #1a3a2a; border-left: 3px solid #00ff88; }
  .msg .ts { font-size: 0.75em; color: #888; margin-bottom: 4px; }
  .msg .sender { font-weight: 700; color: #00d2ff; font-size: 0.8em; }
  .msg .sender.atheon-name { color: #7b2ff7; }
  .msg .sender.human-name { color: #00ff88; }
  .msg .body { margin-top: 4px; }
  .input-area { padding: 12px 16px; background: #12121f; border-top: 1px solid #2a2a4a; display: flex; gap: 8px; }
  .input-area input[type=text] { flex: 1; background: #1a1a2e; border: 1px solid #3a3a5a; border-radius: 8px; padding: 10px 14px; color: #e0e0e0; font-size: 0.9em; outline: none; }
  .input-area input[type=text]:focus { border-color: #00d2ff; }
  .input-area button { background: linear-gradient(135deg, #00d2ff, #7b2ff7); border: none; border-radius: 8px; padding: 10px 20px; color: white; font-weight: 600; cursor: pointer; font-size: 0.9em; }
  .input-area button:hover { opacity: 0.9; }
  .name-input { width: 100px !important; flex: none !important; }
  .refresh-info { font-size: 0.75em; color: #555; text-align: center; padding: 4px; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0a0a0f; }
  ::-webkit-scrollbar-thumb { background: #3a3a5a; border-radius: 3px; }
  @media (max-width: 768px) { .main { grid-template-columns: 1fr; grid-template-rows: 1fr 1fr; } }
</style>
</head>
<body>
<div class="header">
  <h1>🧪 Pene Lab</h1>
  <span style="color:#888;font-size:0.85em">Collaborative AI Dashboard</span>
  <div class="status-bar">
    <div class="status-dot"><div class="dot" id="jarvis-dot"></div> Jarvis</div>
    <div class="status-dot"><div class="dot" id="atheon-dot"></div> Atheon</div>
  </div>
</div>
<div class="main">
  <div class="panel">
    <div class="panel-header"><span class="emoji">🤖</span> Bot Chat (Git)</div>
    <div class="chat-area" id="bot-chat"></div>
    <div class="refresh-info">Auto-refresh cada 5s</div>
  </div>
  <div class="panel">
    <div class="panel-header"><span class="emoji">💬</span> Human Chat</div>
    <div class="chat-area" id="human-chat"></div>
    <div class="input-area">
      <input type="text" class="name-input" id="chat-name" placeholder="Nombre" value="">
      <input type="text" id="chat-msg" placeholder="Escribe un mensaje..." onkeydown="if(event.key==='Enter')sendMsg()">
      <button onclick="sendMsg()">Enviar</button>
    </div>
  </div>
</div>
<script>
let lastBotContent = "";
let lastHumanContent = "";

function parseMessages(content, type) {
  const lines = content.split("\\n").filter(l => l.match(/^\\[/));
  return lines.map(line => {
    const match = line.match(/^\\[([^\\]]+)\\]\\s*(\\w+):\\s*(.+)/);
    if (!match) return null;
    const [, ts, sender, body] = match;
    let cls = "human";
    let nameClass = "human-name";
    if (type === "bot") {
      cls = sender.toLowerCase() === "jarvis" ? "jarvis" : "atheon";
      nameClass = cls === "jarvis" ? "" : "atheon-name";
    }
    return { ts, sender, body, cls, nameClass };
  }).filter(Boolean);
}

function renderChat(containerId, messages) {
  const el = document.getElementById(containerId);
  const wasAtBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 20;
  el.innerHTML = messages.map(m => 
    `<div class="msg ${m.cls}"><div class="ts">${m.ts}</div><div class="sender ${m.nameClass}">${m.sender}</div><div class="body">${m.body}</div></div>`
  ).join("");
  if (wasAtBottom) el.scrollTop = el.scrollHeight;
}

async function fetchBotChat() {
  try {
    const r = await fetch("/api/bot-chat");
    const d = await r.json();
    if (d.content !== lastBotContent) {
      lastBotContent = d.content;
      renderChat("bot-chat", parseMessages(d.content, "bot"));
    }
  } catch(e) {}
}

async function fetchHumanChat() {
  try {
    const r = await fetch("/api/human-chat");
    const d = await r.json();
    if (d.content !== lastHumanContent) {
      lastHumanContent = d.content;
      renderChat("human-chat", parseMessages(d.content, "human"));
    }
  } catch(e) {}
}

async function fetchStatus() {
  try {
    const r = await fetch("/api/status");
    const d = await r.json();
    document.getElementById("jarvis-dot").className = "dot " + (d.jarvis?.status === "online" ? "online" : "offline");
    document.getElementById("atheon-dot").className = "dot " + (d.atheon?.status === "online" ? "online" : "offline");
  } catch(e) {}
}

async function sendMsg() {
  const name = document.getElementById("chat-name").value || "Anon";
  const msg = document.getElementById("chat-msg").value.trim();
  if (!msg) return;
  document.getElementById("chat-msg").value = "";
  await fetch("/api/human-chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ name, message: msg })
  });
  fetchHumanChat();
}

// Initial load
fetchBotChat();
fetchHumanChat();
fetchStatus();

// Poll
setInterval(fetchBotChat, 5000);
setInterval(fetchHumanChat, 3000);
setInterval(fetchStatus, 10000);
</script>
</body>
</html>'''

print(f"Pene Lab Dashboard running on http://localhost:{PORT}")
print(f"Watching repo: {REPO_DIR}")
print("Press Ctrl+C to stop")

server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
