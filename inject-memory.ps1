# inject-memory.ps1
# Run this ONCE inside ANY project folder to inject the full AI memory system
# Usage: cd your-project && powershell -File C:\Users\vikas\.ai-memory\inject-memory.ps1
#
# What it does:
#   1. Creates .ai/ folder with memory.md, progress.md, architecture.md
#   2. Creates AGENTS.md (universal AI instructions)
#   3. Creates .windsurfrules, .antigravity, .github/copilot-instructions.md
#   4. Creates .cursor/rules/ and .cursor/mcp.json (local project override)
#   5. Registers project in global memory (Neo4j)
#   6. Adds .vscode/tasks.json for auto-load

param(
    [string]$ProjectName = "",
    [string]$ProjectDesc = "",
    [string]$Stack = ""
)

$ErrorActionPreference = "Stop"

# Detect project info
if (-not $ProjectName) { $ProjectName = Split-Path -Leaf (Get-Location) }
if (-not $ProjectDesc) { $ProjectDesc = "A software project by vikaspandita12" }
if (-not $Stack) { $Stack = "Unknown (update .ai/memory.md)" }

$GithubUser = "vikaspandita12"
$Now = Get-Date -Format "yyyy-MM-dd HH:mm UTC"
$RepoUrl = "https://github.com/$GithubUser/$ProjectName"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host " Injecting AI Memory System into: $ProjectName" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# ── 1. Create .ai/ folder ──────────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path ".ai" | Out-Null

@"
# $ProjectName — AI Project Memory
<!-- Last updated: $Now -->
<!-- READ THIS FIRST in every session, every IDE, every AI tool -->

## OWNER
- GitHub: $GithubUser
- Repo: $RepoUrl

## WHAT THIS PROJECT IS
$ProjectDesc

## TECH STACK
$Stack

## CURRENT STATE (update this as you work)
- [ ] Project just initialized

## HOW TO START
(fill in your start commands here)

## KEY FILES
(fill in important files here)

## CRITICAL RULES
1. Always update this file after significant changes
2. Commit .ai/ files so all IDEs get the update
"@ | Set-Content ".ai\memory.md" -Encoding UTF8

@"
# $ProjectName — Progress Tracker
<!-- Updated by AI after every significant change -->

## In Progress
- [ ] Initial setup

## Completed
- [x] AI memory system injected ($Now)

## Next Steps
(fill in next steps)
"@ | Set-Content ".ai\progress.md" -Encoding UTF8

@"
# $ProjectName — Architecture Notes
(Document your architecture decisions here)

## Stack
$Stack

## Key Design Decisions
(fill in as the project grows)
"@ | Set-Content ".ai\architecture.md" -Encoding UTF8

Write-Host "  [1/7] Created .ai/ (memory.md, progress.md, architecture.md)" -ForegroundColor Green

# ── 2. AGENTS.md ──────────────────────────────────────────────────────────────
@"
# AGENTS.md — Universal AI Instructions for $ProjectName
<!-- Read by: GitHub Copilot, Cursor, Windsurf, Antigravity, VS Code AI -->

## START EVERY SESSION HERE
1. Call MCP tool: get_project_memory (project: "$ProjectName")
2. Read .ai/memory.md — current state
3. Read .ai/progress.md — pending tasks
4. Confirm: "Memory loaded. [one line state]. Ready."

## Project
- Name: $ProjectName
- Owner: $GithubUser
- Repo: $RepoUrl
- Stack: $Stack

## After Making Changes
Update .ai/memory.md + .ai/progress.md → commit → push
This syncs context to ALL IDEs automatically.

## Memory Query
http://localhost:7688/context/$ProjectName
"@ | Set-Content "AGENTS.md" -Encoding UTF8

Write-Host "  [2/7] Created AGENTS.md" -ForegroundColor Green

# ── 3. IDE rule files ──────────────────────────────────────────────────────────
@"
# $ProjectName — Windsurf Rules
Read .ai/memory.md first. Call get_project_memory MCP tool.
Project: $ProjectName | Owner: $GithubUser | Repo: $RepoUrl
Stack: $Stack
After changes: update .ai/memory.md and commit.
"@ | Set-Content ".windsurfrules" -Encoding UTF8

@"
# $ProjectName — Antigravity Context
Read .ai/memory.md first. Project: $ProjectName
Owner: $GithubUser | Stack: $Stack
Memory API: http://localhost:7688/context/$ProjectName
"@ | Set-Content ".antigravity" -Encoding UTF8

# GitHub Copilot
New-Item -ItemType Directory -Force -Path ".github" | Out-Null
@"
# GitHub Copilot Instructions — $ProjectName
Read .ai/memory.md before starting.
Project: $ProjectName | Owner: $GithubUser | Stack: $Stack
After changes: update .ai/memory.md + .ai/progress.md + commit.
Memory API: http://localhost:7688/context/$ProjectName
"@ | Set-Content ".github\copilot-instructions.md" -Encoding UTF8

