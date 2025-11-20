"""Profile configuration for multi-tenant RAG scoping.

Profiles provide a higher-level abstraction over collections,
allowing different use cases (campus, avatar, etc.) to have
their own isolated data and default settings.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProfileConfig:
    """Configuration for a RAG profile."""

    profile_id: str
    collection: str
    default_k: int = 5
    default_threshold: float = 0.6
    metadata_schema: Optional[List[str]] = None
    description: str = ""


# Profile registry
PROFILES: Dict[str, ProfileConfig] = {
    "campus": ProfileConfig(
        profile_id="campus",
        collection="campus_classroom_data",
        default_k=5,
        default_threshold=0.6,
        metadata_schema=["classroom_id", "subject", "teacher_id", "date", "document_type"],
        description="Smart Campus classroom content and learning materials",
    ),
    "avatar": ProfileConfig(
        profile_id="avatar",
        collection="avatar_knowledge_base",
        default_k=3,
        default_threshold=0.7,
        metadata_schema=["avatar_id", "topic", "personality_trait"],
        description="Avatar knowledge base for speech-to-speech interactions",
    ),
    "default": ProfileConfig(
        profile_id="default",
        collection="general_knowledge",
        default_k=5,
        default_threshold=0.5,
        metadata_schema=None,
        description="General-purpose knowledge base",
    ),
}


def get_profile(profile_id: str) -> ProfileConfig:
    """Get profile configuration by ID.

    Args:
        profile_id: Profile identifier (e.g., "campus", "avatar")

    Returns:
        ProfileConfig for the requested profile

    Raises:
        KeyError: If profile_id is not found
    """
    if profile_id not in PROFILES:
        raise KeyError(f"Profile '{profile_id}' not found. Available profiles: {list(PROFILES.keys())}")

    return PROFILES[profile_id]


def list_profiles() -> List[ProfileConfig]:
    """Get list of all available profiles.

    Returns:
        List of ProfileConfig objects
    """
    return list(PROFILES.values())


def register_profile(config: ProfileConfig) -> None:
    """Register a new profile or update an existing one.

    Args:
        config: ProfileConfig to register
    """
    PROFILES[config.profile_id] = config


def profile_exists(profile_id: str) -> bool:
    """Check if a profile exists.

    Args:
        profile_id: Profile identifier

    Returns:
        True if profile exists, False otherwise
    """
    return profile_id in PROFILES
