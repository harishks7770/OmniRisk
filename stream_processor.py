from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType

# 1. Initialize Spark with Delta and Redis connectors, pointing to the Docker Redis container
spark = SparkSession.builder \
    .appName("OmniRisk_Feature_Pipeline") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.redis.host", "redis") \
    .config("spark.redis.port", "6379") \
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0,com.redislabs:spark-redis_2.12:3.1.0") \
    .getOrCreate()

# 2. Define the schema for incoming transactions
schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("merchant_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("event_timestamp", TimestampType(), True),
    StructField("is_fraud", IntegerType(), True)
])

# 3. Read raw stream (Currently monitoring local JSONs. Swap this block for Event Hubs later)
raw_stream = spark.readStream \
    .schema(schema) \
    .json("data/raw_stream")

# 4. Calculate sliding window features
feature_df = raw_stream \
    .withWatermark("event_timestamp", "10 minutes") \
    .groupBy(
    F.window("event_timestamp", "1 hour", "5 minutes"),
    "user_id"
).agg(
    F.count("transaction_id").alias("transaction_count_1h"),
    F.sum("amount").alias("total_spend_1h")
).select(
    "user_id",
    F.col("window.end").alias("event_timestamp"),
    "transaction_count_1h",
    "total_spend_1h"
)


# 5. Define the function to write to both Feature Stores
def write_to_sinks(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    # Offline Sink: Write to Delta Lake (Mapped to your local /data folder via Docker)
    batch_df.write \
        .format("delta") \
        .mode("append") \
        .save("data/delta/user_features_gold")

    # Online Sink: Write to Redis container (Key format: user_features:{user_id})
    batch_df.write \
        .format("org.apache.spark.sql.redis") \
        .option("table", "user_features") \
        .option("key.column", "user_id") \
        .mode("append") \
        .save()


# 6. Start the stream using foreachBatch
query = feature_df.writeStream \
    .foreachBatch(write_to_sinks) \
    .outputMode("update") \
    .option("checkpointLocation", "data/checkpoints/feature_pipeline") \
    .start()

query.awaitTermination()
