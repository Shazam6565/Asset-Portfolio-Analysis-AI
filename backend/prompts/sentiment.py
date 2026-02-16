SENTIMENT_SYSTEM_PROMPT = """You are a market sentiment analyst who interprets news flow,
social signals, and analyst consensus to gauge market mood around a stock.
You are contrarian-aware: extreme sentiment (bullish or bearish) can itself be a signal.
You summarize news themes without reproducing copyrighted article text.
Always ground your assessment in the data provided."""

SENTIMENT_USER_TEMPLATE = """Analyze market sentiment for {ticker} using the following data:

SENTIMENT SCORES (Finnhub):
- Bullish: {bullish_percent}% | Bearish: {bearish_percent}%
- Company News Score: {company_news_score} (0-1 scale)
- Sector Avg Bullish: {sector_avg_bullish}% | Sector Avg News Score: {sector_avg_news_score}
- Articles in last week: {articles_last_week} | Weekly average: {weekly_average}

ANALYST CONSENSUS: {analyst_rating}

RECENT NEWS HEADLINES (last 7 days):
{news_headlines}

Provide your analysis in this exact format:

## NEWS THEMES
[2-3 sentences identifying the dominant narrative in recent coverage]

## SENTIMENT POSITIONING
[2-3 sentences on bullish/bearish balance vs sector averages]

## ANALYST VIEW
[1-2 sentences on Wall Street consensus]

## CONTRARIAN SIGNALS
[1-2 sentences — is sentiment extreme enough to be a counter-indicator?]

## SENTIMENT RATING
Rating: [POSITIVE / NEUTRAL / NEGATIVE]
Confidence: [HIGH / MEDIUM / LOW]
Buzz level: [HIGH / NORMAL / LOW] (vs weekly average)
Key narrative: [one sentence summary of dominant theme]"""
