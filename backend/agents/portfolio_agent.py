from config import settings
from langchain_openai import ChatOpenAI

async def run_portfolio_qa(query: str, portfolio_context: list, conversation_history: list) -> dict:
    """
    Handle questions specifically about the user's portfolio.
    """
    llm = ChatOpenAI(model=settings.openai_model, temperature=0.2, api_key=settings.openai_api_key)
    
    # Build a rich portfolio summary
    portfolio_summary = "The user has no portfolio data."
    if portfolio_context:
        holdings_lines = []
        total_value = 0.0
        for holding in portfolio_context:
            symbol = holding.get('symbol', 'Unknown')
            qty = holding.get('quantity', 0)
            price = holding.get('price', 0)
            avg_cost = holding.get('average_buy_price', 0)
            equity = holding.get('equity', qty * price)
            pnl = holding.get('unrealized_pnl', (price - avg_cost) * qty if avg_cost else 0)
            pnl_pct = (pnl / (avg_cost * qty)) * 100 if avg_cost and qty else 0
            
            holdings_lines.append(f"- {symbol}: {qty} shares @ ${price:.2f} (Avg: ${avg_cost:.2f}, P&L: ${pnl:.2f} / {pnl_pct:.2f}%)")
            total_value += equity if isinstance(equity, (int, float)) else 0
        
        portfolio_summary = f"""User Portfolio (Total Equity: ~${total_value:,.2f}):
{chr(10).join(holdings_lines)}"""

    system_prompt = f"""You are a Portfolio Analyst specialized in the user's specific holdings.
    
{portfolio_summary}

Answer the user's question mainly using this data. 
If they ask about performance, diversity, or specific positions, use the numbers provided.
Be concise and data-driven."""

    messages = [("system", system_prompt)]
    # Add conversation history
    for m in conversation_history[-4:]:
        role = m.get('role', 'user') if isinstance(m, dict) else m.role
        content = m.get('content', '') if isinstance(m, dict) else m.content
        messages.append((role, content))
    
    messages.append(("user", query))
    
    resp = await llm.ainvoke(messages)
    
    return {
        "ticker": None,
        "synthesis": resp.content,
        "risks": [],
        "catalysts": [],
        "errors": [],
        "decision": None
    }
