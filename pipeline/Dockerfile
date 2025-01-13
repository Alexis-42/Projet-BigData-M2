FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY wait-for-it.sh /app/wait-for-it.sh

# Rendre le script exécutable
RUN chmod +x /app/wait-for-it.sh

RUN pip install --no-cache-dir -r requirements.txt

# Définir l'ENTRYPOINT
ENTRYPOINT ["/app/wait-for-it.sh", "kafka:9092", "--"]

COPY . .

CMD ["python", "kafka_producer.py"]