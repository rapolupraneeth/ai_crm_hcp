import json

from sqlalchemy.orm import Session

from services.interaction_service import InteractionService


def run_history_tool(db: Session, external_id: str | None = None, full_name: str | None = None) -> dict:
    interactions = InteractionService(db).get_hcp_history(external_id=external_id, full_name=full_name)
    if not interactions:
        return {
            "message": "No interaction history found for this HCP.",
            "data": {"hcp": {"external_id": external_id, "full_name": full_name}, "interaction": {}, "follow_up": {}, "compliance_flags": []},
            "metadata": {"tool": "history_tool", "count": 0},
        }

    latest = interactions[0]
    key_points = []
    if latest.key_points:
        try:
            key_points = json.loads(latest.key_points)
        except json.JSONDecodeError:
            key_points = [latest.key_points]

    return {
        "message": f"Retrieved {len(interactions)} historical interactions.",
        "data": {
            "hcp": {"external_id": external_id, "full_name": full_name},
            "interaction": {
                "interaction_id": latest.id,
                "interaction_type": latest.interaction_type,
                "channel": latest.channel,
                "sentiment": latest.sentiment,
                "summary": latest.summary,
                "key_points": key_points,
                "follow_up_required": latest.follow_up_required,
                "interaction_date": latest.interaction_date,
            },
            "follow_up": {},
            "compliance_flags": [],
        },
        "metadata": {"tool": "history_tool", "count": len(interactions)},
    }
