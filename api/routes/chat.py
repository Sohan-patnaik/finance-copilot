from fastapi import APIRouter, Depends
from schemas.all import ChatRequest, ChatResponse
from graph.workflow import run_pipeline
from core.security import get_current_user_id
from core.logger import get_logger
import re

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    payload:ChatRequest,
    user_id:int=Depends(get_current_user_id)
):
    logger.info(f"Chat request from user {user_id}:{payload.query[:80]}")
    ticker=_extract_ticker(payload.query)
    result=await run_pipeline(query=payload.query,ticker=ticker)
    return ChatResponse(**{k:result[k] for k in ChatResponse.model_fields if k in result})

def _extract_ticker(query:str) -> str:
    m = re.search(r'\b([A-Z]{2,6})\b', query.upper())
    return m.group(1) if m else ""