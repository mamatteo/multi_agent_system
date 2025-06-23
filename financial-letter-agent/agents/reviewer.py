# agents/reviewer.py
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState
from agents.base_react_agent import BaseReActAgent
import prompts

#Estendiamo la classe BaseReActAgent con la classe ReviewerAgent, inizializziamo l'agente e lo dotiamo di LLM
class ReviewerAgent(BaseReActAgent):
    def __init__(self, llm):
        super().__init__("REVIEWER", llm)
    
    def get_context(self, state: AgentState) -> str:
        """Ottiene il contesto per il reviewer"""
        context = f"Iterazione: {state.get('iteration_count', 0)}\n"
        context += f"Lettera da revisionare: {state['letter_draft'][:300]}..."
        
        if state.get("action_history"):
            context += f"\nStorico azioni: {len(state['action_history'])} azioni precedenti"
            
        return context
    
    def act(self, state: AgentState, reasoning: str) -> AgentState:
        """Revisiona la lettera basandosi sul ragionamento"""
        print("\n AGENTE REVISORE - Fase di azione...")
        
        user_prompt = prompts.REVIEWER_PROMPT.format(letter_draft=state['letter_draft'])
        
        # Aggiungi il ragionamento al prompt
        enhanced_prompt = f"RAGIONAMENTO CRITICO:\n{reasoning}\n\nREVISIONE RICHIESTA:\n{user_prompt}"
        
        messages = [
            SystemMessage(content=prompts.REVIEWER_SYSTEM),
            HumanMessage(content=enhanced_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        is_approved = "APPROVATA" in response.content.upper()
        if state.get("iteration_count", 0) >= 3:
            is_approved = True
            print(" Limite iterazioni raggiunto - approvazione forzata")
        
        return {
            **state,
            "messages": state["messages"] + [response],
            "review_feedback": response.content,
            "is_approved": is_approved,
            "final_letter": state['letter_draft'] if is_approved else ""
        }

def reviewer_agent(state: AgentState, llm) -> AgentState:
    agent = ReviewerAgent(llm)
    return agent(state)