from pydantic import BaseModel, Field

from ai_agent.llm import get_llm


class SuggestResult(BaseModel):
    suggestion: str = Field(..., description="Specific, actionable follow-up suggestion based on the interaction")
    due_days: int | None = Field(default=7, description="Days until follow-up is due")


def run_suggest_tool(form_data: dict, sentiment: str | None = None) -> dict:
    """Generate a follow-up suggestion based on interaction data"""
    llm = get_llm(temperature=0.5).with_structured_output(SuggestResult)
    
    # Build context from form data
    hcp_name = form_data.get("hcp", {}).get("full_name", "")
    interaction_type = form_data.get("interaction", {}).get("interaction_type", "")
    summary = form_data.get("interaction", {}).get("summary", "")
    outcomes = form_data.get("interaction", {}).get("outcomes", "")
    materials = form_data.get("interaction", {}).get("materials", "")
    
    # Build a detailed context
    context = f"""You are a pharmaceutical sales assistant. Based on the following interaction details, suggest ONE specific, actionable follow-up action that would be appropriate for the sales team.

Interaction Details:
- HCP: {hcp_name}
- Type of Interaction: {interaction_type}
- Summary: {summary}
- Outcomes: {outcomes}
- Materials Discussed: {materials}
- Sentiment: {sentiment or 'neutral'}

Generate a follow-up suggestion that:
1. Is specific and actionable (not generic)
2. Is based on what happened in this interaction
3. Advances the relationship or product education
4. Is realistic for a pharma sales context
5. Is brief (one sentence, max 10 words)

Examples of good suggestions (but DO NOT copy these):
- "Send latest clinical trial data"
- "Schedule lab visit for product demo"
- "Follow up on prescribing questions"
- "Arrange lunch meeting with department"

Generate a unique suggestion based ONLY on the interaction details above."""
    
    try:
        result = llm.invoke(context)
    except Exception as e:
        return {
            "message": "I couldn't generate a follow-up suggestion at this time. Please try again.",
            "data": {
                "hcp": {},
                "interaction": {},
                "follow_up": {},
                "compliance_flags": [],
            },
            "metadata": {"tool": "suggest_tool", "intent": "suggest_follow_up", "error": str(e)},
        }
    
    return {
        "message": f"Here's my suggested follow-up: {result.suggestion}",
        "data": {
            "hcp": {},
            "interaction": {},
            "follow_up": {
                "suggestion": result.suggestion,
                "due_days": result.due_days or 7,
            },
            "compliance_flags": [],
        },
        "metadata": {"tool": "suggest_tool", "intent": "suggest_follow_up"},
    }
