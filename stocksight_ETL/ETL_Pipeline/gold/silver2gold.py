import os
import sys
from datetime import date, datetime
from pathlib import Path
import psycopg2
from psycopg2 import sql
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, col, coalesce, concat_ws, lit, sha2, max, when, avg

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ETL_Pipeline.bronze.landing2bronze import load_env_file, get_last_ingest_partition, write_to_elt_config
from ETL_Pipeline.silver.bronze2silver_indianstocks import postgres_type
from ETL_Pipeline.silver.silver_indianstocks_ema import get_data_from_silver

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
# JDBC_JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../drivers/postgresql-42.7.13.jar")
JDBC_JAR_PATH = str(PROJECT_ROOT / "drivers" / "postgresql-42.7.13.jar")

def ensure_gold_schema_exists() -> None:
    """Create the gold schema in PostgreSQL if it does not already exist."""
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
            cur.execute("CREATE SCHEMA IF NOT EXISTS gold")
    finally:
        conn.close()


def gold_table_exists(schema_name: str, table_name: str) -> bool:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_name = %s
                )
                """,
                (schema_name, table_name),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def ensure_gold_table_exists(table_name: str, df) -> None:
    table_identifier = sql.Identifier("gold", table_name)
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
            expected_columns = {
                field.name: postgres_type(field.dataType)
                for field in df.schema.fields
                if field.name != "hash_key"
            }

            if gold_table_exists("gold", table_name):
                cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    """,
                    ("gold", table_name),
                )
                existing_columns = {
                    column_name: data_type
                    for column_name, data_type in cur.fetchall()
                }

                type_aliases = {
                    "DATE": {"date"},
                    "TIMESTAMP": {"timestamp without time zone", "timestamp"},
                    "DOUBLE PRECISION": {"double precision"},
                    "BIGINT": {"bigint"},
                    "INTEGER": {"integer"},
                    "BOOLEAN": {"boolean"},
                    "TEXT": {"text"},
                }

                for column_name, expected_type in expected_columns.items():
                    current_type = existing_columns.get(column_name, "").lower()
                    if current_type not in type_aliases[expected_type]:
                        cast_expression = sql.SQL(
                            "NULLIF(btrim({column}::text), '')::{target_type}"
                        ).format(
                            column=sql.Identifier(column_name),
                            target_type=sql.SQL(expected_type),
                        )
                        cur.execute(
                            sql.SQL(
                                "ALTER TABLE {table} ALTER COLUMN {column} "
                                "TYPE {target_type} USING {cast_expression}"
                            ).format(
                                table=table_identifier,
                                column=sql.Identifier(column_name),
                                target_type=sql.SQL(expected_type),
                                cast_expression=cast_expression,
                            )
                        )
            else:
                column_definitions = [
                    sql.SQL("{} {} ").format(
                        sql.Identifier(column_name),
                        sql.SQL(sql_type),
                    )
                    for column_name, sql_type in expected_columns.items()
                ]
                column_definitions.append(
                    sql.SQL('{} TEXT').format(sql.Identifier("hash_key"))
                )
                cur.execute(
                    sql.SQL("CREATE TABLE {} ({})").format(
                        table_identifier,
                        sql.SQL(", ").join(column_definitions),
                    )
                )

            cur.execute(
                sql.SQL("CREATE UNIQUE INDEX IF NOT EXISTS {} ON {} ({})").format(
                    sql.Identifier(f"ux_{table_name}_hash_key"),
                    table_identifier,
                    sql.Identifier("hash_key"),
                )
            )
    finally:
        conn.close()
          
        

def main():
    log_file_path = str(PROJECT_ROOT / "ETL_Pipeline" / "bronze" / "conf" / "log4j2.properties")
    # print("Correct log_path:", log_file_path)
    
    if os.name == 'nt':
        log_file_path = log_file_path.replace("\\", "/")

    os.environ["SPARK_SUBMIT_OPTS"] = f"-Dlog4j2.configurationFile=file:///{log_file_path}"
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    
    spark = SparkSession.builder \
        .appName("Silver to Gold ETL") \
        .config("spark.jars", JDBC_JAR_PATH) \
        .getOrCreate()
    
    print("PySpark Session started successfully.\n")
    
    ensure_gold_schema_exists()
    print("Gold schema exists.\n")
    
    # Connect to the silver layer and read data
    print("Reading data from silver.indianstocks table...")
    
    # Incremental data loading from silver table
    last_ingest_record = get_last_ingest_partition("gold", "indianstocks", "daily")
    last_ingest_partition = last_ingest_record["ingest_partition"] if last_ingest_record else None

    gold_df = get_data_from_silver(spark, "indianstocks", last_ingest_partition)
    print("Data read from silver.indianstocks table was successful.")
    print(f"Total new records to write: {gold_df.count()}\n")
    
    
    # Dropping unnecessary columns
    gold_df = gold_df.drop("silver_load_date_time")
    
    # Transforming Column names
    gold_df = gold_df.withColumnRenamed("ticker_symbol", "stock_code")  \
        .withColumnRenamed("financial_instrument_name", "stock_name") \
    
    
    # Adding meta data columns and aggregate columns
    # Average PnL percentage
    avg_pnl_df = gold_df.groupBy("ISIN", "stock_code").agg(avg(col("pnl_percentage").cast("double")).alias("avg_pnl_percentage"))
    gold_df = gold_df.join(avg_pnl_df, on=["ISIN", "stock_code"], how="left")
    
    # metrics column
    ema_df = get_data_from_silver(spark, "indianstocks_ema", None)
    gold_df = gold_df.join(ema_df, on=["hash_key"], how="left")
    
    # gold_load_date_time column
    gold_df = gold_df.withColumn("gold_load_date_time", current_timestamp())
    
    
    
    
    ensure_gold_table_exists("indianstocks", gold_df)

    # Incremental Logic: Check for existing records in the gold table based on hash_key
    gold_prev_df = spark.read \
        .format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", "gold.indianstocks") \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .load().select("hash_key").dropDuplicates()
    
    gold_df_dedup = gold_df.join(gold_prev_df, on="hash_key", how="left_anti")
    print(f"Total new records to write after merge check: {gold_df_dedup.count()}")
    
    gold_df_dedup.write \
            .mode("append") \
            .jdbc(url=DB_URL, table="gold.indianstocks", properties=DB_PROPERTIES)

    # Updating the ELT configuration with the latest partition
    latest_partition_row = gold_df.agg(max("business_date").alias("max_business_date")).collect()[0]
    latest_partition_date = latest_partition_row["max_business_date"]
    
    if latest_partition_date is not None:
        if not isinstance(latest_partition_date, date):
            latest_partition_date = datetime.strptime(str(latest_partition_date), "%Y-%m-%d").date()
        write_to_elt_config("gold", "indianstocks", "daily", latest_partition_date)
    
        print("ELT config table has been updated with the latest partition.")
    else:
        print("No new records were found to update the ELT config table.")

if __name__ == "__main__":
    main()