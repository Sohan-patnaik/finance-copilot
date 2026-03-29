from agents.base_agent import BaseAgent
from tools.yahoo_finance import get_stock_data


class MarketDataAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        ticker = state.get("ticker", "")
        if not ticker:
            return {**state, "market_data": None}
        try:
            data = get_stock_data(ticker)
            self.logger.info(
                f"Market data fetched for {ticker}: ${data.price}")
            return {**state, "market_data": data.model_dump()}
        except Exception as e:
            self.logger.error(f"MarketDataAgent error: {e}")
            return {**state, "market_data": None, "errors": state.get("errors", []) + [str(e)]}
