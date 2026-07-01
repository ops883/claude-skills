#!/usr/bin/env python3
"""
mcp_server.py — minimal MCP (Model Context Protocol) stdio server exposing
context_pipeline.py's search as a single `search_context` tool.

EXPERIMENTAL / REFERENCE IMPLEMENTATION. Implements just enough of the MCP
stdio transport (line-delimited JSON-RPC 2.0) to handle initialize,
tools/list, and tools/call. It has NOT been tested against a live MCP
client — the supported, verified interface for this plugin is the
context_pipeline.py CLI (see ../README.md). Use this only if you need
token-reducer exposed as a tool inside an MCP-aware agent, and verify it
against your specific client before relying on it.

No third-party MCP SDK — stdlib only (json, sys), consistent with the rest
of this plugin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import context_pipeline as cp  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"

TOOL_SCHEMA = {
    "name": "search_context",
    "description": (
        "Search an indexed codebase for the chunks most relevant to a "
        "natural-language query, instead of reading whole files. Indexes "
        "'inputs' if given (incremental — unchanged files are skipped), "
        "then returns the top matching chunks with file path, line range, "
        "and a snippet."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural-language query"},
            "inputs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files/directories to (re)index before searching. "
                                "Omit to search the existing index only.",
            },
            "db": {"type": "string", "description": "SQLite index path", "default": cp.DEFAULT_DB},
            "embedding_backend": {"type": "string", "enum": ["hash", "tfidf"], "default": "hash"},
            "limit": {"type": "integer", "default": 8},
        },
        "required": ["query"],
    },
}


def _respond(id_, result=None, error=None) -> None:
    msg = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle_initialize(id_, _params) -> None:
    _respond(id_, {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "token-reducer", "version": "1.0.0"},
    })


def handle_tools_list(id_, _params) -> None:
    _respond(id_, {"tools": [TOOL_SCHEMA]})


def handle_tools_call(id_, params) -> None:
    name = params.get("name")
    args = params.get("arguments", {}) or {}
    if name != "search_context":
        _respond(id_, error={"code": -32601, "message": f"unknown tool: {name}"})
        return

    query = args.get("query", "")
    db_path = args.get("db", cp.DEFAULT_DB)
    backend = args.get("embedding_backend", "hash")
    limit = int(args.get("limit", 8))
    inputs = args.get("inputs") or []

    try:
        conn = cp.open_db(db_path)
        if inputs:
            cp.index_paths(conn, inputs, cp.DEFAULT_EXTENSIONS, backend,
                            cp.CHUNK_LINES, cp.CHUNK_OVERLAP)
        results = cp.query_index(conn, query, backend, limit)
        text = json.dumps({"query": query, "hits": results}, indent=2, ensure_ascii=False)
        _respond(id_, {"content": [{"type": "text", "text": text}], "isError": False})
    except Exception as exc:  # surface as a tool-level error, not a transport error
        _respond(id_, {"content": [{"type": "text", "text": f"error: {exc}"}], "isError": True})


HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method")
        id_ = req.get("id")
        params = req.get("params", {}) or {}

        if method == "notifications/initialized" or id_ is None:
            continue  # notifications get no response

        handler = HANDLERS.get(method)
        if handler is None:
            _respond(id_, error={"code": -32601, "message": f"method not found: {method}"})
            continue
        handler(id_, params)


if __name__ == "__main__":
    main()
