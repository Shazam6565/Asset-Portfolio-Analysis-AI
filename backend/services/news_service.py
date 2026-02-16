import finnhub
import requests
from config import settings
from datetime import datetime, timedelta
from services.rate_limiter import rate_limiter
from services.cache import data_cache
from typing import List, Dict, Any

class NewsService:
    """Aggregates news and sentiment from multiple sources."""

    def __init__(self):
        self.finnhub_client = finnhub.Client(api_key=settings.finnhub_api_key) if settings.finnhub_api_key else None

    def get_company_news(self, ticker: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch recent news articles for a ticker. Respects rate limits, uses cache."""
        cache_key = f"news:{ticker}:{days_back}"
        cached = data_cache.get(cache_key)
        if cached is not None:
            return cached

        articles = []

        # Finnhub news
        if self.finnhub_client and rate_limiter.can_call("finnhub"):
            try:
                rate_limiter.record_call("finnhub")
                from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
                to_date = datetime.now().strftime("%Y-%m-%d")
                finnhub_news = self.finnhub_client.company_news(ticker, _from=from_date, to=to_date)
                for article in finnhub_news[:15]:  # Cap at 15
                    articles.append({
                        "source": article.get("source", ""),
                        "headline": article.get("headline", ""),
                        "summary": article.get("summary", ""),
                        "datetime": article.get("datetime", 0),
                        "url": article.get("url", ""),
                        "provider": "finnhub"
                    })
            except Exception as e:
                print(f"Finnhub news error: {e}")

        # NewsAPI (check rate limit before calling)
        if settings.newsapi_api_key and rate_limiter.can_call("newsapi"):
            try:
                rate_limiter.record_call("newsapi")
                resp = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": ticker,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 10,
                        "apiKey": settings.newsapi_api_key,
                    },
                    timeout=10,
                )
                if resp.ok:
                    for article in resp.json().get("articles", []):
                        articles.append({
                            "source": article.get("source", {}).get("name", ""),
                            "headline": article.get("title", ""),
                            "summary": article.get("description", ""),
                            "datetime": article.get("publishedAt", ""),
                            "url": article.get("url", ""),
                            "provider": "newsapi"
                        })
            except Exception as e:
                print(f"NewsAPI error: {e}")

        # Deduplicate articles
        unique_articles = []
        seen_headlines = set()

        for article in articles:
            # Normalize headline for dedup: lowercase, alphanumeric only, first 30 chars
            import re
            headline = article.get("headline", "")
            if not headline:
                continue
                
            # Create a simple hash/fingerprint
            normalized = re.sub(r'[^a-z0-9]', '', headline.lower())[:30]
            
            # Also consider date to avoid deduping same headline from different days (unlikely but possible)
            # But usually same headline = same news.
            if normalized not in seen_headlines:
                seen_headlines.add(normalized)
                unique_articles.append(article)
        
        data_cache.set(cache_key, unique_articles)
        return unique_articles

    def get_sentiment_score(self, ticker: str) -> Dict[str, Any]:
        """Get aggregate sentiment from Finnhub. Cached, rate-limited."""
        cache_key = f"sentiment:{ticker}"
        cached = data_cache.get(cache_key)
        if cached is not None:
            return cached
            
        if not self.finnhub_client or not rate_limiter.can_call("finnhub"):
            return {"score": None, "buzz": None}
            
        try:
            rate_limiter.record_call("finnhub")
            data = self.finnhub_client.news_sentiment(ticker)
            sentiment = data.get("sentiment", {})
            buzz = data.get("buzz", {})
            result = {
                "bullish_percent": sentiment.get("bullishPercent", 0),
                "bearish_percent": sentiment.get("bearishPercent", 0),
                "articles_in_last_week": buzz.get("articlesInLastWeek", 0),
                "weekly_average": buzz.get("weeklyAverage", 0),
                "company_news_score": data.get("companyNewsScore", 0),
                "sector_average_bullish": data.get("sectorAverageBullishPercent", 0),
                "sector_average_news_score": data.get("sectorAverageNewsScore", 0),
            }
            data_cache.set(cache_key, result)
            return result
        except Exception:
            return {"score": None, "buzz": None}
