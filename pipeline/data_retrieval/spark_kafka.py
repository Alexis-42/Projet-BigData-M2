from kafka import KafkaProducer
import json
import time
import random
import os
from typing import Dict, Any

add_to_es_topic = "add_to_es"

"""Create a Kafka producer with default settings."""
def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers='kafka:29092',
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8')
    )

def send_message(producer: KafkaProducer, topic: str, key: str, message: Dict[str, Any]) -> None:
    """Send a message to a Kafka topic."""
    try:
        future = producer.send(topic, key=key, value=message)
        metadata = future.get(timeout=5)
        print(f"Message sent - Key: {key}, Partition: {metadata.partition}, Offset: {metadata.offset}")
    except Exception as e:
        print(f"Error sending message: {repr(e)}")


def produce_messages(message, topic):
    producer = KafkaProducer(
        bootstrap_servers='kafka:29092',
        api_version=(0,11,5),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8')
    )
    
    unique_ids = ['id1', 'id2', 'id3', 'id4']
    message_counts = {uid: 0 for uid in unique_ids}
    try:
        key = random.choice(unique_ids)
        message_counts[key] += 1
        send_message(producer, topic, key, message)
    except Exception as e:
        print(f"Failed to produce message: {str(e)}")
    finally:
        producer.close()