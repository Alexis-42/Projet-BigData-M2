from kafka import KafkaProducer
import json
import time

def create_producer():
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    return producer

def send_message(producer, topic, message):
    producer.send(topic, message)
    producer.flush()

if __name__ == "__main__":
    producer = create_producer()
    topic = 'mongo_topic'

    while True:
        message = {
            'data': 'Sample data to be stored in MongoDB',
            'timestamp': time.time()
        }
        send_message(producer, topic, message)
        print(f"Sent: {message}")
        time.sleep(5)
