#!/bin/bash

# wait for kafka using a simple connection check
echo "Waiting for Kafka to be ready..."
while ! nc -z kafka 29092; do 
  sleep 1
done

echo "Creating Kafka topics..."
kafka-topics \
    --bootstrap-server kafka:29092 \
    --create \
    --if-not-exists \
    --topic add_to_es \
    --replication-factor 1 \
    --partitions 2 \
    --config cleanup.policy=delete \
    --config retention.ms=604800000

echo "Successfully created topics:"
kafka-topics --bootstrap-server kafka:29092 --list

echo "Topic details:"
kafka-topics \
    --bootstrap-server kafka:29092 \
    --describe \
    --topic add_to_es