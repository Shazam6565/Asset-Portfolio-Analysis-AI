import re
import json
from typing import Optional, Tuple, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings
from data.ticker_map import TICKER_MAP

class EntityResolutionService:
    """
    Resolves user queries to:
    1. Intent (TICKER_ANALYSIS, PORTFOLIO_QA, GENERIC_CHAT)
    2. Ticker (if applicable)
    
    Uses a cascade: Regex -> Commands -> Portfolio -> Static Map -> LLM (optional)
    """

    @staticmethod
    async def resolve(query: str, portfolio_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main entry point. Returns a dict with:
        {
            "intent": str,
            "ticker": Optional[str],
            "confidence": float,
            "method": str
        }
        """
        query_upper = query.upper()
        
        # 0. Fast Holdings Lookup (Optimization for <500ms response)
        # Checks for "shares of AAPL", "my position in TSLA", etc.
        holdings_match = EntityResolutionService._match_holdings_lookup(query_upper, portfolio_context)
        if holdings_match:
             return {"intent": "HOLDINGS_LOOKUP", "ticker": holdings_match, "confidence": 1.0, "method": "fast_holdings_match"}

        # 1. Regex (Explicit $TICKER)
        ticker = EntityResolutionService._match_ticker_symbol(query_upper)
        if ticker:
            return {"intent": "TICKER_ANALYSIS", "ticker": ticker, "confidence": 1.0, "method": "regex_symbol"}

        # 2. Command Patterns (e.g., "analyze AAPL")
        ticker = EntityResolutionService._match_command_pattern(query)
        if ticker:
            return {"intent": "TICKER_ANALYSIS", "ticker": ticker, "confidence": 0.9, "method": "regex_command"}

        # 3. Portfolio Match
        if portfolio_context:
            ticker = EntityResolutionService._match_portfolio(query_upper, portfolio_context)
            if ticker:
                 return {"intent": "TICKER_ANALYSIS", "ticker": ticker, "confidence": 0.85, "method": "portfolio_match"}

        # 4. Static Name Map
        ticker = EntityResolutionService._match_static_map(query)
        if ticker:
            return {"intent": "TICKER_ANALYSIS", "ticker": ticker, "confidence": 0.8, "method": "static_map"}

        # 5. LLM Resolution (if enabled)
        if settings.ENABLE_ENTITY_RESOLUTION:
            return await EntityResolutionService._resolve_with_llm(query, portfolio_context)

        # Default fallback
        return {"intent": "GENERIC_CHAT", "ticker": None, "confidence": 0.0, "method": "fallback"}

    @staticmethod
    def _match_ticker_symbol(query_upper: str) -> Optional[str]:
        match = re.search(r"\$([A-Z]{1,5})\b", query_upper)
        return match.group(1) if match else None

    @staticmethod
    def _match_command_pattern(query: str) -> Optional[str]:
        patterns = [
            r"(?:analyze|check|review|news|sentiment|technical|fundamental)\s+(?:for\s+)?([A-Z]{1,5})\b",
            r"(?:what|how|tell)\s+(?:is|about|me)\s+(?:going on with\s+)?([A-Z]{1,5})\b",
            r"([A-Z]{1,5})\s+(?:ticker|stock|analysis|news|sentiment)",
            r"(?:look at|examine|evaluate)\s+([A-Z]{1,5})\b",
        ]
        query_upper = query.upper()
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                potential_ticker = match.group(1).upper()
                if potential_ticker not in {'THE', 'FOR', 'AND', 'THIS', 'THAT', 'WITH', 'FROM', 'WHAT', 'HOW', 'NEWS'}:
                    return potential_ticker
        return None

    @staticmethod
    def _match_portfolio(query_upper: str, portfolio_context: List[Dict]) -> Optional[str]:
        portfolio_tickers = [h.get('symbol', '').upper() for h in portfolio_context if h.get('symbol')]
        for ticker in portfolio_tickers:
            if ticker and ticker in query_upper:
                return ticker
        return None

    @staticmethod
    def _match_static_map(query: str) -> Optional[str]:
        # Normalize query: remove punctuation, lowercase
        normalized = re.sub(r'[^\w\s]', '', query.lower())
        words = normalized.split()
        
        # Check explicit full matches or word matches
        for name, ticker in TICKER_MAP.items():
            if name in normalized:
                # Ensure it's a whole word match or significant phrase
                pattern = rf"\b{re.escape(name)}\b"
                if re.search(pattern, normalized):
                    return ticker
        return None

    @staticmethod
    async def _resolve_with_llm(query: str, portfolio_context: List[Dict]) -> Dict[str, Any]:
        """
        Uses LLM to classify intent and extract ticker.
        """
        llm = ChatOpenAI(model=settings.openai_model, temperature=0, api_key=settings.openai_api_key)
        
        portfolio_tickers = [h.get('symbol', '') for h in portfolio_context]
        
        system_prompt = """You are an intent classifier for a financial assistant.
        Determine user intent from:
        1. TICKER_ANALYSIS: User wants analysis on a specific stock. Extract ticker.
        2. PORTFOLIO_QA: User asks about their OWN portfolio holdings/performance.
        3. GENERIC_CHAT: General market questions or chit-chat.

        Return JSON:
        {
            "intent": "TICKER_ANALYSIS" | "PORTFOLIO_QA" | "GENERIC_CHAT",
            "ticker": "Symbol" or null,
            "confidence": float (0.0-1.0)
        }
        """

        user_prompt = f"Query: {query}\nUser Portfolio Holdings: {portfolio_tickers}"
        
        try:
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            data["method"] = "llm"
            return data
        except Exception as e:
            print(f"LLM resolution failed: {e}")
            return {"intent": "GENERIC_CHAT", "ticker": None, "confidence": 0.0, "method": "llm_failed"}

    @staticmethod
    def _match_holdings_lookup(query_upper: str, portfolio_context: List[Dict]) -> Optional[str]:
        """
        Fast check for specific holdings keywords + portfolio ticker match.
        """
        holdings_keywords = ["POSITION", "HOLDING", "SHARES", "AVG COST", "AVERAGE COST", "OWN", "PRICE OF", "MY PL", "MY P&L"]
        
        if any(k in query_upper for k in holdings_keywords):
            # Check if any portfolio ticker is mentioned
            for holding in portfolio_context:
                symbol = holding.get("symbol", "").upper()
                if symbol and symbol in query_upper:
                    return symbol
        return None
