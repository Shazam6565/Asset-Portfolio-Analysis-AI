import pytest
from unittest.mock import MagicMock, patch
from models.schemas import SupervisorDecision
from agents.supervisor_agent import supervisor_node
from config import settings
import json

# Sample V3 output
SAMPLE_JSON_OUTPUT = """
{
  "action": "BUY",
  "confidence": "HIGH",
  "price_target": "180.50",
  "time_horizon": "3-6 months",
  "thesis": "Strong technicals and fundamentals align.",
  "risks": ["Market volatility"],
  "catalysts": ["Earnings report"],
  "position_sizing": "5%",
  "key_metrics": [],
  "sources_used": []
}
"""

@pytest.fixture
def mock_state():
    return {
        "ticker": "AAPL",
        "technical_report": "Bullish",
        "fundamental_report": "Strong",
        "sentiment_report": "Positive",
        "query": "analyze AAPL",
        "portfolio_context": [],
    }

def test_supervisor_decision_schema_validation():
    """Test that valid JSON adheres to the Pydantic schema."""
    data = json.loads(SAMPLE_JSON_OUTPUT)
    decision = SupervisorDecision(**data)
    assert decision.action == "BUY"
    assert decision.confidence == "HIGH"

def test_legacy_supervisor_node(mock_state):
    """Test standard legacy path (regex)."""
    settings.ENABLE_STRUCTURED_OUTPUTS = False
    
    with patch("agents.supervisor_agent.ChatOpenAI") as MockLLM:
        mock_instance = MockLLM.return_value
        # Mock invoking the chain
        mock_instance.invoke.return_value.content = """
        ## RECOMMENDATION
        Action: BUY
        Confidence: HIGH
        12-Month Price Target: $150
        
        ## KEY RISKS
        1. Risk A
        
        ## KEY CATALYSTS
        1. Catalyst B
        """
        
        result = supervisor_node(mock_state)
        assert result["recommendation"] == "BUY"
        assert result["confidence"] == "HIGH"
        # Decision should be None in legacy mode
        assert result.get("decision") is None

def test_structured_supervisor_node(mock_state):
    """Test V3 structured path."""
    settings.ENABLE_STRUCTURED_OUTPUTS = True
    
    with patch("agents.supervisor_agent.ChatOpenAI") as MockLLM:
        mock_instance = MockLLM.return_value
        mock_instance.invoke.return_value.content = SAMPLE_JSON_OUTPUT
        
        result = supervisor_node(mock_state)
        
        # Check V3 field
        assert result["decision"] is not None
        assert result["decision"]["action"] == "BUY"
        assert result["decision"]["confidence"] == "HIGH"
        
        # Check backward compatibility fields
        assert result["recommendation"] == "BUY"
        assert result["confidence"] == "HIGH"
        assert result["synthesis"] == "Strong technicals and fundamentals align."
