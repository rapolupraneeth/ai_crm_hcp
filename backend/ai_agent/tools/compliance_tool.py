from pydantic import BaseModel, Field

from ai_agent.llm import get_llm


class ComplianceResult(BaseModel):
    compliant: bool = True
    flags: list[str] = Field(default_factory=list)
    rationale: str = "No compliance issues detected."


def run_compliance_tool(user_message: str) -> dict:
    llm = get_llm(temperature=0.0).with_structured_output(ComplianceResult)
    result = llm.invoke(
        "Review this pharma CRM note for potential compliance risk.\n"
        "Flag unsupported efficacy claims, off-label promotion, missing disclaimers, or patient data exposure.\n"
        f"Text: {user_message}"
    )
    return {
        "message": result.rationale,
        "data": {"hcp": {}, "interaction": {}, "follow_up": {}, "compliance_flags": result.flags},
        "metadata": {"tool": "compliance_tool", "compliant": result.compliant},
    }
