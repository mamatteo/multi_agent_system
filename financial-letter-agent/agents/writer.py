# agents/writer.py
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState
from agents.base_react_agent import BaseReActAgent
import prompts

class WriterAgent(BaseReActAgent):
    def __init__(self, llm):
        super().__init__("WRITER", llm)
    
    def get_context(self, state: AgentState) -> str:
        """Ottiene il contesto per il writer"""
        context = f"Iterazione: {state.get('iteration_count', 0)}\n"
        
        if state.get("review_feedback"):
            context += f"Feedback precedente: {state['review_feedback'][:200]}...\n"
        
        if state.get("letter_draft"):
            context += f"Bozza attuale: {state['letter_draft'][:200]}..."
        else:
            context += "Prima stesura della lettera"
            
        return context
    
    def act(self, state: AgentState, reasoning: str) -> AgentState:
        """Scrive o riscrive la lettera basandosi sul ragionamento"""
        print("\n AGENTE SCRITTORE - Fase di azione...")
        
        if state.get("iteration_count", 0) == 0:
            user_prompt = prompts.WRITER_INITIAL
        else:
            user_prompt = prompts.WRITER_REVISION.format(
                review_feedback=state['review_feedback'],
                letter_draft=state['letter_draft']
            )
        
        # Aggiungi il ragionamento al prompt
        enhanced_prompt = f"RAGIONAMENTO:\n{reasoning}\n\nAZIONE RICHIESTA:\n{user_prompt}"
        
        messages = [
            SystemMessage(content=prompts.WRITER_SYSTEM),
            HumanMessage(content=enhanced_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            **state,
            "messages": state["messages"] + [response],
            "letter_draft": response.content,
            "review_feedback": "",
            "iteration_count": state.get("iteration_count", 0) + 1
        }

def writer_agent(state: AgentState, llm) -> AgentState:
    agent = WriterAgent(llm)
    return agent(state)