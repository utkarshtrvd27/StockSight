import os
from pathlib import Path
import psycopg2


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


ENV_PATH = find_env_file(Path(__file__).resolve())
load_env_file(ENV_PATH)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def ensure_elt_pipeline_orchestration_schema_exists() -> None:
    """Create the elt_pipeline_orchestration schema in PostgreSQL if it does not already exist."""
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
            cur.execute("CREATE SCHEMA IF NOT EXISTS elt_pipeline_orchestration")
    finally:
        conn.close()


def create_elt_config_table() -> None:
    """Create the elt_pipeline_orchestration.elt_config control table used for incremental ingestion."""
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
                """
                CREATE TABLE IF NOT EXISTS elt_pipeline_orchestration.elt_config (
                    table_layer VARCHAR NOT NULL,
                    table_name VARCHAR NOT NULL,
                    cycle VARCHAR NOT NULL,
                    ingest_partition DATE,
                    PRIMARY KEY (table_layer, table_name, cycle)
                )
                """
            )
            print("Successfully created table elt_pipeline_orchestration.elt_config for date-based incremental ingestion for all layers.")
    finally:
        conn.close()


def main() -> None:
    ensure_elt_pipeline_orchestration_schema_exists()
    create_elt_config_table()


if __name__ == "__main__":
    main()
