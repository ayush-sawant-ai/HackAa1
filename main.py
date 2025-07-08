import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import requests
import google.generativeai as genai
import time


load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://google.serper.dev/search"

def serper_post(endpoint, data):
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    url = f"{BASE_URL}/{endpoint}"
    t0 = time.time()
    resp = requests.post(url, json=data, headers=headers)
    latency = time.time() - t0
    result = resp.json()
    result["_latency_seconds"] = latency
    return result

mcp = FastMCP("Serper MCP Server")


@mcp.tool()
def search_web(query: str, location: str = None, language: str = None, num: int = 10, page: int = 1, autocorrect: bool = True) -> dict:
    """Google Web Search with advanced parameters."""
    data = {"q": query, "num": num, "page": page, "autocorrect": autocorrect}
    if location: data["location"] = location
    if language: data["hl"] = language
    return serper_post("search", data)

@mcp.tool()
def search_news(query: str, location: str = None, language: str = None, num: int = 10) -> dict:
    """Google News Search."""
    data = {"q": query, "num": num}
    if location: data["location"] = location
    if language: data["hl"] = language
    return serper_post("news", data)

@mcp.tool()
def search_images(query: str, num: int = 10) -> dict:
    """Google Image Search."""
    return serper_post("images", {"q": query, "num": num})

@mcp.tool()
def search_videos(query: str, num: int = 10) -> dict:
    """Google Video Search."""
    return serper_post("videos", {"q": query, "num": num})

@mcp.tool()
def search_places(query: str) -> dict:
    """Google Places Search."""
    return serper_post("places", {"q": query})

@mcp.tool()
def search_shopping(query: str) -> dict:
    """Google Shopping Search."""
    return serper_post("shopping", {"q": query})

@mcp.tool()
def search_scholar(query: str) -> dict:
    """Google Scholar Search."""
    return serper_post("scholar", {"q": query})

@mcp.tool()
def search_patent(query: str) -> dict:
    """Google Patents Search."""
    return serper_post("patent", {"q": query})

@mcp.tool()
def search_autocomplete(prefix: str) -> dict:
    """Google Search Autocomplete Suggestions."""
    return serper_post("autocomplete", {"q": prefix})

@mcp.tool()
def extract_structured(query: str) -> dict:
    """Extract knowledge graph, People Also Ask, and related searches from web search."""
    result = serper_post("search", {"q": query})
    return {
        "knowledgeGraph": result.get("knowledgeGraph", {}),
        "peopleAlsoAsk": result.get("peopleAlsoAsk", []),
        "relatedSearches": result.get("relatedSearches", []),
        "organic": result.get("organic", [])
    }

@mcp.tool()
def quick_fact(query: str) -> dict:
    """
     Fact Checker
    """
    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        data = {"q": query, "num": 3}
        resp = requests.post(BASE_URL, json=data, headers=headers, timeout=8)
        resp.raise_for_status()
        result = resp.json()

        # Try featured answer box
        if "answerBox" in result and "answer" in result["answerBox"]:
            return {
                "answer": result["answerBox"]["answer"],
                "source": result["answerBox"].get("source", "featured snippet"),
                "type": "featured_answer"
            }

        # Try knowledge graph
        if "knowledgeGraph" in result and "description" in result["knowledgeGraph"]:
            return {
                "answer": result["knowledgeGraph"]["description"],
                "source": result["knowledgeGraph"].get("website", "knowledge panel"),
                "type": "knowledge_panel"
            }

        # Fallback: first organic result
        organic = result.get("organic", [])
        if organic:
            return {
                "answer": organic[0].get("snippet", "No answer found."),
                "source": organic[0].get("link"),
                "type": "organic"
            }

        return {"error": "No answer found in search results."}
    except Exception as e:
        return {"error": str(e)}

search_count = 0
@mcp.tool()
def get_metrics() -> dict:
    """Return basic usage and performance metrics."""
    global search_count
    search_count+=1
    return {
        "total_searches": search_count,
    }


if __name__ == "__main__":
    mcp.run()
