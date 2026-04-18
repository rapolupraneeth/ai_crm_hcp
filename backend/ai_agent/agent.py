import logging
import os
from typing import Any, Literal, TypedDict, Optional

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_agent.llm import get_llm
from ai_agent.tools.compliance_tool import run_compliance_tool
from ai_agent.tools.edit_tool import run_edit_tool
from ai_agent.tools.history_tool import run_history_tool
from ai_agent.tools.log_tool import run_log_tool
from ai_agent.tools.suggest_tool import run_suggest_tool
from ai_agent.tools.db_check_tool import run_db_check_tool
from services.interaction_service import InteractionService
from schemas.interaction_schema import StructuredFormData,IntentResult,ExtractionResult


def load_prompt(filename: str) -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", filename)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    db: Session  # handled outside graph
    message: str
    session_id: str
    intent: Optional[str]
    extracted_data: Optional[dict[str, Any]]
    current_form_data: dict[str, Any]
    tool_result: dict[str, Any]
    response: Optional[dict[str, Any]]

def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("intent_detection", _intent_node)
    graph.add_node("extraction", _extract_data_node)
    graph.add_node("merge_data", _merge_data_node)
    graph.add_node("tool_execution", _execute_tool_node)
    graph.add_node("response", _respond_node)
    graph.add_edge(START, "intent_detection")
    graph.add_edge("intent_detection", "extraction")
    graph.add_edge("extraction", "merge_data")
    
    graph.add_conditional_edges(
        "merge_data",
        _route_from_intent,
        {
            "log_interaction": "tool_execution",
            "edit_interaction": "tool_execution",
            "suggest_follow_up": "tool_execution",
            "retrieve_history": "tool_execution",
            "emotional_support": "tool_execution",
            "abusive": "tool_execution",
            "out_of_scope": "tool_execution",
        },
    )
    graph.add_edge("tool_execution", "response")
    graph.add_edge("response", END)

    logger.info("LangGraph agent initialized.")
    return graph.compile(checkpointer=False)

def is_complete(data: dict) -> bool:
    try:
        return (
            data.get("hcp", {}).get("full_name") and
            data.get("interaction", {}).get("interaction_type")
        )
    except:
        return False


def deep_merge(old: dict, new: dict) -> dict:
    result = old.copy()
    for key, value in new.items():
        if isinstance(value, dict):
            result[key] = deep_merge(result.get(key, {}), value)
        elif value not in [None, "", [], {}]:
            result[key] = value
    return result


def has_useful_data(data: dict) -> bool:
    if not data:
        return False
    interaction = data.get("interaction", {}) or {}
    hcp = data.get("hcp", {}) or {}
    follow_up = data.get("follow_up", {}) or {}
    candidates = [
        hcp.get("full_name"),
        hcp.get("external_id"),
        interaction.get("interaction_type"),
        interaction.get("summary"),
        interaction.get("date"),
        interaction.get("time"),
        interaction.get("attendees"),
        interaction.get("materials"),
        interaction.get("samples"),
        interaction.get("outcomes"),
        follow_up.get("suggestion"),
    ]
    return any(bool(str(value).strip()) for value in candidates if value is not None)


def _gather_db_context(state: AgentState) -> str:
    """Gather relevant database context for the LLM"""
    message = state.get("message", "").lower()
    db = state.get("db")
    
    if not db:
        return "No database context available."
    
    context_parts = []
    
    # Look for potential HCP names in the message
    import re
    # Simple name pattern - capitalize words that might be names
    potential_names = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', state["message"])
    
    if potential_names:
        for name in potential_names[:3]:  # Limit to first 3 potential names
            try:
                hcps = run_db_check_tool(db, "find_hcp", name=name)["data"].get("hcps", [])
                if hcps:
                    context_parts.append(f"Found HCP '{name}': {hcps[0]}")
                    
                    # Get recent interactions for this HCP
                    hcp_id = hcps[0]["id"]
                    interactions = run_db_check_tool(db, "get_recent_interactions", hcp_id=hcp_id, limit=3)["data"].get("interactions", [])
                    if interactions:
                        context_parts.append(f"Recent interactions for {name}:")
                        for interaction in interactions:
                            context_parts.append(f"  - {interaction['interaction_type']} on {interaction['date']}: {interaction['summary'][:100]}...")
            except Exception as e:
                continue
    
    # Look for dates in the message
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
        r'\b\d{2}-\d{2}-\d{4}\b',  # MM-DD-YYYY
    ]
    
    found_dates = []
    for pattern in date_patterns:
        dates = re.findall(pattern, state["message"])
        found_dates.extend(dates)
    
    if found_dates:
        context_parts.append(f"Dates mentioned in message: {', '.join(found_dates)}")
    
    if not context_parts:
        context_parts.append("No specific database matches found for this message.")
    
    return "\n".join(context_parts)


