import os
import re
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path
from fastapi import logger
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit


def find_env_file(start_file: Path) -> Path:
    """Locate the nearest .env file by walking upward from the given file."""
    current_dir = start_file.resolve().parent
    for candidate_dir in (current_dir, *current_dir.parents):
        env_path = candidate_dir / ".env"
        if env_path.exists():
            return env_path
    return current_dir / ".env"


def load_env_file(env_path: Path) -> None:
    """Load simple KEY=VALUE environment variables from a .env file."""
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# --- CONFIGURATION SECTION ---
ENV_PATH = find_env_file(Path(__file__).resolve())
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



ELT_CONFIG_SCHEMA = "elt_pipeline_orchestration"
ELT_CONFIG_TABLE = "elt_config"
ELT_CONFIG_CYCLE = "daily"


def ensure_bronze_schema_exists() -> None:
    """Create the bronze schema in PostgreSQL if it does not already exist."""
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
            cur.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    finally:
        conn.close()



def get_last_ingest_partition(layer: str, table_name: str, cycle: str):
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
                f"""
                SELECT ingest_partition
                FROM {ELT_CONFIG_SCHEMA}.{ELT_CONFIG_TABLE}
                WHERE table_layer = %s AND table_name = %s AND cycle = %s
                LIMIT 1
                """,
                (layer, table_name, cycle),
            )
            row = cur.fetchone()
            if row:
                return {"ingest_partition": row[0]}
            return None
    finally:
        conn.close()


def write_to_elt_config(layer: str, table_name: str,  cycle: str, ingest_partition: date) -> None:
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
                f"""
                INSERT INTO {ELT_CONFIG_SCHEMA}.{ELT_CONFIG_TABLE} (
                    table_layer,
                    table_name,
                    cycle,
                    ingest_partition
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (table_layer, table_name, cycle)
                DO UPDATE SET ingest_partition = EXCLUDED.ingest_partition
                """,
                (layer, table_name, cycle, ingest_partition),
            )
    finally:
        conn.close()


def bronze_table_exists(schema_name: str, table_name: str) -> bool:
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


def ensure_bronze_table_exists(table_name: str, df) -> None:
    if bronze_table_exists("bronze", table_name):
        return

    column_definitions = []
    for field in df.schema.fields:
        safe_column_name = field.name.replace('"', '""')
        if field.name == "_ingested_at":
            sql_type = "TIMESTAMP"
        else:
            sql_type = "TEXT"
        column_definitions.append(f'"{safe_column_name}" {sql_type}')

    create_table_sql = (
        f'CREATE TABLE IF NOT EXISTS "bronze"."{table_name}" ('
        + ", ".join(column_definitions)
        + ")"
    )

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
            cur.execute(create_table_sql)
    finally:
        conn.close()


def parse_date_from_filename(filename: str):
    match = re.search(r"(\d{8})", filename)
    if not match:
        return None

    try:
        return datetime.strptime(match.group(1), "%Y%m%d").date()
    except ValueError:
        return None
    

