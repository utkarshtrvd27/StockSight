import os
import sys
from datetime import date, datetime
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ETL_Pipeline.bronze.landing2bronze import load_env_file, get_last_ingest_partition, write_to_elt_config
from ETL_Pipeline.silver.bronze2silver_indianstocks import ensure_silver_schema_exists, silver_table_exists, ensure_silver_table_exists

# --- CONFIGURATION SECTION ---
ENV_PATH = PROJECT_ROOT / ".env"
load_env_file(ENV_PATH)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
DB_PROPERTIES = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "driver": "org.postgresql.Driver"
}
# Path to your downloaded PostgreSQL JDBC Driver Jar
JDBC_JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../drivers/postgresql-42.7.13.jar")


def get_data_from_silver(spark: SparkSession, table_name: str, latest_ingest_partition: date):
    if latest_ingest_partition is not None:
        if not isinstance(latest_ingest_partition, date):
            latest_ingest_partition = datetime.strptime(str(latest_ingest_partition), "%Y-%m-%d").date()

        partition_value = latest_ingest_partition.strftime("%Y-%m-%d")
        query = f"""
            SELECT *
            FROM silver.{table_name}
            WHERE "business_date" > '{partition_value}'
        """
    else:
        query = f"SELECT * FROM silver.{table_name}"

    return spark.read \
        .format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", f"({query}) AS silver_data") \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .load()

def get_EMA(spark: SparkSession, df, period: int, group_col =None, target_col: str = "business_date", value_col: str = "closing_price"):    
    if "hash_key" not in df.columns:
        raise ValueError("Input DataFrame must contain a hash_key column for EMA join-back.")
    if value_col not in df.columns:
        raise ValueError(f"Input DataFrame must contain '{value_col}' column for EMA calculation.")

    alpha = 2.0 / (period + 1.0)
    ema_col = f"ema_{period}"

    ordered_rows = df.select("hash_key", group_col, target_col, value_col) \
        .orderBy(group_col, target_col) \
        .collect()

    print(f"Calculating EMA for period {period} with alpha {alpha}. Total rows to process: {len(ordered_rows)}")

    stocks = []
    for row in ordered_rows:   
        if row[group_col] not in stocks:
            stocks.append(row[group_col])

    rows_with_ema = []
    for stock in stocks:
        stock_rows = [row for row in ordered_rows if row[group_col] == stock]
        # print(f"Processing stock: {stock} with {len(stock_rows)} rows.")

        previous_ema = None
        for row in stock_rows:
            current_closing_price = float(row[value_col])

            if previous_ema is None:
                current_ema = current_closing_price
            else:
                current_ema = (alpha * current_closing_price) + ((1 - alpha) * previous_ema)
            previous_ema = current_ema
            
            # print(f"Date: {row[target_col]}, Closing Price: {current_closing_price}, EMA: {current_ema}")

        for row in stock_rows:
            row_with_ema = row.asDict()
            row_with_ema[ema_col] = current_ema
            rows_with_ema.append(row_with_ema)

    ema_schema = df.select("hash_key", group_col, target_col, value_col) \
        .schema.add(StructField(ema_col, DoubleType(), True))

    # ema_df = spark.createDataFrame(rows_with_ema)
    ema_df = spark.createDataFrame(rows_with_ema, schema=ema_schema)
    
    return ema_df, rows_with_ema


def drop_table(layer: str, table_name: str):
    conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {}.{}")
                .format(sql.Identifier(layer), sql.Identifier(table_name))
            )
    finally:
        conn.close()


def insert_into(layer: str, table_name: str, df, rows_with_ema):
    ema_columns = df.columns
    insert_sql = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({})"
    ).format(
        sql.Identifier(layer, table_name),
        sql.SQL(", ").join(sql.Identifier(column) for column in ema_columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in ema_columns),
    )

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            execute_batch(
                cur,
                insert_sql,
                [tuple(row[column] for column in ema_columns) for row in rows_with_ema],
                page_size=1000,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    log_file_path = os.path.abspath("ETL_Pipeline/bronze/conf/log4j2.properties")
    # print("Correct log_path:", log_file_path)
    
    if os.name == 'nt':
        log_file_path = log_file_path.replace("\\", "/")

    os.environ["SPARK_SUBMIT_OPTS"] = f"-Dlog4j2.configurationFile=file:///{log_file_path}"
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    
    spark = SparkSession.builder \
        .appName("Silver ETL") \
        .master("local[1]") \
        .config("spark.jars", JDBC_JAR_PATH) \
        .config("spark.pyspark.python", sys.executable) \
        .config("spark.pyspark.driver.python", sys.executable) \
        .config("spark.executorEnv.PYSPARK_PYTHON", sys.executable) \
        .config("spark.executorEnv.PYSPARK_DRIVER_PYTHON", sys.executable) \
        .getOrCreate()
        
    print("PySpark Session started successfully.\n")
    
    ensure_silver_schema_exists()
    print("Silver schema exists.\n")
    
    # Connect to the silver layer table and read data
    print("Reading data from silver.indianstocks table...")
    
    silver_df = get_data_from_silver(spark, "indianstocks", None)  # Full refresh: fetch all source data
    print("Data read from silver.indianstocks table was successful.")
    print(f"Total new records to write: {silver_df.count()}\n")
    
    print("Creating EMA table")
        
    ema_df, rows_with_ema = get_EMA(
        spark,
        silver_df,
        period=7,
        group_col= "ISIN",
        target_col="business_date",
        value_col="closing_price",
    )

    ema_columns = [column for column in ema_df.columns if column.startswith("ema_")]
    ema_df = ema_df.select("hash_key", *ema_columns)
    
    # Writing into silver.indianstocks_ema table using psycopg2 for better performance
    drop_table("silver", "indianstocks_ema")
    
    ensure_silver_table_exists("indianstocks_ema", ema_df)
    
    insert_into("silver", "indianstocks_ema", ema_df, rows_with_ema)
    
    # ema_df.write \
    #         .mode("overwrite") \
    #         .option("batchsize", 1000) \
    #         .option("numPartitions", 1) \
    #         .jdbc(url=DB_URL, table="silver.indianstocks_ema", properties=DB_PROPERTIES)
    
    print("Data written to silver.indianstocks_ema table successfully.\n")
    
if __name__ == "__main__":
    main()