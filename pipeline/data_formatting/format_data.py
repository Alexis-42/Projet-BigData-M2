import sys
import os
import time
from spark_kafka import consume_messages, add_to_es_topic

if __name__ == "__main__":
    print("Starting Spark job" )
    consume_messages(add_to_es_topic)