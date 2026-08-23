import os
import sys
from datetime import date, datetime
from pathlib import Path
import psycopg2
from psycopg2 import sql
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    StringType,
    TimestampType,
)
from pyspark.sql.functions import current_timestamp, col, coalesce, concat_ws, lit, sha2, max, when

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ETL_Pipeline.bronze.landing2bronze import load_env_file, get_last_ingest_partition, write_to_elt_config

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

def ensure_silver_schema_exists() -> None:
    """Create the silver schema in PostgreSQL if it does not already exist."""
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
            cur.execute("CREATE SCHEMA IF NOT EXISTS silver")
    finally:
        conn.close()


def silver_table_exists(schema_name: str, table_name: str) -> bool:
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


def postgres_type(spark_type) -> str:
    if isinstance(spark_type, DateType):
        return "DATE"
    if isinstance(spark_type, TimestampType):
        return "TIMESTAMP"
    if isinstance(spark_type, DoubleType) or isinstance(spark_type, FloatType):
        return "DOUBLE PRECISION"
    if isinstance(spark_type, LongType):
        return "BIGINT"
    if isinstance(spark_type, IntegerType):
        return "INTEGER"
    if isinstance(spark_type, BooleanType):
        return "BOOLEAN"
    if isinstance(spark_type, StringType):
        return "TEXT"
    return "TEXT"


