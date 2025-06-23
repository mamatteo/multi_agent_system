# prompts/__init__.py
from pathlib import Path

def load_prompt(filename: str) -> str:
    """Carica un prompt dal file"""
    prompt_path = Path(__file__).parent / filename
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

# Carica tutti i prompt
WRITER_SYSTEM = load_prompt("writer_system.txt")
WRITER_INITIAL = load_prompt("writer_initial.txt")
WRITER_REVISION = load_prompt("writer_revision.txt")
REVIEWER_SYSTEM = load_prompt("reviewer_system.txt")
REVIEWER_PROMPT = load_prompt("reviewer_prompt.txt")

# Prompt ReAct
REACT_REASONING = load_prompt("react_reasoning.txt")