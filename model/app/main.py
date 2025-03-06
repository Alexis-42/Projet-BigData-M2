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
            # Repo(
            #     id=hit["_id"],
            #     name=hit["_source"]["name"],
            #     description=hit["_source"]["description"],
            #     readme=hit["_source"]["readme"]
            # )
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

    
"""
    This function generates a README using the LLM model.
"""
def generate_readme_with_LLM(search_query: str, params : RagParams):
    try:
        top_readmes = search(q=search_query, params=params)

        # Préparer l'entrée pour le modèle
        input_text = (
            f"Generate a simple and effective README for a project about: {search_query}.\n\n"
            f"The README should be well-structured, concise, and include the following sections:\n"
            f"1. **Project Title**: A clear and descriptive title.\n"
            f"2. **Description**: A brief overview of the project, its purpose, and its main features.\n"
            f"3. **Installation**: Step-by-step instructions to install and set up the project.\n"
            f"4. **Usage**: Examples and instructions on how to use the project.\n"
            f"5. **Contributing**: Guidelines for contributing to the project.\n"
            f"6. **License**: Information about the project's license.\n\n"
            f"Here is an example of a well-structured README:\n\n{EXAMPLE_README}\n\n"
            f"Here are some related README files for inspiration:\n\n" +
            "\n\n".join([f"Repository: {repo.name}\nREADME:\n{repo.cleaned_readme}" for repo in top_readmes]) + "\n\n"
            f"Please generate a README in English for my project based on the structure above. "
            f"Ensure the content is clear, concise, and ready to be copied into a README.md file.\n"
            f"Do not include this prompt in the generated README."
        )
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)

        # Générer la réponse en streaming
        output_token_ids = llm_model.generate(
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
        print(f"Output lenth: {len(output_token_ids)} = {output_token_ids}")
        for token_id in output_token_ids:
            # Décoder le token généré
            token = tokenizer.decode(token_id, skip_special_tokens=True)
            print("Token",token)
            yield token

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