from fastapi import APIRouter
from models.schemas import LoginRequest
from services.robinhood_service import RobinhoodService

router = APIRouter()

@router.post("/login")
def login(request: LoginRequest):
    return RobinhoodService.login(
        username=request.username,
        password=request.password,
        mfa_code=request.mfa_code
    )
