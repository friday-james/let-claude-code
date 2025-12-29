"""Let Claude Code - Automatically improve your codebase with Claude."""

from .automator import (
    AutoReviewer,
    IMPROVEMENT_MODES,
    get_combined_prompt,
    get_goal_prompt,
    get_northstar_prompt,
)

__version__ = "0.1.3"
__all__ = [
    "AutoReviewer",
    "IMPROVEMENT_MODES",
    "get_combined_prompt",
    "get_goal_prompt",
    "get_northstar_prompt",
]
