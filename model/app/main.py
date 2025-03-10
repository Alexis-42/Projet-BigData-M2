from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sentence_transformers import SentenceTransformer
from es_connector import ES_connector
from models import Repo, RagParams, ProjectInfo, ReadmeDatas
from common.text_utils.cleaning import remove_all_tags
import time
import uvicorn
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, TextStreamer
import traceback
from fastapi import HTTPException

# Load model once at startup
tokenizer = AutoTokenizer.from_pretrained("./flan-t5-large")
llm_model = AutoModelForSeq2SeqLM.from_pretrained("./flan-t5-large")


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

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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
    query_vector = embedding_model.encode(q)

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

    raw_results = es.get_data(default_index_name, search_query, params.docCount)

    if raw_results is None or raw_results["hits"]["total"]["value"] == 0:
        return []
    else:
        repos = [
            ReadmeDatas(
                id=hit["_id"],
                name=hit["_source"]["name"],
                cleaned_readme=hit["_source"]["cleaned_readme"],
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
            data["embedding"] = embedding_model.encode(data["cleaned_readme"]).tolist()
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
   
from fastapi import Body

"""
    This endpoint calls your custom LLM.
"""
@app.post("/call_llm/")
def call_llm(
    project_info: ProjectInfo = Body(...), 
    params: RagParams = Body(default=RagParams(docCount=3, similarityThreshold=0.7))
):
    try:
        # Concaténer les informations pour former la requête de recherche
        search_query = f"{project_info.name} {project_info.description} {project_info.technologies}"
        print(f"Search query: {search_query}")
        return StreamingResponse(generate_readme_with_LLM(search_query, params), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LLM response: {str(e)}")

    
def generate_readme_with_LLM(search_query: str, params: RagParams):
    try:
        # Phase 1 - Génération du titre
        title_prompt = (
            f"Corrige et formate ce nom de projet en titre Markdown professionnel : {search_query}.\n"
            f"Ne renvoie que le titre corrigé sans commentaires."
        )
        title_inputs = tokenizer(title_prompt, return_tensors="pt", max_length=128, truncation=True)
        title_output = llm_model.generate(**title_inputs, max_length=30)
        project_title = tokenizer.decode(title_output[0], skip_special_tokens=True).strip()
        print(f"Titre généré : {project_title}")
        yield f"# {project_title}\n\n"

        # Phase 2 - Génération de la description
        desc_prompt = (
            f"Génère une description concise pour le projet '{project_title}' incluant :\n"
            f"- Objectif principal\n- Fonctionnalités clés\n- Public cible\n"
            f"Format : paragraphe unique en Markdown"
        )
        desc_inputs = tokenizer(desc_prompt, return_tensors="pt", max_length=512, truncation=True)

        project_desc = llm_model.generate(**desc_inputs, max_length=300)
        
        print(f"Description générée : {project_desc}")
        yield "## Description\n"
        for token in project_desc:
            yield token.replace("<pad>", "").replace("</s>", "")
        yield "\n\n"

        # Phase 3 - Génération des technologies
        tech_prompt = (
            f"Liste les technologies principales utilisées dans '{project_title}' sous forme de liste Markdown.\n"
            f"Exemple :\n- Python\n- React\n- Docker"
        )
        tech_inputs = tokenizer(tech_prompt, return_tensors="pt", max_length=256, truncation=True)
        tech_output = llm_model.generate(**tech_inputs, max_length=150)
        technologies = tokenizer.decode(tech_output[0], skip_special_tokens=True)
        print(f"Technologies générées : {technologies}")
        yield f"## Technologies\n{technologies}\n\n"

    except GeneratorExit:
        print("Client disconnected")
    except Exception as e:
        print(f"Erreur : {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


   
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