from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from db.session import get_supabase
from schemas.all import PortfolioCreate, PortfolioOut, TransactionCreate, TransationOut,Holding
from core.security import get_current_user_id
from graph.workflow import run_pipeline

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("", response_model=PortfolioOut, status_code=201)
async def create_portfolio(
    payload: PortfolioCreate,
    user_id: int = Depends(get_current_user_id),
):
    sb = get_supabase()
    result = sb.table("portfolios").insert({
        "user_id": user_id,
        "name": payload.name,
        "holdings": [h.model_dump() for h in payload.holdings],
        "created_at": datetime.utcnow().isoformat(),
    }).execute()
    p = result.data[0]
    return PortfolioOut(
        id=p["id"],
        name=p["name"],
        holdings=p["holdings"] or [],
        created_at=p["created_at"],
    )


@router.get("", response_model=list[PortfolioOut])
async def list_portfolios(user_id: int = Depends(get_current_user_id)):
    sb = get_supabase()
    result = sb.table("portfolios").select(
        "*").eq("user_id", user_id).execute()
    return [
        PortfolioOut(id=p["id"], name=p["name"], holdings=p["holdings"] or [], created_at=p["created_at"]) for p in result.data
    ]


@router.get("/{portfolio_id}/analyze")
async def analyze_portfolio(
    portfolio_id: int, user_id: int = Depends(get_current_user_id),
):
    sb = get_supabase()
    result = sb.table("portfolios").select(
        "*").eq("id", portfolio_id).execute()
    if not result.data or result.data[0]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    p = result.data[0]
    return await run_pipeline(
        query="Act as a senior analyzer and analyze my portfolio risk and diversification properly",
        holdings=p["holdings"] or [],
    )

@router.post("{portfolio_id}//transaction",response_model=TransationOut,status_code=201)
async def add_transaction(portfolio_id:int,payload:TransactionCreate,user_id:int=Depends(get_current_user_id),):
    sb=get_supabase()

    p_result=sb.table("portfolios").select("*").eq("id",portfolio_id).execute()
    if not p_result.data or p_result.data[0]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Portfolio not found")


    p=p_result.data[0]

    txn_result=sb.table("transactions").insert({
        "portfolio_id": portfolio_id,
        "ticker": payload.ticker,
        "action": payload.action,
        "quantity": payload.quantity,
        "price": payload.price,
        "executed_at": datetime.utcnow().isoformat(),
    }).execute()
    
    txn=txn_result.data[0]

    return TransationOut(
        id=txn["id"],
        ticker=txn["ticker"],
        action=txn["action"],
        quantity=txn["quantity"],
        price=txn["price"],
        executed_at=txn["executed_at"],
    )

def _apply_transaction(holdings: list[Holding],txn:TransactionCreate)->list[Holding]:
    existing=next((h for h in holdings if h.ticker==txn.ticker),None)
    if txn.action=="BUY":
        if existing:
            total_qty=existing.qty+txn.quantity
            existing.avg_price=(existing.avg_price*existing.qty+txn.price*txn.quantity)/total_qty
            existing.qty=total_qty
        else:
            holdings.append(Holding(ticker=txn.ticker,qty=txn.quantity,avg_price=txn.price))
    elif txn.action=="SELL" and existing:
        existing.qty-=txn.quantity
        if existing.qty <= 0:
            holdings = [h for h in holdings if h.ticker != txn.ticker]
    return holdings        

    