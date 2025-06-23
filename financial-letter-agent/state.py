# state.py
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
    action_history: Annotated[List[str], operator.add]