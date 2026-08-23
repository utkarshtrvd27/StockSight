# Stocksight

Currently, The Stocksight is a local ETL pipeline for ingesting NSE equity market data into PostgreSQL using a bronze/silver medallion-style design. The project currently supports downloading NSE bhavcopy ZIP files, loading them into a bronze layer, transforming them into a silver layer, and tracking incremental ingestion via an ELT configuration table.

## Current project setup

### Architecture

- Bronze layer: downloads NSE ZIP files and loads the raw data into PostgreSQL
- Silver layer: cleans, renames, and standardizes the bronze data before writing it to the silver table
- ELT control table: stores the latest ingest partition so future runs can process only new data

### Repository structure

```text
Stocksight/
├── ETL_Pipeline/
│   ├── bronze/
│   │   ├── conf/
│   │   │   ├── elt_config.py
│   │   │   └── log4j2.properties
│   │   ├── landing/
│   │   ├── landing2bronze.py
│   │   └── src2landing.py
│   ├── silver/
│   │   └── bronze2silver.py
│   └── orchestration/
│       └── jobs/
├── drivers/
│   └── postgresql-42.7.13.jar
├── archived/
└── Readme.md
```

## Components

### Bronze pipeline

- [ETL_Pipeline/bronze/src2landing.py](ETL_Pipeline/bronze/src2landing.py): downloads the latest NSE UDiFF bhavcopy ZIP via Selenium
- [ETL_Pipeline/bronze/landing2bronze.py](ETL_Pipeline/bronze/landing2bronze.py): reads the downloaded ZIP, extracts the CSV, and loads it into the bronze table in PostgreSQL
- The bronze load uses incremental logic based on the stored ingest partition

### Silver pipeline

- [ETL_Pipeline/silver/bronze2silver.py](ETL_Pipeline/silver/bronze2silver.py): reads from the bronze table, applies transformations, writes to the silver table, and updates the ELT config with the latest partition date

## Prerequisites

- Python 3.12 (current environment)
- Java runtime for PySpark
- PostgreSQL database
- Chrome browser with ChromeDriver available for the Selenium download step
- PostgreSQL JDBC driver

## Environment configuration

Create a root-level .env file with the database settings used by the ETL scripts:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

## Python dependencies

Install the runtime packages used by the project:

```bash
pip install pyspark psycopg2-binary selenium fastapi
```

## Running the pipeline

From the project root:

```bash
python ETL_Pipeline/bronze/src2landing.py
python ETL_Pipeline/bronze/landing2bronze.py
python ETL_Pipeline/silver/bronze2silver.py
```

## Data targets

- Bronze table: bronze.indianstocks
- Silver table: silver.indianstocks
- Orchestration table: elt_pipeline_orchestration.elt_config

## Current status

- Bronze ingestion is implemented
- Silver transformation and incremental checkpointing are implemented
- Gold-layer analytics and ML feature generation are planned for a future phase


