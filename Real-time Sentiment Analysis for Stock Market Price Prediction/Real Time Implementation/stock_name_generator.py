#!/usr/bin/env python
# coding: utf-8

import json
import random
import time
from kafka import KafkaProducer


# Kafka topic
# Make sure to create this topic first
STOCK_NAME_KAFKA_TOPIC = "stock-name-selector"
# Stopping criteria for while (True) loop
ORDER_LIMIT = 1

# Producer class - write to Kafka
producer = KafkaProducer(
    # server where kafka is running
    bootstrap_servers="localhost:9092"
)

print("Generating Stock Name after 3 minutes")


# List of stock names
stock_names = ["TSLA", "AAPL", "MSFT", "AMZN", "GOOG",
                 "NFLX", "META", "TSM", "PG"]

while True:
    # Generate dictionary
    stock = {
        "stock_name": random.choice(stock_names)
    }

    # send data to producer
    producer.send(
        STOCK_NAME_KAFKA_TOPIC,
        #encode the data
        json.dumps(stock).encode("utf-8")
    )
    print(stock)

    time.sleep(240)

