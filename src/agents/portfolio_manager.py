import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI

from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing import Literal


class PortfolioManagerOutput(BaseModel):
    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(description="Number of shares to trade")
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the decision")


##### Portfolio Management Agent #####
def portfolio_management_agent(state: AgentState):
    """Makes final trading decisions and generates orders"""

    # Create the prompt template
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a portfolio manager making final trading decisions.
                Your job is to make a trading decision based on the team's analysis. You have the following analysts in your team:
                Technical Analyst: it gives signals based on the tehnical analysis of the given stock,
                Fundamental Analysis: it gives signals based on the funamental analysis of the given stock,
                Insider Sentiment Analyst: it look at insider trades
                Valuation Analyst: it checks if the valuation of the given stock is fair, by methods such as Discounted Cash Flow, Book-to-value etc
                Analysts Ratings Analyst: it looks at the last 10 analysts target price and compares to the actual price        
                """,
            ),
            (
                "human",
                """Based on the team's analysis below, make your trading decision.

                Technical Analysis Trading Signal: {technical_signal}
                Fundamental Analysis Trading Signal: {fundamentals_signal}
                Insider Sentiment Analysis Trading Signal: {insider_sentiment_signal}
                Valuation Analysis Trading Signal: {valuation_signal}
                Analysts Price Target Signal: {analysts_rating_signal}
                """,
            ),
        ]
    )

    # Get the portfolio and analyst signals
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]

    # Generate the prompt
    prompt = template.invoke(
        {
            "technical_signal": analyst_signals.get("technical_analyst_agent", {}).get(
                "signal", ""
            ),
            "fundamentals_signal": analyst_signals.get("fundamentals_agent", {}).get(
                "signal", ""
            ),
            "insider_sentiment_signal": analyst_signals.get("insider_sentiment_agent", {}).get(
                "signal", ""
            ),
            "valuation_signal": analyst_signals.get("valuation_agent", {}).get(
                "signal", ""
            ),
            "analysts_rating_signal": analyst_signals.get("analyst_ratings_agent",{}).get(
                "signal", ""
            ),
            "sentiment_signal": analyst_signals.get("sentiment_agent",{}).get(
                "signal", ""
            )
        }
    )
    # Create the LLM
    llm = ChatOpenAI(model="gpt-4").with_structured_output(
        PortfolioManagerOutput,
        method="function_calling",
    )

    try:
        # Invoke the LLM
        result = llm.invoke(prompt)
    except Exception as e:
        # Try again with same prompt
        result = llm.invoke(prompt)

    message_content = {
        "action": result.action.lower(),
        "quantity": int(result.quantity),
        "confidence": float(result.confidence),
        "reasoning": result.reasoning,
    }

    # Create the portfolio management message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="portfolio_management",
    )

    # Print the decision if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(message_content, "Portfolio Management Agent")

    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
    }
