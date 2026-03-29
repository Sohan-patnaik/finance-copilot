import json
from agents.base_agent import BaseAgent
from tools.yahoo_finance import get_fundamentals
from tools.llm_client import chat_complete

SYSTEM = """You are a fundamental stock analyst. Given financial ratios, return ONLY valid JSON:
{
  "quality": "<poor|fair|good|excellent>",
  "highlights": ["<highlight1>", "<highlight2>"],
  "concerns": ["<concern1>"]
}"""


class FundamentalAnalysisAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        ticker = state.get("ticker", "")
        if not ticker:
            return {**state, "fundamentals_data": None}
        try:
            fund = get_fundamentals(ticker)
            ratios_text = (
                f"P/E: {fund.pe_ratio}, EPS: {fund.eps}, ROE: {fund.roe}, "
                f"Debt/Equity: {fund.debt_to_equity}, Revenue Growth: {fund.revenue_growth}, "
                f"Analyst Rating: {fund.analyst_rating}"
            )
            raw = await chat_complete(SYSTEM, f"Ticker: {ticker}\nRatios: {ratios_text}")
            analysis = json.loads(raw)
            result = {**fund.model_dump(), **analysis}
            self.logger.info(f"Fundamentals for {ticker}: {analysis['quality']}")
            return {**state, "fundamentals_data": result}
        except Exception as e:
            self.logger.error(f"FundamentalAnalysisAgent error: {e}")
            return {**state, "fundamentals_data": None, "errors": state.get("errors", []) + [str(e)]}
