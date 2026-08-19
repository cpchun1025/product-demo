from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pyodbc

from config import settings


PRODUCT_SQL = """
SELECT TOP (1000)
      [ProductID]
      ,[Name]
      ,[ProductNumber]
      ,[MakeFlag]
      ,[FinishedGoodsFlag]
      ,[Color]
      ,[SafetyStockLevel]
      ,[ReorderPoint]
      ,[StandardCost]
      ,[ListPrice]
      ,[Size]
      ,[SizeUnitMeasureCode]
      ,[WeightUnitMeasureCode]
      ,[Weight]
      ,[DaysToManufacture]
      ,[ProductLine]
      ,[Class]
      ,[Style]
      ,[ProductSubcategoryID]
      ,[ProductModelID]
      ,[SellStartDate]
      ,[SellEndDate]
      ,[DiscontinuedDate]
      ,[rowguid]
      ,[ModifiedDate]
FROM [AdventureWorks2025].[Production].[Product]
"""


def ensure_data_directory() -> None:
    settings.parquet_path.parent.mkdir(parents=True, exist_ok=True)
    settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)


def sync_products_from_sql_server() -> dict[str, Any]:
    """
    Read products from SQL Server and write them to Parquet.
    """

    ensure_data_directory()

    with pyodbc.connect(settings.sql_connection_string) as connection:
        dataframe = pd.read_sql_query(PRODUCT_SQL, connection)

    dataframe.to_parquet(
        settings.parquet_path,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    return {
        "status": "success",
        "rows_written": len(dataframe),
        "parquet_file": str(settings.parquet_path),
        "columns": list(dataframe.columns),
    }


def _require_parquet_file() -> None:
    if not settings.parquet_path.exists():
        raise FileNotFoundError(
            f"Parquet file does not exist: {settings.parquet_path}. "
            "Run the sync operation first."
        )


def _convert_dataframe_to_json(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Convert pandas values such as Timestamp, UUID, and NaN into JSON-safe values.
    """
    json_text = dataframe.to_json(
        orient="records",
        date_format="iso",
    )

    return json.loads(json_text)


def query_products(
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """
    Query products from Parquet through DuckDB.
    """

    _require_parquet_file()

    limit = max(1, min(limit, 1000))
    offset = max(0, offset)

    conditions = []
    parameters: list[Any] = []

    if search:
        conditions.append(
            """
            (
                lower("Name") LIKE lower(?)
                OR lower("ProductNumber") LIKE lower(?)
                OR lower(coalesce("Color", '')) LIKE lower(?)
            )
            """
        )

        search_value = f"%{search}%"
        parameters.extend([search_value, search_value, search_value])

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT *
        FROM read_parquet(?)
        {where_clause}
        ORDER BY "ProductID"
        LIMIT ?
        OFFSET ?
    """

    parameters = [str(settings.parquet_path), *parameters, limit, offset]

    with duckdb.connect(str(settings.duckdb_path)) as connection:
        dataframe = connection.execute(sql, parameters).fetchdf()

    return _convert_dataframe_to_json(dataframe)


def get_product(product_id: int) -> dict[str, Any] | None:
    """
    Get a single product from Parquet through DuckDB.
    """

    _require_parquet_file()

    sql = """
        SELECT *
        FROM read_parquet(?)
        WHERE "ProductID" = ?
        LIMIT 1
    """

    with duckdb.connect(str(settings.duckdb_path)) as connection:
        dataframe = connection.execute(
            sql,
            [str(settings.parquet_path), product_id],
        ).fetchdf()

    products = _convert_dataframe_to_json(dataframe)

    if not products:
        return None

    return products[0]


def count_products() -> int:
    """
    Count products in the Parquet file.
    """

    _require_parquet_file()

    sql = """
        SELECT COUNT(*) AS product_count
        FROM read_parquet(?)
    """

    with duckdb.connect(str(settings.duckdb_path)) as connection:
        result = connection.execute(
            sql,
            [str(settings.parquet_path)],
        ).fetchone()

    return int(result[0])