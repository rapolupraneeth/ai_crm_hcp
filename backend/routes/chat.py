import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.interaction_schema import ChatRequest, ChatResponse
from services.agent_service import AgentService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])
agent_service = AgentService()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    try:
        return agent_service.process_message(db, request.session_id, request.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat processing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to process chat request.") from exc
    
@router.post("/reset")
def reset_chat(request: dict, db: Session = Depends(get_db)):
    session_id = request.get("session_id")
    agent_service.reset_session(db, session_id)
    return {"message": "Session reset successful"}
