from fastapi import APIRouter
from models.schemas import TradeRequest
from services.robinhood_service import RobinhoodService

router = APIRouter()

@router.post("/trade")
def execute_trade(trade: TradeRequest):
    return RobinhoodService.execute_trade(
        symbol=trade.symbol,
        action=trade.action,
        quantity=trade.quantity,
        order_type=trade.order_type
    )
