from pyspark.sql import SparkSession
from kafka import KafkaConsumer
import json

add_to_es_topic = "add_to_es"

def create_spark_session():
    spark = SparkSession.builder \
        .appName("KafkaSpark") \
        .getOrCreate()
    return spark
    
def consume_messages(spark, topic):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers='kafka:29092',
        api_version=(0,11,5),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    for message in consumer:
        process_message(spark, message.value)


def process_message(spark, message):
    print("Processing message: ", message)