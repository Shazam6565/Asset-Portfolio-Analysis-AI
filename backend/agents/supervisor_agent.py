import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError

from agents.state import AnalysisState
from prompts.supervisor import SUPERVISOR_SYSTEM_PROMPT, SUPERVISOR_USER_TEMPLATE, SUPERVISOR_OUTPUT_FORMAT
from config import settings
from models.schemas import SupervisorDecision

# Add this to allow structured output parsing
def supervisor_node(state: AnalysisState) -> dict:
    return _supervisor_node_sync(state)

def _supervisor_node_sync(state: AnalysisState) -> dict:
    """
    LangGraph node: Supervisor / Synthesis Agent.
    Combines all three agent reports into a final recommendation.
    Parses structured fields from the LLM output.
    """
    ticker = state["ticker"]
    
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
    )

    # Build portfolio summary string
    portfolio_summary = "No portfolio context available."
    portfolio = state.get("portfolio_context", [])
    if portfolio:
        holdings = [f"{h.get('symbol', '?')}: {h.get('quantity', 0)} shares @ ${h.get('price', 0):.2f}" for h in portfolio[:10]]
        portfolio_summary = "\n".join(holdings)

    # If V3 structured outputs are enabled, append the format instructions
    system_prompt = SUPERVISOR_SYSTEM_PROMPT
    if settings.ENABLE_STRUCTURED_OUTPUTS:
        system_prompt += f"\n\n{SUPERVISOR_OUTPUT_FORMAT}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", SUPERVISOR_USER_TEMPLATE),
    ])

    messages = prompt.format_messages(
        ticker=ticker,
        technical_report=state.get("technical_report", "Technical analysis unavailable."),
        fundamental_report=state.get("fundamental_report", "Fundamental analysis unavailable."),
        sentiment_report=state.get("sentiment_report", "Sentiment analysis unavailable."),
        query=state.get("query", ""),
        portfolio_summary=portfolio_summary,
    )

    # --- V3 logic vs Legacy logic ---
    if settings.ENABLE_STRUCTURED_OUTPUTS:
        return _get_structured_decision(llm, messages, state)
    else:
        return _legacy_parse(llm, messages, state)


def _get_structured_decision(llm: ChatOpenAI, messages: list, state: AnalysisState) -> dict:
    """
    V3 Logic: Use structured output or JSON parsing + retry.
    """
    # Attempt 1: Direct JSON parsing from standard generation
    # (We are not using .with_structured_output() yet to keep dependencies simple and robust)
    
    try:
        response = llm.invoke(messages)
        content = response.content
        return _parse_json_result(content, state)
    except Exception as e:
        # Retry with a repair prompt
        repair_messages = messages + [
             SystemMessage(content=f"The previous output was invalid. Error: {str(e)}. "
                                   "Return ONLY the corrected JSON object matching the schema.")
        ]
        try:
            retry_response = llm.invoke(repair_messages)
            return _parse_json_result(retry_response.content, state)
        except Exception as e2:
             # Fallback
             print(f"Supervisor JSON parse failed: {e2}")
             state.setdefault("errors", []).append(f"supervisor_parse_failed: {str(e2)}")
             return _fallback_decision(state)

def _parse_json_result(raw_text: str, state: AnalysisState) -> dict:
    """Parse JSON from LLM output, validate against schema, and return state update dict."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # remove first line (e.g. ```json)
        cleaned = "\n".join(lines[1:])
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)
    decision = SupervisorDecision(**data)
    
    return {
        "decision": decision.model_dump(),
        # Backward compatibility
        "recommendation": decision.action,
        "confidence": decision.confidence,
        "price_target": decision.price_target or "",
        "synthesis": decision.thesis,
        "risks": decision.risks,
        "catalysts": decision.catalysts,
        "messages": [f"Supervisor V3 analysis completed for {state['ticker']}"],
    }

def _fallback_decision(state: AnalysisState) -> dict:
    """Safe fallback if structured output fails completely."""
    return {
        "recommendation": "HOLD",
        "confidence": "LOW",
        "price_target": "",
        "synthesis": "Analysis could not be completed securely. Please try again.",
        "risks": ["Automated analysis failed."],
        "catalysts": [],
        "decision": None,
        "messages": ["Supervisor analysis failed"],
    }


def _legacy_parse(llm: ChatOpenAI, messages: list, state: AnalysisState) -> dict:
    """V2 Logic: Regex parsing."""
    response = llm.invoke(messages)
    synthesis_text = response.content
    
    recommendation = _extract_field(synthesis_text, r"Action:\s*(BUY|HOLD|SELL)", "HOLD")
    confidence = _extract_field(synthesis_text, r"Confidence:\s*(HIGH|MEDIUM|LOW)", "MEDIUM")
    price_target = _extract_field(synthesis_text, r"12-Month Price Target:\s*\$?([\d,.]+)", "")
    if price_target:
        price_target = f"${price_target}"

    risks = _extract_list(synthesis_text, "KEY RISKS")
    catalysts = _extract_list(synthesis_text, "KEY CATALYSTS")

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "price_target": price_target,
        "synthesis": synthesis_text,
        "risks": risks,
        "catalysts": catalysts,
        "messages": [f"Supervisor synthesis completed for {state['ticker']}"],
    }


def _extract_field(text: str, pattern: str, default: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default

def _extract_list(text: str, section_header: str) -> list[str]:
    pattern = rf"##\s*{section_header}(.*?)(?=\n##|\Z)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    block = match.group(1)
    items = re.findall(r"\n\s*\d+\.\s*(.+)", block)
    return [item.strip() for item in items]
