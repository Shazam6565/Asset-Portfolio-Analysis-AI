# Start of file
from langgraph.graph import StateGraph, END, START
from agents.state import AnalysisState
from agents.technical_agent import technical_analysis_node
from agents.fundamental_agent import fundamental_analysis_node
from agents.sentiment_agent import sentiment_analysis_node
from agents.supervisor_agent import supervisor_node
from services.market_data_service import MarketDataService
from services.fundamentals_service import FundamentalsService
from services.news_service import NewsService
import asyncio
import json
from config import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from services.entity_resolution_service import EntityResolutionService
from agents.portfolio_agent import run_portfolio_qa
from agents.chat_agent import run_general_chat

# --- Data Gathering Node ---
def gather_data_node(state: AnalysisState) -> dict:
    """
    First node in the graph.
    Fetches all required data from external APIs in parallel (where possible)
    to populate the state for downstream agents.
    """
    ticker = state["ticker"]
    
    # We can run these synchronously for now, or use asyncio.gather if services were async.
    # Since services use blocking requests, we'll just call them sequentially here
    # or wrap them in threads if performance becomes an issue. 
    # For Phase 4 prototype, sequential is fine as they are fast/cached.
    
    prices = MarketDataService.get_price_history(ticker)
    # V4: Deep Technical Metrics
    tech_indicators = MarketDataService.compute_technical_indicators(prices)
    stock_info = MarketDataService.get_stock_info(ticker)
    
    fundamentals = FundamentalsService.get_fundamentals(ticker)
    
    news_svc = NewsService()
    news = news_svc.get_company_news(ticker)
    sentiment = news_svc.get_sentiment_score(ticker)
    
    return {
        "price_data": tech_indicators, # Legacy support (aliased)
        "technical_indicators": tech_indicators, # New V4 field
        "stock_info": stock_info,
        "fundamentals": fundamentals,
        "news_articles": news,
        "sentiment_scores": sentiment,
        "messages": [f"Data gathered for {ticker}"],
    }

# --- Graph Construction ---

def build_analysis_graph():
    """Construct the LangGraph workflow."""
    workflow = StateGraph(AnalysisState)

    # Add nodes
    workflow.add_node("gather_data", gather_data_node)
    workflow.add_node("technical_analysis", technical_analysis_node)
    workflow.add_node("fundamental_analysis", fundamental_analysis_node)
    workflow.add_node("sentiment_analysis", sentiment_analysis_node)
    workflow.add_node("supervisor", supervisor_node)

    # Edges
    # 1. Start -> Gather Data
    workflow.add_edge(START, "gather_data")
    
    # 2. Gather Data -> Fan out to 3 agents
    workflow.add_edge("gather_data", "technical_analysis")
    workflow.add_edge("gather_data", "fundamental_analysis")
    workflow.add_edge("gather_data", "sentiment_analysis")
    
    # 3. Agents -> Supervisor (Fan in)
    workflow.add_edge("technical_analysis", "supervisor")
    workflow.add_edge("fundamental_analysis", "supervisor")
    workflow.add_edge("sentiment_analysis", "supervisor")
    
    # 4. Supervisor -> End
    workflow.add_edge("supervisor", END)

    return workflow.compile()

# Compile once at module level
analysis_graph = build_analysis_graph()

async def run_analysis(
    query: str,
    ticker: str | None,
    portfolio_context: list,
    conversation_history: list,
    trace_id: str | None = None,
) -> dict:
    """
    Entry point called by the /api/analyze endpoint.
    Routes based on intent:
    - TICKER_ANALYSIS -> Orchestrator Graph
    - PORTFOLIO_QA -> Portfolio RAG/LLM
    - GENERIC_CHAT -> Conversational Fallback
    """
    # 1. Resolve Entity & Intent
    resolution = await EntityResolutionService.resolve(query, portfolio_context)
    intent = resolution["intent"]
    ticker = resolution["ticker"]
    
    # Override if ticker was explicitly provided in request (unlikely but possible)
    if not ticker and resolution["ticker"]:
        ticker = resolution["ticker"]

    # 2. Routing
    if intent in ["PORTFOLIO_QA", "HOLDINGS_LOOKUP"]:
        return await run_portfolio_qa(query, portfolio_context, conversation_history)
    
    if intent == "GENERIC_CHAT" or not ticker:
        return await run_general_chat(query, portfolio_context, conversation_history)

    # 3. TICKER_ANALYSIS -> Run Graph

    # Prepare context for supervisor
    conversation_context = ""
    if conversation_history:
        recent = conversation_history[-10:]
        lines = [f"{m.role.title()}: {m.content}" for m in recent]
        conversation_context = "\n".join(lines)

    initial_state = {
        "ticker": ticker.upper(),
        "query": query + (f"\n\n[Prior conversation context]\n{conversation_context}" if conversation_context else ""),
        "portfolio_context": portfolio_context,
        "trace_id": trace_id,
        "intent": intent,
        "entity_resolution": resolution,
        "price_data": {},
        "fundamentals": {},
        "news_articles": [],
        "sentiment_scores": {},
        "stock_info": {},
        "technical_report": "",
        "fundamental_report": "",
        "sentiment_report": "",
        "recommendation": "",
        "confidence": "",
        "price_target": "",
        "synthesis": "",
        "risks": [],
        "catalysts": [],
        "messages": [],
        "errors": [],
        # V3 Fields
        "decision": None,
        "timings": {},
    }

    # Execute graph
    result = await analysis_graph.ainvoke(initial_state)

    return {
        "ticker": result["ticker"],
        "recommendation": result["recommendation"],
        "confidence": result["confidence"],
        "price_target": result["price_target"],
        "synthesis": result["synthesis"],
        "risks": result["risks"],
        "catalysts": result["catalysts"],
        "technical_report": result["technical_report"],
        "fundamental_report": result["fundamental_report"],
        "sentiment_report": result["sentiment_report"],
        "stock_info": result["stock_info"],
        "errors": result.get("errors", []),
        # V3 Fields
        "decision": result.get("decision"),
        "trace_id": result.get("trace_id"),
        "timings": result.get("timings"),
    }

