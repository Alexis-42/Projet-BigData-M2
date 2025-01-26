from kafka import KafkaConsumer
from pyspark.sql import SparkSession
import json
import requests
import sys

add_to_es_topic = "add_to_es"

def create_spark_session():
    """
    The function `create_spark_session` creates a Spark session with the app name "KafkaSpark".
    :return: The function `create_spark_session()` returns a Spark session that is created using the
    SparkSession builder with the application name "KafkaSpark".
    """
    spark = SparkSession.builder \
        .appName("KafkaSpark") \
        .getOrCreate()
    return spark
    
def consume_messages(topic):
    """
    The function `consume_messages` consumes messages from a Kafka topic and processes them using a
    KafkaConsumer.
    
    :param topic: The `topic` parameter in the `consume_messages` function is the name of the Kafka
    topic from which messages will be consumed
    """
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
    """
    The `process_message` function processes a message and send it to an API to add to Elasticsearch
    after formatting the readme field.
    
    :param message: The `process_message` function takes a message as input, processes it, and sends it
    to an API to add to Elasticsearch. The function assumes that the message is a JSON string and
    converts it to a Python dictionary before further processing
    """
    if isinstance(message, str):
            message = json.loads(message)
    
    message["readme"] = format_readme(message["readme"])
    
    url_store = "http://model:8000/store/"
    response = requests.post(url_store, json=message)
    if response.status_code == 200:
        print(f"Document {message['name']} indexed successfully")
        print(response.json())
    else:
        print(f"Failed to index document: {response.status_code}")
        print(response.text)
        
def format_readme(readme):
    """
    The `format_readme` function in Python replaces double quotes with escaped double quotes in a given
    README text.
    
    :param readme: A string containing the content of a README file
    :return: The `format_readme` function is returning the `readme` string with all instances of double
    quotes (`"`) replaced with escaped double quotes (`\"`).
    """
    return readme.replace('"', '\"')