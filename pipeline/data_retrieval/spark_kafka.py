from kafka import KafkaProducer
import json
import os

add_to_es_topic = "add_to_es"

def produce_messages(message, topic):
    producer = KafkaProducer(
        bootstrap_servers='kafka:29092',
        api_version=(0,11,5),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    producer.send(topic, value=message)
    
    producer.flush()
    producer.close()