def _intent_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.0).with_structured_output(IntentResult)
    prompt = load_prompt("intent_detection_prompt.txt").format(message=state['message'])
    try:
        result = llm.invoke(prompt)
    except Exception as e:
        if "rate limit" in str(e).lower():
            logger.warning("LLM rate limit on intent detection: %s", e)
            return {"intent": "log_interaction"}
        raise
    return {"intent": result.intent}


def _route_from_intent(state: AgentState) -> str:
    intent = state.get("intent", "log_interaction")
    message = state.get("message", "").lower().strip()

    if intent == "out_of_scope":
        return "out_of_scope"

    # Only allow history if explicitly asked
    if intent == "retrieve_history":
        if any(keyword in message for keyword in [
            "history",
            "previous",
            "past",
            "earlier"
        ]):
            return "retrieve_history"
        else:
            return "log_interaction"

    return intent

def _extract_data_node(state: AgentState) -> AgentState:
    intent = state.get("intent")

    # Only extract for relevant intents
    if intent not in ["log_interaction", "edit_interaction"]:
        return {"extracted_data": {}}
    
    # Gather database context
    db_context = _gather_db_context(state)
    
    llm = get_llm(temperature=0.0).with_structured_output(ExtractionResult)
    prompt = load_prompt("extraction_with_context_prompt.txt").format(
        db_context=db_context,
        message=state['message']
    )
    try:
        result = llm.invoke(prompt)
    except Exception as e:
        if "rate_limit" in str(e):
            return {"extracted_data": {}}
        raise 
    cleaned=clean_data(result.model_dump())
    return {"extracted_data": cleaned}

def _merge_data_node(state: AgentState) -> AgentState:
    current_form_data = state.get("current_form_data", {}) or {}
    extracted_data = state.get("extracted_data", {}) or {}
    llm = get_llm()

    def merge_dicts(old: dict, new: dict):
        result = old.copy()
        for key, value in new.items():
            if isinstance(value, dict):
                result[key] = merge_dicts(result.get(key, {}), value)
            elif value not in [None, "", [], {}]:
                if key == "interaction_type":
                    validation_prompt = load_prompt("interaction_type_validation_prompt.txt")
                    try:
                        valid_types = llm.invoke(validation_prompt)
                        if valid_types.content.strip().lower() in ["yes", "no"]:
                            if valid_types.content.strip().lower() == "yes":
                                result[key] = value
                            else:
                                result[key] = valid_types.content
                    except Exception as e:
                        if "rate limit" in str(e).lower():
                            logger.warning("LLM rate limit while validating interaction_type: %s", e)
                            result[key] = value
                        else:
                            raise

                if key == "summary":
                    old_summary = result.get(key, "") or ""
                    if isinstance(value, str):
                        if value.lower() not in old_summary.lower():
                            result[key] = (old_summary + " " + value).strip()
                    continue

                existing_value = result.get(key)
                if (
                    isinstance(existing_value, str)
                    and isinstance(value, str)
                    and len(value.strip()) < len(existing_value.strip())
                ):
                    continue

                if isinstance(value, str) and len(value.strip()) < 3:
                    continue

                result[key] = value
        return result

    temp_data = merge_dicts(current_form_data, extracted_data)
    return {"current_form_data": temp_data}

