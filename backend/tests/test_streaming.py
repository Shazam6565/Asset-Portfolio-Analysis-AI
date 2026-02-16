import pytest
import json
from fastapi.testclient import TestClient
from main import app
from services.entity_resolution_service import EntityResolutionService

client = TestClient(app)

# Helper to mock resolution since we don't want real LLM calls in tests
async def mock_resolve(*args, **kwargs):
    return {"intent": "TICKER_ANALYSIS", "ticker": "AAPL", "confidence": 1.0}

@pytest.mark.asyncio
async def test_analyze_stream_structure():
    """
    Test that the /api/analyze/stream endpoint returns
    a valid event stream with the expected event types.
    """
    # Mock entity resolution to avoid external calls
    EntityResolutionService.resolve = mock_resolve
    
    # We can't easily mock the whole graph without complex DI override,
    # but we can check if the stream connects and returns initial status events.
    # Note: This integration test might try to hit real APIs if not fully mocked.
    # For smoke testing, we just want to see the stream format.
    
    with client.stream("GET", "/api/analyze/stream?query=analyze%20AAPL") as response:
        assert response.status_code == 200
        
        events = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                events.append(line.split(": ")[1])
            if len(events) >= 2: # Just check first few events
                break
        
        assert "status" in events

@pytest.mark.asyncio
async def test_analyze_stream_portfolio_qa():
    """Test streaming for Portfolio QA intent (simpler path)."""
    
    # Mock for portfolio intent
    async def mock_resolve_port(*args, **kwargs):
        return {"intent": "PORTFOLIO_QA", "ticker": None}
    
    EntityResolutionService.resolve = mock_resolve_port
    
    with client.stream("GET", "/api/analyze/stream?query=my%20portfolio") as response:
        assert response.status_code == 200
        content = ""
        for line in response.iter_lines():
            content += line + "\n"
        
        assert "event: status" in content
        assert "event: result" in content
        assert "event: done" in content
