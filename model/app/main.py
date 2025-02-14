from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sentence_transformers import SentenceTransformer
from es_connector import ES_connector
from models import Repo, RagParams, ProjectInfo
from common.text_utils.cleaning import remove_all_tags
import time
import uvicorn
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import traceback
from fastapi import HTTPException

# Load model once at startup
tokenizer = AutoTokenizer.from_pretrained("./flan-t5-large")
model = AutoModelForSeq2SeqLM.from_pretrained("./flan-t5-large")


CLE_API_GITHUB = os.getenv('CLE_API_GITHUB')


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

app = FastAPI()

es = ES_connector()

model = SentenceTransformer('all-MiniLM-L6-v2')

default_index_name = "github_repos_data"

@app.get("/")
def home():
    return "Bienvenue sur l'API de recherche des readme de dépôts Github"


"""
    This endpoint retrieves search results from Elasticsearch based on a query string and returns 
    by default one repo but can return a list of repositories if `number_of_result` != 1.
"""
@app.get("/search", response_model=List[Repo])
def search(q: str, params: RagParams):
    query_vector = model.encode(q)

    search_query = {
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vector.tolist()}
                }
            }
        },
        "size": params.docCount,
    }

    raw_results = es.get_data(default_index_name, search_query, params.docCount, min_score=1.0 + params.similarityThreshold)

    if raw_results is None or raw_results["hits"]["total"]["value"] == 0:
        return []
    else:
        repos = [
            Repo(
                id=hit["_id"],
                name=hit["_source"]["name"],
                description=hit["_source"]["description"],
                readme=hit["_source"]["readme"]
            )
            for hit in raw_results["hits"]["hits"]
        ]
        return repos


"""
    This endpoint stores data in an Elasticsearch index.
"""
@app.post("/store/")
@app.post("/store/{index_name}")
def store_data(data: dict, index_name: Optional[str] = default_index_name) -> dict:
    required_fields = ["name", "description", "readme", "html_url"]
    missing_fields = [field for field in required_fields if field not in data]
    if "readme" in data:
        if not isinstance(data["readme"], str):
            raise HTTPException(status_code=400, detail="Readme must be a string")
        if len(data["readme"]) == 0:
            raise HTTPException(status_code=400, detail="Readme cannot be empty")
    
        data["cleaned_readme"] = remove_all_tags(data["readme"])
        try:
            data["embedding"] = model.encode(data["cleaned_readme"]).tolist()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {e}")
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
def call_llm(project_info: ProjectInfo, params: Optional[RagParams] = RagParams(docCount=3, similarityThreshold=0.7)):
    try:
        # Concaténer les informations pour former la requête de recherche
        search_query = f"{project_info.name} {project_info.description} {project_info.technologies}"
        return StreamingResponse(generate_readme_with_LLM(search_query, params), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LLM response: {str(e)}")
    
"""
    This function generates a README using the LLM model.
"""
def generate_readme_with_LLM(search_query: str, params : RagParams):
    try:
        top_readmes = search(q=search_query, params=params)

        # Préparer l'entrée pour le modèle
        input_text = (
            f"Generate a README based on the following topic: {search_query}.\n\n"
            f"Here is an example of a well-structured README on which you can base the structure of your response:\n\n{EXAMPLE_README}\n\n"
            f"Here are some related README files:\n\n" +
            "\n\n".join([f"Repository: {repo.name}\nREADME:\n{repo.readme}" for repo in top_readmes]) + "\n\n"
            f"Please generate a complete and formatted README in English for my project based on the example for the structure and followed by the related README files, ready to be copied into a README.md file.\n"
            f"Do not include this prompt in the generated README."
            f"Replace by \\n the line breaks in the generated README."
        )
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)

        output_sequences = model.generate(
            input_ids=inputs['input_ids'],
            max_length=512,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            early_stopping=True
        )

        for token_ids in output_sequences:
            token = tokenizer.decode(token_ids, skip_special_tokens=True)
            yield token
            time.sleep(0.1)  # Simuler un délai pour le streaming

    except GeneratorExit:
        print("Client disconnected")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")  # Log de l'exception
        print("Traceback of the exception:")
        traceback.print_exc()  # Affiche un traceback détaillé
        raise HTTPException(status_code=500, detail=f"Failed generate LLM in generate LLM response: {str(e)}")


   
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