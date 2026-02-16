from services.market_data_service import MarketDataService

def test_invalid_ticker():
    ticker = "APPL" # Invalid
    print(f"Testing {ticker}...")
    try:
        df = MarketDataService.get_price_history(ticker)
        print(f"DF Empty: {df.empty}")
        ind = MarketDataService.compute_indicators(df)
        print(f"Indicators: {ind}")
    except Exception as e:
        print(f"CRASHED: {e}")

if __name__ == "__main__":
    test_invalid_ticker()
