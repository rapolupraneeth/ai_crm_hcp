import logging
from typing import Any
from sqlalchemy.orm import Session
from services.session_service import SessionService
from ai_agent.agent import build_agent
from schemas.interaction_schema import ChatResponse, StructuredFormData

logger = logging.getLogger(__name__)

def deep_merge(old: dict, new: dict):
    result = old.copy()

    for key, value in new.items():
        if isinstance(value, dict):
            result[key] = deep_merge(result.get(key, {}), value)

        elif isinstance(value, list):
            # only overwrite if list has actual content
            if value:
                result[key] = value

        else:
            # ignore empty / null values
            if value is not None and str(value).strip() != "":
                result[key] = value

    return result

class AgentService:
    def __init__(self):
        self.graph = build_agent()

    def process_message(self, db: Session, session_id: str, message: str) -> ChatResponse:
        # Load from DB
        current_form_data = SessionService.load_session_state(db, session_id)

        result = self.graph.invoke(
            {"db": db, "message": message, "session_id": session_id, "current_form_data": current_form_data},
            config={"configurable": {"thread_id": session_id}},
        )
        response_data = result.get("response", {})
        new_data = response_data.get("data", {})
        final_data = deep_merge(current_form_data, new_data)
        structured_data = StructuredFormData.model_validate(final_data)
        
        # Save to DB
        SessionService.save_session_state(db, session_id, structured_data)

        response = ChatResponse(
            data=structured_data,
            message=response_data.get("message", "Processed message."),
            metadata=response_data.get("metadata", {}),
        )
        logger.info("Chat processed for session=%s action=%s", session_id, response.metadata.get("intent"))
        return response

    def reset_session(self, db: Session, session_id: str):
        SessionService.delete_session_state(db, session_id)