def _execute_tool_node(state: AgentState) -> AgentState:
    # db handled by service/tool functions externally
    llm = get_llm()
    message = state["message"]
    intent = state["intent"]
    current_form_data = dict(state.get("current_form_data", {})or {})
    extracted_data = state.get("extracted_data", {})

    if intent == "log_interaction":
        merged_data = deep_merge(current_form_data, extracted_data)
        form = StructuredFormData.model_validate(merged_data)
        interaction_id = form.interaction.interaction_id
        interaction = None

        if interaction_id:
            interaction = InteractionService(state["db"]).update_interaction_from_form(
                interaction_id=interaction_id,
                form_data=form,
                edit_instruction=message,
            )
        elif has_useful_data(merged_data):
            interaction = InteractionService(state["db"]).create_interaction_from_form(
                form,
                message,
            )
            form.interaction.interaction_id = interaction.id

        if not is_complete(merged_data):
            db_context = _gather_db_context(state)
            prompt = load_prompt("incomplete_data_prompt.txt").format(
                db_context=db_context,
                current_form_data=form.model_dump(),
                message=message,
            )
            try:
                llm_response = llm.invoke(prompt)
                response_text = llm_response.content
            except Exception as e:
                if "rate limit" in str(e).lower():
                    logger.warning("LLM rate limit while prompting for missing details: %s", e)
                    response_text = "I'm currently unable to reach the AI service due to rate limits. Please try again in a few minutes."
                else:
                    raise

            return {
                "tool_result": {
                    "message": response_text,
                    "data": form.model_dump(),
                    "metadata": {"status": "partial_saved" if interaction else "incomplete"},
                }
            }

        response_text = generate_response(message, intent, form.model_dump())
        return {
            "tool_result": {
                "message": response_text,
                "data": form.model_dump(),
                "metadata": {"status": "success", "interaction_id": form.interaction.interaction_id},
            }
        }
    elif intent == "edit_interaction":
        interaction_id = current_form_data.get("interaction", {}).get("interaction_id")
        if not interaction_id:
            response_text = generate_response(message, intent, current_form_data)
            tool_result = {
                    "message": response_text,
                    "data": current_form_data,
                    "metadata": {"tool": "edit_tool", "error": "missing_interaction_id"}
                }
        else:
            tool_result = run_edit_tool(state["db"], message, current_form_data, interaction_id)
    elif intent == "retrieve_history":
        hcp = current_form_data.get("hcp", {})
        external_id = hcp.get("external_id")
        full_name = hcp.get("full_name")
        tool_result = run_history_tool(external_id=external_id, full_name=full_name)
    elif intent == "out_of_scope":
        response_text = generate_response(message, intent, current_form_data)
        tool_result = {
            "message": response_text,
            "data": current_form_data,
            "metadata": {"tool": "scope_guard"},
        }
    elif intent == "emotional_support":
        response_text = generate_response(message, intent, current_form_data)
        tool_result = {
            "message": response_text,
            "data": current_form_data,
            "metadata": {"tool": "support"},
        }
    elif intent == "abusive":
        response_text = generate_response(message, intent, current_form_data)
        tool_result = {
            "message": response_text,
            "data": current_form_data,
            "metadata": {"tool": "safety"},
        }
    elif intent == "suggest_follow_up":
        sentiment = current_form_data.get("interaction", {}).get("sentiment")
        tool_result = run_suggest_tool(current_form_data, sentiment=sentiment)
    else:
        response_text = generate_response(message, intent, current_form_data)
        tool_result = {
            "message": response_text,
            "data": current_form_data,
            "metadata": {"tool": "default"},
        }

    compliance_result = run_compliance_tool(message)
    compliance_flags = compliance_result["data"].get("compliance_flags", [])
    tool_result.setdefault("data", {}).setdefault("compliance_flags", compliance_flags)
    tool_result.setdefault("metadata", {})["intent"] = intent
    return {"tool_result": tool_result}

def generate_response(message: str, intent: str, data: dict) -> str:
    llm = get_llm()

    prompt = load_prompt("response_generation_prompt.txt").format(
        data=data,
        message=message,
        intent=intent
    )

    try:
        result = llm.invoke(prompt)
        return result.content.strip()
    except Exception as e:
        if "rate_limit" in str(e):
            return "I'm a bit busy right now. Please try again in a few minutes."
        raise e


def clean_data(data):
    cleaned = {}
    for k, v in data.items():
        if isinstance(v, dict):
            nested = clean_data(v)
            if nested:
                cleaned[k] = nested
        elif v not in [None, "", [], {}]:
            cleaned[k] = v
    return cleaned


def is_valid_update(field: str, value: str) -> bool:
    llm = get_llm(temperature=0.0)

    prompt = load_prompt("validation_prompt.txt").format(field=field, value=value)

    try:
        result = llm.invoke(prompt).content.strip().upper()
        return result == "YES"
    except:
        return False


def _respond_node(state: AgentState) -> AgentState:
    tool_result = state.get("tool_result", {}) or {}
    current_form_data = state.get("current_form_data", {}) or {}
    final_data = {**current_form_data, **tool_result.get("data", {})}
    structured_data = StructuredFormData.model_validate(final_data)
    response={
        "action": "update_form",
        "data": structured_data.model_dump(),
        "message": tool_result.get("message", "Processed message."),
        "metadata": tool_result.get("metadata", {}),
    }
    return {"response": response}
