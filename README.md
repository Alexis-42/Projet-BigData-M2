# BigData / MLOps Project: README Generation System

## Description
Ce projet implémente un système de génération de fichiers README automatisé à l'aide de modèles de langage (LLM) et d'un mécanisme de retrieval-augmented generation (RAG). Le système s'appuie sur une base de données Elasticsearch pour la récupération de données pertinentes et utilise un frontend développé en Flask, une API FastAPI pour la gestion des requêtes, et un modèle de machine learning pour la génération des README. L'ensemble de l'application est déployé avec Docker.

## Architecture du projet
L'architecture du projet est composée des éléments suivants :
  
  **Elasticsearch** : Base de données utilisée pour stocker et récupérer des informations nécessaires à la génération des README. Elasticsearch facilite la recherche et l'indexation des données.

  **Frontend** (Flask) : Interface utilisateur simple développée en Flask permettant aux utilisateurs de soumettre des requêtes pour générer des README.
  
  **API** (FastAPI) : Service d'API permettant la communication avec le modèle de machine learning. Elle est responsable de la gestion des requêtes liées à la génération des README et à l'interaction avec la base de données Elasticsearch.
  
  **Modèle** (LLM) : Modèle de langage utilisé pour générer des README en fonction des données récupérées via Elasticsearch.

## Installation 
**Cloner le projet**

```
git clone https://github.com/Alexis-42/Projet-BigData-M2.git
```

**Construction et Lancement avec Docker Compose**
Construire les images Docker :
```
docker-compose build
```
Démarrer les services :
```
docker-compose up -d
```
Et voila vous pouvez maintenant acceder aux adresses suivantes :

- localhost:5000 : Frontend
- localhost:8000 : FastApi
- localhost:5001 : MLflow UI
- localhost:5601 : Kibana ( vue de la BDD )

**Prérequis**
- Installer le modèle à ce lien : https://huggingface.co/google/flan-t5-large
et le placer tel que : /model/app/flan-t5-large/

- Vous devez créer un fichier .env à la racine du projet avec les variables suivantes :
  ```
  CLE_API_GITHUB="[mettre clé ici]"
  ELASTICSEARCH_USERNAME=[définir un nom ici]
  ELASTICSEARCH_PASSWORD=[définir un mot de passe ici]
  ```

## Mise en route
Lancer Docker Desktop et saisir dans un terminal à la racine du projet :
docker-compose up -d --build

