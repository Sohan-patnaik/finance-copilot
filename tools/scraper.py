import httpx
from bs4 import BeautifulSoup
from core.logger import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


async def scrape_news(ticker: str, max_articles: int = 5) -> list[dict]:
    articles = []
    try:
        articles = await _fetch_via_api(ticker, max_articles)
        if articles:
            return articles
    except Exception as e:
        logger.warning(f"API fetch failed for {ticker}: {e}")
    try:
        articles = await _scrape_yahoo(ticker, max_articles)
    except Exception as e:
        logger.warning(f"Scrape failed for {ticker}: {e}")
    return articles


async def _fetch_via_api(ticker: str, max_articles: int) -> list[dict]:
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": ticker, "newsCount": max_articles, "quotesCount": 0}
    async with httpx.AsyncClient(headers=HEADERS, timeout=10, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    return [
        {
            "headline": item.get("title", ""),
            "url": item.get("link", ""),
            "ticker": ticker.upper(),
            "publisher": item.get("publisher", ""),
        }
        for item in data.get("news", [])[:max_articles]
    ]


async def _scrape_yahoo(ticker: str, max_articles: int) -> list[dict]:
    url = f"https://finance.yahoo.com/quote/{ticker}/news/"
    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    for selector in ["li.js-stream-content", "div[data-testid='news-stream'] li", "li[class*='stream']"]:
        items = soup.select(selector)
        if items:
            for item in items[:max_articles]:
                headline = item.select_one("h3") or item.select_one("h2")
                link = item.select_one("a[href]")
                if headline and link:
                    href = link.get("href", "")
                    if not href.startswith("http"):
                        href = "https://finance.yahoo.com" + href
                    articles.append({"headline": headline.get_text(strip=True), "url": href, "ticker": ticker.upper()})
            if articles:
                break
    return articles