FROM python:3.10-slim

WORKDIR /app

COPY model/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./model/app /app
COPY common /app/common

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]