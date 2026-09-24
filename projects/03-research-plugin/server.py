"""Minimal MCP skeleton for the Research Agent plugin.

Replace search_papers() with the already-tested ResearchPilot retrieval pipeline.
Install the MCP Python SDK in the environment that launches this server.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("research")


@mcp.tool()
def search_papers(query: str, top_k: int = 5) -> dict:
    """Search the local research-paper corpus and return source-preserving passages."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    # TODO: replace this with the tested ResearchPilot retrieval module.
    # Keep this output contract stable so Nanobot can preserve provenance.
    return {
        "query": query,
        "results": [],
        "note": "Wire this tool to the existing ResearchPilot multi-paper retriever.",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