def extract_zip(zip_path, extract_to):
    """Extracts the ZIP file into a temporary workspace and returns the CSV file paths."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        extracted_files = [
            os.path.join(extract_to, file_name)
            for file_name in zip_ref.namelist()
            if file_name.lower().endswith(".csv")
        ]
        print(f"Extracted: {extracted_files}")
        return extracted_files


def build_incremental_zip_file_list(landing_dir: str, latest_partition: date):
    zip_files = [
        os.path.join(landing_dir, f)
        for f in os.listdir(landing_dir)
        if f.lower().endswith(".zip")
    ]
    if not zip_files:
        return []

    dated_files = []
    for path in zip_files:
        file_date = parse_date_from_filename(os.path.basename(path))
        if file_date is None:
            file_date = datetime.fromtimestamp(os.path.getmtime(path)).date()
        dated_files.append((file_date, path))

    dated_files.sort(key=lambda item: item[0])

    if latest_partition:
        dated_files = [item for item in dated_files if item[0] > latest_partition]

    # print("dated_files=", dated_files)
    return dated_files

def main():
    # 1. Locate the zip files dynamically
    base_dir = os.path.dirname(os.path.abspath(__file__))
    landing_dir = os.path.join(base_dir, "landing")

    ensure_bronze_schema_exists()
    print("Bronze schema exists")

    try:
        last_loaded = get_last_ingest_partition("bronze", "indianstocks", "daily")
        print("Last ingest partition retrieved successfully.")
    except psycopg2.Error as exc:
        print(
            "elt_pipeline_orchestration.elt_config is not available. Run the dedicated setup script first: "
            "python ETL_Pipeline/bronze/conf/elt_config.py"
        )
        print(f"Database error: {exc}")
        return


    last_partition = last_loaded["ingest_partition"] if last_loaded else None
    new_zip_files = build_incremental_zip_file_list(landing_dir, last_partition)

    if not new_zip_files:
        print("No newer zip files available for ingestion.")
        return

    print(f"Found {len(new_zip_files)} zip file(s) newer than ingest_partition.")
    tmp_extract_dir = os.path.join(base_dir, "tmp_extracted")
    os.makedirs(tmp_extract_dir, exist_ok=True)

    # 2. Initialize PySpark Session with JDBC Driver configuration

    log_file_path = os.path.abspath("ETL_Pipeline/bronze/conf/log4j2.properties")
    # print("Correct log_path:", log_file_path)

    if os.name == 'nt':
        log_file_path = log_file_path.replace("\\", "/")

    os.environ["SPARK_SUBMIT_OPTS"] = f"-Dlog4j2.configurationFile=file:///{log_file_path}"

    spark = SparkSession.builder \
        .appName("LandingToBronze-Bhavcopy") \
        .config("spark.jars", JDBC_JAR_PATH) \
        .getOrCreate()

    print("PySpark Session started successfully\n")

    csv_paths = []
    bronze_df = None

    try:
        for file_date, target_zip in new_zip_files:
            print(f"Processing zip file: {os.path.basename(target_zip)}")
            extracted_csv_paths = extract_zip(target_zip, tmp_extract_dir)
            csv_paths.extend(extracted_csv_paths)

            for csv_file_path in extracted_csv_paths:
                # 3. Read Raw CSV (Infer everything as String for Bronze layer safety)
                raw_df = spark.read \
                    .option("header", "true") \
                    .option("inferSchema", "false") \
                    .csv(csv_file_path)

                # Clean trailing/leading spaces from column headers (Common in NSE files)
                cleaned_columns = [col.strip() for col in raw_df.columns]
                raw_df = raw_df.toDF(*cleaned_columns)

                # 4. Add Databricks Best Practices Audit Metadata
                current_file_df = raw_df \
                    .withColumn("_ingested_at", current_timestamp()) \
                    .withColumn("_source_file", lit(os.path.basename(target_zip)))

                bronze_df = current_file_df if bronze_df is None else bronze_df.unionByName(current_file_df)
        
        if bronze_df is None:
            print("No data found in the selected zip files.")
            return

        print()
        
        # Dropping duplicate records based on the combination of ISIN and BizDt
        bronze_df = bronze_df.dropDuplicates(["ISIN", "BizDt"])

        if not bronze_table_exists("bronze", "indianstocks"):
            ensure_bronze_table_exists("indianstocks", bronze_df)
            print("Created missing table bronze.indianstocks.")
            deduped_df = bronze_df
        else:
            existing_df = spark.read \
                .format("jdbc") \
                .option("url", DB_URL) \
                .option("dbtable", "bronze.indianstocks") \
                .option("user", DB_USER) \
                .option("password", DB_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .load()

            # Perform a left anti join to find new records that do not exist in the existing table
            existing_keys = existing_df.select("ISIN", "BizDt").dropDuplicates()
            deduped_df = bronze_df.join(existing_keys, ["ISIN", "BizDt"], "left_anti")

        print(f"Total new records to write after merge check: {deduped_df.count()}")

        # 5. Merge-safe write to PostgreSQL Bronze Schema (Append-Only)
        deduped_df.write \
            .mode("append") \
            .jdbc(url=DB_URL, table="bronze.indianstocks", properties=DB_PROPERTIES)

        latest_partition_date = max(file_date for file_date, _ in new_zip_files)
        write_to_elt_config("bronze", "indianstocks", "daily", latest_partition_date)
        print("ELT config table has been updated with the latest partition.")

    except Exception as e:
        print(f"Pipeline failed due to: {str(e)}")

    finally:
        # Clean up temporary unzipped files
        for csv_file_path in csv_paths:
            if os.path.exists(csv_file_path):
                os.remove(csv_file_path)
        if os.path.exists(tmp_extract_dir):
            shutil.rmtree(tmp_extract_dir, ignore_errors=True)
        if 'spark' in locals():
            spark.stop()

if __name__ == "__main__":
    main()