from mcp import ClientSession
from mcp.client.sse import sse_client
import asyncio

async def run():
    # The URL for the MCP SSE endpoint
    async with sse_client("http://localhost:8000/sse") as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print("Available tools:", tools)

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