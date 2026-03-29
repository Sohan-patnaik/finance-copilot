from fastapi import APIRouter, Depends
from core.security import get_current_user_id
from tools.scraper import scrape_news
from tools.rag import store_article, retrieve_relevant_news
from db.session import get_supabase
from datetime import datetime

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/{ticker}")
async def get_news(ticker: str, user_id: int = Depends(get_current_user_id)):
    articles = await scrape_news(ticker.upper(), max_articles=10)
    sb = get_supabase()
    for a in articles:
        store_article(a)

        try:
            sb.table("news_embeddings").upsert({
                "url": a.get("url", ""),
                "ticker": ticker.upper(),
                "headline": a.get("headline", ""),
                "content": a.get("headline", ""),
                "sentiment_score": 0.0,
                "published_at": datetime.utcnow().isoformat(),
            }).execute()
        except Exception:
            pass
    return {"ticker": ticker.upper(), "articles": articles}


@router.get("/{ticker}/relevant")
async def get_relevant_news(ticker: str, q: str = "", user_id: int = Depends(get_current_user_id)):
    query = q or f"Latest news about {ticker}"
    articles = retrieve_relevant_news(ticker.upper(), query)
    return {"ticker": ticker.upper(), "articles": articles}
