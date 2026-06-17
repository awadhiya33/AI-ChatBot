from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
import asyncio


async def run():
    # Connect to a streamable HTTP server
    async with streamable_http_client("http://localhost:8000/mcp") as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")

            db_path = "c:\\database\\fintech.db"

            # List all tables
            tables = await session.call_tool("list_tables", {"db_path": db_path})
            print("Tables in database:", tables)

            # Get table schema
            schema = await session.call_tool("get_table_schema", {
                "db_path": db_path,
                "table_name": "customers"
            })
            print("Table schema for customers:", schema)

            # Execute a query
            results = await session.call_tool("execute_query", {
               "db_path": db_path,
               "query": "SELECT * FROM customers LIMIT 5"
            })
            print("First 5 customers:", results)


if __name__ == "__main__":
    asyncio.run(run())