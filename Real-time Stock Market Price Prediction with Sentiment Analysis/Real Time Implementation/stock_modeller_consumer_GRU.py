# -*- coding: utf-8 -*-
"""stock_modeller_consumer_GRU.ipynb
"""

# read and write back to kafka
from datetime import datetime, date, timedelta
import json
from kafka import KafkaConsumer, KafkaProducer
from pyspark.sql import SparkSession

# Pyspark functions required
import pyspark.sql as sql_f
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.sql.functions import udf, col, to_timestamp, to_date, collect_list, lag, size, lit, date_format, concat, when
from pyspark.sql.functions import from_unixtime, unix_timestamp
from pyspark.sql.window import Window
from pyspark.ml.feature import MinMaxScaler, VectorAssembler
from pyspark.ml.linalg import Vectors

# Basic Packages required
import numpy as np
import pandas as pd
import os
import yfinance as yf
import numpy as np
import requests
import matplotlib.pyplot as plt

import tensorflow as tf
from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, GRU, Dropout
from keras.optimizers import Adam
from keras.layers import LSTM, Dense, Dropout


spark = SparkSession.builder \
    .appName("Streaming from Kafka") \
    .config("spark.streaming.stopGracefullyOnShutdown", True) \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0') \
    .config("spark.sql.shuffle.partitions", 4) \
    .getOrCreate()


# Make sure to create these topics first
STOCK_MODEL_TOPIC = "stock-model-output"
STOCK_PREDICTION_TOPIC = "stock-prediction-output"

# tickers is the consumer that reads the stock name and provides ticker to extract data
consumer = KafkaConsumer(
    STOCK_MODEL_TOPIC,
    bootstrap_servers = "localhost:9092"
)

print("done with reading stock data")


