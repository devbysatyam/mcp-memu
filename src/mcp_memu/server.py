"""
MCP-MEmu Server — FastMCP entry point.

Exposes MEmu Android Emulator control through the Model Context Protocol.
Wraps MEMUC CLI via PyMEMUC and provides 60+ tools for VM lifecycle,
configuration, app management, UI interaction, screenshots, networking,
shell access, and high-level compound operations.

Run:  python server.py
Test: mcp dev server.py
"""

import logging
import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

# ── Initialize MCP server ──────────────────────────────────────────────
mcp = FastMCP("mcp-memu", dependencies=["pymemuc"])

# ── Logging (stderr only — stdout is MCP JSON-RPC channel) ─────────────
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="[%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp-memu")

# ── Register all tool modules ──────────────────────────────────────────
from mcp_memu.tools import lifecycle, config, apps, input, capture, network, shell, compound

lifecycle.register_tools(mcp)
config.register_tools(mcp)
apps.register_tools(mcp)
input.register_tools(mcp)
capture.register_tools(mcp)
network.register_tools(mcp)
shell.register_tools(mcp)
compound.register_tools(mcp)

# ── Register resources ─────────────────────────────────────────────────
import os
import sys

# Ensure resources are registered directly to the server instance
try:
    from mcp_memu.resources import vm_status
    vm_status.register_resources(mcp)
except Exception as e:
    logger.error(f"Failed to register resources: {e}")

logger.info("MCP-MEmu server initialized with all tools and resources")

# ── Run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")

