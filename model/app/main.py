from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
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
def call_llm(prompt: str):
    try:
        return StreamingResponse(your_llm_function(prompt), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LLM response: {str(e)}")

def your_llm_function(prompt: str):
    readme_ex = """
    ## Welcome to The Build a SAAS App with Flask Course!

    *A video course where we build a real world web application with Flask, Celery,
    Redis, PostgreSQL, Stripe and Docker.*

    **Full details on the course can be found here:**  
    [https://buildasaasappwithflask.com](https://buildasaasappwithflask.com/?utm_source=github&utm_medium=bsawf&utm_campaign=readme-top)

    ### Getting started

    You'll need to enable Docker Compose v2 support if you're using Docker
    Desktop. On native Linux without Docker Desktop you can [install it as a plugin
    to Docker](https://docs.docker.com/compose/install/linux/). It's been generally
    available for a while now and is stable. This project uses specific [Docker
    Compose v2
    features](https://nickjanetakis.com/blog/optional-depends-on-with-docker-compose-v2-20-2)
    that only work with Docker Compose v2 2.20.2+.

    ```sh
    cp .env.example .env
    docker compose up --build
    ```

    After everything is up and running, visit http://localhost:8000.

    Did you receive a `depends_on` "Additional property required is not allowed"
    error? Please update to at least Docker Compose v2.20.2+ or Docker Desktop
    4.22.0+.

    Did you receive an error about a port being in use? Chances are it's because
    something on your machine is already running on port 8000. Check out the docs
    in the `.env` file for the `DOCKER_WEB_PORT_FORWARD` variable to fix this.

    Did you receive a permission denied error? Chances are you're running native
    Linux and your `uid:gid` aren't `1000:1000` (you can verify this by running
    `id`). Check out the docs in the `.env` file to customize the `UID` and `GID`
    variables to fix this.

    ### How does this source code differ than what's in the course?

    In the course we build up a 4,000+ line Flask application in 15 stages while
    I'm at your side explaining my thought process along the way. You will get to
    see the source code grow from a single `app.py` file to a large code base that
    spans across dozens of files and folders.

    #### This repo includes up to the 6th stage. By this point in the code base, you'll be introduced to concepts such as:

    - Using Docker to "Dockerize" a multi-service Flask app
    - Using Flask extensions
    - Flask blueprints
    - Jinja templates
    - Working with forms
    - Sending e-mails through Celery
    - Testing and analyzing your code base

    #### The rest of the course covers topics such as:

    - A crash course on Docker and Docker Compose (including multi-stage builds)
    - Going over the application's architecture and tech choices
    - Creating a full blown user management system
    - Creating a custom admin dashboard
    - Logging, middleware and error handling
    - Using Click to create custom CLI commands
    - Accepting recurring credit card payments with Stripe
    - Building up a dice game called "Snake Eyes"
    - Responding with JSON from Flask and creating AJAX requests
    - Processing microtransaction payments with Stripe
    - Dealing with database migrations
    - Converting your app to support multiple languages (i18n)
    - A crash course on Webpack, ES6 JavaScript and SCSS

    **By the time you finish the course, you'll have all the confidence you need to
    build a large web application with Flask**.

    """
    response = ["hello ", "i am a custom LLM ", "i am generating text", " this is the last part of the response","### README START ###", readme_ex, "### README END ###"]
    try:
        for i in range(len(response)):
            time.sleep(1)
            yield response[i]
    except GeneratorExit:
        print("Client disconnected")
   
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