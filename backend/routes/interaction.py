from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from db.database import get_db
from models.interaction_model import Interaction
from schemas.interaction_schema import InteractionOut


router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("/recent", response_model=list[InteractionOut])
def get_recent_interactions(limit: int = 20, db: Session = Depends(get_db)) -> list[Interaction]:
    stmt = select(Interaction).order_by(desc(Interaction.interaction_date)).limit(limit)
    return list(db.scalars(stmt).all())
