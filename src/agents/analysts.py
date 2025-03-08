from scrapy.crawler import CrawlerProcess
from analyst_spider.analyst_spider.spiders.analyst_spider import AnalystSpider
from analyst_spider.analyst_spider.pipelines import AnalystSpiderPipeline
import json
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_prices
from colorama import Fore


def analyst_ratings_agent(state: AgentState):
    """
    This function acts as the 'agent' that invokes the spider.
    It can be triggered by your state machine.
    """

    data = state["data"]
    ticker = data["ticker"]

    start_date = data["start_date"]
    end_date = data["end_date"]

    # Get the historical price data
    prices = get_prices(
        ticker=data["ticker"],
        start_date=start_date,
        end_date=end_date,
    )

    current_price = prices[-1]["close"]


    analysts_price = AnalystSpiderPipeline.average_price

    signal = "neutral"
    if analysts_price > 1.05 * current_price:
        signal = "bullish"
    elif analysts_price<0.95*current_price:
        signal="bearish"

    message_content = {
        "analysts_average_price": AnalystSpiderPipeline.average_price,
        "reasoning": f'We looked over the last 10 analysts target prices on the given stock, and the average of those 10 target prices is {analysts_price} and the last closing price is {current_price}',
    }

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(message_content, "Fundamental Analysis Agent")

    state["data"]["analyst_signals"]["analyst_ratings_agent"] = {
        "signal": signal,
        "confidence": 100, #TODO: Here the confidence can be modified
        "reasoning": f'We looked over the last 10 analysts target prices on the given stock, and the average of those 10 target prices is {analysts_price}.',
    }

    # Create the fundamental analysis message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="analyst_ratings_agent",
    )

    #print(Fore.GREEN+f'ANALYSTS RATINGS TEAM: We looked over the last 10 analysts target prices on the given stock, and the average of those 10 target prices is {analysts_price} and the last closing price is {current_price}')
    return {
        "messages": [message],
        "data": data,
    }