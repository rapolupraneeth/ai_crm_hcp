from sqlalchemy import select
from sqlalchemy.orm import Session
from models.session_state import SessionState
from models.interaction_model import UploadedFile
from schemas.interaction_schema import StructuredFormData, UploadedFileInfo
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class SessionService:
    @classmethod
    def load_session_state(cls, db: Session, session_id: str) -> Dict[str, Any]:
        stmt = select(SessionState).where(SessionState.session_id == session_id)
        state = db.scalar(stmt)
        if not state:
            return {"hcp": {}, "interaction": {}, "follow_up": {}, "compliance_flags": []}
        
        # Merge data sections
        data = {}
        if state.hcp_data:
            data["hcp"] = state.hcp_data
        if state.interaction_data:
            data["interaction"] = state.interaction_data
            # Load uploaded files for the interaction if interaction_id exists
            interaction_data = data["interaction"]
            interaction_id = interaction_data.get("interaction_id")
            if interaction_id:
                uploaded_files = db.query(UploadedFile).filter(UploadedFile.interaction_id == interaction_id).all()
                interaction_data["uploaded_files"] = [
                    UploadedFileInfo(
                        id=file.id,
                        filename=file.filename,
                        original_filename=file.original_filename,
                        file_path=file.file_path,
                        file_type=file.file_type,
                        mime_type=file.mime_type,
                        file_size=file.file_size,
                        uploaded_at=file.uploaded_at
                    ).model_dump()
                    for file in uploaded_files
                ]
        if state.follow_up_data:
            data["follow_up"] = state.follow_up_data
        if state.compliance_flags:
            data["compliance_flags"] = state.compliance_flags
        return data or {"hcp": {}, "interaction": {}, "follow_up": {}, "compliance_flags": []}

    @classmethod
    def save_session_state(cls, db: Session, session_id: str, form_data: StructuredFormData):
        stmt = select(SessionState).where(SessionState.session_id == session_id)
        state = db.scalar(stmt)
        data = form_data.model_dump()
        
        if state:
            state.hcp_data = data.get("hcp")
            state.interaction_data = data.get("interaction")
            state.follow_up_data = data.get("follow_up")
            state.compliance_flags = data.get("compliance_flags")
            state.updated_at = datetime.now(timezone.utc)
            db.add(state)
        else:
            state = SessionState(
                session_id=session_id,
                hcp_data=data.get("hcp"),
                interaction_data=data.get("interaction"),
                follow_up_data=data.get("follow_up"),
                compliance_flags=data.get("compliance_flags")
            )
            db.add(state)
        db.commit()
        db.refresh(state)

    @classmethod
    def delete_session_state(cls, db: Session, session_id: str):
        stmt = select(SessionState).where(SessionState.session_id == session_id)
        state = db.scalar(stmt)
        if state:
            db.delete(state)
            db.commit()

