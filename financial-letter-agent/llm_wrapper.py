# llm_wrapper.py
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
        return AIMessage(content=response.choices[0].message.content)