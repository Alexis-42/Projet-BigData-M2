from dotenv import load_dotenv
import schedule
import time
import json
import requests
import random
import base64
import sys
import os
from spark_kafka import produce_messages, add_to_es_topic

load_dotenv("../../.env")

CLE_API_GITHUB = os.getenv("CLE_API_GITHUB")
HEADERS = {"Authorization": f"token {CLE_API_GITHUB}"}

def get_repos():
    # Recherche générale avec le mot "a" (ou autre lettre)
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "a", # recherche avec la lettre "a"
        "order": "desc",
        "per_page": 5, 
        "page": random.randint(1, 100), # page random entre 1 et 100
        }  
    response = requests.get(url, headers=HEADERS, params=params)
    data_repos = []
    
    if response.status_code == 200:
        data = response.json()
        repos = data.get("items", [])
        if repos:
            for repo in repos:
                if(fetch_and_check_readme(repo)):
                    data_repos.append({
                        "name": repo["name"],
                        "description": repo["description"],
                        "readme" : repo["readme_content"],
                        "html_url": repo["html_url"]
                    })
            return data_repos
        else:
            return "Aucun dépôt trouvé."
    else:
        if response.status_code == 401:
            return f"Erreur: Clé API invalide. {CLE_API_GITHUB}"
        if response.status_code == 403:
            print("Taux limite atteint. Attente de 10 secondes pour une autre tentative ...")
            time.sleep(2)
            return get_repos()
        else :
            return f"Erreur: {response.status_code}, {response.text}"

def fetch_and_check_readme(repo):
    readme_url = repo["url"] + "/readme"
    response = requests.get(readme_url, headers=HEADERS)
    readme_is_present = False
    if response.status_code == 200:
        data = response.json()
        if "content" in data:
            # Décoder le contenu encodé en base64
            content = base64.b64decode(data["content"]).decode("utf-8").strip()
            if content:  # Vérifier que le README n'est pas vide
                repo["readme_content"] = content
                readme_is_present = True
    return readme_is_present

def find_and_send_repos():
    print("Recherche de dépôts ...")
    repo = get_repos()
    print(f'Recherche terminée, {len(repo)} dépôts trouvés')
    while type(repo) is str:
        print(f'erreur : repo est un string {repo}')
        repo = get_repos()
    for r in repo:
        print(f"Envoi du repo {r['name']} à Kafka")
        produce_messages(json.dumps(r, indent=4), 'add_to_es')

if __name__ == "__main__":
    print("Lancement du programme de récupération des dépôts ...")
    schedule.every(20).seconds.do(find_and_send_repos)
    while True:
        schedule.run_pending()
        time.sleep(5)
