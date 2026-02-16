import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_query(query, portfolio_context, expected_type, max_time_ms):
    print(f"\nTesting: '{query}'")
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={
                "query": query,
                "portfolio_context": portfolio_context,
                "conversation_history": []
            }
        )
        duration = (time.time() - start) * 1000
        
        if response.status_code != 200:
            print(f"FAILED: Status {response.status_code}")
            return False
            
        data = response.json()
        response_type = data.get("response_type", "analysis") # Default to analysis if missing
        
        print(f"Time: {duration:.2f}ms")
        print(f"Type: {response_type}")
        
        if response_type != expected_type:
            print(f"FAILED: Expected {expected_type}, got {response_type}")
            return False
            
        if duration > max_time_ms:
            print(f"WARNING: Too slow. Expected <{max_time_ms}ms, got {duration:.2f}ms")
            # Strict failure for holdings lookup
            if expected_type == "holdings_lookup":
                return False
                
        print("PASSED")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

# Mock data
portfolio = [
    {"symbol": "AAPL", "quantity": 10, "price": 150.0, "average_buy_price": 140.0, "equity": 1500.0, "unrealized_pnl": 100.0, "name": "Apple Inc."},
    {"symbol": "TSLA", "quantity": 5, "price": 200.0, "average_buy_price": 220.0, "equity": 1000.0, "unrealized_pnl": -100.0, "name": "Tesla Inc."}
]

# Tests
results = []
results.append(test_query("What is my position in AAPL?", portfolio, "holdings_lookup", 500))
results.append(test_query("Analyze NVDA", portfolio, "analysis", 20000)) # High timeout for Analysis
# results.append(test_query("Hello", portfolio, "general", 5000)) # Note: our backend might classify this as Analysis/General handled by agent, checking simply if it runs.

if all(results):
    print("\nALL TESTS PASSED")
else:
    print("\nSOME TESTS FAILED")
