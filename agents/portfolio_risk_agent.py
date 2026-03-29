from agents.base_agent import BaseAgent
from tools.yahoo_finance import get_stock_data

SECTOR_MAP = {
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCL": "IT",
    "RELIANCE": "Energy", "ONGC": "Energy",
    "HDFC": "Finance", "ICICI": "Finance", "SBI": "Finance", "AXIS": "Finance",
    "TATAMOTORS": "Auto", "M&M": "Auto",
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma",
    "AAPL": "IT", "MSFT": "IT", "GOOGL": "IT", "META": "IT", "AMZN": "Retail",
    "TSLA": "Auto", "JPM": "Finance", "BAC": "Finance",
}


class PortfolioRiskAgent(BaseAgent):
    async def run(self, state: dict) -> dict:
        holdings: list[dict] = state.get("holdings", [])
        if not holdings:
            return {**state, "risk_data": None}
        try:
            total_value = 0.0
            enriched = []
            for h in holdings:
                try:
                    stock = get_stock_data(h["ticker"])
                    current_value = stock.price * h["qty"]
                    total_value += current_value
                    enriched.append(
                        {**h, "current_price": stock.price, "current_value": current_value})
                except Exception:
                    enriched.append(
                        {**h, "current_price": h["avg_price"], "current_value": h["avg_price"] * h["qty"]})
                    total_value += h["avg_price"] * h["qty"]
            sector_exposure = dict[str, float] = {}
            max_concentration = 0.0
            for h in enriched:
                pct = (h["current_value"]/total_value) * \
                    100 if total_value else 0
                h["weight_pct"] = round(pct, 2)
                sector = SECTOR_MAP.get(h["ticker"].upper(), "Other")
                sector_exposure[sector] = round(
                    sector_exposure.get(sector, 0)+pct, 2)
                if pct > max_concentration:
                    max_concentration = pct

            risk_score = self._compute_risk_score(
                max_concentration, len(holdings), sector_exposure)
            suggestions = self._build_suggestions(
                max_concentration, sector_exposure, len(holdings))

            result = {
                "risk_score": risk_score,
                "volatility": "high" if risk_score > 70 else "medium" if risk_score > 40 else "low",
                "concentration": round(max_concentration, 2),
                "sector_exposure": sector_exposure,
                "suggestions": suggestions,
                "total_value": round(total_value, 2),
                "holdings": enriched,
            }
            self.logger.info(f"Portfolio risk score: {risk_score}")
            return {**state, "risk_data": result}

        except Exception as e:
            self.logger.error(f"PortfolioRiskAgent error: {e}")
            return {**state, "risk_data": None, "errors": state.get("errors", []) + [str(e)]}

    def _compute_risk_score(self, concentration: float, n_stocks: int, sectors: dict) -> float:
        score = 0.0
        score += min(concentration, 50)
        score += max(0, (5-n_stocks)*5)
        score += max(0, (3-len(sectors))*10)
        return round(min(score, 100), 1)

    def _build_suggestions(self, conc: float, sectors: dict, n: int) -> list[str]:
        tips = []
        if conc > 40:
            tips.append(
                "Top holding exceeds 40% — consider trimming to reduce concentration risk.")
        if n < 5:
            tips.append(
                "Portfolio has fewer than 5 stocks — diversify across more names.")
        if len(sectors) < 3:
            tips.append(
                "Exposure limited to fewer than 3 sectors — add cross-sector positions.")
        it_pct = sectors.get("IT", 0)
        if it_pct > 60:
            tips.append(
                "Over 60% in IT sector — consider adding defensive sectors like Pharma or FMCG.")
        if not tips:
            tips.append("Portfolio looks reasonably diversified.")
        return tips
