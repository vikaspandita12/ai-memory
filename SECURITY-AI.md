# AI Security Checklist — ai-memory

Reference: [Awesome AI Security](https://github.com/vikaspandita12/awesome-ai-security)

**AI features:** Global MCP memory across all projects (Neo4j + Graphiti)

## Never store

- [ ] API keys, `.env`, passwords, live session cookies from scans

## Hooks

- [ ] Commit hook skips secret files
- [ ] Scan ingest: severity + summary only, redacted

## Infrastructure

- [ ] Neo4j not public without auth; change default passwords in prod
- [ ] Port 7688 not exposed to internet without TLS + auth

**Tracking issue:** #1
