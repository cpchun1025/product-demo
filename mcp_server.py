from typing import Any

from mcp.server.mcpserver import MCPServer

from storage import (
    count_products,
    get_product,
    query_products,
    sync_products_from_sql_server,
)

mcp = MCPServer(
    "AdventureWorks Product MCP Server",
    version="1.0.0",
    instructions=(
        "Use these tools to synchronize and query AdventureWorks products. "
        "Products are loaded from Microsoft SQL Server into Parquet and queried "
        "using DuckDB."
    ),
)


@mcp.tool()
def sync_products() -> dict[str, Any]:
    """
    Synchronize the AdventureWorks Product table from SQL Server into Parquet.
    """

    return sync_products_from_sql_server()


@mcp.tool()
def list_products(
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> dict[str, Any]:
    """
    List products from the Parquet dataset.

    Args:
        limit: Maximum number of products to return. Maximum is 1000.
        offset: Number of products to skip.
        search: Optional search text for product name, product number, or color.
    """

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


@mcp.tool()
def get_product_by_id(product_id: int) -> dict[str, Any]:
    """
    Get one AdventureWorks product by ProductID.
    """

    product = get_product(product_id)

    if product is None:
        return {
            "found": False,
            "product_id": product_id,
        }

    return {
        "found": True,
        "item": product,
    }


@mcp.tool()
def product_count() -> dict[str, int]:
    """
    Return the number of products currently stored in Parquet.
    """

    return {
        "count": count_products(),
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        stateless_http=True,
        json_response=True,
    )