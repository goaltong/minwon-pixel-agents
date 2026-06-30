# Change log (created 2026-06-26):
# - Updated 2026-06-30 12:07 KST:
#   * Saved a backup before editing at OLD/web_app_Ver.2606301207.py.
#   * Added a Pixel Agents reporting toggle to the browser workflow payload.
#   * Wired web-triggered workflow runs to PixelAgentsReporter so the same
#     OpenRouter/local-agent stages can appear as Pixel Agents characters when a
#     Pixel Agents server is running with the local-agent provider.
# - Updated 2026-06-26 15:02 KST:
#   * Saved a backup before editing at OLD/web_app_Ver.2606261502.py.
#   * Changed the bind host from 127.0.0.1 to 0.0.0.0 so the web app can accept
#     connections from other devices on reachable network interfaces.
# - Updated 2026-06-26 15:00 KST:
#   * Saved a backup before editing at OLD/web_app_Ver.2606261500.py.
#   * Changed the local web server port from 8765 to 8004 as requested.
# - Updated 2026-06-26 14:55 KST:
#   * Saved a backup before editing at OLD/web_app_Ver.2606261455.py.
#   * Localized the visible web UI from English to Korean, including the workflow
#     subtitle, form labels, run button, status messages, result metadata, and output
#     links.
#   * Kept server console messages in English to follow the project instruction that
#     console outputs stay English.
# - Updated 2026-06-26 14:52 KST:
#   * Saved a backup before editing at OLD/web_app_Ver.2606261452.py.
#   * Added visual workflow progress states for the four agent stages.
#   * Added a blinking animation for the currently active stage while a run request
#     is in progress.
#   * Added front-end progress timer logic that cycles through classify, search,
#     draft, and review while the backend request is running, then marks every stage
#     complete when results arrive.
# - Updated 2026-06-26 14:53 KST:
#   * Saved a backup before editing at OLD/web_app_Ver.2606261453.py.
#   * Added a minimum visible progress duration so the blinking stage indicator is
#     observable even when local-template mode finishes almost instantly.
# - Added a local browser-based practice UI for the complaint multi-agent workflow.
# - Reuses the existing multi_agent_complaint_practice.py agents instead of duplicating
#   the classification, search, draft, and review logic.
# - Provides controls for input workbook path, processing limit, draft mode, model,
#   API key file, and API base URL.
# - Runs entirely on localhost with Python standard-library HTTP serving; no web
#   framework, package install, or frontend build step is required.
# - Keeps API key contents server-side only and never returns the key to the browser.
# - Writes generated CSV/Markdown outputs to the existing outputs directory.

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from multi_agent_complaint_practice import (
    AVAILABLE_MODELS,
    DEFAULT_API_BASE_URL,
    DEFAULT_API_KEY_FILE,
    DEFAULT_INPUT,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    ChatClient,
    PixelAgentsReporter,
    read_api_key,
    read_complaints,
    resolve_model,
    run_pipeline,
    write_csv,
    write_markdown,
)


