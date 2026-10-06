# Interview Prep Agent

A focused Python buildathon prototype that acts as a personalized AI interview coach.

## Features
- Targets a specific role such as backend engineer
- Uses Mem0 to remember prior answers and candidate profile
- Generates tailored technical interview questions
- Evaluates candidate responses and provides actionable improvement feedback

## Setup
1. Create a virtual environment
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Add your API key
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and set your OpenAI API key.
4. Run the app
   ```bash
   python main.py
   ```

## Notes
- This prototype is designed for a 90-minute buildathon and keeps the workflow simple.
- Mem0 stores context across sessions so the coach becomes more personalized over time.

## Example use cases
- Backend engineer prep
- Frontend interviews
- Data engineer mock interviews
- System design practice
