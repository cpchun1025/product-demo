from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    sql_server: str = "localhost"
    sql_port: int = 1433
    sql_database: str = "AdventureWorks2025"
    sql_username: str = "sa"
    sql_password: str
    sql_driver: str = "ODBC Driver 18 for SQL Server"

    parquet_path: Path = Path("data/products.parquet")
    duckdb_path: Path = Path("data/products.duckdb")

    rest_host: str = "127.0.0.1"
    rest_port: int = 8000

    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8001

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sql_connection_string(self) -> str:
        return (
            f"DRIVER={{{self.sql_driver}}};"
            f"SERVER={self.sql_server},{self.sql_port};"
            f"DATABASE={self.sql_database};"
            f"UID={self.sql_username};"
            f"PWD={self.sql_password};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )


settings = Settings()