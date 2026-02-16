from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = None

class TradeRequest(BaseModel):
    symbol: str
    action: str  # buy or sell
    quantity: float
    order_type: str = "market"

class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class AnalyzeRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    portfolio_context: Optional[list] = None
    conversation_history: Optional[List[ConversationMessage]] = None

class KeyMetric(BaseModel):
    name: str
    value: str
    why_it_matters: str = ""

class SourceUsed(BaseModel):
    type: str  # "technical" | "fundamental" | "sentiment" | "portfolio"
    provider: str  # "yfinance" | "finnhub" | "newsapi" | "robinhood"
    label: str = ""
    ts: Optional[str] = None  # ISO format string or datetime

class SupervisorDecision(BaseModel):
    action: Literal["BUY", "HOLD", "SELL"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    price_target: Optional[str] = None
    time_horizon: Optional[str] = None  # e.g. "3-6 months"
    thesis: str  # 2-4 sentence narrative, markdown-safe
    risks: List[str] = Field(default_factory=list, min_length=1, max_length=7)
    catalysts: List[str] = Field(default_factory=list, max_length=7)
    position_sizing: Optional[str] = None  # e.g. "2-3% of portfolio"
    key_metrics: List[KeyMetric] = Field(default_factory=list, max_length=10)
    sources_used: List[SourceUsed] = Field(default_factory=list)
    verdict_reasoning: Optional[str] = None # Quick summary of why BUY/HOLD/SELL (e.g. "ROIC > WACC + ADX Bullish")

class HoldingsResponse(BaseModel):
    response_type: Literal["holdings_lookup"] = "holdings_lookup"
    ticker: str
    company_name: str
    shares_held: float
    current_price: float
    total_value: float
    average_cost: float
    unrealized_pl_dollars: float
    unrealized_pl_percent: float
    purchase_value: float
    timestamp: str

class AnalyzeResponse(BaseModel):
    # Common fields
    response_type: Literal["analysis", "general"] = "analysis"
    
    # Legacy fields (kept for backward compatibility during V3 migration)
    ticker: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: Optional[str] = None
    price_target: Optional[str] = None
    synthesis: str
    risks: List[str] = []
    catalysts: List[str] = []
    technical_report: Optional[str] = None
    fundamental_report: Optional[str] = None
    sentiment_report: Optional[str] = None
    stock_info: Optional[Dict[str, Any]] = None
    
    # V3 fields
    decision: Optional[SupervisorDecision] = None
    trace_id: Optional[str] = None
    timings: Optional[Dict[str, float]] = None
    errors: List[str] = []
