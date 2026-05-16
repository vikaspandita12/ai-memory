"""Global AI Memory HTTP API + MCP stdio server.

HTTP API (port 7688) — any IDE/script can call:
  GET  /context/{project}         → full project context
  GET  /projects                  → all known projects
  GET  /search?q=...&project=...  → search episodes
  POST /episode                   → store new episode
  GET  /global                    → recent activity across all projects
  GET  /mcp-config                → returns MCP config to paste into IDE

MCP stdio — pipe stdin/stdout for Cursor/Claude/Windsurf:
  python http_server.py --mcp
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import memory_core

app = FastAPI(title="Global AI Memory", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "vikaspandita12")


@app.on_event("startup")
def startup():
    try:
        memory_core.ensure_schema()
    except Exception as e:
        print(f"Schema init warning: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-memory-global", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/projects")
def list_projects():
    return {"projects": memory_core.get_all_projects()}


@app.get("/context/{project}")
def get_context(project: str):
    return memory_core.get_project_context(project)


@app.get("/global")
def global_context(limit: int = 20):
    return {"episodes": memory_core.get_global_context(limit=limit)}


@app.get("/search")
def search(q: str = Query(...), project: str | None = None, limit: int = 10):
    return {"results": memory_core.search_episodes(project, q, limit)}


class EpisodeIn(BaseModel):
    project: str
    title: str
    body: str
    source: str = "ai"
    tags: list[str] = []


@app.post("/episode")
def add_episode(ep: EpisodeIn):
    ep_id = memory_core.add_episode(ep.project, ep.title, ep.body, ep.source, ep.tags)
    return {"id": ep_id, "stored": True}


@app.get("/mcp-config")
def mcp_config():
    """Returns the MCP config JSON to paste into any IDE."""
    return {
        "description": "Paste this into your IDE MCP config",
        "cursor_path": "~/.cursor/mcp.json",
        "config": {
            "mcpServers": {
                "ai-memory-global": {
                    "command": "curl",
                    "args": ["-s", "http://localhost:7688/context/{project}"],
                    "description": "Global AI memory — reads GitHub + Graphiti context for any project"
                }
            }
        }
    }


# ── MCP stdio server (for Cursor/Claude direct pipe) ─────────────────────────

MCP_TOOLS = {
    "get_project_memory": {
        "description": "Get full context for a project (current state, recent episodes, all past work). Call this FIRST at session start.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name (e.g. 'ThreatForge', 'MyApp'). Use 'auto' to detect from git."}
            },
            "required": ["project"]
        }
    },
    "search_memory": {
        "description": "Search across all projects for any past work, bugs found, decisions made, or context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "project": {"type": "string", "description": "Optional: filter to specific project"}
            },
            "required": ["query"]
        }
    },
    "save_note": {
        "description": "Save important context, decision, or finding to memory so future sessions remember it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["project", "title", "content"]
        }
    },
    "list_projects": {
        "description": "List all projects stored in memory with last activity.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    }
}


def _detect_project() -> str:
    """Try to detect project name from environment."""
    cwd = os.getcwd()
    return os.path.basename(cwd) or "unknown"


async def _handle_mcp_tool(name: str, args: dict) -> str:
    if name == "get_project_memory":
        project = args.get("project", "auto")
        if project == "auto":
            project = _detect_project()
        ctx = memory_core.get_project_context(project)
        episodes = ctx.get("episodes", [])
        lines = [f"# Memory: {project}\n"]
        lines.append(f"Total episodes: {len(episodes)}\n")
        for ep in episodes[:10]:
            lines.append(f"## [{ep.get('timestamp','')[:10]}] {ep.get('title','')}")
            lines.append(ep.get("body", "")[:400])
            lines.append("")
        all_p = ctx.get("all_projects", [])
        if all_p:
            lines.append(f"\nAll known projects: {', '.join(p['name'] for p in all_p)}")
        return "\n".join(lines)

    elif name == "search_memory":
        results = memory_core.search_episodes(args.get("project"), args["query"], limit=8)
        if not results:
            return f"No memory found for: {args['query']}"
        lines = [f"Search results for '{args['query']}':\n"]
        for r in results:
            lines.append(f"[{r.get('project','')}] {r.get('title','')}: {r.get('body','')[:300]}")
        return "\n".join(lines)

    elif name == "save_note":
        ep_id = memory_core.add_episode(
            args["project"], args["title"], args["content"],
            source="ai-note", tags=["manual"]
        )
        return f"Saved to memory: '{args['title']}' (id: {ep_id})"

    elif name == "list_projects":
        projects = memory_core.get_all_projects()
        if not projects:
            return "No projects in memory yet."
        lines = ["Projects in memory:\n"]
        for p in projects:
            lines.append(f"- {p['name']}: {p['episodes']} episodes, last active {str(p.get('updated',''))[:10]}")
        return "\n".join(lines)

    return f"Unknown tool: {name}"


async def run_mcp_stdio():
    """MCP stdio server — pipe stdin/stdout."""
    reader = asyncio.StreamReader()
    loop = asyncio.get_event_loop()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    try:
        memory_core.ensure_schema()
    except Exception:
        pass

    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            req = json.loads(line.decode())
            method = req.get("method", "")
            req_id = req.get("id")

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "ai-memory-global", "version": "1.0.0"},
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"tools": [{"name": k, **v} for k, v in MCP_TOOLS.items()]}
                }
            elif method == "tools/call":
                tool_name = req.get("params", {}).get("name", "")
                tool_args = req.get("params", {}).get("arguments", {})
                result = await _handle_mcp_tool(tool_name, tool_args)
                resp = {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"content": [{"type": "text", "text": result}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

            sys.stdout.buffer.write((json.dumps(resp) + "\n").encode())
            sys.stdout.buffer.flush()
        except Exception:
            continue


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        asyncio.run(run_mcp_stdio())
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=7688)
