import pytest
from unittest.mock import MagicMock, patch
from services.robinhood_service import RobinhoodService
from services.news_service import NewsService
from services.fundamentals_service import FundamentalsService

@patch("services.robinhood_service.rh")
def test_portfolio_enrichment(mock_rh):
    """Test allocation % and P&L calculations."""
    # Mock rh.account.build_user_profile
    mock_rh.account.build_user_profile.return_value = {"active": True}
    
    # Mock holdings
    mock_rh.build_holdings.return_value = {
        "AAPL": {
            "price": "150.00",
            "quantity": "10.00",
            "equity": "1500.00",
            "percent_change": "1.00",
            "average_buy_price": "100.00"
        },
        "GOOGL": {
            "price": "200.00",
            "quantity": "5.00",
            "equity": "1000.00", # Total = 2500
            "percent_change": "-0.50",
            "average_buy_price": "210.00"
        }
    }
    # Mock crypto
    mock_rh.get_crypto_positions.return_value = []
    mock_rh.get_name_by_symbol.side_effect = lambda s: s

    portfolio = RobinhoodService.get_portfolio()
    
    aapl = next(p for p in portfolio if p["symbol"] == "AAPL")
    googl = next(p for p in portfolio if p["symbol"] == "GOOGL")
    
    # Check allocation (Total 2500)
    assert aapl["allocation_pct"] == 60.0  # 1500/2500
    assert googl["allocation_pct"] == 40.0 # 1000/2500
    
    # Check P&L
    # AAPL: Val 1500, Cost 1000 -> +500
    assert aapl["unrealized_pnl"] == 500.0
    assert aapl["unrealized_pnl_pct"] == 50.0
    
    # GOOGL: Val 1000, Cost 1050 -> -50
    assert googl["unrealized_pnl"] == -50.0
    assert round(googl["unrealized_pnl_pct"], 2) == -4.76


@patch("services.news_service.settings")
@patch("services.news_service.data_cache")
@patch("services.news_service.rate_limiter")
def test_news_deduplication(mock_limiter, mock_cache, mock_settings):
    """Test news deduplication logic."""
    service = NewsService()
    service.finnhub_client = MagicMock()
    
    # Mock Finnhub response with duplicates
    mock_news = [
        {"headline": "Market Crash!", "datetime": 100},
        {"headline": "market crash!", "datetime": 101}, # Duplicate (normalized)
        {"headline": "Market Rebound", "datetime": 102}
    ]
    service.finnhub_client.company_news.return_value = mock_news
    
    # Mock dependencies
    mock_cache.get.return_value = None
    mock_limiter.can_call.return_value = True
    mock_settings.newsapi_api_key = None # Skip NewsAPI
    
    articles = service.get_company_news("AAPL")
    
    headlines = [a["headline"] for a in articles]
    assert len(headlines) == 2
    assert "Market Crash!" in headlines
    assert "Market Rebound" in headlines
    # The duplicate "market crash!" should be filtered out

@patch("services.fundamentals_service.data_cache")
@patch("services.fundamentals_service.yf.Ticker")
def test_fundamentals_caching(mock_ticker, mock_cache):
    """Test caching in FundamentalsService."""
    mock_cache.get.return_value = {"cached": "data"}
    
    result = FundamentalsService.get_fundamentals("AAPL")
    assert result == {"cached": "data"}
    mock_ticker.assert_not_called()
