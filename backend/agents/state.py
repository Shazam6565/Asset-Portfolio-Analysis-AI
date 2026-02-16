from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AnalysisState(TypedDict, total=False):
    """
    State schema for the analysis graph.
    Shared data structure passed between agents.
    All fields optional to support incremental V3 migration.
    """
    # Inputs
    ticker: str
    query: str
    portfolio_context: List[Dict[str, Any]]
    
    # V3 Core Fields
    intent: str  # "TICKER_ANALYSIS" | "PORTFOLIO_QA" | "GENERIC_CHAT"
    trace_id: str
    timings: Dict[str, float]
    
    # V3 Intelligence
    entity_resolution: Dict[str, Any]  # raw result
    resolved_ticker: Optional[str]
    resolved_ticker_confidence: float
    position_context: Optional[Dict[str, Any]]
    portfolio_summary: Optional[Dict[str, Any]]
    decision: Optional[Dict[str, Any]]  # SupervisorDecision payload
    
    # Data gathered
    price_data: Dict[str, Any]
    fundamentals: Dict[str, Any]
    stock_info: Dict[str, Any]
    news_articles: List[Dict[str, Any]]
    sentiment_scores: Dict[str, Any]

    # Professional Grade Data Clusters (V4)
    technical_indicators: Dict[str, Any]  # ADX, Ichimoku, Pivots, etc.
    financial_metrics: Dict[str, Any]     # ROIC, FCF Yield, Piotroski, etc.
    market_sentiment: Dict[str, Any]      # Put/Call Ratio, Max Pain, Shorts

    # Agent Outputs
    technical_report: str
    fundamental_report: str
    sentiment_report: str
    
    # Synthesis / Legacy Output (Backwards Compat)
    recommendation: str
    confidence: str
    price_target: str
    synthesis: str
    risks: List[str]
    catalysts: List[str]
    
    # Conversation history & Errors
    messages: Annotated[List[BaseMessage], add_messages]
    errors: Annotated[List[str], operator.add]
