from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from es_connector import ES_connector
from models import Repo
import time
import uvicorn
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

load_dotenv()

CLE_API_GITHUB = os.getenv('CLE_API_GITHUB')

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
def call_llm(prompt: str):

    try:
        return StreamingResponse(generate_readme_with_LLM(prompt), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LLM response: {str(e)}")

def generate_readme_with_LLM(input_text: str, model_name: str = "google/flan-t5-large"):
    """
    Generate a README using the given LLM.
    
    Args:
        input_text (str): LLM input string.
        model_name (str): LLM model name to use. Defaults to "google/flan-t5-large".
    
    Returns:
        str: generated README.
    """

        
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    input_text = prepare_input_for_LLM(input_text)

    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=500)
    outputs = model.generate(inputs["input_ids"], max_length=1024, num_beams=5, early_stopping=True)
    generated_readme = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return [generated_readme]

# Exemple structuré de README en Markdown
EXAMPLE_README = """
    # Example Project

    ## Description
    This is a sample project demonstrating best practices for structuring a README file. It includes sections that provide all necessary details to understand and use the project effectively.

    ## Features
    - List of features here
    - Add any additional functionality

    ## Technologies Used
    - Technology 1
    - Technology 2

    ## Installation
    1. Clone the repository:
    ```bash
    git clone https://github.com/username/example-project.git
"""

def prepare_input_for_LLM(user_query,k=5):
    """
    Prepare the input for the LLM to generate a README based on the user query and related README files.

    Args:
        user_query (str): User query.
        readmes (list): List of related README files.
        k (int): Number of related README files to include. Defaults to 5.

    Returns:
        str: Input text for the LLM.
    """
    # Rechercher les documents les plus similaires
    k = 5  # Nombre de documents à récupérer

    top_readmes = search(q = user_query, number_of_result=k)

    # Préparer l'entrée pour le modèle
    input_text = (
        f"Generate a README based on the following topic: {user_query}.\n\n"
        f"Here is an example of a well-structured README on which you can base the structure of your response:\n\n{EXAMPLE_README}\n\n"
        f"Here are some related README files:\n\n" +
        "\n\n".join([f"Repository: {repo['name']}\nREADME:\n{repo['readme']}" for repo in top_readmes]) + "\n\n"
        f"Please generate a complete and formatted README in English for my project based on the example for the structure and followed by the related README files, ready to be copied into a README.md file.\n"
        f"Do not include this prompt in the generated README."
        f"Replace by \\n the line breaks in the generated README."
    )

    return input_text

   
@app.get("/llm_list")
def llm_list():
    return {
        "llms": [
            {"id": "llm1", "name": "LLM 1"},
            {"id": "llm2", "name": "LLM 2"},
            {"id": "llm3", "name": "LLM 3"}
        ]
    }
   
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)