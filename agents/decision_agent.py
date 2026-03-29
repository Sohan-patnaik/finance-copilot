from agents.base_agent import BaseAgent
import json
from tools.llm_client import chat_complete

SYSTEM = """You are a senior equity analyst. Given aggregated data, return ONLY valid JSON:
{
  "recommendation": "<BUY|HOLD|SELL>",
  "confidence": <0.0-1.0>,
  "reasons": ["<reason1>", "<reason2>", "<reason3>"],
  "risks": ["<risk1>", "<risk2>"],
  "data_sources": ["market_data", "news", "fundamentals"]
}
Base recommendation strictly on data. Be concise and specific."""


class DecisionAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        ticker = state.get("ticker", "N/A")
        context = self._build_context(state, ticker)
        try:
            raw = await chat_complete(SYSTEM, context)
            decision = json.loads(raw)
            self.logger.info(
                f"Decision for {ticker}:{decision['recommendation']} {decision['confidence']}")
            return {**state, "decision": decision}
        except Exception as e:
            self.logger.error(f"DecisionAgent error: {e}")
            return {**state, "decision": self._fallback(e)}

    def _build_context(self, state: dict, ticker: str) -> str:
        parts = [f"Stock: {ticker}", f"Query: {state.get('query', '')}"]

        if md := state.get("market_data"):
            parts.append(
                f"Price: ${md.get('price')} ({md.get('change_pct')}% today ) |"
                f"52w High: ${md.get('week_52_high')} | Low: ${md.get('week_52_low')}"
            )
        if nd := state.get("news_data"):
            parts.append(
                f"News Sentiment: {nd.get('label')} (score: {nd.get('score')}) | {nd.get('summary', '')}")
        if fd := state.get("fundamentals_data"):
            parts.append(
                f"Fundamentals: P/E={fd.get('pe_ratio')} | EPS={fd.get('eps')} | "
                f"ROE={fd.get('roe')} | Quality={fd.get('quality')}"
            )
        if rd := state.get("risk_data"):
            parts.append(
                f"Portfolio Risk: {rd.get('risk_score')}/100 | {', '.join(rd.get('suggestions', []))}")

        return "\n".join(parts)

    def _fallback(self, error: Exception) -> dict:
        return {
            "recommendation": "HOLD",
            "confidence": 0.0,
            "reasons": ["Unable to complete analysis due to an error."],
            "risks": [str(error)],
            "data_sources": [],
        }
