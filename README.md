<!--
Change log (created 2026-06-30 12:23 KST):
- Created this submission README for the GitHub upload folder.
- Summarized the OpenRouter-backed Pixel Agents implementation.
- Added run commands for Pixel Agents local-agent mode and the Python multi-agent workflow.
- Added a clear note that API keys such as Agent/Key.txt must not be committed.
-->

# Pixel Agents OpenRouter Multi-Agent Submission

이 폴더는 과제 제출용 GitHub 업로드 파일 모음입니다.

## 구현 요약

- Claude CLI hook만 바라보던 Pixel Agents에 `local-agent` provider를 추가했습니다.
- Python workflow가 Pixel Agents HTTP hook API로 직접 이벤트를 보내도록 연결했습니다.
- OpenRouter Chat Completions API를 사용해 민원 답변 초안을 생성할 수 있게 했습니다.
- 민원 처리 workflow를 다음 4개 역할 agent로 분리했습니다.
  - `ClassificationAgent`
  - `SearchAgent`
  - `DraftAgent`
  - `ReviewAgent`
- workflow 완료 시 Pixel Agents 화면의 캐릭터가 자동 제거되도록 `SessionEnd(completed)`를 처리합니다.

## 폴더 구성

- `pixel-agents/`: Pixel Agents 수정본
- `Agent/`: OpenRouter 기반 Python multi-agent workflow 및 웹 실행 UI

## 실행 방법

### 1. Pixel Agents 실행

```powershell
cd .\pixel-agents
npm install
npm run build:extension
node dist\cli.js --provider local-agent --port 3210
```

브라우저에서 다음 주소를 엽니다.

```text
http://127.0.0.1:3210
```

### 2. OpenRouter API key 준비

`Agent` 폴더 안에 `Key.txt` 파일을 만들고 OpenRouter API key를 넣습니다.

주의: `Key.txt`는 GitHub에 올리면 안 됩니다.

### 3. Python workflow 실행

```powershell
cd .\Agent
pip install openpyxl
python multi_agent_complaint_practice.py --limit 1 --use-llm --model phi --pixel-agents
```

### 4. 웹 UI 실행

```powershell
cd .\Agent
python web_app.py
```

브라우저에서 다음 주소를 엽니다.

```text
http://127.0.0.1:8004
```

## GitHub 업로드 예시

```powershell
cd D:\AI_Champion\6차수과제2\제출
git init
git add .
git commit -m "Add OpenRouter local-agent Pixel Agents submission"
git branch -M main
git remote add origin https://github.com/<your-id>/<your-repo>.git
git push -u origin main
```

GitHub repository는 public으로 생성한 뒤 제출 주소에 해당 repository URL을 입력하면 됩니다.
