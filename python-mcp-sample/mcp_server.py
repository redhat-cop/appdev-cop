"""MCP server exposing insurance policy data from SQLite."""

import os
import sqlite3
from textwrap import dedent

from mcp.server.fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "insurance.db")

mcp = FastMCP("Insurance Policy Server")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _format_policy(row: sqlite3.Row) -> str:
    return dedent(f"""\
        Policy Number : {row["policy_number"]}
        Holder        : {row["holder_name"]} ({row["holder_email"]})
        Type          : {row["policy_type"]}
        Premium       : ${row["premium"]:,.2f}
        Deductible    : ${row["deductible"]:,.2f}
        Coverage Limit: ${row["coverage_limit"]:,.2f}
        Period        : {row["start_date"]} to {row["end_date"]}
        Status        : {row["status"]}""")


@mcp.tool()
def get_policy(policy_number: str) -> str:
    """Look up a single insurance policy by its policy number.

    Args:
        policy_number: The unique policy identifier (e.g. POL-2024005).
    """
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM policies WHERE policy_number = ?", (policy_number,)
    ).fetchone()
    conn.close()

    if row is None:
        return f"No policy found with number '{policy_number}'."
    return _format_policy(row)


@mcp.tool()
def list_policies(status: str | None = None, policy_type: str | None = None) -> str:
    """List insurance policies with optional filters.

    Args:
        status: Filter by status (Active, Expired, or Cancelled). None returns all.
        policy_type: Filter by type (Auto, Home, Life, or Health). None returns all.
    """
    query = "SELECT * FROM policies WHERE 1=1"
    params: list[str] = []

    if status is not None:
        query += " AND status = ?"
        params.append(status)
    if policy_type is not None:
        query += " AND policy_type = ?"
        params.append(policy_type)

    query += " ORDER BY policy_number"

    conn = _get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        return "No policies match the given filters."

    header = f"{'#':<4} {'Policy Number':<16} {'Holder':<25} {'Type':<8} {'Premium':>10} {'Status':<10}"
    separator = "-" * len(header)
    lines = [header, separator]

    for i, row in enumerate(rows, 1):
        lines.append(
            f"{i:<4} {row['policy_number']:<16} {row['holder_name']:<25} "
            f"{row['policy_type']:<8} ${row['premium']:>9,.2f} {row['status']:<10}"
        )

    lines.append(separator)
    lines.append(f"Total: {len(rows)} policies")
    return "\n".join(lines)


@mcp.tool()
def send_policy_to_agent(policy_number: str) -> str:
    """Retrieve an insurance policy and send its data to the AI agent for processing.

    Args:
        policy_number: The unique policy identifier to look up and forward.
    """
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM policies WHERE policy_number = ?", (policy_number,)
    ).fetchone()
    conn.close()

    if row is None:
        return f"No policy found with number '{policy_number}'. Nothing sent."

    policy_data = dict(row)

    # TODO: send extra info to the agent
    print(f"TODO: send policy {policy_number} data to AI agent: {policy_data}")

    return (
        f"Policy {policy_number} data retrieved and queued for the AI agent (not yet implemented).\n\n"
        + _format_policy(row)
    )


if __name__ == "__main__":
    mcp.run()
