# main.py
from orchestration.workflow import create_workflow

def main():
    print("Avvio Sistema Multi-Agente con Paradigma ReAct")
    print("="*50)
    
    app = create_workflow()
    
    initial_state = {
        "messages": [], 
        "letter_draft": "", 
        "review_feedback": "", 
        "iteration_count": 0, 
        "is_approved": False, 
        "final_letter": "",
        # Aggiunti per ReAct
        "current_reasoning": None,
        "action_history": []
    }
    
    config = {"configurable": {"thread_id": "loan_request_001"}}
    
    print("\n📝 Inizio elaborazione...")
    print("="*50)
    
    for event in app.stream(initial_state, config):
        for node, data in event.items():
            print(f"\n✨ Nodo completato: {node.upper()}")
            if "current_reasoning" in data and data["current_reasoning"]:
                print(f"Ultimo ragionamento: {data['current_reasoning'][:150]}...")
            if "messages" in data and data["messages"]:
                print(f"Output: {data['messages'][-1].content[:150]}...")
    
    print("\n" + "="*50)
    print("Processo completato con successo!")
    print("="*50)

if __name__ == "__main__":
    main()