while True:

    for message in consumer:

        consumed_message = json.loads(message.value.decode())

        read_df = pd.read_json(consumed_message)

        print("scaled_df:", read_df.head())

        read_df = spark.createDataFrame(read_df)

        df = read_df
        
        ticker_name = df.limit(1).select('Stock').collect()[0][0]
        
        df = df.withColumn('Date', date_format('Date', 'yyyy-MM-dd'))

        # Create a VectorAssembler to convert 'Close' prices into vector format
        assembler = VectorAssembler(inputCols=["Close"], outputCol="CloseVec")
        vector_df = assembler.transform(df)
        

        # Initialize and fit the MinMaxScaler
        scaler = MinMaxScaler(inputCol="CloseVec", outputCol="ScaledClosePrices")
        scalerModel = scaler.fit(vector_df)
        scaled_df = scalerModel.transform(vector_df)
        
        scaled_df = scaled_df.select('Date', 'Close', 'Avg_sentiment_score', 'CloseVec', 'ScaledClosePrices')

        today = date.today().strftime("%Y-%m-%d")
        new_row = spark.createDataFrame([(today, -1.0, 0.0, Vectors.dense([0]), Vectors.dense([0]))], scaled_df.columns)
        
        scaled_df_1 = scaled_df.union(new_row)
        
        windowSpec = Window.orderBy('Date').rowsBetween(-10, -1)

        # Create a new column 'Prev10ScaledClosePrices' that contains an array of the previous 10 days' 'ScaledClosePrices'
        scaled_df_1 = scaled_df_1.withColumn(
            'Prev10ScaledClosePrices',
            collect_list('ScaledClosePrices').over(windowSpec)
        )

        min_date = scaled_df_1.sort('Date').select('Date').take(10)[-1]['Date']
        scaled_df_1 = scaled_df_1.filter(col('Date') > min_date)
        scaled_df_1.select('Date', 'Prev10ScaledClosePrices').show(5, truncate=False)

       
        scaled_df_1 = scaled_df_1.withColumn("label", col("ScaledClosePrices"))
        # Remove rows with null labels
        scaled_df_1 = scaled_df_1.filter(col("label").isNotNull())

        # Repartition the DataFrame based on the "Date" column
        scaled_df_1 = scaled_df_1.repartition("Date")

        # Calculate the maximum date to determine the last date for the 30 days period
        max_date = scaled_df_1.agg(F.max("Date")).collect()[0][0]
        threshold_date = max_date - F.expr('INTERVAL 1 DAY')

        # Split the dataset into train and test based on the date threshold
        train_df = scaled_df_1.filter(col("Date") <= threshold_date)
        test_df = scaled_df_1.filter(col("Date") > threshold_date)

        train_df = train_df.fillna(0)
        test_df = test_df.fillna(0)

        train_df = train_df.orderBy('Date', ascending=False)
        test_df = test_df.orderBy('Date', ascending=True)

        # Collect features and labels as lists of rows
        train_features = [(np.array(row['Prev10ScaledClosePrices']).flatten(), row['Avg_sentiment_score']) for row in train_df.select('Prev10ScaledClosePrices', 'Avg_sentiment_score').collect()]
        train_labels = [row['label'] for row in train_df.select('label').collect()]
        test_features = [(np.array(row['Prev10ScaledClosePrices']).flatten(), row['Avg_sentiment_score']) for row in test_df.select('Prev10ScaledClosePrices', 'Avg_sentiment_score').collect()]
        test_labels = [row['label'] for row in test_df.select('label').collect()]

        # Convert lists of tuples to NumPy arrays and combine the features into a single array
        # For features, use a list comprehension to unpack the tuples and horizontally stack them using np.hstack()
        x_train = np.array([np.hstack(row) for row in train_features])
        x_test = np.array([np.hstack(row) for row in test_features])

        # Convert labels to NumPy arrays and reshape them to match the input requirements
        y_train = np.array(train_labels).reshape(-1, 1)
        y_test = np.array(test_labels).reshape(-1, 1)

        print("model definition:")

        input_shape = (x_train.shape[1], 1)

        print("GRU MODEL:")

        # Define GRU model within the scope of MirroredStrategy

        strategy = tf.distribute.MirroredStrategy()

        with strategy.scope():
            GRU_model = Sequential([
                GRU(units = 64, return_sequences = True, input_shape = input_shape),
                GRU(units = 64),
                Dense(32, activation='relu'),
                Dropout(0.5),
                Dense(1)
            ])
            GRU_model.compile(optimizer = Adam(), loss = 'mean_squared_error', metrics = ['mae'])

        GRU_model.summary()

        history_GRU = GRU_model.fit(x_train, y_train, epochs=50)

        print("Model predictions:")

        # Make predictions on the training and testing data
        train_predictions_gru = GRU_model.predict(x_train)
        test_predictions_gru = GRU_model.predict(x_test)

        # Convert NumPy arrays to pandas DataFrames
        train_predictions_df_gru = pd.DataFrame(train_predictions_gru, columns=["ScaledPrediction"])
        test_predictions_df_gru = pd.DataFrame(test_predictions_gru, columns=["ScaledPrediction"])


        # Now, `train_predictions_df` and `test_predictions_df` are pandas DataFrames
        # with a single column named "ScaledPrediction"
        
        test_df = test_df.select('Date')
        
        test_pred = spark.createDataFrame(test_predictions_df_gru)
        
        # Add a row index to each DataFrame for joining
        test_df_1 = test_df.withColumn("row_index", F.lit(1))
        test_pred_1 = test_pred.withColumn("row_index", F.lit(1))

        # Perform a join between the two DataFrames based on their row index
        joined_df = test_df_1.crossJoin(test_pred_1)

        # Dropping the row index column as it's no longer needed
        joined_df = joined_df.drop("row_index")
        
        def inverse_transform_scaled_predictions(predictions_df, scaler_model, scaled_col="ScaledPrediction", predicted_col="Prediction"):
            
            # Inversely transforms scaled predictions back to original numerical values using the min and max values stored in the scaler model.
            # Get the original min and max values from the scaler model
            original_min = scaler_model.originalMin.toArray()[0]
            original_max = scaler_model.originalMax.toArray()[0]
            range_val = original_max - original_min

            # Create the expression for inversely transforming the scaled predictions
            inverse_expr = f"{original_min} + ({scaled_col} * {range_val})"

            # Apply the expression to calculate the original predictions
            restored_df = predictions_df.withColumn(
                predicted_col,
                F.expr(inverse_expr)
            )

            # Return the DataFrame with the original predictions, scaled predictions, and date
            return restored_df.select("Date", predicted_col, scaled_col)
        
        final_prediction_value = inverse_transform_scaled_predictions(joined_df, scalerModel)
        
        send_dict = {'Date': final_prediction_value.select('Date').collect()[0][0],
                     'Prediction': final_prediction_value.select('Prediction').collect()[0][0],
                     'Prev_date': train_df.limit(1).select('Date').collect()[0][0],
                     'Close': train_df.limit(1).select('Close').collect()[0][0],
                     'Stock Name': ticker_name
                    }
        
        # Producer - write the final prediction to send for output
        producer = KafkaProducer(
            bootstrap_servers = "localhost:9092"
        )

        print("sending predictions to Kafka..")

        # Sending the JSON string via Kafka producer
        producer.send(STOCK_PREDICTION_TOPIC, json.dumps(send_dict).encode("utf-8"))


        
