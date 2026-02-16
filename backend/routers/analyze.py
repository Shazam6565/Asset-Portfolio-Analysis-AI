from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from models.schemas import AnalyzeRequest, AnalyzeResponse, HoldingsResponse, SupervisorDecision
from agents.orchestrator import run_analysis, run_analysis_stream, run_general_chat
from services.entity_resolution_service import EntityResolutionService
import uuid
import time
import json
import asyncio
import re
from datetime import datetime

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse | HoldingsResponse)
async def analyze_portfolio(request: AnalyzeRequest):
    """
    Analyze portfolio using multi-agent LangGraph workflow.
    """
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        portfolio_context = request.portfolio_context or []
        
        # 1. Resolve Entity & Intent (Unified Service)
        resolution = await EntityResolutionService.resolve(request.query, portfolio_context)
        intent = resolution["intent"]
        
        # 2. Fast Path: Holdings Lookup
        if intent == "HOLDINGS_LOOKUP":
            target_ticker = resolution["ticker"]
            target_holding = next((h for h in portfolio_context if h.get("symbol") == target_ticker), None)
            
            if target_holding:
                qty = float(target_holding.get("quantity", 0))
                price = float(target_holding.get("price", 0))
                avg_cost = float(target_holding.get("average_buy_price", 0))
                
                # Use pre-calculated fields if available, else calc on fly
                equity = float(target_holding.get("equity", qty * price))
                pnl = float(target_holding.get("unrealized_pnl", (price - avg_cost) * qty))
                pnl_pct = float(target_holding.get("unrealized_pnl_pct", 0.0))
                
                # Recalculate pnl_pct if missing/zero but we have data
                if pnl_pct == 0.0 and avg_cost > 0 and qty > 0:
                     pnl_pct = (pnl / (avg_cost * qty)) * 100

                return HoldingsResponse(
                    ticker=target_ticker,
                    company_name=target_holding.get("name", target_ticker),
                    shares_held=qty,
                    current_price=price,
                    total_value=equity,
                    average_cost=avg_cost,
                    unrealized_pl_dollars=pnl,
                    unrealized_pl_percent=pnl_pct,
                    purchase_value=avg_cost * qty,
                    timestamp=datetime.now().isoformat()
                )

        # 3. General/Analysis Path (Orchestrator)
        # We pass the resolution result to avoid re-resolving inside orchestrator if we update it
        # For now, orchestrator resolves again (see next refactor step), but that's fine.
        result = await run_analysis(
            query=request.query,
            ticker=request.ticker, # User might explicitly override
            portfolio_context=portfolio_context,
            conversation_history=request.conversation_history or [],
            trace_id=trace_id,
        )
        
        # Calculate total duration
        duration = time.time() - start_time
        timings = result.get("timings") or {}
        if "total" not in timings:
            timings["total"] = duration
        result["timings"] = timings
        result["trace_id"] = trace_id
        
        return AnalyzeResponse(**result)

    except Exception as e:
        print(f"Analysis error: {e}")
        # Return a valid response structure even on error
        return AnalyzeResponse(
            synthesis="I encountered an internal error while processing your analysis request.",
            errors=[str(e)],
            trace_id=trace_id
        )



