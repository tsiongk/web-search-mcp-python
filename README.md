# Web Search MCP Server (Python)

A Python MCP server for web search and content extraction using DuckDuckGo. Built with the [Dedalus MCP framework](https://github.com/dedalus-labs/dedalus-mcp-python).

## Features

- **full_web_search** - Search and extract content from top results
- **get_web_search_summaries** - Get search result summaries without full content
- **get_single_web_page_content** - Extract content from a specific URL

No API key required - uses DuckDuckGo for search.

## Installation

```bash
# Clone the repository
git clone https://github.com/dedalus-labs/web-search-mcp-python.git
cd web-search-mcp-python

# Install dependencies with uv
uv sync
```

## Usage

### Running the Server

```bash
uv run python src/main.py
```

The server will start on `http://localhost:3013/mcp`.

### Testing with the Client

```bash
uv run python src/client.py
```

## Tools

### full_web_search

Perform a web search and extract full content from top results.

**Parameters:**
- `query` (required): Search query
- `max_results` (optional): Number of results (default: 5)

**Returns:** Search results with extracted page content

### get_web_search_summaries

Get search result summaries without extracting full content.

**Parameters:**
- `query` (required): Search query
- `max_results` (optional): Number of results (default: 10)

**Returns:** Search result titles, URLs, and snippets

### get_single_web_page_content

Extract content from a specific URL.

**Parameters:**
- `url` (required): URL to extract content from

**Returns:** Extracted page content

## Dependencies

- `duckduckgo-search` - For web search functionality
- `beautifulsoup4` - For HTML parsing and content extraction
- `httpx` - For HTTP requests

## License

MIT
