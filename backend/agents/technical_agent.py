from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AnalysisState
from prompts.technical import TECHNICAL_SYSTEM_PROMPT, TECHNICAL_USER_TEMPLATE
from config import settings

def technical_analysis_node(state: AnalysisState) -> dict:
    """LangGraph node: Technical Analysis Agent."""
    ticker = state["ticker"]
    # Use V4 AnalysisState field
    indicators = state.get("technical_indicators", {})

    # If no data, return empty report
    if not indicators:
        return {
            "technical_report": "Insufficient price data for technical analysis.",
            "messages": [f"Technical analysis skipped for {ticker} — no data"],
        }

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.1,  # Low temp for analytical precision
        api_key=settings.openai_api_key,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", TECHNICAL_SYSTEM_PROMPT),
        ("human", TECHNICAL_USER_TEMPLATE),
    ])

    chain = prompt | llm
    
    # Safely get values with defaults (Updated keys to match MarketDataService V4)
    response = chain.invoke({
        "ticker": ticker,
        "current_price": indicators.get("current_price", "N/A"),
        # Trend
        "adx": indicators.get("adx", "N/A"),
        "ichimoku_conv": indicators.get("ichimoku_conv", "N/A"), 
        "ichimoku_base": indicators.get("ichimoku_base", "N/A"),
        "sma_50": indicators.get("sma_50", "N/A"),
        "sma_200": indicators.get("sma_200", "N/A"),
        # Momentum
        "rsi": indicators.get("rsi", "N/A"),
        "stoch_k": indicators.get("stoch_k", "N/A"),
        "macd": indicators.get("macd", "N/A"),
        "macd_signal": indicators.get("macd_signal", "N/A"),
        "macd_hist": indicators.get("macd_hist", "N/A"),
        # Volatility
        "atr": indicators.get("atr", "N/A"),
        "bb_upper": indicators.get("bb_upper", "N/A"),
        "bb_lower": indicators.get("bb_lower", "N/A"),
        "kc_upper": indicators.get("kc_upper", "N/A"),
        # Volume
        "obv": indicators.get("obv", "N/A"),
        "cmf": indicators.get("cmf", "N/A"),
        # Levels
        "pivot_point": indicators.get("pivot_point", "N/A"),
        "r1": indicators.get("r1", "N/A"),
        "s1": indicators.get("s1", "N/A"),
    })

    return {
        "technical_report": response.content,
        "messages": [f"Technical analysis completed for {ticker}"],
    }
