import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI

from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing import Literal


class PortfolioManagerOutput(BaseModel):
    action: Literal["buy", "sell", "hold"]
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the decision. Give a full paragraph of in-depth reasoning for the decision")


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
                Analysts Ratings Analyst: it looks at the last 10 analysts target price and compares to the actual price.
                Sentiment Analyst: it looks over retail investors sentiment and news sentiment about the given company
                If all analysts give you values, I want you to weight as following: Fundamental 25%, Valuation 20%, Analysts 20%, Sentiment 15% ,Tehnical 10%, Insider sentiment 10%.
                Analyze the reasoning of each analysis, and based on their signals and reasoning, give a final trading decision, but also explain the reasoning behind your decision.        
                It's not mandatory for all the analysts to give you values, so you only have to rely on the given analysts responses.
                """,
            ),
            (
                "human",
                """Based on the team's analysis below, make your trading decision.

                Technical Analysis: {technical_signal}
                Fundamental Analysis: {fundamentals_signal}
                Insider Sentiment Analysis: {insider_sentiment_signal}
                Valuation Analysis: {valuation_signal}
                Analysts Price: {analysts_rating_signal}
                Sentiment Analysis: {sentiment_signal}
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
            "technical_signal": json.dumps(analyst_signals.get("technical_analyst_agent", {})),
            "fundamentals_signal": json.dumps(analyst_signals.get("fundamentals_agent", {})),
            "insider_sentiment_signal": json.dumps(analyst_signals.get("insider_sentiment_agent", {})),
            "valuation_signal": json.dumps(analyst_signals.get("valuation_agent", {})),
            "analysts_rating_signal": json.dumps(analyst_signals.get("analyst_ratings_agent",{})),
            "sentiment_signal": json.dumps(analyst_signals.get("sentiment_agent",{}))
        }
    )
    # Create the LLM
    llm = ChatOpenAI(model="o3-mini", max_tokens=8192).with_structured_output(
        PortfolioManagerOutput,
        #method="function_calling",
    )

    try:
        # Invoke the LLM
        result = llm.invoke(prompt)
    except Exception as e:
        # Try again with same prompt
        result = llm.invoke(prompt)

    message_content = {
        "action": result.action.lower(),
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
