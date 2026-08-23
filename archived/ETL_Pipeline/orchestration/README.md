# Orchestration

This folder contains Databricks job definitions and scheduling configurations.

## Contents

- **jobs/**: YAML files defining Databricks jobs for pipeline orchestration

## Usage

Upload these YAML files to Databricks and create jobs from them, or use the Databricks CLI to deploy:

```bash
databricks jobs create --json-file daily_stock_pipeline.yml
```

## Job Structure

- **daily_stock_pipeline**: Runs the full ETL pipeline daily
  - Extract Bronze → Validate Silver → Aggregate Gold
  - Includes error handling and notifications