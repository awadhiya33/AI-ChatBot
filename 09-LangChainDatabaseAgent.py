from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import asyncio
import os

# Ensure you have OPENAI_API_KEY set in your environment
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"


async def main():
    # Create a MultiServerMCPClient with the Database Server
    client = MultiServerMCPClient(
        {
            "database": {
                "transport": "stdio",  # Local subprocess communication
                "command": "python",
                # Update with the absolute path to your DatabaseServer script
                "args": ["C:\\path\\to\\your\\workspace\\03-DatabaseServer.py"],
            }
        }
    )

    # Get tools from the MCP server
    tools = await client.get_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")

    # Create a LangChain agent using create_agent with gpt-4o-mini
    agent = create_agent(
        "openai:gpt-4o-mini",  # Model specification
        tools  # MCP tools
    )

    # Example query: list all tables
    print("\n" + "="*80)
    print("List all tables in the fintech database")
    print("="*80)
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "List all tables in the database located at c:\\database\\fintech.db"}]
    })
    print(f"\nResult: {result['messages'][-1].content}\n")

    # Close the client
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())