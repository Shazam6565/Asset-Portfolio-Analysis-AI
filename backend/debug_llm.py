import asyncio
import os
from dotenv import load_dotenv

# Force load .env
load_dotenv()

from config import settings
from langchain_openai import ChatOpenAI
from services.entity_resolution_service import EntityResolutionService

async def test_llm():
    print("Testing direct LLM connection...")
    try:
        llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key)
        resp = await llm.ainvoke("Hello")
        print(f"LLM Response: {resp.content}")
    except Exception as e:
        print(f"LLM Failed: {e}")

async def test_resolution():
    print("\nTesting Entity Resolution Service...")
    try:
        # Test generic query
        res = await EntityResolutionService.resolve("hi there", [])
        print(f"Resolution Result: {res}")
    except Exception as e:
        print(f"Resolution Failed: {e}")

async def main():
    await test_llm()
    await test_resolution()

if __name__ == "__main__":
    asyncio.run(main())
