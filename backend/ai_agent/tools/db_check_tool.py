from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from pydantic import BaseModel, Field
from typing import List, Optional

from ai_agent.llm import get_llm
from models.hcp_model import HCP
from models.interaction_model import Interaction


class HCPInfo(BaseModel):
    id: int
    full_name: str
    external_id: Optional[str]
    specialty: Optional[str]
    organization: Optional[str]
    city: Optional[str]


class InteractionSummary(BaseModel):
    id: int
    interaction_type: Optional[str]
    date: Optional[str]
    time: Optional[str]
    summary: Optional[str]
    interaction_date: str


def find_hcp_by_name(db: Session, name: str) -> List[HCPInfo]:
    """Find HCP by name (partial match)"""
    stmt = select(HCP).where(HCP.full_name.ilike(f"%{name}%"))
    results = db.scalars(stmt).all()
    return [HCPInfo(
        id=hcp.id,
        full_name=hcp.full_name,
        external_id=hcp.external_id,
        specialty=hcp.specialty,
        organization=hcp.organization,
        city=hcp.city
    ) for hcp in results]


def get_hcp_by_id(db: Session, hcp_id: int) -> Optional[HCPInfo]:
    """Get HCP details by ID"""
    hcp = db.get(HCP, hcp_id)
    if hcp:
        return HCPInfo(
            id=hcp.id,
            full_name=hcp.full_name,
            external_id=hcp.external_id,
            specialty=hcp.specialty,
            organization=hcp.organization,
            city=hcp.city
        )
    return None


def get_recent_interactions(db: Session, hcp_id: int, limit: int = 5) -> List[InteractionSummary]:
    """Get recent interactions for an HCP"""
    stmt = select(Interaction).where(Interaction.hcp_id == hcp_id).order_by(desc(Interaction.interaction_date)).limit(limit)
    results = db.scalars(stmt).all()
    return [InteractionSummary(
        id=interaction.id,
        interaction_type=interaction.interaction_type,
        date=interaction.date,
        time=interaction.time,
        summary=interaction.summary,
        interaction_date=interaction.interaction_date.isoformat()
    ) for interaction in results]


def check_interaction_exists(db: Session, hcp_id: int, date: str = None, interaction_type: str = None) -> bool:
    """Check if an interaction already exists for given criteria"""
    stmt = select(Interaction).where(Interaction.hcp_id == hcp_id)
    if date:
        stmt = stmt.where(Interaction.date == date)
    if interaction_type:
        stmt = stmt.where(Interaction.interaction_type == interaction_type)
    
    result = db.scalar(stmt)
    return result is not None


def run_db_check_tool(db: Session, query_type: str, **kwargs) -> dict:
    """Main tool function that LLM can call to query database"""
    try:
        if query_type == "find_hcp":
            name = kwargs.get("name", "")
            results = find_hcp_by_name(db, name)
            return {
                "message": f"Found {len(results)} HCP(s) matching '{name}'",
                "data": {"hcps": [hcp.model_dump() for hcp in results]},
                "metadata": {"tool": "db_check", "query_type": query_type}
            }
        
        elif query_type == "get_hcp_details":
            hcp_id = kwargs.get("hcp_id")
            if not hcp_id:
                return {"message": "No HCP ID provided", "data": {}, "metadata": {"tool": "db_check", "error": "missing_hcp_id"}}
            hcp = get_hcp_by_id(db, hcp_id)
            if hcp:
                return {
                    "message": f"HCP details for ID {hcp_id}",
                    "data": {"hcp": hcp.model_dump()},
                    "metadata": {"tool": "db_check", "query_type": query_type}
                }
            else:
                return {"message": f"No HCP found with ID {hcp_id}", "data": {}, "metadata": {"tool": "db_check", "query_type": query_type}}
        
        elif query_type == "get_recent_interactions":
            hcp_id = kwargs.get("hcp_id")
            limit = kwargs.get("limit", 5)
            if not hcp_id:
                return {"message": "No HCP ID provided", "data": {}, "metadata": {"tool": "db_check", "error": "missing_hcp_id"}}
            interactions = get_recent_interactions(db, hcp_id, limit)
            return {
                "message": f"Found {len(interactions)} recent interactions for HCP ID {hcp_id}",
                "data": {"interactions": [interaction.model_dump() for interaction in interactions]},
                "metadata": {"tool": "db_check", "query_type": query_type}
            }
        
        elif query_type == "check_interaction_exists":
            hcp_id = kwargs.get("hcp_id")
            date = kwargs.get("date")
            interaction_type = kwargs.get("interaction_type")
            if not hcp_id:
                return {"message": "No HCP ID provided", "data": {}, "metadata": {"tool": "db_check", "error": "missing_hcp_id"}}
            exists = check_interaction_exists(db, hcp_id, date, interaction_type)
            return {
                "message": f"Interaction exists: {exists}",
                "data": {"exists": exists},
                "metadata": {"tool": "db_check", "query_type": query_type}
            }
        
        else:
            return {"message": f"Unknown query type: {query_type}", "data": {}, "metadata": {"tool": "db_check", "error": "unknown_query_type"}}
    
    except Exception as e:
        return {"message": f"Database query failed: {str(e)}", "data": {}, "metadata": {"tool": "db_check", "error": str(e)}}