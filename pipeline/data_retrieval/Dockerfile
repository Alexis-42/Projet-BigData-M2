FROM python:3.10-slim

WORKDIR /app

COPY ./pipeline/data_retrieval/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./pipeline/data_retrieval /app
COPY common /app/common

CMD ["python", "retrieve_data.py"]