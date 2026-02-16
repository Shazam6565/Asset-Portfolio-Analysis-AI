import robin_stocks.robinhood as rh
import builtins
from typing import Optional, List, Dict, Any
from fastapi import HTTPException

class RobinhoodService:
    """Wraps robin_stocks with error handling and session management."""

    _logged_in: bool = False

    @classmethod
    def login(cls, username: str, password: str, mfa_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Authenticate with Robinhood. Returns status dict.
        Monkeypatches builtins.input to detect MFA prompts from robin_stocks.
        """
        original_input = builtins.input

        def mock_input(prompt=None):
            # Check if this is likely the MFA prompt
            if prompt and ("code" in prompt.lower() or "sms" in prompt.lower()):
                raise ValueError("MFA_REQUIRED_SIGNAL")
            return original_input(prompt)

        try:
            # Inject mock input if we don't have an MFA code yet
            if not mfa_code:
                builtins.input = mock_input

            # Note: by_sms=True is removed as per previous fix
            login_data = rh.login(
                username=username,
                password=password,
                expiresIn=86400,
                mfa_code=mfa_code,
            )
            cls._logged_in = True
            return {"status": "success", "message": "Logged in successfully", "data": login_data}

        except ValueError as e:
            if str(e) == "MFA_REQUIRED_SIGNAL":
                return {"status": "mfa_required", "message": "MFA Code sent. Please enter it."}
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            error_msg = str(e)
            if "challenge" in error_msg.lower() or "mfa" in error_msg.lower():
                return {"status": "mfa_required", "message": "MFA challenge started. Check your device."}
            raise HTTPException(status_code=400, detail=error_msg)
        finally:
            # Restore input
            builtins.input = original_input

    @classmethod
    def get_portfolio(cls) -> List[Dict[str, Any]]:
        """
        Fetch stock + crypto holdings.
        Returns list of dicts with keys: symbol, name, price, quantity, value, change, average_buy_price.
        Raises HTTPException(401) if not logged in.
        """
        try:
            # Verify connectivity / login status
            if not rh.account.build_user_profile():
                raise HTTPException(status_code=401, detail="Not logged in")

            portfolio = []

            # Stocks
            my_stocks = rh.build_holdings()
            for symbol, data in my_stocks.items():
                portfolio.append({
                    "symbol": symbol,
                    "name": rh.get_name_by_symbol(symbol),
                    "price": float(data["price"]),
                    "quantity": float(data["quantity"]),
                    "value": float(data["equity"]),
                    "change": float(data["percent_change"]),
                    "average_buy_price": float(data["average_buy_price"]),
                })

            # Crypto
            my_crypto = rh.get_crypto_positions()
            for crypto in my_crypto:
                currency = crypto["currency"]
                qty = float(crypto["quantity"])
                if qty > 0:
                    quote = rh.get_crypto_quote(currency["code"])
                    price = float(quote["mark_price"])
                    portfolio.append({
                        "symbol": currency["code"],
                        "name": currency["name"],
                        "price": price,
                        "quantity": qty,
                        "value": qty * price,
                        "change": 0.0,
                    })

            # Calculate Total Equity for Allocation %
            total_equity = sum(item["value"] for item in portfolio)
            
            # Enrich with calculated fields
            for item in portfolio:
                item["equity"] = item["value"]  # Standardize key
                item["allocation_pct"] = (item["value"] / total_equity * 100) if total_equity > 0 else 0
                
                # Check if we have averages to calc P&L
                if item.get("average_buy_price") and item.get("quantity"):
                    cost_basis = item["average_buy_price"] * item["quantity"]
                    item["unrealized_pnl"] = item["value"] - cost_basis
                    item["unrealized_pnl_pct"] = (item["unrealized_pnl"] / cost_basis * 100) if cost_basis > 0 else 0
                else:
                    item["unrealized_pnl"] = 0.0
                    item["unrealized_pnl_pct"] = 0.0

            return portfolio

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error fetching portfolio: {e}")
            raise HTTPException(status_code=401, detail="Failed to fetch portfolio. Ensure you are logged in.")

    @classmethod
    def execute_trade(cls, symbol: str, action: str, quantity: float, order_type: str = "market") -> Dict[str, Any]:
        """
        Execute a trade. Currently SIMULATED — real execution lines are commented out.
        To enable real trading, uncomment the rh.order_* calls and remove the simulated return.
        """
        try:
            if action == "buy":
                # For real execution, use rh.order_buy_market(symbol, quantity)
                return {"status": "simulated", "message": f"Simulated BUY {quantity} {symbol}"}
            elif action == "sell":
                # For real execution, use rh.order_sell_market(symbol, quantity)
                return {"status": "simulated", "message": f"Simulated SELL {quantity} {symbol}"}
            else:
                raise HTTPException(status_code=400, detail="Invalid action. Must be 'buy' or 'sell'.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._logged_in
