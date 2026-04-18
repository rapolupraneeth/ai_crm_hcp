from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_agent.llm import get_llm
from schemas.interaction_schema import StructuredFormData
from services.interaction_service import InteractionService


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "edit_prompt.txt"


class EditResult(BaseModel):
    hcp: dict = Field(default_factory=dict)
    interaction: dict = Field(default_factory=dict)
    follow_up: dict = Field(default_factory=dict)


def _merge_nested(base: dict, patch: dict) -> dict:
    merged = base.copy()
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_nested(merged[key], value)
        elif value is not None:
            merged[key] = value
    return merged


def run_edit_tool(db: Session, user_message: str, current_form_data: dict, interaction_id: int) -> dict:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    llm = get_llm(temperature=0.0).with_structured_output(EditResult)
    edited = llm.invoke(
        f"{system_prompt}\n\nExisting record:\n{current_form_data}\n\nEdit request:\n{user_message}"
    )
    merged_data = _merge_nested(current_form_data, edited.model_dump())

    form = StructuredFormData.model_validate(merged_data)
    interaction = InteractionService(db).update_interaction_from_form(
        interaction_id=interaction_id, form_data=form, edit_instruction=user_message
    )
    return {
        "message": "Interaction updated successfully.",
        "data": form.model_dump(),
        "metadata": {"interaction_id": interaction.id, "tool": "edit_tool"},
    }
