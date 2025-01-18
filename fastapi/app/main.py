from typing import Optional
from fastapi import FastAPI
from es_connector import ES_connector

app = FastAPI()

es = ES_connector()

total_result_per_page = 10

@app.get("/")
def home():
    return "Bienvenue sur l'API de recherche de dépôts Github"

@app.get("/search")
def search(q: str, page: Optional[int] = 1):
    search_query = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["name", "description", "readme"]
            }
        }
    }
    result = es.get_data("github", search_query, total_result_per_page)
    return result

@app.post("/store/{index_name}")
def store_data(index_name: str, data: dict) -> dict:
    required_fields = ["name", "description", "readme"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    try:
        # Call the ES_connector to index the data
        response = es.index_data(index_name, data)
        return {
            "message": "Document indexed successfully",
            "response": response
        }
    except Exception as e:
        raise Exception(f"Failed to index data: {str(e)}")
