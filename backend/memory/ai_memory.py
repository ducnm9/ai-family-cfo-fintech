"""AI Financial Memory — Store and retrieve historical advice and financial context."""

import json
from db.database import get_wrapped_db


def store_memory(user_id: int, category: str, content: str, metadata: dict = None) -> dict:
    """Store a memory entry for the user."""
    db = get_wrapped_db()
    db.execute(
        "INSERT INTO ai_memory (user_id, category, content, metadata) VALUES (%s, %s, %s, %s) RETURNING id",
        (user_id, category, content, json.dumps(metadata or {})),
    )
    entry_id = db.lastrowid
    db.commit()
    db.close()
    return {"id": entry_id, "category": category, "stored": True}


def retrieve_memories(user_id: int, category: str = None, limit: int = 20) -> list[dict]:
    """Retrieve memory entries for the user, optionally filtered by category."""
    db = get_wrapped_db()
    if category:
        rows = db.execute(
            "SELECT id, category, content, metadata, created_at FROM ai_memory "
            "WHERE user_id = %s AND category = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, category, limit),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id, category, content, metadata, created_at FROM ai_memory "
            "WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit),
        ).fetchall()
    db.close()

    return [
        {
            "id": r["id"],
            "category": r["category"],
            "content": r["content"],
            "metadata": r["metadata"] if isinstance(r["metadata"], dict) else json.loads(r["metadata"] or "{}"),
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


def delete_memory(user_id: int, memory_id: int) -> dict:
    """Delete a specific memory entry."""
    db = get_wrapped_db()
    db.execute("DELETE FROM ai_memory WHERE id = %s AND user_id = %s", (memory_id, user_id))
    db.commit()
    db.close()
    return {"deleted": True}


def store_recommendation_memory(user_id: int, recommendations: list[dict], score: int) -> dict:
    """Auto-store advisor recommendations as memory for future personalization."""
    summary = f"Score: {score}/100. " + " | ".join(
        r.get("title", "") for r in recommendations[:5]
    )
    return store_memory(user_id, "advisor_recommendation", summary, {
        "score": score,
        "recommendation_count": len(recommendations),
    })


def store_goal_memory(user_id: int, goal_name: str, status: str, details: dict) -> dict:
    """Track goal progress in memory."""
    content = f"Goal '{goal_name}': {status}"
    return store_memory(user_id, "goal_history", content, details)
