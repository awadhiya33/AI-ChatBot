from mcp.server.fastmcp import FastMCP
import sqlite3
from typing import List, Dict, Any
from pathlib import Path

# Create a stateless MCP server with JSON responses (recommended)
mcp = FastMCP("DatabaseServerStreamable", stateless_http=True, json_response=True)

# Other configuration options:
# Stateless server with SSE streaming responses
# mcp = FastMCP("DatabaseServerStreamable", stateless_http=True)

# Stateful server with session persistence
# mcp = FastMCP("DatabaseServerStreamable")

@mcp.tool()
def list_tables(db_path: str) -> List[str]:
    """List all tables in the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        return [f"Error listing tables: {str(e)}"]

@mcp.tool()
def get_table_schema(db_path: str, table_name: str) -> str:
    """Get schema information for a specific table as a CREATE TABLE string"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
        return f"Table '{table_name}' not found"
    except Exception as e:
        return f"Error getting schema: {str(e)}"

@mcp.tool()
def execute_query(db_path: str, query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        return [{"error": f"Error executing query: {str(e)}"}]

if __name__ == "__main__":
    # Run server with streamable_http transport
    mcp.run(transport="streamable-http")