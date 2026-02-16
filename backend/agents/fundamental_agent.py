from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AnalysisState
from prompts.fundamental import FUNDAMENTAL_SYSTEM_PROMPT, FUNDAMENTAL_USER_TEMPLATE
from config import settings

def fundamental_analysis_node(state: AnalysisState) -> dict:
    """LangGraph node: Fundamental Analysis Agent."""
    ticker = state["ticker"]
    fundamentals = state["fundamentals"]
    stock_info = state["stock_info"]

    if not fundamentals:
        return {
            "fundamental_report": "Insufficient fundamental data available.",
            "messages": [f"Fundamental analysis skipped for {ticker} — no data"],
        }

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
    )

    # Extract yfinance fundamentals (our primary fallback)
    yf_data = fundamentals.get("yfinance", {})
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", FUNDAMENTAL_SYSTEM_PROMPT),
        ("human", FUNDAMENTAL_USER_TEMPLATE),
    ])

    chain = prompt | llm

    def fmt(val):
        """Format a value for prompt injection. Returns 'N/A' for None."""
        if val is None:
            return "N/A"
        if isinstance(val, (int, float)) and val > 1_000_000:
            return f"{val:,.0f}"
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    response = chain.invoke({
        "ticker": ticker,
        "company_name": stock_info.get("name", ticker),
        "sector": stock_info.get("sector", "Unknown"),
        "industry": stock_info.get("industry", "Unknown"),
        "gross_margins": fmt(yf_data.get("gross_margins")),
        "operating_margins": fmt(yf_data.get("operating_margins")),
        "profit_margins": fmt(yf_data.get("profit_margins")),
        "return_on_equity": fmt(yf_data.get("return_on_equity")),
        "return_on_assets": fmt(yf_data.get("return_on_assets")),
        "revenue": fmt(yf_data.get("revenue")),
        "revenue_growth": fmt(yf_data.get("revenue_growth")),
        "earnings_growth": fmt(yf_data.get("earnings_growth")),
        "total_debt": fmt(yf_data.get("total_debt")),
        "total_cash": fmt(yf_data.get("total_cash")),
        "debt_to_equity": fmt(yf_data.get("debt_to_equity")),
        "current_ratio": fmt(yf_data.get("current_ratio")),
        "operating_cash_flow": fmt(yf_data.get("operating_cash_flow")),
        "free_cash_flow": fmt(yf_data.get("free_cash_flow")),
        "pe_ratio": fmt(yf_data.get("pe_ratio")),
        "forward_pe": fmt(yf_data.get("forward_pe")),
        "peg_ratio": fmt(yf_data.get("peg_ratio")),
        "price_to_book": fmt(yf_data.get("price_to_book")),
        "price_to_sales": fmt(yf_data.get("price_to_sales")),
        "ev_to_ebitda": fmt(yf_data.get("ev_to_ebitda")),
        "market_cap": fmt(yf_data.get("market_cap") or stock_info.get("market_cap")),
    })

    return {
        "fundamental_report": response.content,
        "messages": [f"Fundamental analysis completed for {ticker}"],
    }
