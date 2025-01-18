from pyspark.sql import SparkSession
from pyspark.sql.functions import json_tuple
from kafka import KafkaConsumer
import json
import os

def create_spark_session():
    spark = SparkSession.builder \
        .appName("KafkaSparkConsumer") \
        .getOrCreate()
    return spark

def consume_messages(spark):
    consumer = KafkaConsumer(
        'add_to_db',
        bootstrap_servers='kafka:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    for message in consumer:
        process_message(spark, message.value)

def process_message(spark, message):
    # Assuming the message is a JSON object
    df = spark.createDataFrame([message])
    # Here you can add logic to insert the data into MongoDB
    # For example, df.write.format("mongo").mode("append").save("mongodb://mongo:[MONGOPORT]/your_db.your_collection")

if __name__ == "__main__":
    spark = create_spark_session()