# --- Helpers ---

# --- Helpers ---

# helper functions removed as they are now in separate agents

async def run_analysis_stream(
    query: str,
    ticker: str | None,
    portfolio_context: list,
    trace_id: str,
    conversation_history: list
):
    """
    Generator for SSE events.
    Runs the graph and emits events for each node completion.
    """
    import json
    
    # 1. Resolve Intent/Ticker (reusing logic from run_analysis would be ideal, but for stream we want early events)
    yield {"event": "status", "data": json.dumps({"status": "resolving_intent"})}
    
    resolution = await EntityResolutionService.resolve(query, portfolio_context)
    intent = resolution["intent"]
    resolved_ticker = resolution["ticker"]
    
    # Override if ticker was explicitly provided in request
    if not ticker and resolved_ticker:
        ticker = resolved_ticker.upper()

    yield {
        "event": "status", 
        "data": json.dumps({
            "status": "intent_resolved", 
            "intent": intent, 
            "ticker": ticker
        })
    }
    
    # Handle non-analysis intents
    if intent in ["PORTFOLIO_QA", "HOLDINGS_LOOKUP"]:
        result = await run_portfolio_qa(query, portfolio_context, conversation_history)
        yield {"event": "result", "data": json.dumps(result)}
        yield {"event": "done", "data": "[DONE]"}
        return
        
    if intent == "GENERIC_CHAT" or not ticker:
        result = await run_general_chat(query, portfolio_context, conversation_history)
        yield {"event": "result", "data": json.dumps(result)}
        yield {"event": "done", "data": "[DONE]"}
        return

    # Prepare detailed context
    conversation_context = ""
    if conversation_history:
        recent = conversation_history[-10:]
        lines = [f"{m.role.title()}: {m.content}" for m in recent]
        conversation_context = "\n".join(lines)

    # D3: Extract specific Position Context for this ticker
    position_context = {}
    if ticker and portfolio_context:
        # Find exact match
        for holding in portfolio_context:
            if holding.get("symbol") == ticker:
                position_context = holding
                break

    initial_state = {
        "ticker": ticker,
        "query": query + (f"\n\n[Prior conversation context]\n{conversation_context}" if conversation_context else ""),
        "portfolio_context": portfolio_context, # Full portfolio
        "position_context": position_context,   # specific holding info (V3)
        "trace_id": trace_id,
        "intent": intent,
        "entity_resolution": resolution,
        # Initialize other fields
        "price_data": {}, "fundamentals": {}, "news_articles": [], "sentiment_scores": {}, "stock_info": {},
        "technical_report": "", "fundamental_report": "", "sentiment_report": "",
        "recommendation": "", "confidence": "", "price_target": "", "synthesis": "",
        "risks": [], "catalysts": [], "messages": [], "errors": [],
        "decision": None, "timings": {},
    }

    # Stream graph updates
    # We use .astream to get updates from each node
    async for output in analysis_graph.astream(initial_state):
        for node_name, node_state in output.items():
            # Gather Data
            if node_name == "gather_data":
                yield {"event": "status", "data": json.dumps({"status": "data_gathered"})}
                
            # Agent completions
            elif node_name == "technical_analysis":
                yield {"event": "partial", "data": json.dumps({"type": "technical", "content": node_state.get("technical_report", "")[:100] + "..."})}
            elif node_name == "fundamental_analysis":
                yield {"event": "partial", "data": json.dumps({"type": "fundamental", "content": node_state.get("fundamental_report", "")[:100] + "..."})}
            elif node_name == "sentiment_analysis":
                yield {"event": "partial", "data": json.dumps({"type": "sentiment", "content": node_state.get("sentiment_report", "")[:100] + "..."})}
            
            # Supervisor (Final)
            elif node_name == "supervisor":
                final_result = {
                    "ticker": node_state["ticker"],
                    "recommendation": node_state["recommendation"],
                    "confidence": node_state["confidence"],
                    "price_target": node_state["price_target"],
                    "synthesis": node_state["synthesis"],
                    "risks": node_state["risks"],
                    "catalysts": node_state["catalysts"],
                    "technical_report": node_state["technical_report"],
                    "fundamental_report": node_state["fundamental_report"],
                    "sentiment_report": node_state["sentiment_report"],
                    "stock_info": node_state["stock_info"],
                    "errors": node_state.get("errors", []),
                    "decision": node_state.get("decision"),
                    "trace_id": node_state.get("trace_id"),
                    "timings": node_state.get("timings"),
                }
                yield {"event": "result", "data": json.dumps(final_result)}

    yield {"event": "done", "data": "[DONE]"}
