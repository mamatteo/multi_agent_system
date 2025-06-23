# orchestration/orchestrator.py
from typing import Literal
from langgraph.graph import END
from state import AgentState

def orchestrator(state: AgentState) -> Literal["writer", "reviewer", "mailman", END]:
    print("\n ORCHESTRATORE - Decisione routing...")
    
    # Log dello stato per debugging
    print(f"Stato attuale:")
    print(f"- Bozza presente: {bool(state.get('letter_draft'))}")
    print(f"- Feedback presente: {bool(state.get('review_feedback'))}")
    print(f"- Approvata: {state.get('is_approved', False)}")
    print(f"- Iterazione: {state.get('iteration_count', 0)}")
    
    if not state.get("letter_draft"):
        print("Routing verso WRITER (prima stesura)")
        return "writer"
    elif not state.get("is_approved", False):
        if state.get("review_feedback"):
            print("Routing verso WRITER (revisione)")
            return "writer"
        else:
            print("Routing verso REVIEWER")
            return "reviewer"
    elif state.get("final_letter"):
        print("Routing verso MAILMAN")
        return "mailman"
    else:
        print("Processo completato")
        return END