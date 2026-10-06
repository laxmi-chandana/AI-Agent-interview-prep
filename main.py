import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

try:
    from mem0 import Memory
except Exception:  # pragma: no cover
    Memory = None

load_dotenv()


class FileMemoryStore:
    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, List[Dict[str, Any]]] = self._load()

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                raw = json.load(file)
            if isinstance(raw, dict):
                return raw
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    def _save(self) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=2)

    def _user_entries(self, user_id: str) -> List[Dict[str, Any]]:
        if user_id not in self.data:
            self.data[user_id] = []
        return self.data[user_id]

    def add(self, entries: List[Dict[str, Any]], user_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            content = entry.get("content") if isinstance(entry, dict) else str(entry)
            if not content:
                continue
            self._user_entries(user_id).append({
                "memory": str(content),
                "metadata": metadata or {},
            })
        self._save()

    def search(self, query: str, user_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_lower = (query or "").lower()
        matches = []
        for item in self._user_entries(user_id):
            memory_text = str(item.get("memory", ""))
            base = {
                "memory": memory_text,
                "metadata": item.get("metadata", {}),
            }
            if not query_lower:
                matches.append(base)
                continue
            score = 0
            if query_lower in memory_text.lower():
                score += 10
            for token in query_lower.split():
                if token in memory_text.lower():
                    score += 1
            if score > 0:
                matches.append({**base, "_score": score})
        matches.sort(key=lambda item: item.get("_score", 0), reverse=True)
        results = []
        for item in matches[:top_k]:
            result = {"memory": item["memory"], "metadata": item.get("metadata", {})}
            results.append(result)
        return results if results else [{"memory": "No prior memory yet.", "metadata": {}}]


class Mem0MemoryAdapter:
    def __init__(self, primary: Any, fallback: FileMemoryStore):
        self.primary = primary
        self.fallback = fallback

    def add(self, entries: List[Dict[str, Any]], user_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        try:
            self.primary.add(entries, user_id=user_id, metadata=metadata or {})
        except Exception as exc:  # pragma: no cover - fallback for broken vector store
            print(f"Mem0 add failed, using local file backup: {exc}")
            self.fallback.add(entries, user_id=user_id, metadata=metadata or {})

    def search(self, query: str, user_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            return self.primary.search(query, user_id=user_id, top_k=top_k)
        except Exception as exc:  # pragma: no cover - fallback for broken vector store
            print(f"Mem0 search failed, using local file backup: {exc}")
            return self.fallback.search(query, user_id=user_id, top_k=top_k)


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11437").rstrip("/")


def get_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.1:8b")


def get_embed_model() -> str:
    return os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def build_memory() -> Any:
    fallback = FileMemoryStore(os.path.join(os.getcwd(), "memory_store.json"))
    backend = os.getenv("MEMORY_BACKEND", "mem0").lower()
    if backend in {"file", "json", "local", "simple"}:
        return fallback
    if Memory is None:
        print("Mem0 is not installed; using local file memory instead.")
        return fallback

    base_url = get_ollama_base_url()
    config = {
        "llm": {
            "provider": "ollama",
            "config": {
                "model": get_model(),
                "ollama_base_url": base_url,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": get_embed_model(),
                "ollama_base_url": base_url,
            },
        },
        "history_db_path": os.path.join(os.getcwd(), ".mem0_history.db"),
        "custom_instructions": (
            "You are a focused technical interview coach for software engineering roles. "
            "Remember the candidate's strengths, weaknesses, target role, and previous answers "
            "so the coaching can be personalized over time."
        ),
    }
    try:
        return Mem0MemoryAdapter(Memory.from_config(config), fallback)
    except Exception as exc:
        print(f"Mem0 failed to initialize; using local file memory instead: {exc}")
        return fallback


class InterviewCoach:
    def __init__(self, user_id: str, target_role: str):
        self.user_id = user_id
        self.target_role = target_role
        self.memory = build_memory()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=f"{get_ollama_base_url()}/v1",
        )

    def remember(self, text: str, memory_type: str) -> None:
        self.memory.add(
            [{"role": "user", "content": text}],
            user_id=self.user_id,
            metadata={"type": memory_type, "role": self.target_role},
        )

    def get_context(self) -> str:
        memories = self.memory.search(
            f"{self.target_role} interview preparation, strengths, weaknesses, goals, previous feedback",
            user_id=self.user_id,
            top_k=5,
        )
        if not memories:
            return "No prior memory yet."
        context_parts = []
        for item in memories:
            memory_text = item.get("memory") if isinstance(item, dict) else str(item)
            if memory_text:
                context_parts.append(str(memory_text))
        return "\n".join(context_parts)

    def ask_question(self) -> str:
        context = self.get_context()
        prompt = (
            f"You are a senior engineer interviewing a candidate for {self.target_role}. "
            f"Generate one sharp but fair interview question. "
            f"Take into account this context from the candidate: {context}. "
            "Keep the question practical and focused on real engineering judgment."
        )
        response = self.client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()

    def evaluate_answer(self, question: str, answer: str) -> str:
        context = self.get_context()
        prompt = (
            f"You are a senior interviewer for {self.target_role}. "
            f"Question: {question}\n\nCandidate answer: {answer}\n\n"
            f"Candidate context: {context}\n\n"
            "Provide concise but useful feedback in 5 parts: "
            "1) what was good, 2) gaps, 3) what to improve, 4) a better answer outline, "
            "5) one follow-up question."
        )
        response = self.client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()


def interactive_session() -> None:
    print("=== Interview Prep Coach ===")
    user_id = input("Enter a candidate name or user ID: ").strip() or "candidate"
    role = input("Target interview role (default: backend engineer): ").strip() or "backend engineer"
    years = input("Years of experience (optional): ").strip()
    strengths = input("Top strengths or areas you want to improve (optional): ").strip()

    coach = InterviewCoach(user_id, role)

    if years:
        coach.remember(f"Candidate target role: {role}; experience: {years}", "profile")
    if strengths:
        coach.remember(f"Candidate notes: {strengths}", "profile")

    print(f"\nGreat. I will coach you for {role} interviews.\n")

    for round_number in range(1, 4):
        question = coach.ask_question()
        print(f"\nQuestion {round_number}:\n{question}\n")
        answer = input("Your answer: \n")
        coach.remember(f"Question: {question}\nAnswer: {answer}", "answer")
        feedback = coach.evaluate_answer(question, answer)
        print(f"\nFeedback:\n{feedback}\n")

        if round_number < 3:
            next_step = input("Press Enter to continue to the next interview question... ")

    print("\nSession complete. Your memory is saved so the next session can personalize questions further.")


if __name__ == "__main__":
    try:
        interactive_session()
    except Exception as exc:  # pragma: no cover
        print(f"\nUnexpected error: {exc}")
        print("1. Start Ollama locally: ollama serve")
        print("2. Pull a model: ollama pull llama3.1:8b")
        print("3. Optional: set OLLAMA_BASE_URL and OLLAMA_MODEL in .env")
        print("4. Run: python main.py")
