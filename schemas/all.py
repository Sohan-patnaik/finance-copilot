from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Holding(BaseModel):
    ticker: str
    qty: float
    avg_price: float


class PortfolioCreate(BaseModel):
    name: str = "My Portfolio"
    holdings: list[Holding] = []


class PortfolioOut(BaseModel):
    id: int
    name: str
    holdings: list[Holding]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    ticker: str
    action: str
    quantity: float
    price: float


class TransationOut(TransactionCreate):
    id: int
    executed_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    query: str
    portfolio_id: Optional[int] = None


class AgentResult(BaseModel):
    agent: str
    data: dict


class ChatResponse(BaseModel):
    recommendation: str
    confidence: float
    reasons: list[str]
    risks: list[str]
    data_sources: list[str]
    raw_data: Optional[dict] = None


class StockData(BaseModel):
    ticker: str
    price: float
    change_pct: float
    volume: int
    week_52_high: float
    week_52_low: float
    market_cap: Optional[float] = None

class FundamentalsData(BaseModel):
    ticker:str
    pe_ratio:Optional[float]
    eps:Optional[float]
    roe:Optional[float]
    debt_to_equity:Optional[float]
    revenue_growth:Optional[float]
    analyst_rating:Optional[str]


class SentimentData(BaseModel):
    ticker:str
    score:float
    label:str
    articles:list[dict]

class RiskData(BaseModel):
    risk_score:float
    volatility:str
    concentration:float
    sector_exposure:dict
    suggestions:list[str]
        