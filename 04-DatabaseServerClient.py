from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["03-DatabaseServer.py"],  # Server script
    env=None,
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
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