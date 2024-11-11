# -*- coding: utf-8 -*-
"""stock_predictions_output.ipynb
"""

# -*- coding: utf-8 -*-

# yfinance installed in requirements
import os
import numpy as np
import pandas as pd

# read and write back to kafka
from datetime import datetime, date, timedelta
import json
from kafka import KafkaConsumer
import requests


# Make sure to create these topics first
STOCK_PREDICTION_TOPIC = "stock-prediction-output"

# tickers is the consumer that reads the stock name and provides ticker to extract data
consumer = KafkaConsumer(
    STOCK_PREDICTION_TOPIC,
    bootstrap_servers = "localhost:9092"
)

while True:
    for message in consumer:

        print("Ongoing selected stock reading.. ")
        consumed_message = json.loads(message.value.decode())
        print('consumed_message:',consumed_message)
        
        stock_name = consumed_message['Stock Name']

        df1_data = {'Date': consumed_message['Date'], 'Predicted Close Price': consumed_message['Prediction']}

        df2_data = {'Previous Date': consumed_message['Prev_date'], 'Close Price': consumed_message['Close']}

        df1 = pd.DataFrame([df1_data])

        df2 = pd.DataFrame([df2_data])

        # Display the DataFrames
        
        print("Stock Name: ", stock_name)
        print("Previous Close Price")
        print(df2)
        
        print("\nPredicted Close Price")
        print(df1)
        
        change = df1_data['Predicted Close Price'] - df2_data['Close Price']
        
        print('Stock Price Increases' if change > 0 else ('Stock Price Decreases' if change < 0 else 'Stock Price remains the same'))
        print()
        print()