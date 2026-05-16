"""Global AI memory core — stores context for ALL projects.

Every project, every IDE, every session writes here.
Neo4j stores the knowledge graph. Projects are tagged by name.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from neo4j import GraphDatabase

log = logging.getLogger("ai.memory")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "vikasai123")

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


def ensure_schema():
    """Create constraints and indexes on first run."""
    with _get_driver().session() as s:
        s.run("CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE")
        s.run("CREATE CONSTRAINT episode_id IF NOT EXISTS FOR (e:Episode) REQUIRE e.id IS UNIQUE")
        s.run("CREATE INDEX episode_project IF NOT EXISTS FOR (e:Episode) ON (e.project)")
        s.run("CREATE INDEX episode_time IF NOT EXISTS FOR (e:Episode) ON (e.timestamp)")


def add_episode(project: str, title: str, body: str, source: str = "ai", tags: list[str] | None = None) -> str:
    """Store an episode (event/note/finding) for a project."""
    ep_id = f"{project}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    ts = datetime.now(timezone.utc).isoformat()
    with _get_driver().session() as s:
        s.run("""
            MERGE (p:Project {name: $project})
            SET p.last_updated = $ts
            CREATE (e:Episode {
                id: $id, project: $project, title: $title,
                body: $body, source: $source, tags: $tags, timestamp: $ts
            })
            CREATE (p)-[:HAS_EPISODE]->(e)
        """, project=project, id=ep_id, title=title, body=body,
             source=source, tags=tags or [], ts=ts)
    return ep_id


def search_episodes(project: str | None, query: str, limit: int = 10) -> list[dict]:
    """Full-text search over episodes. Project=None searches all projects."""
    with _get_driver().session() as s:
        if project:
            result = s.run("""
                MATCH (e:Episode {project: $project})
                WHERE toLower(e.body) CONTAINS toLower($query)
                   OR toLower(e.title) CONTAINS toLower($query)
                RETURN e ORDER BY e.timestamp DESC LIMIT $limit
            """, project=project, query=query, limit=limit)
        else:
            result = s.run("""
                MATCH (e:Episode)
                WHERE toLower(e.body) CONTAINS toLower($query)
                   OR toLower(e.title) CONTAINS toLower($query)
                RETURN e ORDER BY e.timestamp DESC LIMIT $limit
            """, query=query, limit=limit)
        return [dict(r["e"]) for r in result]


def get_project_context(project: str, max_episodes: int = 15) -> dict:
    """Get full context for a project — recent episodes + summary."""
    with _get_driver().session() as s:
        # Recent episodes
        episodes = s.run("""
            MATCH (p:Project {name: $project})-[:HAS_EPISODE]->(e:Episode)
            RETURN e ORDER BY e.timestamp DESC LIMIT $limit
        """, project=project, limit=max_episodes).data()

        # All projects list
        projects = s.run("MATCH (p:Project) RETURN p.name as name, p.last_updated as updated ORDER BY p.last_updated DESC").data()

    return {
        "project": project,
        "episodes": [dict(e["e"]) for e in episodes],
        "all_projects": projects,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


def get_all_projects() -> list[dict]:
    with _get_driver().session() as s:
        result = s.run("""
            MATCH (p:Project)
            OPTIONAL MATCH (p)-[:HAS_EPISODE]->(e:Episode)
            RETURN p.name as name, p.last_updated as updated, count(e) as episodes
            ORDER BY p.last_updated DESC
        """)
        return [dict(r) for r in result]


def get_global_context(limit: int = 20) -> list[dict]:
    """Get most recent episodes across ALL projects."""
    with _get_driver().session() as s:
        result = s.run("""
            MATCH (e:Episode)
            RETURN e ORDER BY e.timestamp DESC LIMIT $limit
        """, limit=limit)
        return [dict(r["e"]) for r in result]
