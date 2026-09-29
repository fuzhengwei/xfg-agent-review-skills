"""Optional model/channel profiles for provider-aware agent runs."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("id", "provider", "model")


def _validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if not isinstance(profile.get(field), str) or not profile[field]]
    if missing:
        raise ValueError("model profile missing required fields: " + ", ".join(missing))
    if not isinstance(profile.get("request", {}), dict):
        raise ValueError("model profile.request must be an object")
    api_key_env = profile.get("api_key_env")
    if api_key_env is not None:
        if not isinstance(api_key_env, str) or not api_key_env:
            raise ValueError("model profile.api_key_env must be a non-empty string")
        if not os.getenv(api_key_env):
            raise ValueError(f"model profile requires environment variable {api_key_env}")
    return profile


def resolve_model_profile(config_path: Path | None, profile_id: str | None) -> dict[str, Any] | None:
    """Return an optional, secret-free model profile."""

    if config_path is None:
        if profile_id is not None:
            raise ValueError("--profile requires --model-config")
        return None

    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must contain a JSON object")

    profiles = config.get("profiles")
    if isinstance(profiles, list):
        selected_id = profile_id or config.get("default_profile")
        matches = [profile for profile in profiles if isinstance(profile, dict) and profile.get("id") == selected_id]
        if not matches:
            raise ValueError(f"model profile not found: {selected_id}")
        if len(matches) > 1:
            raise ValueError(f"duplicate model profile id: {selected_id}")
        return _validate_profile(copy.deepcopy(matches[0]))

    if profile_id is not None:
        raise ValueError("--profile cannot select from a single-profile model config")
    return _validate_profile(copy.deepcopy(config))
