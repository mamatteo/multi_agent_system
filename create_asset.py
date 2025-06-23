#!/usr/bin/env python3
"""
Script per creare il progetto Financial Letter Agent con paradigma ReAct
"""

import os
from pathlib import Path

# Definizione di tutti i file del progetto
PROJECT_FILES = {
    "config.py": '''# config.py
from openai import AzureOpenAI

AZURE_ENDPOINT = "https://matte-mb4x24lj-eastus2.cognitiveservices.azure.com/"
AZURE_DEPLOYMENT = "gpt-4o-2"
AZURE_API_KEY = "DF3ExC1zxMYZiu1NFefdjQPfJzum2bH3Kk7OE5aOj6yi7leDOSP1JQQJ99BEACHYHv6XJ3w3AAAAACOGvXwd"
AZURE_API_VERSION = "2024-12-01-preview"

azure_client = AzureOpenAI(
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
)''',

    "prompts/__init__.py": '''# prompts/__init__.py
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
REACT_REASONING = load_prompt("react_reasoning.txt")''',

    "prompts/writer_system.txt": '''Sei un esperto consulente finanziario. Scrivi lettere persuasive e professionali.''',

    "prompts/writer_initial.txt": '''Scrivi una lettera di richiesta finanziamento...''',

    "prompts/writer_revision.txt": '''Riscrivi la lettera precedente considerando questo feedback:
FEEDBACK REVISORE: {review_feedback}
LETTERA PRECEDENTE: {letter_draft}''',

    "prompts/reviewer_system.txt": '''Sei un severo analista bancario. Revisiona criticamente la lettera e fornisci feedback.''',

    "prompts/reviewer_prompt.txt": '''Revisiona criticamente questa lettera:
{letter_draft}
Fornisci:
1. Valutazione complessiva (APPROVATA/DA RIVEDERE)
2. Problemi riscontrati
3. Suggerimenti di miglioramento.''',

    "prompts/react_reasoning.txt": '''Prima di procedere con il tuo compito, ragiona sui seguenti punti:

THOUGHT: Qual è l'obiettivo specifico di questa fase?
OBSERVATION: Cosa osservi nello stato attuale (dati, feedback precedenti, etc.)?
ACTION: Qual è l'azione migliore da intraprendere?

Fornisci il tuo ragionamento prima di procedere con l'azione.''',

    "state.py": '''# state.py
from typing import TypedDict, Annotated, List, Optional
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    letter_draft: str
    review_feedback: str
    iteration_count: int
    is_approved: bool
    final_letter: str
    # Aggiunti per ReAct
    current_reasoning: Optional[str]
    action_history: Annotated[List[str], operator.add]''',

    "llm_wrapper.py": '''# llm_wrapper.py
from typing import List
from openai import AzureOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

class AzureOpenAIWrapper:
    def __init__(self, client: AzureOpenAI, deployment: str, temperature: float = 0.7):
        self.client = client
        self.deployment = deployment
        self.temperature = temperature
    
    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
        
        response = self.client.chat.completions.create(
            messages=openai_messages,
            model=self.deployment,
            temperature=self.temperature,
            max_tokens=2000
        )
        return AIMessage(content=response.choices[0].message.content)''',

    "agents/__init__.py": '''# agents/__init__.py
# File vuoto per rendere agents un package Python''',

    "agents/base_react_agent.py": '''# agents/base_react_agent.py
from abc import ABC, abstractmethod
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import AgentState
import prompts

class BaseReActAgent(ABC):
    """Classe base per agenti che implementano il paradigma ReAct"""
    
    def __init__(self, name: str, llm):
        self.name = name
        self.llm = llm
    
    def reason(self, state: AgentState) -> str:
        """Fase di ragionamento (Thought + Observation)"""
        print(f"\\n🤔 {self.name} - Fase di ragionamento...")
        
        context = self.get_context(state)
        reasoning_prompt = f"{prompts.REACT_REASONING}\\n\\nCONTESTO ATTUALE:\\n{context}"
        
        messages = [
            SystemMessage(content=f"Sei l'agente {self.name}. Ragiona sul tuo prossimo passo."),
            HumanMessage(content=reasoning_prompt)
        ]
        
        response = self.llm.invoke(messages)
        reasoning = response.content
        
        print(f"💭 Ragionamento: {reasoning[:200]}...")
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
        
        return new_state''',

    "agents/writer.py": '''# agents/writer.py
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState
from agents.base_react_agent import BaseReActAgent
import prompts

class WriterAgent(BaseReActAgent):
    def __init__(self, llm):
        super().__init__("WRITER", llm)
    
    def get_context(self, state: AgentState) -> str:
        """Ottiene il contesto per il writer"""
        context = f"Iterazione: {state.get('iteration_count', 0)}\\n"
        
        if state.get("review_feedback"):
            context += f"Feedback precedente: {state['review_feedback'][:200]}...\\n"
        
        if state.get("letter_draft"):
            context += f"Bozza attuale: {state['letter_draft'][:200]}..."
        else:
            context += "Prima stesura della lettera"
            
        return context
    
    def act(self, state: AgentState, reasoning: str) -> AgentState:
        """Scrive o riscrive la lettera basandosi sul ragionamento"""
        print("\\n✍️ AGENTE SCRITTORE - Fase di azione...")
        
        if state.get("iteration_count", 0) == 0:
            user_prompt = prompts.WRITER_INITIAL
        else:
            user_prompt = prompts.WRITER_REVISION.format(
                review_feedback=state['review_feedback'],
                letter_draft=state['letter_draft']
            )
        
        # Aggiungi il ragionamento al prompt
        enhanced_prompt = f"RAGIONAMENTO:\\n{reasoning}\\n\\nAZIONE RICHIESTA:\\n{user_prompt}"
        
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
    return agent(state)''',

    "agents/reviewer.py": '''# agents/reviewer.py
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState
from agents.base_react_agent import BaseReActAgent
import prompts

class ReviewerAgent(BaseReActAgent):
    def __init__(self, llm):
        super().__init__("REVIEWER", llm)
    
    def get_context(self, state: AgentState) -> str:
        """Ottiene il contesto per il reviewer"""
        context = f"Iterazione: {state.get('iteration_count', 0)}\\n"
        context += f"Lettera da revisionare: {state['letter_draft'][:300]}..."
        
        if state.get("action_history"):
            context += f"\\nStorico azioni: {len(state['action_history'])} azioni precedenti"
            
        return context
    
    def act(self, state: AgentState, reasoning: str) -> AgentState:
        """Revisiona la lettera basandosi sul ragionamento"""
        print("\\n🔍 AGENTE REVISORE - Fase di azione...")
        
        user_prompt = prompts.REVIEWER_PROMPT.format(letter_draft=state['letter_draft'])
        
        # Aggiungi il ragionamento al prompt
        enhanced_prompt = f"RAGIONAMENTO CRITICO:\\n{reasoning}\\n\\nREVISIONE RICHIESTA:\\n{user_prompt}"
        
        messages = [
            SystemMessage(content=prompts.REVIEWER_SYSTEM),
            HumanMessage(content=enhanced_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        is_approved = "APPROVATA" in response.content.upper()
        if state.get("iteration_count", 0) >= 3:
            is_approved = True
            print("⚠️ Limite iterazioni raggiunto - approvazione forzata")
        
        return {
            **state,
            "messages": state["messages"] + [response],
            "review_feedback": response.content,
            "is_approved": is_approved,
            "final_letter": state['letter_draft'] if is_approved else ""
        }

def reviewer_agent(state: AgentState, llm) -> AgentState:
    agent = ReviewerAgent(llm)
    return agent(state)''',

    "agents/mailman.py": '''# agents/mailman.py
from datetime import datetime
from langchain_core.messages import AIMessage
from state import AgentState

def mailman_agent(state: AgentState, llm=None) -> AgentState:
    print("\\n📮 AGENTE POSTINO attivato...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lettera_finanziamento_{timestamp}.txt"
    
    # Includi lo storico del ragionamento nel documento finale
    action_history_text = "\\n".join(state.get("action_history", []))
    
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
    print(f"✅ Lettera salvata in: {filename}")
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=f"Lettera inviata e salvata in {filename}")],
        "action_history": state.get("action_history", []) + [f"MAILMAN: Documento salvato in {filename}"]
    }''',

    "orchestration/__init__.py": '''# orchestration/__init__.py
# Package per orchestrazione e workflow''',

    "orchestration/orchestrator.py": '''# orchestration/orchestrator.py
from typing import Literal
from langgraph.graph import END
from state import AgentState

def orchestrator(state: AgentState) -> Literal["writer", "reviewer", "mailman", END]:
    print("\\n🎯 ORCHESTRATORE - Decisione routing...")
    
    # Log dello stato per debugging
    print(f"   📊 Stato attuale:")
    print(f"      - Bozza presente: {bool(state.get('letter_draft'))}")
    print(f"      - Feedback presente: {bool(state.get('review_feedback'))}")
    print(f"      - Approvata: {state.get('is_approved', False)}")
    print(f"      - Iterazione: {state.get('iteration_count', 0)}")
    
    if not state.get("letter_draft"):
        print("   ➡️ Routing verso WRITER (prima stesura)")
        return "writer"
    elif not state.get("is_approved", False):
        if state.get("review_feedback"):
            print("   ➡️ Routing verso WRITER (revisione)")
            return "writer"
        else:
            print("   ➡️ Routing verso REVIEWER")
            return "reviewer"
    elif state.get("final_letter"):
        print("   ➡️ Routing verso MAILMAN")
        return "mailman"
    else:
        print("   ✅ Processo completato")
        return END''',

    "orchestration/workflow.py": '''# orchestration/workflow.py
from functools import partial
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from agents.writer import writer_agent
from agents.reviewer import reviewer_agent
from agents.mailman import mailman_agent
from orchestration.orchestrator import orchestrator
from llm_wrapper import AzureOpenAIWrapper
from config import azure_client, AZURE_DEPLOYMENT

llm = AzureOpenAIWrapper(azure_client, AZURE_DEPLOYMENT)

def create_workflow():
    print("🔧 Creazione workflow con paradigma ReAct...")
    
    workflow = StateGraph(AgentState)
    
    # Crea funzioni parziali con llm
    writer_with_llm = partial(writer_agent, llm=llm)
    reviewer_with_llm = partial(reviewer_agent, llm=llm)
    mailman_with_llm = partial(mailman_agent, llm=llm)
    
    # Aggiungi nodi
    workflow.add_node("writer", writer_with_llm)
    workflow.add_node("reviewer", reviewer_with_llm)
    workflow.add_node("mailman", mailman_with_llm)
    
    # Configura routing
    workflow.set_entry_point("writer")
    workflow.add_conditional_edges(
        "writer", 
        orchestrator, 
        {
            "reviewer": "reviewer", 
            "writer": "writer", 
            "mailman": "mailman", 
            END: END
        }
    )
    workflow.add_conditional_edges(
        "reviewer", 
        orchestrator, 
        {
            "writer": "writer", 
            "reviewer": "reviewer", 
            "mailman": "mailman", 
            END: END
        }
    )
    workflow.add_conditional_edges("mailman", lambda x: END)
    
    # Aggiungi checkpointer
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)''',

    "main.py": '''# main.py
from orchestration.workflow import create_workflow

def main():
    print("🚀 Avvio Sistema Multi-Agente con Paradigma ReAct")
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
    
    print("\\n📝 Inizio elaborazione...")
    print("="*50)
    
    for event in app.stream(initial_state, config):
        for node, data in event.items():
            print(f"\\n✨ Nodo completato: {node.upper()}")
            if "current_reasoning" in data and data["current_reasoning"]:
                print(f"   💭 Ultimo ragionamento: {data['current_reasoning'][:150]}...")
            if "messages" in data and data["messages"]:
                print(f"   📄 Output: {data['messages'][-1].content[:150]}...")
    
    print("\\n" + "="*50)
    print("✅ Processo completato con successo!")
    print("="*50)

if __name__ == "__main__":
    main()''',

    "requirements.txt": '''langchain>=0.1.0
langgraph>=0.0.20
openai>=1.0.0
python-dotenv>=1.0.0''',

    ".gitignore": '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment variables
.env

# Output files
lettera_finanziamento_*.txt

# OS
.DS_Store
Thumbs.db'''
}

def create_project_structure():
    """Crea la struttura completa del progetto"""
    
    # Nome del progetto
    project_name = "financial-letter-agent"
    
    # Crea la directory principale
    project_dir = Path(project_name)
    project_dir.mkdir(exist_ok=True)
    
    print(f"📁 Creazione progetto: {project_name}")
    
    # Crea tutti i file
    for file_path, content in PROJECT_FILES.items():
        full_path = project_dir / file_path
        
        # Crea le directory se necessario
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Scrivi il file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Creato: {file_path}")
    
    print(f"\\n🎉 Progetto creato con successo in: {project_dir.absolute()}")
    print("\\n📋 Nuova struttura con paradigma ReAct:")
    print("   agents/")
    print("   ├── base_react_agent.py (classe base ReAct)")
    print("   ├── writer.py (con reasoning)")
    print("   ├── reviewer.py (con reasoning)")
    print("   └── mailman.py")
    print("   orchestration/")
    print("   ├── orchestrator.py (logica routing)")
    print("   └── workflow.py (costruzione grafo)")
    print("\\n📋 Prossimi passi:")
    print("1. cd financial-letter-agent")
    print("2. python3 -m venv venv")
    print("3. source venv/bin/activate")
    print("4. pip install -r requirements.txt")
    print("5. python main.py")

if __name__ == "__main__":
    create_project_structure()
