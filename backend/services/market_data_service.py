import yfinance as yf
import pandas as pd
import ta
import datetime
from massive import RESTClient
from config import settings
from services.cache import data_cache
from typing import Dict, Any, Optional

class MarketDataService:
    """
    Fetches market data (Massive.com primary, yfinance fallback)
    and computes professional-grade technical indicators.
    """
    
    _massive_client: Optional[RESTClient] = None

    @classmethod
    def _get_massive_client(cls):
        if cls._massive_client is None and settings.massive_api_key:
            cls._massive_client = RESTClient(settings.massive_api_key)
        return cls._massive_client

    @staticmethod
    def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
        """
        Get OHLCV data.
        Primary: Massive.com (Aggregates)
        Fallback: yfinance
        """
        cache_key = f"price_history:{ticker}:{period}"
        cached = data_cache.get(cache_key)
        if cached is not None:
            return cached

        df = pd.DataFrame()
        
        # 1. Try Massive.com
        client = MarketDataService._get_massive_client()
        if client:
            try:
                # Map period to massive parameters (approximate)
                end_date = datetime.date.today()
                if period == "1y":
                    start_date = end_date - datetime.timedelta(days=365)
                    timespan, multiplier = "day", 1
                elif period == "1mo":
                    start_date = end_date - datetime.timedelta(days=30)
                    timespan, multiplier = "hour", 1
                elif period == "5d":
                     start_date = end_date - datetime.timedelta(days=5)
                     timespan, multiplier = "minute", 30
                else: 
                    # Default to 1y pattern
                    start_date = end_date - datetime.timedelta(days=365)
                    timespan, multiplier = "day", 1

                aggs = []
                # list(client.list_aggs(...)) to consume generator
                for a in client.list_aggs(
                    ticker=ticker,
                    multiplier=multiplier,
                    timespan=timespan,
                    from_=start_date.isoformat(),
                    to=end_date.isoformat(),
                    limit=5000
                ):
                    aggs.append({
                        "Open": a.open,
                        "High": a.high,
                        "Low": a.low,
                        "Close": a.close,
                        "Volume": a.volume,
                        "Date": datetime.datetime.fromtimestamp(a.timestamp / 1000)
                    })
                
                if aggs:
                    df = pd.DataFrame(aggs)
                    df.set_index("Date", inplace=True)
            except Exception as e:
                print(f"[MarketDataService] Massive.com failed: {e}")
                # Fallthrough to yfinance

        # 2. Fallback to yfinance
        if df.empty:
            df = yf.download(ticker, period=period, progress=False, multi_level_index=False)
        
        if not df.empty:
            # Normalize columns just in case
            df.columns = [c.capitalize() for c in df.columns] # Ensure Open, High, Low, Close, Volume
            data_cache.set(cache_key, df)
            
        return df

    @staticmethod
    def compute_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute 'Professional Grade' technical indicators.
        Returns a dictionary matching AnalysisState['technical_indicators'].
        """
        if df.empty or len(df) < 50:
            return {}

        try:
            # Ensure proper types
            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]

            indicators = {}
            
            # --- 1. TREND ---
            # ADX (Strength > 25 = Strong Trend)
            adx_obj = ta.trend.ADXIndicator(high, low, close, window=14)
            indicators["adx"] = float(adx_obj.adx().iloc[-1])
            indicators["adx_pos"] = float(adx_obj.adx_pos().iloc[-1]) # DI+
            indicators["adx_neg"] = float(adx_obj.adx_neg().iloc[-1]) # DI-

            # Ichimoku Cloud
            ichimoku = ta.trend.IchimokuIndicator(high, low, window1=9, window2=26, window3=52)
            indicators["ichimoku_conv"] = float(ichimoku.ichimoku_conversion_line().iloc[-1]) # Tenkan
            indicators["ichimoku_base"] = float(ichimoku.ichimoku_base_line().iloc[-1]) # Kijun
            indicators["ichimoku_span_a"] = float(ichimoku.ichimoku_a().iloc[-1])
            indicators["ichimoku_span_b"] = float(ichimoku.ichimoku_b().iloc[-1])
            
            # EMA Ribbon
            indicators["ema_9"] = float(ta.trend.EMAIndicator(close, window=9).ema_indicator().iloc[-1])
            indicators["ema_21"] = float(ta.trend.EMAIndicator(close, window=21).ema_indicator().iloc[-1])
            indicators["sma_50"] = float(ta.trend.SMAIndicator(close, window=50).sma_indicator().iloc[-1])
            indicators["sma_200"] = float(ta.trend.SMAIndicator(close, window=200).sma_indicator().iloc[-1])

            # --- 2. MOMENTUM ---
            # RSI
            indicators["rsi"] = float(ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1])
            
            # Stochastic RSI
            stoch_rsi = ta.momentum.StochRSIIndicator(close, window=14)
            indicators["stoch_k"] = float(stoch_rsi.stochrsi_k().iloc[-1])
            indicators["stoch_d"] = float(stoch_rsi.stochrsi_d().iloc[-1])
            
            # MACD
            macd = ta.trend.MACD(close)
            indicators["macd"] = float(macd.macd().iloc[-1])
            indicators["macd_signal"] = float(macd.macd_signal().iloc[-1])
            indicators["macd_hist"] = float(macd.macd_diff().iloc[-1])
            
            # Williams %R
            indicators["williams_r"] = float(ta.momentum.WilliamsRIndicator(high, low, close).williams_r().iloc[-1])

            # --- 3. VOLATILITY ---
            # ATR
            indicators["atr"] = float(ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1])
            
            # Keltner Channels (using ATR) vs BB
            bb = ta.volatility.BollingerBands(close)
            indicators["bb_upper"] = float(bb.bollinger_hband().iloc[-1])
            indicators["bb_lower"] = float(bb.bollinger_lband().iloc[-1])
            indicators["bb_width"] = float(bb.bollinger_wband().iloc[-1])
            
            keltner = ta.volatility.KeltnerChannel(high, low, close)
            indicators["kc_upper"] = float(keltner.keltner_channel_hband().iloc[-1])
            indicators["kc_lower"] = float(keltner.keltner_channel_lband().iloc[-1])

            # --- 4. VOLUME ---
            # OBV
            indicators["obv"] = float(ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume().iloc[-1])
            # CMF
            indicators["cmf"] = float(ta.volume.ChaikinMoneyFlowIndicator(high, low, close, volume).chaikin_money_flow().iloc[-1])
            
            # --- 5. LEVELS (Pivot Points - Classic) ---
            # Calculate based on previous day's data (iloc[-2])
            prev_high = float(high.iloc[-2])
            prev_low = float(low.iloc[-2])
            prev_close = float(close.iloc[-2])
            
            pp = (prev_high + prev_low + prev_close) / 3
            indicators["pivot_point"] = pp
            indicators["r1"] = (2 * pp) - prev_low
            indicators["s1"] = (2 * pp) - prev_high
            
            indicators["current_price"] = float(close.iloc[-1])
            
            return indicators

        except Exception as e:
            print(f"[MarketDataService] Indicator computation failed: {e}")
            return {}

    @staticmethod
    def get_stock_info(ticker: str) -> Dict[str, Any]:
        """
        Get basic stock info. 
        Tries Massive Reference API first, fails back to yfinance.
        """
        # Note: Implementing basic yfinance fallback for now to keep it simple, 
        # as FundamentalsService will handle the heavy lifting for stock details.
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "name": info.get("longName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap"),
                "beta": info.get("beta"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
            }
        except Exception:
            return {"name": ticker}
