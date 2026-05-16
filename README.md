# Global AI Memory — vikaspandita12

Persistent memory across ALL projects, ALL IDEs, ALL sessions.
Never start over. Every AI picks up exactly where you left off.

## Architecture

```
Any IDE (Cursor / Windsurf / VS Code / Antigravity)
        ↓  MCP tool: get_project_memory
ai-memory-mcp container  ←→  Neo4j (Graphiti graph)
        ↑
  Every git commit (global hook) → stores context automatically
  Every scan result (ThreatForge) → stores findings automatically
  Every project open → reads latest context from GitHub + Neo4j
```

## Start the Global Memory Service (once, then always-on)

```powershell
cd C:\Users\vikas\.ai-memory
docker compose up -d
```

Services:
- Neo4j graph DB:   http://localhost:7474  (neo4j / vikasai123)
- Memory HTTP API:  http://localhost:7688
- MCP stdio:        docker exec -i ai-memory-mcp python http_server.py --mcp

## Add Memory to Any New Project

```powershell
cd C:\path\to\your-new-project
powershell -File C:\Users\vikas\.ai-memory\inject-memory.ps1 -ProjectName "MyApp" -ProjectDesc "What it does" -Stack "Python/React/etc"
```

## Query Memory from Anywhere

```powershell
# All projects
curl http://localhost:7688/projects

# Specific project
curl http://localhost:7688/context/ThreatForge

# Search across ALL projects
curl "http://localhost:7688/search?q=XSS+vulnerability"

# Recent activity globally
curl http://localhost:7688/global
```

## How Memory Gets Updated (Zero Manual Work)

| Trigger | What's stored |
|---------|--------------|
| Any git commit (any repo) | Commit message, files, branch |
| ThreatForge scan completes | Target, findings, severity |
| Branch checkout | Branch switch context |
| IDE session start | Session start event |
| Manual note | Whatever you tell it |

## Cursor MCP (auto-configured globally)
`~/.cursor/mcp.json` is already set to use `ai-memory-global` server.
Every Cursor workspace gets the memory tools automatically.
