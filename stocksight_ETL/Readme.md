# Stocksight ETL

Stocksight ETL is a local PySpark pipeline for ingesting NSE equity market data into PostgreSQL. It follows a bronze/silver/gold medallion architecture and supports source extraction, raw-data persistence, transformation, technical-indicator generation, gold-layer enrichment, and date-based incremental processing.

## Project status

The ETL pipeline is implemented through the gold layer:

- Bronze ingestion downloads NSE UDiFF bhavcopy ZIP files and loads their CSV contents into PostgreSQL.
- Silver transformation standardizes the source columns, keeps equity and SME records, calculates daily PnL percentages, and prevents duplicate rows with a hash key.
- Silver analytics calculates seven-period EMA values for each security.
- Gold transformation enriches the silver data with average PnL and EMA metrics for analytics-ready output.
- The ELT control table tracks the latest processed business date for the silver and gold layers.

The pipeline is currently run locally in sequence. No production scheduler is included yet.

### Repository structure

```text
stocksight_ETL/
├── ETL_Pipeline/
│   ├── bronze/
│   │   ├── conf/
│   │   │   ├── elt_config.py
│   │   │   └── log4j2.properties
│   │   ├── landing/
│   │   ├── landing2bronze.py
│   │   └── src2landing.py
│   ├── silver/
│   │   ├── bronze2silver_indianstocks.py
│   │   └── silver_indianstocks_ema.py
│   ├── gold/
│   │   └── silver2gold.py
│   └── orchestration/
├── drivers/
│   └── postgresql-42.7.13.jar
├── .env
└── Readme.md
```

## Components

### Bronze pipeline

- [ETL_Pipeline/bronze/conf/elt_config.py](ETL_Pipeline/bronze/conf/elt_config.py): creates the ELT orchestration schema and checkpoint table
- [ETL_Pipeline/bronze/src2landing.py](ETL_Pipeline/bronze/src2landing.py): downloads the latest NSE UDiFF bhavcopy ZIP via Selenium
- [ETL_Pipeline/bronze/landing2bronze.py](ETL_Pipeline/bronze/landing2bronze.py): extracts CSV files and loads new partitions into the bronze table

### Silver pipeline

- [ETL_Pipeline/silver/bronze2silver_indianstocks.py](ETL_Pipeline/silver/bronze2silver_indianstocks.py): reads bronze data incrementally, standardizes it, calculates PnL percentages, and writes deduplicated rows to silver
- [ETL_Pipeline/silver/silver_indianstocks_ema.py](ETL_Pipeline/silver/silver_indianstocks_ema.py): calculates seven-period EMA values and writes them to `silver.indianstocks_ema`

### Gold pipeline

- [ETL_Pipeline/gold/silver2gold.py](ETL_Pipeline/gold/silver2gold.py): combines silver prices and EMA values, adds average PnL metrics, and writes analytics-ready records to gold

## Prerequisites

- Python 3.12
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
pip install pyspark psycopg2-binary selenium
```

## Running the pipeline

From the `stocksight_ETL` directory, run the stages in this order:

```bash
python ETL_Pipeline/bronze/conf/elt_config.py
python ETL_Pipeline/bronze/src2landing.py
python ETL_Pipeline/bronze/landing2bronze.py
python ETL_Pipeline/silver/bronze2silver_indianstocks.py
python ETL_Pipeline/silver/silver_indianstocks_ema.py
python ETL_Pipeline/gold/silver2gold.py
```

## Data targets

- Bronze table: bronze.indianstocks
- Silver table: silver.indianstocks
- Silver EMA table: silver.indianstocks_ema
- Gold table: gold.indianstocks
- Orchestration table: elt_pipeline_orchestration.elt_config

## Incremental processing

The bronze, silver, and gold stages use business-date partitions and the `elt_pipeline_orchestration.elt_config` table to identify previously processed data. Silver and gold records also use hash-key deduplication before append operations.

## Future work

- Add a production scheduler and job definitions.
- Add automated tests and deployment configuration.
- Extend the gold layer with additional analytics and ML feature generation.


