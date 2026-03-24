import requests
import yfinance as yf
from schemas.all import StockData, FundamentalsData
from core.logger import get_logger

logger = get_logger(__name__)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})
yf.utils.get_json = lambda url, proxy=None: session.get(url).json()


def get_stock_data(ticker: str) -> StockData:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="5d")

        price = info.get("currentPrice") or info.get(
            "regularMarketPrice") or hist["Close"].iloc[-1]
        prev_close = info.get(
            "previousClose") or hist["Close"].iloc[-2] if len(hist) >= 2 else price
        change_pct = ((price - prev_close) / prev_close) * \
            100 if prev_close else 0

        return StockData(
            ticker=ticker.upper(),
            price=round(float(price), 2),
            change_pct=round(float(change_pct), 2),
            volume=int(info.get("volume") or info.get("averageVolume") or 0),
            week_52_high=round(
                float(info.get("fiftyTwoWeekHigh") or price), 2),
            week_52_low=round(float(info.get("fiftyTwoWeekLow") or price), 2),
            market_cap=info.get("marketCap"),
        )
    except Exception as e:
        logger.error(f"Market data fetch failed for {ticker}: {e}")
        raise


def get_fundamentals(ticker: str) -> FundamentalsData:
    try:
        info = yf.Ticker(ticker).info
        return FundamentalsData(
            ticker=ticker.upper(),
            pe_ratio=info.get("trailingPE"),
            eps=info.get("trailingEps"),
            roe=info.get("returnOnEquity"),
            debt_to_equity=info.get("debtToEquity"),
            revenue_growth=info.get("revenueGrowth"),
            analyst_rating=info.get("recommendationKey"),
        )
    except Exception as e:
        logger.error(f"Fundamentals fetch failed for {ticker}: {e}")
        raise
