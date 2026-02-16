from massive import RESTClient
import os
from datetime import date, timedelta, datetime

# Initialize client (picks up MASSIVE_API_KEY env var)
# Ensure API key is available
api_key = os.getenv("MASSIVE_API_KEY")
if not api_key:
    # Try to get from config if loaded, but this is a standalone tool script
    # For now, we rely on env var or let RESTClient fail if it handles it
    pass

client = RESTClient(api_key=api_key) if api_key else RESTClient()

def get_stock_aggregates(ticker: str, days_back: int = 30):
    """
    Fetches daily stock aggregates (bars) for a given ticker.
    Useful for analyzing price trends over time.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)
    
    aggs = []
    # Fetch daily bars
    try:
        for a in client.list_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=start_date.strftime("%Y-%m-%d"),
            to=end_date.strftime("%Y-%m-%d"),
            limit=50000
        ):
            aggs.append({
                "date": datetime.fromtimestamp(a.timestamp / 1000).strftime('%Y-%m-%d'),
                "open": a.open,
                "high": a.high,
                "low": a.low,
                "close": a.close,
                "volume": a.volume
            })
    except Exception as e:
        print(f"Error fetching aggregates for {ticker}: {e}")
        return []
    
    return aggs

def get_current_price(ticker: str):
    """
    Fetches the latest trade price for a ticker.
    """
    try:
        trade = client.get_last_trade(ticker=ticker)
        return {
            "ticker": ticker,
            "price": trade.price,
            "size": trade.size,
            "timestamp": trade.sip_timestamp
        }
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None
