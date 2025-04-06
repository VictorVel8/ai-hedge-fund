from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from langchain_xai import ChatXAI
from pydantic import BaseModel, Field
from typing import Literal
import json

class SentimentAgentOutput(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="In-depth reasoning for the decision")

def sentiment_agent(state: AgentState):
    data = state["data"]
    ticker = data["ticker"]

    llm = ChatXAI(model="grok-2-1212", temperature=0, max_tokens=None, timeout=None, max_retries=2)
    messages = [("system", "You are an agent that works in a hedge fund, and you job is to do an in-depth analysis over the overall sentiment of a given stock symbol, on X platform and other news providers"), 
                ("human", f'Analyze the trends and sentiments about {ticker} stock. Based on your resposne, I want you you give me the sentiment, the confidence of the response, and an in-depth reasoning')]
    
    structured_llm = llm.with_structured_output(SentimentAgentOutput, method="function_calling")
    structured_llm_output = structured_llm.invoke(messages)
    state["data"]["analyst_signals"]["sentiment_agent"] = json.loads(json.dumps(structured_llm_output.__dict__))

    # # Create the fundamental analysis message
    message = HumanMessage(
        content=json.dumps(structured_llm_output.__dict__),
        name="sentiment_agent",
    )


    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(json.loads(json.dumps(structured_llm_output.__dict__)), "Sentiment Agent")
    #print(state["data"]["analyst_signals"]["sentiment_agent"])
  
    return {
        "messages": [message],
        "data": data,
    }
