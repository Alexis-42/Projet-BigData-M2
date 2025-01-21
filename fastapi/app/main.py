from typing import Optional, List
from fastapi import FastAPI, HTTPException
from es_connector import ES_connector
from models import Repo
import time
import uvicorn

app = FastAPI()

es = ES_connector()

default_index_name = "github_repos_data"

@app.get("/")
def home():
    return "Bienvenue sur l'API de recherche des readme de dépôts Github"


"""
    This endpoint retrieves search results from Elasticsearch based on a query string and returns 
    by default one repo but can return a list of repositories if `number_of_result` != 1.
"""
@app.get("/search", response_model=List[Repo])
def search(q: str, number_of_result: Optional[int] = 1):
    search_query = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["name", "description", "readme"]
            }
        }
    }
    raw_results = es.get_data(default_index_name, search_query, number_of_result)
    if(raw_results is None or raw_results["hits"]["total"]["value"] == 0):
        return []
    else:
        repos = [Repo(**hit["_source"]) for hit in raw_results["hits"]["hits"]]
        return repos


"""
    This endpoint stores data in an Elasticsearch index.
"""
@app.post("/store/")
@app.post("/store/{index_name}")
def store_data(data: dict, index_name: Optional[str] = default_index_name) -> dict:
    required_fields = ["name", "description", "readme", "html_url"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    try:
        response = es.index_data(index_name, data)
        return {
            "message": "Document indexed successfully",
            "response": response
        }
    except Exception as e:
        raise Exception(f"Failed to index data: {str(e)}")
   
"""
    This endpoint calls your custom LLM.
"""
@app.post("/call_llm/")
async def call_llm(prompt: str) -> dict:
    try:
        # Replace this with the actual call to your LLM
        response = await your_llm_function(prompt)
        return {
            "message": "LLM response generated successfully",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LLM response: {str(e)}")

async def your_llm_function(prompt: str) -> str:
    # Implement the logic to call your LLM here
    # For example, you might load a model and generate a response based on the prompt
    time.sleep(2)
    return "This is a response from your custom LLM."
   
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)