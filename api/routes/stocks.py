from fastapi import APIRouter, Depends, HTTPException
from schemas.all import StockData, FundamentalsData
from tools.yahoo_finance import get_stock_data, get_fundamentals
from core.security import get_current_user_id
from db.session import get_supabase
from datetime import datetime

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/{ticker}", response_model=StockData)
async def stock_quote(ticker: str, user_id: int = Depends(get_current_user_id)):
    try:
        data = get_stock_data(ticker.upper())
        sb = get_supabase()
        try:
            sb.table("cached_stock_data").upsert({
                "ticker": ticker.upper(),
                "data": data.model_dump(),
                "cached_at": datetime.utcnow().isoformat(),
            }).execute()
        except Exception:
            pass
        return data
    except Exception as e:
        
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}: {e}")


@router.get("/{ticker}/fundamentals", response_model=FundamentalsData)
async def stock_fundamentals(ticker: str, user_id: int = Depends(get_current_user_id)):
    try:
        return get_fundamentals(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch fundamentals for {ticker}: {e}")
