# Utilisation de l'image openjdk 11 avec Python intégré
FROM openjdk:11-jre-slim

# Installer Python et pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Installer PySpark
RUN pip3 install pyspark
RUN pip3 install kafka-python==2.0.2
RUN pip3 install requests

# Copier le code Python dans le conteneur
WORKDIR /app
COPY . /app

# Exécuter votre script Python
CMD ["python3", "format_data.py"]