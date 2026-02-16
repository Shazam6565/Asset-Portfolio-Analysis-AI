
import sys
import os

# Add backend to path to allow imports if running as script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from massive import RESTClient

def test_integration():
    print("--- Testing Direct Client ---")
    try:
        # Env var should be picked up from .env if python-dotenv loads it, 
        # but RESTClient might read os.environ directly.
        # We need to load .env first if not running via uvicorn/main
        from dotenv import load_dotenv
        # Explicitly load from backend/.env if not finding it
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env')
        load_dotenv(env_path)
        
        api_key = os.environ.get("MASSIVE_API_KEY")
        print(f"Loaded API Key: {api_key[:4]}...{api_key[-4:] if api_key else ''}")

        client = RESTClient() 
        print("Success: Massive Client initialized")
        
        # This might fail if key is invalid, catch it
        try:
            print("Attempting to fetch AAPL trade...")
            trade = client.get_last_trade("AAPL")
            print(f"Trade: {trade}")
        except Exception as e:
            print(f"Direct Client Call Failed (Expected if key invalid): {e}")

    except Exception as e:
        print(f"Client Init Error: {e}")

    print("\n--- Testing Tool Wrapper ---")
    try:
        from tools.stock_data import get_stock_aggregates, get_current_price
        
        print("Fetching current price via tool...")
        price = get_current_price("AAPL")
        print(f"Tool Price: {price}")
        
        print("Fetching aggregates via tool...")
        aggs = get_stock_aggregates("AAPL", days_back=5)
        print(f"Tool Aggregates (last 5 days): {len(aggs)} records")
        if aggs:
            print(f"Sample: {aggs[0]}")
            
    except Exception as e:
        print(f"Tool Wrapper Error: {e}")

if __name__ == "__main__":
    test_integration()
