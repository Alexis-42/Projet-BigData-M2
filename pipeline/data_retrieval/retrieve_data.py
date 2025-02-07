from dotenv import load_dotenv
import schedule
import time
import json
import requests
import random
import base64
import sys
import os
from spark_kafka import produce_messages
from langdetect import detect_langs, LangDetectException

load_dotenv("../../.env")

CLE_API_GITHUB = os.getenv("CLE_API_GITHUB")
HEADERS = {"Authorization": f"token {CLE_API_GITHUB}"}

def get_repos():
    url = "https://api.github.com/search/repositories"
    random_letter = chr(random.randint(97, 122))  # Générer une lettre aléatoire entre 'a' et 'z'
    params = {
        "q": random_letter,  # recherche avec une lettre aléatoire
        "order": "desc",
        "per_page": 10, 
        "page": random.randint(1, 100), # page random entre 1 et 100
    }
    response = requests.get(url, headers=HEADERS, params=params)
    data_repos = []
    
    if response.status_code == 200:
        data = response.json()
        repos = data.get("items", [])
        if repos:
            for repo in repos:
                if fetch_and_check_readme(repo):
                    data_repos.append({
                        "name": repo["name"],
                        "description": repo["description"],
                        "readme": repo["readme_content"],
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
        else:
            return f"Erreur: {response.status_code}, {response.text}"

def fetch_and_check_readme(repo):
    readme_url = repo["url"] + "/readme"
    response = requests.get(readme_url, headers=HEADERS)
    readme_is_valid = False
    if response.status_code == 200:
        data = response.json()
        if "content" in data:
            # Décoder le contenu encodé en base64
            content = base64.b64decode(data["content"]).decode("utf-8").strip()
            if (content and len(content) >= 300 and repo["description"]):
                try:
                    lang_prob = get_english_probability(content)
                    # Détecter la langue du contenu
                    if lang_prob >= 0.85:
                        repo["readme_content"] = content
                        readme_is_valid = True
                except LangDetectException:
                    # En cas d'erreur de détection de langue, ignorer ce README
                    pass
                else:
                    readme_is_valid = False
    return readme_is_valid

def get_english_probability(text):
    try:
        # Détecter les langues probables avec leurs scores
        lang_probs = detect_langs(text)
        
        # Parcourir les résultats pour trouver l'anglais
        for lang_prob in lang_probs:
            # Extraire la langue et la probabilité
            lang, prob = str(lang_prob).split(':')
            if lang == 'en':
                return float(prob)  # Retourner la probabilité de l'anglais
        
        # Si l'anglais n'est pas trouvé, retourner 0
        return 0.0
    except:
        # En cas d'erreur (texte trop court, etc.), retourner 0
        return 0.0

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