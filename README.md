# Interview Coach Agent

An AI-powered interview preparation assistant for technical roles. It simulates realistic interview rounds, adapts to the user's profile, and gives feedback on technical responses in a focused, role-specific way.

## Why this project matters
Candidates often prepare for interviews by memorizing generic questions, but they struggle with:
- role-specific questioning
- personalized follow-up based on weak areas
- realistic feedback after answering
- continuous improvement across multiple sessions

This agent solves that by combining:
- local LLM inference via Ollama
- persistent memory across sessions
- role-aware question generation
- answer evaluation and coaching feedback

## Core value proposition
"Practice like a real interviewer, but personalized to your background and target role."

Examples:
- backend engineer interview prep
- frontend engineer interviews
- system design coaching
- candidate profile tracking over time

## Features
- Role-based interview question generation
- Personalized memory across sessions
- Candidate profile tracking (years of experience, strengths, gaps)
- Real-time answer evaluation with improvement guidance
- Local-first setup to reduce cost and privacy concerns
- Compatible with Ollama for zero-token local inference

## Technical overview
The agent includes:
- Python app in `main.py`
- local model usage via Ollama
- optional memory via Mem0
- file-backed fallback memory to prevent vector mismatch issues
- environment-based configuration via `.env`

## Architecture

1. User enters their profile
   - name or user ID
   - target role
   - years of experience
   - strengths or areas to improve

2. The app builds candidate memory
   - saved as session memory or local JSON fallback

3. The LLM generates a realistic interview question
   - tailored based on the target role and previous feedback

4. The user answers
   - answer is stored as a historical memory

5. The model evaluates the answer
   - good points
   - gaps
   - improvement suggestions
   - stronger answer outline
   - follow-up question

## Quick start

### 1. Create the virtual environment
```bash
cd /Users/laxmichandana/Desktop/Code/interview-agent
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Ollama locally
```bash
ollama serve
```

If needed, pull the models:
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 4. Configure environment
```bash
cp .env.example .env
```

Example configuration:
```env
OLLAMA_BASE_URL=http://localhost:11437
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBED_MODEL=nomic-embed-text
OPENAI_API_KEY=ollama
MEMORY_BACKEND=file
```

### 5. Run the app
```bash
python main.py
```

## Demo flow
A typical buildathon demo can be:

1. Enter candidate ID: `demo-user`
2. Enter target role: `backend engineer`
3. Enter experience: `4 years`
4. Enter strengths: `API design, debugging, DB optimization`
5. Agent asks a practical system design or coding question
6. User gives a sample answer
7. Agent returns structured feedback
8. Agent remembers the history for future sessions

## Why this is useful for a buildathon
This project is easy to explain and demo in under 5 minutes:
- it solves a real problem
- it is persuasive to users
- it feels like a real coaching product
- it can run locally without paid LLM APIs
- it shows personalization and memory

## Memory model
This project supports two memory modes:

- `MEMORY_BACKEND=mem0` for vector-based memory
- `MEMORY_BACKEND=file` for a simpler local fallback

The file-based mode is recommended during buildathon use because it avoids stale embedding mismatch errors caused by older persisted vector data.

## Troubleshooting

### Mem0 vector mismatch error
If you see an error similar to:
```text
shapes (0,1536) and (768,) not aligned
```
that means old vector memory is being reused with a new embedder model.

Fix:
```bash
rm -rf /tmp/qdrant
rm -f ~/.mem0/history.db
rm -rf ~/.mem0
```

Or simply use the file-based backup mode:
```env
MEMORY_BACKEND=file
```

### Ollama server not running
```bash
ollama serve
```

### Port not listening
Check your configured URL:
```env
OLLAMA_BASE_URL=http://localhost:11437
```

## Project files
- `main.py` — core interview coaching logic
- `.env.example` — environment template
- `requirements.txt` — dependencies
- `memory_store.json` — local fallback memory store
- `test_memory_backend.py` — regression tests for fallback memory

## Future enhancements
- multiple interview rounds with adaptive difficulty
- coding challenge mode
- resume-based personalization
- analytics dashboard for skill gaps
- browser UI for better demo experience
- integration with a real interview grading rubric

## License
This project is intended for hackathon use and learning purposes.

## Hackathon summary
This agent is a strong buildathon MVP because it demonstrates:
- AI personalization
- memory across sessions
- practical end-user value
- low-cost local deployment
- easy storytelling for judges

