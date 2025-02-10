from dotenv import load_dotenv
from readme_utils import remove_all_tags
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
import random
import string


load_dotenv("../../.env")

CLE_API_GITHUB = os.getenv("CLE_API_GITHUB")
HEADERS = {"Authorization": f"token {CLE_API_GITHUB}"}

def get_repos():
    url = "https://api.github.com/search/repositories"
    random_letter = random.choice( string.ascii_lowercase )
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
                if has_non_latin_chars(content):
                    return False
                try:
                    lang_prob = get_english_probability(content)

                    if lang_prob >= 0.90:
                        repo["readme_content"] = content
                        readme_is_valid = True
                except LangDetectException:
                    pass
    return readme_is_valid

def has_non_latin_chars(text, threshold=0.4):
    total = max(len(text), 1)
    non_latin = sum(1 for c in text if ord(c) > 0x7f)
    return (non_latin / total) > threshold

def get_english_probability(text):
    try:
        text = remove_all_tags(text)
        
        lang_probs = detect_langs(text)
        if not lang_probs:
            return 0.0
            
        top_lang = lang_probs[0]
        lang, prob = str(top_lang).split(':')
        
        return float(prob) if lang == 'en' else 0.0
    except Exception:
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