HOST = "0.0.0.0"
PORT = 8004


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>민원 Multi-Agent 실습</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f4ee;
      --panel: #ffffff;
      --ink: #181512;
      --muted: #6f665c;
      --line: #ded5c8;
      --accent: #b76031;
      --accent-strong: #8f421f;
      --ok: #237044;
      --warn: #9b5a00;
      --bad: #9e2f2f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, "Malgun Gothic", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      background: #17120e;
      color: white;
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }
    header h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
    }
    header span {
      color: #d8cabe;
      font-size: 13px;
    }
    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }
    .workflow {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .step {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-height: 96px;
      box-shadow: 0 1px 3px rgba(40, 30, 20, 0.08);
      transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
    }
    .step.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(183, 96, 49, 0.18), 0 4px 14px rgba(80, 45, 25, 0.14);
      animation: stageBlink 0.8s ease-in-out infinite;
    }
    .step.done {
      border-color: #9fd1b4;
      background: #f4fbf6;
    }
    .step.done .badge {
      background: var(--ok);
    }
    .step.active .badge {
      background: var(--accent-strong);
    }
    @keyframes stageBlink {
      0%, 100% { transform: translateY(0); opacity: 1; }
      50% { transform: translateY(-2px); opacity: 0.68; }
    }
    .badge {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: var(--accent);
      color: white;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .step strong { display: block; font-size: 16px; }
    .step small { color: var(--muted); }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 18px;
    }
    form {
      display: grid;
      grid-template-columns: 1.7fr 0.5fr 0.8fr 1fr;
      gap: 12px;
      align-items: end;
    }
    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }
    input, select {
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 14px;
      color: var(--ink);
      background: white;
    }
    .mode {
      display: flex;
      gap: 10px;
      align-items: center;
      min-height: 38px;
    }
    .mode label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
      color: var(--ink);
    }
    .mode input { width: auto; min-height: auto; }
    button {
      min-height: 38px;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: white;
      font-weight: 700;
      cursor: pointer;
      padding: 8px 14px;
    }
    button:hover { background: var(--accent-strong); }
    button:disabled { opacity: 0.6; cursor: wait; }
    .status {
      margin-top: 12px;
      font-size: 14px;
      color: var(--muted);
    }
    .status.ok { color: var(--ok); }
    .status.bad { color: var(--bad); }
    .results {
      display: grid;
      gap: 12px;
    }
    .result {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fffdf9;
    }
    .result h3 {
      margin: 0 0 8px;
      font-size: 16px;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }
    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 12px;
      background: white;
      color: var(--muted);
    }
    .pill.pass { color: var(--ok); border-color: #9fd1b4; }
    .pill.warn { color: var(--warn); border-color: #e5c17d; }
    pre {
      margin: 0;
      padding: 12px;
      background: #f3eee7;
      border-radius: 6px;
      white-space: pre-wrap;
      line-height: 1.45;
      font-size: 13px;
      max-height: 280px;
      overflow: auto;
    }
    .links {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 10px;
    }
    .links a {
      color: var(--accent-strong);
      font-weight: 700;
      text-decoration: none;
    }
    @media (max-width: 900px) {
      .workflow, form { grid-template-columns: 1fr; }
      main { padding: 16px; }
      header { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <header>
    <h1>민원 초안 생성 Multi Agent</h1>
    <span>분류 -> 검색 -> 작성 -> 검수 -> 사람 확인</span>
  </header>
  <main>
    <section class="workflow" aria-label="workflow">
      <div class="step" data-stage="0"><div class="badge">1</div><strong>분류</strong><small>민원 유형과 담당 영역 판단</small></div>
      <div class="step" data-stage="1"><div class="badge">2</div><strong>검색</strong><small>관련 법령/근거 후보 매칭</small></div>
      <div class="step" data-stage="2"><div class="badge">3</div><strong>작성</strong><small>근거 기반 답변 초안 생성</small></div>
      <div class="step" data-stage="3"><div class="badge">4</div><strong>검수</strong><small>필수 항목과 근거 포함 여부 확인</small></div>
    </section>

    <section class="panel">
      <form id="runForm">
        <label>엑셀 파일
          <input name="input" value="1782341096215_file (2).xlsx">
        </label>
        <label>처리 건수
          <input name="limit" type="number" min="1" max="999" value="1">
        </label>
        <label>실행 방식
          <div class="mode">
            <label><input type="radio" name="mode" value="local" checked> 로컬</label>
            <label><input type="radio" name="mode" value="llm"> LLM</label>
          </div>
        </label>
        <label>모델
          <select name="model" id="modelSelect"></select>
        </label>
        <label>API 키 파일
          <input name="apiKeyFile" value="Key.txt">
        </label>
        <label>API 주소
          <input name="apiBaseUrl" value="https://openrouter.ai/api/v1">
        </label>
        <label>Pixel Agents
          <div class="mode">
            <label><input type="checkbox" name="pixelAgents" checked> 연동</label>
          </div>
        </label>
        <button id="runButton" type="submit">실행</button>
      </form>
      <div id="status" class="status">대기 중입니다.</div>
      <div id="links" class="links"></div>
    </section>

    <section class="panel">
      <div id="results" class="results"></div>
    </section>
  </main>
  <script>
    const modelSelect = document.querySelector("#modelSelect");
    const statusEl = document.querySelector("#status");
    const resultsEl = document.querySelector("#results");
    const linksEl = document.querySelector("#links");
    const runButton = document.querySelector("#runButton");
    const stageEls = [...document.querySelectorAll(".step[data-stage]")];
    let progressTimer = null;
    let activeStage = 0;

    async function loadModels() {
      const response = await fetch("/api/models");
      const data = await response.json();
      modelSelect.innerHTML = "";
      for (const item of data.models) {
        const option = document.createElement("option");
        option.value = item.alias;
        option.textContent = `${item.alias} - ${item.model}`;
        if (item.default) option.selected = true;
        modelSelect.appendChild(option);
      }
    }

    function renderResults(results) {
      resultsEl.innerHTML = "";
      for (const item of results) {
        const node = document.createElement("article");
        node.className = "result";
        const reviewClass = item.review_status === "Pass" ? "pass" : "warn";
        node.innerHTML = `
          <h3>${escapeHtml(item.complaint_id)} - ${escapeHtml(item.title)}</h3>
          <div class="meta">
            <span class="pill">${escapeHtml(item.department)}</span>
            <span class="pill">${escapeHtml(item.complaint_type)}</span>
            <span class="pill">신뢰도 ${escapeHtml(String(item.confidence))}</span>
            <span class="pill ${reviewClass}">${escapeHtml(item.review_status)}</span>
          </div>
          <pre>${escapeHtml(item.draft_response)}</pre>
        `;
        resultsEl.appendChild(node);
      }
    }

    function escapeHtml(value) {
      return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function setStageState(index, running) {
      stageEls.forEach((stage, stageIndex) => {
        stage.classList.toggle("done", running && stageIndex < index);
        stage.classList.toggle("active", running && stageIndex === index);
      });
    }

    function startProgressBlink() {
      stopProgressBlink(false);
      activeStage = 0;
      setStageState(activeStage, true);
      progressTimer = window.setInterval(() => {
        activeStage = Math.min(activeStage + 1, stageEls.length - 1);
        setStageState(activeStage, true);
      }, 900);
    }

    function stopProgressBlink(markDone) {
      if (progressTimer) {
        window.clearInterval(progressTimer);
        progressTimer = null;
      }
      stageEls.forEach((stage) => {
        stage.classList.remove("active", "done");
        if (markDone) stage.classList.add("done");
      });
    }

    function delay(ms) {
      return new Promise((resolve) => window.setTimeout(resolve, ms));
    }

    document.querySelector("#runForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const payload = {
        input: form.get("input"),
        limit: Number(form.get("limit")),
        useLlm: form.get("mode") === "llm",
        model: form.get("model"),
        apiKeyFile: form.get("apiKeyFile"),
        apiBaseUrl: form.get("apiBaseUrl"),
        pixelAgents: form.get("pixelAgents") === "on"
      };
      runButton.disabled = true;
      linksEl.innerHTML = "";
      resultsEl.innerHTML = "";
      statusEl.className = "status";
      statusEl.textContent = "민원 처리 흐름을 실행 중입니다...";
      startProgressBlink();
      try {
        const minimumProgress = delay(2200);
        const response = await fetch("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        await minimumProgress;
        if (!response.ok) throw new Error(data.error || "요청 처리에 실패했습니다.");
        statusEl.className = "status ok";
        statusEl.textContent = `완료되었습니다. 처리 건수: ${data.processed}. 실행 방식: ${data.mode}.`;
        stopProgressBlink(true);
        linksEl.innerHTML = `
          <a href="/outputs/complaint_multi_agent_results.md" target="_blank">Markdown 결과 열기</a>
          <a href="/outputs/complaint_multi_agent_results.csv" target="_blank">CSV 결과 열기</a>
        `;
        renderResults(data.results);
      } catch (error) {
        stopProgressBlink(false);
        statusEl.className = "status bad";
        statusEl.textContent = error.message;
      } finally {
        runButton.disabled = false;
      }
    });

    loadModels().catch((error) => {
      statusEl.className = "status bad";
      statusEl.textContent = error.message;
    });
  </script>
</body>
</html>
"""


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_text(INDEX_HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/models":
            models = [
                {
                    "alias": alias,
                    "model": model,
                    "default": model == DEFAULT_MODEL,
                }
                for alias, model in AVAILABLE_MODELS.items()
            ]
            self.send_json({"models": models})
            return
        if parsed.path.startswith("/outputs/"):
            self.serve_output(parsed.path.removeprefix("/outputs/"))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            payload = self.read_json()
            result = self.run_workflow(payload)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        self.send_json(result)

    def run_workflow(self, payload: dict) -> dict:
        input_path = Path(str(payload.get("input") or DEFAULT_INPUT))
        limit = int(payload.get("limit") or 1)
        use_llm = bool(payload.get("useLlm"))
        model = resolve_model(str(payload.get("model") or DEFAULT_MODEL))
        api_key_file = Path(str(payload.get("apiKeyFile") or DEFAULT_API_KEY_FILE))
        api_base_url = str(payload.get("apiBaseUrl") or DEFAULT_API_BASE_URL)
        pixel_agents_enabled = bool(payload.get("pixelAgents"))

        chat_client = None
        if use_llm:
            api_key = read_api_key(api_key_file)
            chat_client = ChatClient(api_key=api_key, model=model, api_base_url=api_base_url)

        complaints = read_complaints(input_path, limit)
        reporter = PixelAgentsReporter(
            enabled=pixel_agents_enabled,
            provider_id="local-agent",
            cwd=Path.cwd(),
        )
        results = run_pipeline(complaints, chat_client=chat_client, pixel_agents=reporter)
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        write_csv(results, DEFAULT_OUTPUT_DIR / "complaint_multi_agent_results.csv")
        write_markdown(results, DEFAULT_OUTPUT_DIR / "complaint_multi_agent_results.md")

        return {
            "processed": len(results),
            "mode": "LLM" if use_llm else "로컬 템플릿",
            "model": model if use_llm else "사용 안 함",
            "results": [result.__dict__ for result in results],
        }

    def serve_output(self, filename: str) -> None:
        safe_name = Path(filename).name
        path = DEFAULT_OUTPUT_DIR / safe_name
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Output not found")
            return
        content_type = "text/plain; charset=utf-8"
        if path.suffix.lower() == ".csv":
            content_type = "text/csv; charset=utf-8"
        elif path.suffix.lower() == ".md":
            content_type = "text/markdown; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, body: str, content_type: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), format % args))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Web app running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
