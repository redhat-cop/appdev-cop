# Python MCP Sample

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server built with Python that exposes insurance policy data from a local SQLite database. An AI agent (or any MCP-compatible client) can query, list, and retrieve insurance policies through the tools this server provides.

## What It Does

The project contains two scripts:

- **`setup_db.py`** — Generates a SQLite database (`insurance.db`) populated with 30 fake insurance policies (Auto, Home, Life, Health) using the Faker library.
- **`mcp_server.py`** — Runs an MCP server over stdio that exposes three tools:
  - `get_policy` — Look up a single policy by its policy number.
  - `list_policies` — List all policies with optional filters by status (`Active`, `Expired`, `Cancelled`) and type (`Auto`, `Home`, `Life`, `Health`).
  - `send_policy_to_agent` — Retrieve a policy and queue it for AI agent processing (placeholder for future integration).

## Prerequisites

- Python 3.10+
- [pip](https://pip.pypa.io/) or [uv](https://docs.astral.sh/uv/)

## Getting Started

### 1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or with **uv**:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Generate the sample database

```bash
python setup_db.py
```

This creates `insurance.db` in the project directory with 30 randomly generated policies.

### 3. Run the MCP server

```bash
python mcp_server.py
```

The server communicates over **stdio** using the MCP protocol. It is designed to be launched by an MCP-compatible client (e.g., Claude Desktop, Cursor, or any agent that supports MCP).

### 4. Connect from an MCP client

Add the server to your client's MCP configuration. For example, in a `mcp.json` or equivalent config:

```json
{
  "mcpServers": {
    "insurance-policy-server": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/python-mcp-sample"
    }
  }
}
```

Replace `/path/to/python-mcp-sample` with the actual path to this directory.

## Project Structure

```
python-mcp-sample/
├── README.md
├── pyproject.toml        # Project metadata and dependencies
├── setup_db.py           # Database seeding script
├── mcp_server.py         # MCP server entry point
└── insurance.db          # Generated SQLite database (after running setup_db.py)
```
