# agents/base_react_agent.py
from abc import ABC, abstractmethod
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import AgentState
import prompts

class BaseReActAgent(ABC):
    """Classe base per agenti che implementano il paradigma ReAct"""
    
    def __init__(self, name: str, llm):
        self.name = name
        self.llm = llm
    
    #Fase di ragionamento dell'agente
    def reason(self, state: AgentState) -> str:
        """Fase di ragionamento (Thought + Observation)"""
        
        print(f"\n {self.name} - Fase di ragionamento...")
        
        #L'agente ottiene il contesto su cui operare
        context = self.get_context(state)
        #Costruisce il prompt
        reasoning_prompt = f"{prompts.REACT_REASONING}\n\nCONTESTO ATTUALE:\n{context}"
        
        #Invia i messaggi al modello LLM
        messages = [
            SystemMessage(content=f"Sei l'agente {self.name}. Ragiona sul tuo prossimo passo."),
            HumanMessage(content=reasoning_prompt)
        ]
        
        response = self.llm.invoke(messages)
        reasoning = response.content
        
        print(f" Ragionamento: {reasoning[:200]}...")
        return reasoning
    
    @abstractmethod
    def get_context(self, state: AgentState) -> str:
        """Ottiene il contesto specifico per l'agente"""
        pass
    
    @abstractmethod
    def act(self, state: AgentState, reasoning: str) -> AgentState:
        """Esegue l'azione basata sul ragionamento"""
        pass
    
    def __call__(self, state: AgentState) -> AgentState:
        """Esegue il ciclo ReAct completo"""
        # Reason
        reasoning = self.reason(state)
        
        # Act
        new_state = self.act(state, reasoning)
        
        # Aggiorna history
        new_state["current_reasoning"] = reasoning
        new_state["action_history"] = [f"{self.name}: {reasoning[:100]}..."]
        
        return new_state