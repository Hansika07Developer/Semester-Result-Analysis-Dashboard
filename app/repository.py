from __future__ import annotations

from pathlib import Path
import pandas as pd


class CSVRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch_results(self) -> pd.DataFrame:
        return pd.read_csv(self.path)


class MySQLRepository:
    """Optional MySQL adapter. Requires mysql-connector-python."""
    def __init__(self, host: str, user: str, password: str, database: str, table: str = "results"):
        self.config = dict(host=host, user=user, password=password, database=database)
        self.table = table

    def fetch_results(self) -> pd.DataFrame:
        import mysql.connector
        conn = mysql.connector.connect(**self.config)
        try:
            return pd.read_sql(f"SELECT * FROM {self.table}", conn)
        finally:
            conn.close()
