# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client for testing the Web Search MCP server."""

import asyncio

from dedalus_mcp import MCPClient


SERVER_URL = "http://localhost:3013/mcp"


async def main() -> None:
    client = await MCPClient.connect(SERVER_URL)

    # List tools
    result = await client.list_tools()
    print(f"\nAvailable tools ({len(result.tools)}):\n")
    for t in result.tools:
        print(f"  {t.name}")
        if t.description:
            print(f"    {t.description[:80]}...")
        print()

    # Test get_web_search_summaries
    print("--- get_web_search_summaries ---")
    summaries = await client.call_tool(
        "get_web_search_summaries",
        {"query": "Python programming best practices", "limit": 3},
    )
    print(summaries)
    print()

    # Test full_web_search
    print("--- full_web_search ---")
    full_results = await client.call_tool(
        "full_web_search",
        {"query": "what is MCP model context protocol", "limit": 2, "max_content_length": 1000},
    )
    print(str(full_results)[:2000] + "..." if len(str(full_results)) > 2000 else full_results)
    print()

    # Test get_single_web_page_content
    print("--- get_single_web_page_content ---")
    page_content = await client.call_tool(
        "get_single_web_page_content",
        {"url": "https://www.anthropic.com/", "max_content_length": 500},
    )
    print(page_content)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
