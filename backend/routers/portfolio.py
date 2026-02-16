from fastapi import APIRouter
from services.robinhood_service import RobinhoodService

router = APIRouter()

@router.get("/portfolio")
def get_portfolio():
    return {"status": "success", "data": RobinhoodService.get_portfolio()}
