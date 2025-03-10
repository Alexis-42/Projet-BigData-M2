FROM python:3.10-slim

WORKDIR /app

COPY model/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update
RUN apt-get install -y git

COPY ./model/app /app
COPY common /app/common

CMD sh -c "mlflow server --host 0.0.0.0 --port 5001 --backend-store-uri file:/mlflow --default-artifact-root file:/mlflow & uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4"