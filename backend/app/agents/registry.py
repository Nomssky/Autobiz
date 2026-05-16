"""Agent registry: model classification, requirements, and metadata."""

import logging
import re

logger = logging.getLogger(__name__)

MODEL_TIERS = {
    "tiny":  {"up_to": 3,   "label": "≤3B",   "level": 0},
    "small": {"up_to": 14,  "label": "4-14B",  "level": 1},
    "medium": {"up_to": 34, "label": "20-34B", "level": 2},
    "large": {"up_to": 80,  "label": "70-80B", "level": 3},
    "xl":    {"up_to": 999, "label": "120B+",  "level": 4},
}

TIER_ORDER = ["tiny", "small", "medium", "large", "xl"]

AGENTS = {
    "researcher": {
        "label": "Market Researcher",
        "description": "Market analysis, competitor research, opportunity scoring",
        "min_tier": "medium",
        "enabled": True,
    },
    "developer": {
        "label": "Software Engineer",
        "description": "Code generation, architecture design, technical planning",
        "min_tier": "large",
        "enabled": True,
    },
    "designer": {
        "label": "Brand Designer",
        "description": "Brand identity, UI/UX planning, color schemes",
        "min_tier": "medium",
        "enabled": True,
    },
    "marketer": {
        "label": "Marketing Specialist",
        "description": "Campaign strategy, content creation, go-to-market",
        "min_tier": "small",
        "enabled": True,
    },
    "finance": {
        "label": "Finance Analyst",
        "description": "Pricing, financial projections, cost analysis",
        "min_tier": "small",
        "enabled": True,
    },
    "support": {
        "label": "Customer Support",
        "description": "Ticket handling, FAQ responses, sentiment analysis",
        "min_tier": "tiny",
        "enabled": True,
    },
}


def _parse_params(model_name: str) -> int:
    """Extract approximate parameter count from model name."""
    name = model_name.lower().strip()

    # Known patterns: qwen3:8b, llama3:70b, mistral-7b, etc.
    patterns = [
        # Explicit: "llama3:70b", "qwen3:8b", "mistral-7b-v2"
        (r"(?:^|[/:_-])?(\d+)b(?:[\-_]|$|\.)", lambda m: int(m.group(1))),
        # Bare: "llama3" = 8B, "qwen3" or "qwen2.5" = estimated
        (r"^(llama|qwen|gemma|phi)(\d+)(?:\..*)?$", lambda m: {3: 8, 2: 7, 1: 1}.get(int(m.group(2)), int(m.group(2)) * 3)),
        (r"^llama3", lambda _: 8),
        (r"^qwen3", lambda _: 8),
        (r"^gemma2", lambda _: 9),
        (r"^mistral", lambda _: 7),
        (r"^phi[_-]?3", lambda _: 4),
        (r"^deepseek", lambda _: 67),
        (r"^yi[_-]?(?:1\.5)?[-_]?(\d+)", lambda m: int(m.group(1))),
        (r"mixtral.*8x(\d+)", lambda m: int(m.group(1)) * 8),
        (r"phi.*mini", lambda _: 3),
        (r"gemma.*2b", lambda _: 2),
        (r"deepseek.*v2", lambda _: 236),
    ]

    for pat, extractor in patterns:
        m = re.search(pat, name)
        if m:
            return extractor(m)

    # Claude models
    if "opus" in name:
        return 999
    if "sonnet" in name:
        return 200
    if "haiku" in name:
        return 50

    # GPT models
    if "gpt-4" in name:
        return 200
    if "gpt-3.5" in name:
        return 20

    logger.debug(f"Could not determine params for model: {model_name}")
    return 0


def classify_model(model_name: str) -> dict:
    """Classify a model name into a tier."""
    params = _parse_params(model_name)
    tier = "unknown"
    for t, info in MODEL_TIERS.items():
        if params <= info["up_to"]:
            tier = t
            break
    if params == 0:
        tier = "unknown"

    return {
        "name": model_name,
        "tier": tier,
        "params": f"{params}B" if params > 0 else "unknown",
        "params_b": params,
    }


def check_warnings(agent_configs: dict, model_tier: str) -> list:
    """Compare model tier against agent requirements."""
    model_level = MODEL_TIERS.get(model_tier, {}).get("level", -1)
    warnings = []

    for name, cfg in AGENTS.items():
        if not agent_configs.get(name, {}).get("enabled", True):
            continue

        min_tier = cfg["min_tier"]
        # Check override: if user set model_override, use that instead
        override_model = agent_configs.get(name, {}).get("model_override", "")
        current_tier = model_tier
        if override_model:
            current_tier = classify_model(override_model)["tier"]

        current_level = MODEL_TIERS.get(current_tier, {}).get("level", -1)
        min_level = MODEL_TIERS.get(min_tier, {}).get("level", 99)

        if current_level < min_level:
            warnings.append({
                "agent": name,
                "label": cfg["label"],
                "min_tier": min_tier,
                "current_tier": current_tier,
                "warning": (
                    f"{cfg['label']} membutuhkan model tier {min_tier} "
                    f"({MODEL_TIERS[min_tier]['label']} params). "
                    f"Model saat ini: {current_tier} ({MODEL_TIERS.get(current_tier,{}).get('label','?')}). "
                    f"Saran gunakan model dengan ≥{MODEL_TIERS[min_tier]['label']} parameter."
                ),
            })

    return warnings


def recommend_model(agent_role: str) -> str:
    """Recommend a suitable model tier for an agent."""
    info = AGENTS.get(agent_role)
    if not info:
        return "unknown"
    return info["min_tier"]
