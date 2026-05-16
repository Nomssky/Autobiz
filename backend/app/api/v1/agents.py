"""Agent configuration endpoints — per-agent model override, enable/disable, custom prompt."""

import logging
from uuid import UUID

from app.agents.registry import AGENTS, MODEL_TIERS, check_warnings, classify_model
from app.api.dependencies import get_db_session, require_ceo
from app.config import settings as app_settings
from app.models.agent_config import AgentConfig
from app.schemas.agent import (
    AgentConfigUpdate,
    AgentInfoResponse,
    AgentListResponse,
    ModelInfoResponse,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_user_configs(user_id: UUID, db: Session) -> dict:
    """Load all agent configs for a user as dict keyed by agent_name."""
    rows = db.execute(
        select(AgentConfig).where(AgentConfig.user_id == user_id)
    ).scalars().all()
    return {r.agent_name: {
        "enabled": r.enabled,
        "model_override": r.model_override or "",
        "custom_prompt": r.custom_prompt or "",
        "temperature": float(r.temperature) if r.temperature else 0.7,
    } for r in rows}


def _get_or_create_config(user_id: UUID, agent_name: str, db: Session) -> AgentConfig:
    """Get existing config or return a new unsaved one with defaults."""
    row = db.execute(
        select(AgentConfig).where(
            AgentConfig.user_id == user_id,
            AgentConfig.agent_name == agent_name,
        )
    ).scalar_one_or_none()
    if row:
        return row
    return AgentConfig(user_id=user_id, agent_name=agent_name, enabled=True)


@router.get("", response_model=AgentListResponse)
def list_agents(
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(require_ceo),
):
    """List all agents with user's config and model compatibility status."""
    # Detect current model
    model_name = app_settings.LLM_MODEL or app_settings.OPENAI_MODEL or "unknown"
    provider = (app_settings.LLM_PROVIDER or "").lower()
    if provider == "ollama":
        # Use the Ollama model name directly
        pass
    elif model_name == "unknown":
        model_name = provider

    model_info = classify_model(model_name)
    user_configs = _get_user_configs(user_id, db)
    warnings = check_warnings(user_configs, model_info["tier"])

    # Build warning lookup
    warning_map = {w["agent"]: w for w in warnings}

    agents = []
    for name, info in AGENTS.items():
        cfg = user_configs.get(name, {})
        # Use override tier for current_tier if set
        current_tier = model_info["tier"]
        override = cfg.get("model_override", "")
        if override:
            current_tier = classify_model(override)["tier"]

        agent_warning = warning_map.get(name, {})
        min_level = MODEL_TIERS.get(info["min_tier"], {}).get("level", 99)
        cur_level = MODEL_TIERS.get(current_tier, {}).get("level", -1)

        if cur_level < min_level:
            status_val = "suboptimal"
        elif cur_level >= min_level:
            status_val = "optimal"
        else:
            status_val = "unknown"

        agents.append(AgentInfoResponse(
            name=name,
            label=info["label"],
            description=info["description"],
            min_tier=info["min_tier"],
            current_tier=current_tier,
            status=status_val,
            warning=agent_warning.get("warning", ""),
            enabled=cfg.get("enabled", True),
            model_override=cfg.get("model_override", ""),
            custom_prompt=cfg.get("custom_prompt", ""),
            temperature=cfg.get("temperature", 0.7),
        ))

    return AgentListResponse(
        model=ModelInfoResponse(
            name=model_info["name"],
            tier=model_info["tier"],
            params=model_info["params"],
        ),
        agents=agents,
    )


@router.get("/{agent_name}", response_model=AgentInfoResponse)
def get_agent(
    agent_name: str,
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(require_ceo),
):
    """Get details and config for a single agent."""
    info = AGENTS.get(agent_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    model_info = classify_model(app_settings.LLM_MODEL or "unknown")
    user_configs = _get_user_configs(user_id, db)
    warnings = check_warnings(user_configs, model_info["tier"])

    cfg = user_configs.get(agent_name, {})
    current_tier = model_info["tier"]
    override = cfg.get("model_override", "")
    if override:
        current_tier = classify_model(override)["tier"]

    warning = next((w["warning"] for w in warnings if w["agent"] == agent_name), "")
    min_level = MODEL_TIERS.get(info["min_tier"], {}).get("level", 99)
    cur_level = MODEL_TIERS.get(current_tier, {}).get("level", -1)

    if cur_level < min_level:
        status_val = "suboptimal"
    elif cur_level >= min_level:
        status_val = "optimal"
    else:
        status_val = "unknown"

    return AgentInfoResponse(
        name=agent_name,
        label=info["label"],
        description=info["description"],
        min_tier=info["min_tier"],
        current_tier=current_tier,
        status=status_val,
        warning=warning,
        enabled=cfg.get("enabled", True),
        model_override=cfg.get("model_override", ""),
        custom_prompt=cfg.get("custom_prompt", ""),
        temperature=cfg.get("temperature", 0.7),
    )


@router.put("/{agent_name}/config", response_model=AgentInfoResponse)
def update_agent_config(
    agent_name: str,
    updates: AgentConfigUpdate,
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(require_ceo),
):
    """Update config for a specific agent (model override, enable/disable, prompt)."""
    info = AGENTS.get(agent_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    config = _get_or_create_config(user_id, agent_name, db)

    if updates.enabled is not None:
        config.enabled = updates.enabled
    if updates.model_override is not None:
        config.model_override = updates.model_override or None
    if updates.custom_prompt is not None:
        config.custom_prompt = updates.custom_prompt or None
    if updates.temperature is not None:
        config.temperature = updates.temperature

    db.add(config)
    db.flush()

    # Return updated info
    model_info = classify_model(app_settings.LLM_MODEL or "unknown")
    current_tier = model_info["tier"]
    if config.model_override:
        current_tier = classify_model(config.model_override)["tier"]

    min_level = MODEL_TIERS.get(info["min_tier"], {}).get("level", 99)
    cur_level = MODEL_TIERS.get(current_tier, {}).get("level", -1)

    if cur_level < min_level:
        status_val = "suboptimal"
    elif cur_level >= min_level:
        status_val = "optimal"
    else:
        status_val = "unknown"

    return AgentInfoResponse(
        name=agent_name,
        label=info["label"],
        description=info["description"],
        min_tier=info["min_tier"],
        current_tier=current_tier,
        status=status_val,
        warning="" if status_val == "optimal" else f"Model tier {current_tier} di bawah minimum {info['min_tier']}",
        enabled=config.enabled,
        model_override=config.model_override or "",
        custom_prompt=config.custom_prompt or "",
        temperature=float(config.temperature) if config.temperature else 0.7,
    )
