import json
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from models.hcp_model import HCP
from models.interaction_model import FollowUp, Interaction, InteractionEditHistory
from schemas.interaction_schema import StructuredFormData


class InteractionService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_hcp(self, payload: dict) -> HCP:
        external_id = payload.get("external_id")
        full_name = payload.get("full_name")

        hcp = None
        if external_id:
            hcp = self.db.scalar(select(HCP).where(HCP.external_id == external_id))
        if not hcp and full_name:
            hcp = self.db.scalar(select(HCP).where(HCP.full_name == full_name))

        if hcp:
            for field in ["full_name", "specialty", "organization", "city"]:
                if payload.get(field):
                    setattr(hcp, field, payload[field])
            return hcp

        hcp = HCP(
            external_id=external_id or f"auto-{int(datetime.utcnow().timestamp())}",
            full_name=full_name or "Unknown HCP",
            specialty=payload.get("specialty"),
            organization=payload.get("organization"),
            city=payload.get("city"),
        )
        self.db.add(hcp)
        self.db.flush()
        return hcp

    def create_interaction_from_form(self, form_data: StructuredFormData, message: str | None = None) -> Interaction:
        hcp = self._get_or_create_hcp(form_data.hcp.model_dump())
        payload = form_data.interaction.model_dump()
        key_points = payload.pop("key_points", [])
        interaction_date = payload.pop("interaction_date", None) or datetime.utcnow()
        payload.pop("interaction_id", None)

        interaction = Interaction(
            hcp_id=hcp.id,
            key_points=json.dumps(key_points),
            interaction_date=interaction_date,
            message_content=message,
            **payload,
        )
        self.db.add(interaction)
        self.db.flush()

        if form_data.follow_up.suggestion:
            followup = FollowUp(
                interaction_id=interaction.id,
                suggestion=form_data.follow_up.suggestion,
                due_days=form_data.follow_up.due_days,
            )
            self.db.add(followup)

        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def update_interaction_from_form(
        self, interaction_id: int, form_data: StructuredFormData, edit_instruction: str
    ) -> Interaction:
        interaction = self.db.get(Interaction, interaction_id)
        if interaction is None:
            raise ValueError(f"Interaction {interaction_id} not found")

        old_snapshot = {
            "interaction_type": interaction.interaction_type,
            "channel": interaction.channel,
            "sentiment": interaction.sentiment,
            "summary": interaction.summary,
            "key_points": interaction.key_points,
            "follow_up_required": interaction.follow_up_required,
        }
        payload = form_data.interaction.model_dump(exclude_none=True)
        payload.pop("interaction_id", None)
        if "key_points" in payload:
            payload["key_points"] = json.dumps(payload["key_points"])

        for key, value in payload.items():
            setattr(interaction, key, value)

        history = InteractionEditHistory(
            interaction_id=interaction.id,
            original_snapshot=json.dumps(old_snapshot),
            edited_snapshot=json.dumps(payload),
            edit_instruction=edit_instruction,
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def get_hcp_history(self, external_id: str | None = None, full_name: str | None = None) -> list[Interaction]:
        stmt = select(Interaction).join(HCP)
        if external_id:
            stmt = stmt.where(HCP.external_id == external_id)
        elif full_name:
            stmt = stmt.where(HCP.full_name == full_name)
        else:
            return []
        stmt = stmt.order_by(desc(Interaction.interaction_date)).limit(10)
        return list(self.db.scalars(stmt).all())
