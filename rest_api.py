from typing import Any

from fastapi import FastAPI, HTTPException, Query

from storage import (
    count_products,
    get_product,
    query_products,
    sync_products_from_sql_server,
)

app = FastAPI(
    title="AdventureWorks Product API",
    version="1.0.0",
    description="REST API over SQL Server data stored as Parquet and queried by DuckDB.",
)


@app.get("/")
def health_check() -> dict[str, str]:
    return {
        "service": "AdventureWorks Product REST API",
        "status": "running",
    }


@app.post("/sync")
def sync_products() -> dict[str, Any]:
    """
    Load products from SQL Server into Parquet.
    """

    try:
        return sync_products_from_sql_server()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"SQL Server synchronization failed: {exc}",
        ) from exc


@app.get("/products")
def list_products(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Query products from Parquet using DuckDB.
    """

    try:
        products = query_products(
            limit=limit,
            offset=offset,
            search=search,
        )

        return {
            "count": len(products),
            "limit": limit,
            "offset": offset,
            "search": search,
            "items": products,
        }

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Product query failed: {exc}",
        ) from exc


@app.get("/products/count")
def products_count() -> dict[str, int]:
    try:
        return {
            "count": count_products(),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Product count failed: {exc}",
        ) from exc


@app.get("/products/{product_id}")
def product_by_id(product_id: int) -> dict[str, Any]:
    try:
        product = get_product(product_id)

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} was not found.",
            )

        return product

    except HTTPException:
        raise

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Product lookup failed: {exc}",
        ) from exc