# agents/mailman.py
from datetime import datetime
from langchain_core.messages import AIMessage
from state import AgentState

#In input passiamo tutto lo stato (state) contenente le informazioni accumulate nel sistema
def mailman_agent(state: AgentState, llm=None) -> AgentState:
    print("\n AGENTE POSTINO attivato...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lettera_finanziamento_{timestamp}.txt"
    
    # Includi lo storico del ragionamento nel documento finale
    action_history_text = "\n".join(state.get("action_history", []))
    
    content = f"""
=====================================
LETTERA DI RICHIESTA FINANZIAMENTO
=====================================
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
Destinatario: direzione@banca.it
Oggetto: Richiesta di Finanziamento

{state['final_letter']}

=====================================
PROCESSO DI REVISIONE (PARADIGMA ReAct)
=====================================
Numero di iterazioni: {state['iteration_count']}

STORICO RAGIONAMENTI:
{action_history_text}

ULTIMO FEEDBACK DEL REVISORE:
{state['review_feedback']}
=====================================
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f" Lettera salvata in: {filename}")
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=f"Lettera inviata e salvata in {filename}")],
        "action_history": state.get("action_history", []) + [f"MAILMAN: Documento salvato in {filename}"]
    }