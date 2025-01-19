from kafka import KafkaConsumer
import json
import requests
import sys

add_to_es_topic = "add_to_es"

def create_spark_session():
    spark = SparkSession.builder \
        .appName("KafkaSpark") \
        .getOrCreate()
    return spark
    
def consume_messages(topic):
    print("starting consumer" )
    consumer = KafkaConsumer(
        topic,
        group_id='id1',
        bootstrap_servers='kafka:29092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    for message in consumer:
        process_message(message.value)
        
        consumer.commit()


def process_message(message):
    # send message to api to add to elasticsearch
    if isinstance(message, str):
            message = json.loads(message)
    message = message[0]
    message["readme"] = message["readme"].replace('"', '\\"')
    url_store = "http://fastapi:8000/store/"
    response = requests.post(url_store, json=message)
    if response.status_code == 200:
        print(f"Document {message['name']} indexed successfully")
        print(response.json())
    else:
        print(f"Failed to index document: {response.status_code}")
        print(response.text)