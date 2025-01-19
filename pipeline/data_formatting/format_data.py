import sys
import os
import time
from spark_kafka import create_spark_session, consume_messages, add_to_es_topic

if __name__ == "__main__":
    spark = create_spark_session()
    consume_messages(spark, add_to_es_topic)