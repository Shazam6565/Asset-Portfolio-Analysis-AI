from config import settings
from langchain_openai import ChatOpenAI

async def run_general_chat(query: str, portfolio_context: list, conversation_history: list) -> dict:
    """Simple LLM chat when no ticker is involved."""
    llm = ChatOpenAI(model=settings.openai_model, temperature=0.7, api_key=settings.openai_api_key)
    
    system_prompt = """You are Sentinel AI, a helpful financial assistant.
    You can analyze stocks (e.g. "Analyze AAPL") or discuss general market concepts.
    If the user asks for financial advice, remind them you are an educational tool."""
    
    messages = [("system", system_prompt)]
    for m in conversation_history[-6:]:
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
