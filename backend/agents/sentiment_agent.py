from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AnalysisState
from prompts.sentiment import SENTIMENT_SYSTEM_PROMPT, SENTIMENT_USER_TEMPLATE
from config import settings

def sentiment_analysis_node(state: AnalysisState) -> dict:
    """LangGraph node: Market Sentiment Agent."""
    ticker = state["ticker"]
    sentiment = state["sentiment_scores"]
    articles = state["news_articles"]
    stock_info = state["stock_info"]

    if not sentiment and not articles:
        return {
            "sentiment_report": "No sentiment data or news available.",
            "messages": [f"Sentiment analysis skipped for {ticker} — no data"],
        }

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
    )

    # Format headlines
    headlines_text = "No recent headlines available."
    if articles:
        headline_lines = []
        for i, article in enumerate(articles[:15], 1):
            source = article.get("source", "Unknown")
            headline = article.get("headline", "")
            headline_lines.append(f"{i}. [{source}] {headline}")
        headlines_text = "\n".join(headline_lines)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SENTIMENT_SYSTEM_PROMPT),
        ("human", SENTIMENT_USER_TEMPLATE),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "ticker": ticker,
        "bullish_percent": sentiment.get("bullish_percent", "N/A"),
        "bearish_percent": sentiment.get("bearish_percent", "N/A"),
        "company_news_score": sentiment.get("company_news_score", "N/A"),
        "sector_avg_bullish": sentiment.get("sector_average_bullish", "N/A"),
        "sector_avg_news_score": sentiment.get("sector_average_news_score", "N/A"),
        "articles_last_week": sentiment.get("articles_in_last_week", "N/A"),
        "weekly_average": sentiment.get("weekly_average", "N/A"),
        "analyst_rating": stock_info.get("avg_analyst_rating", "N/A"),
        "news_headlines": headlines_text,
    })

    return {
        "sentiment_report": response.content,
        "messages": [f"Sentiment analysis completed for {ticker}"],
    }