Write-Host "  [3/7] Created .windsurfrules, .antigravity, .github/copilot-instructions.md" -ForegroundColor Green

# ── 4. Cursor rules ──────────────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path ".cursor\rules" | Out-Null
@"
---
description: Auto-load memory for $ProjectName
alwaysApply: true
---
MANDATORY: Before anything else, call MCP tool get_project_memory with project="$ProjectName".
Then read .ai/memory.md and .ai/progress.md.
Confirm: "Memory loaded. [state summary]. Ready."
After changes: update .ai/memory.md + commit.
"@ | Set-Content ".cursor\rules\auto-memory.mdc" -Encoding UTF8

@"
{
  "mcpServers": {
    "ai-memory-global": {
      "command": "docker",
      "args": ["exec", "-i", "ai-memory-mcp", "python", "http_server.py", "--mcp"],
      "description": "Global AI memory for $ProjectName"
    }
  }
}
"@ | Set-Content ".cursor\mcp.json" -Encoding UTF8

Write-Host "  [4/7] Created .cursor/rules + .cursor/mcp.json" -ForegroundColor Green

# ── 5. VS Code tasks ─────────────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path ".vscode" | Out-Null
@"
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Load AI Memory",
      "type": "shell",
      "command": "curl -s http://localhost:7688/context/$ProjectName",
      "runOptions": { "runOn": "folderOpen" },
      "presentation": { "reveal": "silent", "panel": "shared" }
    },
    {
      "label": "Save Note to Memory",
      "type": "shell",
      "command": "curl -s -X POST http://localhost:7688/episode -H 'Content-Type: application/json' -d '{\"project\":\"$ProjectName\",\"title\":\"Note\",\"body\":\"` + '${input:note}' + `\",\"source\":\"manual\"}'",
      "presentation": { "reveal": "always" }
    }
  ],
  "inputs": [{"id": "note", "type": "promptString", "description": "Note to save to memory"}]
}
"@ | Set-Content ".vscode\tasks.json" -Encoding UTF8

Write-Host "  [5/7] Created .vscode/tasks.json" -ForegroundColor Green

# ── 6. GitHub Action for auto-memory ────────────────────────────────────────
New-Item -ItemType Directory -Force -Path ".github\workflows" | Out-Null
@"
name: Auto-Update AI Memory
on:
  push:
    branches: [main, master]
permissions:
  contents: write
jobs:
  memory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: `${{ secrets.GITHUB_TOKEN }}
      - name: Update memory timestamp
        run: |
          NOW=`$(date -u '+%Y-%m-%d %H:%M UTC')
          MSG=`$(git log -1 --format='%s')
          sed -i "s|<!-- Last updated:.*-->|<!-- Last updated: `$NOW -->|g" .ai/memory.md
          echo "" >> .ai/progress.md
          echo "- [`$NOW`] `$MSG" >> .ai/progress.md
          git config user.name 'AI Memory Bot'
          git config user.email 'memory@ai.local'
          git add .ai/
          git diff --staged --quiet || git commit -m 'chore: auto-update memory [skip ci]'
          git push
"@ | Set-Content ".github\workflows\update-memory.yml" -Encoding UTF8

Write-Host "  [6/7] Created .github/workflows/update-memory.yml" -ForegroundColor Green

# ── 7. Register in global memory ─────────────────────────────────────────────
$body = @{
    project = $ProjectName
    title   = "Project initialized: $ProjectName"
    body    = "New project registered in global AI memory.`nName: $ProjectName`nOwner: $GithubUser`nRepo: $RepoUrl`nStack: $Stack`nCreated: $Now"
    source  = "inject-memory-script"
    tags    = @("init", "project")
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "http://localhost:7688/episode" -Method POST -Body $body -ContentType "application/json" | Out-Null
    Write-Host "  [7/7] Registered in global Graphiti memory" -ForegroundColor Green
} catch {
    Write-Host "  [7/7] Global memory API not running yet — start with: docker compose -f C:\Users\vikas\.ai-memory\docker-compose.yml up -d" -ForegroundColor Yellow
}

# ── Update .gitignore ────────────────────────────────────────────────────────
if (Test-Path ".gitignore") {
    $gi = Get-Content ".gitignore" -Raw
    if ($gi -notmatch "\.env") { Add-Content ".gitignore" "`n.env" }
} else {
    ".env`n.env.local`nnode_modules/`n__pycache__/`n*.pyc" | Set-Content ".gitignore"
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host " Done! $ProjectName is now memory-enabled." -ForegroundColor Green
Write-Host ""
Write-Host " Next steps:" -ForegroundColor White
Write-Host "  1. Edit .ai/memory.md — describe the project" -ForegroundColor White
Write-Host "  2. git add . && git commit -m 'feat: add AI memory system'" -ForegroundColor White
Write-Host "  3. Open in any IDE — memory auto-loads" -ForegroundColor White
Write-Host ""
Write-Host " Query memory: curl http://localhost:7688/context/$ProjectName" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
