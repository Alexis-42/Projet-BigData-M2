# Projet BigData M2

This project is a multi-container Docker application that includes the following components:

- **MongoDB**: A NoSQL database used to store application data.
- **FastAPI**: A modern web framework for building APIs with Python, which interacts with MongoDB and utilizes Elasticsearch and Kibana for data communication.
- **LLM Model**: A language model that generates README files based on input specifications.
- **Kafka and Spark**: A data pipeline that continuously fills the MongoDB database with data.

## Project Structure

```
my-docker-project
├── fastapi
│   ├── app
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   └── dependencies.py
│   ├── Dockerfile
│   └── requirements.txt
├── model
│   ├── generate_readme.py
│   ├── Dockerfile
│   └── requirements.txt
├── kafka-spark
│   ├── kafka_producer.py
│   ├── spark_consumer.py
│   ├── Dockerfile
│   └── requirements.txt
├── mongo
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd my-docker-project
   ```

2. **Build and run the containers**:
   ```
   docker-compose up --build
   ```

3. **Access the FastAPI application**:
   Open your browser and navigate to `http://localhost:8000`.

4. **Access Kibana**:
   Open your browser and navigate to `http://localhost:5601`.

## Usage

- The FastAPI application provides endpoints to interact with the MongoDB database.
- The LLM model can be invoked to generate README files based on specific inputs.
- Kafka and Spark continuously process data and populate the MongoDB database.

## Architecture

This project utilizes Docker to containerize each component, ensuring isolation and ease of deployment. The services communicate with each other through defined APIs and message queues, allowing for a scalable and maintainable architecture.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.