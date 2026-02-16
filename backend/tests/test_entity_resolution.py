import pytest
from services.entity_resolution_service import EntityResolutionService

@pytest.mark.asyncio
async def test_resolve_explicit_ticker():
    """Test $AAPL regex."""
    res = await EntityResolutionService.resolve("Check $AAPL price", [])
    assert res["ticker"] == "AAPL"
    assert res["intent"] == "TICKER_ANALYSIS"
    assert res["method"] == "regex_symbol"

@pytest.mark.asyncio
async def test_resolve_command_pattern():
    """Test 'analyze AAPL' command."""
    res = await EntityResolutionService.resolve("analyze AAPL please", [])
    assert res["ticker"] == "AAPL"
    assert res["intent"] == "TICKER_ANALYSIS"
    assert res["method"] == "regex_command"

@pytest.mark.asyncio
async def test_resolve_static_map():
    """Test 'apple' -> 'AAPL' static map."""
    res = await EntityResolutionService.resolve("what do you think about apple?", [])
    assert res["ticker"] == "AAPL"
    assert res["intent"] == "TICKER_ANALYSIS"
    assert res["method"] == "static_map"

@pytest.mark.asyncio
async def test_resolve_portfolio_match():
    """Test matching ticker from portfolio."""
    portfolio = [{"symbol": "NVDA", "quantity": 10}]
    res = await EntityResolutionService.resolve("should I sell NVDA?", portfolio)
    assert res["ticker"] == "NVDA"
    assert res["intent"] == "TICKER_ANALYSIS"
    assert res["method"] == "portfolio_match"

@pytest.mark.asyncio
async def test_resolve_generic_chat():
    """Test generic chat fallback."""
    res = await EntityResolutionService.resolve("hello, how are you?", [])
    # Should not resolve to a ticker
    assert res["ticker"] is None
    # intent might be GENERIC_CHAT (if LLM is disabled/skipped) or fallback
    assert res["intent"] == "GENERIC_CHAT"
