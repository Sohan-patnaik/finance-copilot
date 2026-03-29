from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime

from db.session import get_supabase
from core.security import hash_password, verify_password, create_access_token
from schemas.all import UserCreate, UserOut, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate):
    sb = get_supabase()
    existing = sb.table("users").select("id").eq(
        "email", payload.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    result = sb.table("users").insert({
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "full_name": payload.full_name,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    user = result.data[0]
    return UserOut(
        id=user["id"],
        email=user["email"],
        full_name=user.get("full_name"),
        created_at=user["created_at"],
    )


@router.post("/token", response_model=TokenOut)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    sb = get_supabase()

    result = sb.table("users").select("*").eq("email", form.username).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = result.data[0]
    if not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user["id"])})
    return TokenOut(access_token=token)
