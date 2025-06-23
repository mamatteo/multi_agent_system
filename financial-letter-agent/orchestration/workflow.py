# orchestration/workflow.py
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
    print("Creazione workflow con paradigma ReAct...")
    
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
    return workflow.compile(checkpointer=checkpointer)