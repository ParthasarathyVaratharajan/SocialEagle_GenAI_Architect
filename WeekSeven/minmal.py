import asyncio
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

async def main():
    server_params = StdioServerParams(
        command="playwright-mcp",
        args=["--headless"],
    )
    async with McpWorkbench(server_params) as mcp:
        # List available tools from the MCP server
        tools = await mcp.list_tools()
        print("Available tools:", tools)

asyncio.run(main())
