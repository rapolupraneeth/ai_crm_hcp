from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_agent.llm import get_llm
from schemas.interaction_schema import StructuredFormData
from services.interaction_service import InteractionService


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extraction_prompt.txt"


class ExtractionResult(BaseModel):
    hcp: dict = Field(default_factory=dict)
    interaction: dict = Field(default_factory=dict)
    follow_up: dict = Field(default_factory=dict)


def run_log_tool(db: Session, user_message: str) -> dict:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    llm = get_llm(temperature=0.1).with_structured_output(ExtractionResult)
    extracted = llm.invoke(
        f"{system_prompt}\n\nUser message:\n{user_message}\n\nReturn strict JSON."
    )

    form = StructuredFormData.model_validate(extracted.model_dump())
    interaction = InteractionService(db).create_interaction_from_form(form, user_message)

    return {
        "message": "Interaction logged successfully.",
        "data": form.model_dump(),
        "metadata": {"interaction_id": interaction.id, "tool": "log_tool"},
    }