def ensure_silver_table_exists(table_name: str, df) -> None:
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
            table_identifier = sql.Identifier("silver", table_name)
            
            # expected_columns = {}
            # for field in df.schema.fields:
            #     if field.name != "hash_key":
            #         expected_columns[field.name] = postgres_type(field.dataType)
                    
            expected_columns = {
                field.name: postgres_type(field.dataType)
                for field in df.schema.fields
                if field.name != "hash_key"
            }
            

            if silver_table_exists("silver", table_name):
                cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    """,
                    ("silver", table_name),
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


def get_data_from_bronze(spark: SparkSession, table_name: str, latest_ingest_partition: date):
    if latest_ingest_partition is not None:
        if not isinstance(latest_ingest_partition, date):
            latest_ingest_partition = datetime.strptime(str(latest_ingest_partition), "%Y-%m-%d").date()

        partition_value = latest_ingest_partition.strftime("%Y-%m-%d")
        query = f"""
            SELECT *
            FROM bronze.{table_name}
            WHERE "BizDt" > '{partition_value}'
        """
    else:
        query = f"SELECT * FROM bronze.{table_name}"

    return spark.read \
        .format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", f"({query}) AS bronze_data") \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .load()
        
def main():
    project_root = Path(__file__).resolve().parents[2]
    log_file_path = str(project_root / "ETL_Pipeline" / "bronze" / "conf" / "log4j2.properties")
    # print("Correct log_path:", log_file_path)

    if os.name == 'nt':
        log_file_path = log_file_path.replace("\\", "/")

    os.environ["SPARK_SUBMIT_OPTS"] = f"-Dlog4j2.configurationFile=file:///{log_file_path}"
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    
    spark = SparkSession.builder \
        .appName("Bronze to Silver ETL") \
        .config("spark.jars", JDBC_JAR_PATH) \
        .getOrCreate()
    
    print("PySpark Session started successfully.\n")
    
    ensure_silver_schema_exists()
    print("Silver schema exists.\n")
    
    # Connect to the bronze layer and read data
    print("Reading data from bronze.indianstocks table...")
    
    last_ingest_record = get_last_ingest_partition("silver", "indianstocks", "daily")
    last_ingest_partition = last_ingest_record["ingest_partition"] if last_ingest_record else None

    silver_df = get_data_from_bronze(spark, "indianstocks", last_ingest_partition)
    print("Data read from bronze.indianstocks table was successful.")
    
    # Dropping unnecessary columns
    silver_df = silver_df.drop('Sgmt', 'FinInstrmTp', 'FinInstrmId', 'FininstrmActlXpryDt', 'StrkPric', 'OptnTp',
        'UndrlygPric', 'SttlmPric', 'OpnIntrst', 'ChngInOpnIntrst', 'NewBrdLotQty', 'Rmks', 'Rsvd1', 'Rsvd2',
        'Rsvd3', 'Rsvd4', 'SsnId', '_source_file')
    
    # Transforming Column names
    silver_df = silver_df.withColumnRenamed("TradDt", "trading_date") \
        .withColumnRenamed("BizDt", "business_date") \
        .withColumnRenamed("Src", "data_source_code") \
        .withColumnRenamed("TckrSymb", "ticker_symbol") \
        .withColumnRenamed("SctySrs", "security_series") \
        .withColumnRenamed("XpryDt", "expiry_date") \
        .withColumnRenamed("FinInstrmNm", "financial_instrument_name") \
        .withColumnRenamed("OpnPric", "open_price") \
        .withColumnRenamed("HghPric", "high_price") \
        .withColumnRenamed("LwPric", "low_price") \
        .withColumnRenamed("ClsPric", "closing_price") \
        .withColumnRenamed("LastPric", "last_price") \
        .withColumnRenamed("PrvsClsgPric", "previous_closing_price") \
        .withColumnRenamed("TtlTradgVol", "total_trading_volume") \
        .withColumnRenamed("TtlTrfVal", "total_turnover_value") \
        .withColumnRenamed("TtlNbOfTxsExctd", "total_number_of_transactions_executed") \
        .withColumnRenamed("_ingested_at", "ingestion_date_time")
    
    # Changing data types for required columns
    silver_df = silver_df.withColumn("trading_date", col("trading_date").cast("date")) \
        .withColumn("business_date", col("business_date").cast("date")) \
        .withColumn("expiry_date", col("expiry_date").cast("date")) \
        .withColumn("open_price", col("open_price").cast("double")) \
        .withColumn("high_price", col("high_price").cast("double")) \
        .withColumn("low_price", col("low_price").cast("double")) \
        .withColumn("closing_price", col("closing_price").cast("double")) \
        .withColumn("last_price", col("last_price").cast("double")) \
        .withColumn("previous_closing_price", col("previous_closing_price").cast("double")) \
        .withColumn("total_trading_volume", col("total_trading_volume").cast("integer")) \
        .withColumn("total_turnover_value", col("total_turnover_value").cast("double")) \
        .withColumn("total_number_of_transactions_executed", col("total_number_of_transactions_executed").cast("integer")) \
        .withColumn("ingestion_date_time", col("ingestion_date_time").cast("timestamp"))

    # Filtering out records with Security Series as 'EQ' and 'SM' only
    silver_df = silver_df.filter(col("security_series").isin("EQ", "SM"))

    # Keep the original hash_key definition to preserve current row identity semantics.
    hash_columns = ["data_source_code", "ISIN", "ticker_symbol", "business_date"]

    hash_input = concat_ws(
        "|",
        *[coalesce(col(c).cast("string"), lit("")) for c in hash_columns]
    )

    # Adding data columns
    silver_df = silver_df.withColumn("silver_load_date_time", current_timestamp().cast("timestamp")) \
                .withColumn("hash_key", sha2(hash_input, 256)) \
                .withColumn("pnl_percentage",
                    when( col("previous_closing_price").cast("double").isNotNull(),
                        ((col("closing_price").cast("double") - col("previous_closing_price").cast("double"))/col("previous_closing_price").cast("double")) * 100,
                    )
                )

    # print("Silver DataFrame schema:")
    # silver_df.printSchema()
    # print(f"Silver DataFrame data types: {silver_df.dtypes}")

    ensure_silver_table_exists("indianstocks", silver_df)

    # Incremental Logic: Check for existing records in the silver table based on hash_key
    silver_prev_df = spark.read \
        .format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", "silver.indianstocks") \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .load() \
        .select("hash_key") \
        .dropDuplicates()

    silver_df_dedup = silver_df.join(silver_prev_df, on="hash_key", how="left_anti")
    print(f"Total new records to write after merge check: {silver_df_dedup.count()}")
    
    silver_df_dedup.write \
            .mode("append") \
            .jdbc(url=DB_URL, table="silver.indianstocks", properties=DB_PROPERTIES)

    # Updating the ELT configuration with the latest partition
    latest_partition_row = silver_df.agg(max("business_date").alias("max_business_date")).collect()[0]
    latest_partition_date = latest_partition_row["max_business_date"]
    
    # DEBUG
    print(f"latest_partition_date= {latest_partition_date}")
    
    if latest_partition_date is not None:
        if not isinstance(latest_partition_date, date):
            latest_partition_date = datetime.strptime(str(latest_partition_date), "%Y-%m-%d").date()
        write_to_elt_config("silver", "indianstocks", "daily", latest_partition_date)
    
        print("ELT config table has been updated with the latest partition.")
    else:
        print("No new records were found to update the ELT config table.")

if __name__ == "__main__":
    main()