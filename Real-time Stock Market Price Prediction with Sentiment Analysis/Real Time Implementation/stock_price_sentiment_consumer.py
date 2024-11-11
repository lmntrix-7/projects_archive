# -*- coding: utf-8 -*-

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

# NLTK packages required for Sentiment Analysis
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Basic Packages required
import numpy as np
import pandas as pd
import os
import yfinance as yf
import numpy as np
import requests
import matplotlib.pyplot as plt


spark = SparkSession.builder \
    .appName("Streaming from Kafka") \
    .config("spark.streaming.stopGracefullyOnShutdown", True) \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0') \
    .config("spark.sql.shuffle.partitions", 4) \
    .getOrCreate()


# Make sure to create these topics first
STOCK_NAME_TOPIC = "stock-name-selector"
STOCK_MODEL_TOPIC = "stock-model-output"



url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT'

# tickers is the consumer that reads the stock name and provides ticker to extract data
consumer = KafkaConsumer(
    STOCK_NAME_TOPIC,
    bootstrap_servers = "localhost:9092"
)

while True:
    for message in consumer:
        
        print("Ongoing selected stock reading.. ")
        consumed_message = json.loads(message.value.decode())
        print('consumed_message:',consumed_message)

        
        tickers = consumed_message['stock_name']
        print('ticker:',tickers)
        
        old_date = date.today() - timedelta(days=300)
        
        # api key: UZQ2P4DCQDRODMBQ (Enter API key in the final_url) 
        
        final_url = url + '&tickers=' + tickers + '&time_from=' + (old_date.strftime("%Y%m%d")) + 'T0130&sort=EARLIEST&limit=1000&apikey=UZQ2P4DCQDRODMBQ'

        print(final_url)


        # scrape the news from the given ticker and to the given date
        r = requests.get(final_url)
        data = r.json()
        
        rdd = spark.sparkContext.parallelize([data])

        extracted_data = rdd.flatMap(lambda item: [(feed_item["title"], feed_item["summary"], feed_item["time_published"], feed_item["overall_sentiment_score"]) for feed_item in item["feed"]])

        schema = StructType([
            StructField("title", StringType(), True),
            StructField("summary", StringType(), True),
            StructField("datetime", StringType(), True),
            StructField("given_sentiment_score", DoubleType(), True)
        ])

        # Create DataFrame
        df_sent = spark.createDataFrame(extracted_data, schema)
        df_sent.show(5)
        
                
        tickerData = yf.Ticker(tickers)

        yesterday = date.today() - timedelta(days=1)

        # historical prices for this ticker
        tickerDf = tickerData.history(period='1d', start=old_date, end = yesterday)
        print("Data Collected")
        
        # Convert the Pandas DataFrame to a Spark DataFrame
        sparkDF = spark.createDataFrame(tickerDf.reset_index())
        sparkDF.show(5)

        # Drop the Unnecessary columns
        stock_price_df = sparkDF.select('Date', 'Open', 'High', 'Low', 'Close', 'Volume') 
        stock_price_df = stock_price_df.withColumn("Date_1_pr", to_date(col("Date")))
        
        
        # Convert the date time column to the proper format
        df_sent = df_sent.withColumn("datetime", to_timestamp(col("datetime"), "yyyyMMdd'T'HHmmss"))

        
        df_sent = df_sent.withColumn("Date_1", to_date(col("datetime")))
        

        analyzer = SentimentIntensityAnalyzer()

        # Define a UDF (User Defined Function) to apply NLTK sentiment analysis
        def analyze_sentiment(text):
            sentiment = analyzer.polarity_scores(text)
            return sentiment['compound']

        # Register the UDF
        analyze_sentiment_udf = udf(analyze_sentiment, StringType())

        # Apply sentiment analysis to the 'text' column and store the result in a new column 'sentiment_score'
        df_1 = df_sent.withColumn("sentiment_score_title", analyze_sentiment_udf(df_sent["title"]))

        print("Calculating sentiment score..")

        
        df_1 = df_1.withColumn('sentiment_title', F.when(F.col("sentiment_score_title") >= 0.05, 'positive')
                           .when(F.col('sentiment_score_title') <= -0.05, 'negative')
                           .when(F.col('sentiment_score_title') == 0, 'neutral'))

        df_1 = df_1.select('Date_1','sentiment_score_title')
        
        final_sentiment_score_df = df_1.groupBy('Date_1').agg(F.avg('sentiment_score_title').alias('Avg_sentiment_score'))

        joined_df = stock_price_df.join(final_sentiment_score_df, stock_price_df['Date_1_pr'] == final_sentiment_score_df['Date_1'], how = 'left')

        joined_df_1 = joined_df.select('Date_1_pr', 'Close', 'Avg_sentiment_score').orderBy('Date_1_pr')
        joined_df_1 = joined_df_1.withColumnRenamed("Date_1_pr", "Date")
        joined_df_1 = joined_df_1.withColumn("Stock", F.lit(tickers))
        
        joined_df_1.show(5)
        
        # Producer - write the sentiment scores of different dates
        producer = KafkaProducer(
            bootstrap_servers = "localhost:9092"
        )

        print("sending data to Kafka..")

        df_json = joined_df_1.toPandas().to_json(orient="records")


        # Sending the JSON string via Kafka producer
        producer.send(STOCK_MODEL_TOPIC, json.dumps(df_json).encode("utf-8"))

