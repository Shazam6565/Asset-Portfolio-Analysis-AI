import requests
import yfinance as yf
from config import settings
from services.cache import data_cache
from services.rate_limiter import rate_limiter
from typing import Dict, Any

class FundamentalsService:
    """Fetches fundamental financial data from FMP and yfinance."""

    @staticmethod
    def get_fundamentals(ticker: str) -> Dict[str, Any]:
        """Aggregate fundamental data from multiple sources."""
        cache_key = f"fundamentals:{ticker}"
        cached = data_cache.get(cache_key)
        if cached is not None:
            return cached

        fundamentals = {}

        try:
            # yfinance fundamentals (always available, no API key)
            stock = yf.Ticker(ticker)
            info = stock.info
            fundamentals["yfinance"] = {
                "revenue": info.get("totalRevenue"),
                "revenue_growth": info.get("revenueGrowth"),
                "gross_margins": info.get("grossMargins"),
                "operating_margins": info.get("operatingMargins"),
                "profit_margins": info.get("profitMargins"),
                "net_income": info.get("netIncomeToCommon"),
                "total_debt": info.get("totalDebt"),
                "total_cash": info.get("totalCash"),
                "free_cash_flow": info.get("freeCashflow"),
                "operating_cash_flow": info.get("operatingCashflow"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                "earnings_growth": info.get("earningsGrowth"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "enterprise_value": info.get("enterpriseValue"),
                "ev_to_ebitda": info.get("enterpriseToEbitda"),
                "market_cap": info.get("marketCap"),
            }
        except Exception as e:
            print(f"yfinance fundamentals error: {e}")
            fundamentals["yfinance"] = {}

        # FMP fundamentals (if API key available — richer data)
        if settings.fmp_api_key and rate_limiter.can_call("fmp"):
            try:
                rate_limiter.record_call("fmp")
                base = "https://financialmodelingprep.com/api/v3"
                params = {"apikey": settings.fmp_api_key}

                # Income statement
                resp = requests.get(f"{base}/income-statement/{ticker}", params={**params, "limit": 4}, timeout=10)
                if resp.ok:
                    fundamentals["income_statements"] = resp.json()[:4]  # Last 4 quarters

                # Key metrics
                resp = requests.get(f"{base}/key-metrics/{ticker}", params={**params, "limit": 1}, timeout=10)
                if resp.ok:
                    data = resp.json()
                    fundamentals["key_metrics"] = data[0] if data else {}

                # Financial ratios
                resp = requests.get(f"{base}/ratios/{ticker}", params={**params, "limit": 1}, timeout=10)
                if resp.ok:
                    data = resp.json()
                    fundamentals["ratios"] = data[0] if data else {}
            except Exception as e:
                 print(f"FMP fundamentals error: {e}")

        data_cache.set(cache_key, fundamentals)
        return fundamentals
