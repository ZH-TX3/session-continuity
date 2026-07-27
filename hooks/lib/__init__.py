"""Session Continuity Plugin - 共享库模块"""

from .paths import find_project_root, get_claude_dir, get_config_path, get_state_path, get_handoff_path
from .config import load_config, get_config_value
from .state import (
    get_session_model,
    set_session_model,
    is_session_prompted,
    mark_session_prompted,
    is_session_warned,
    mark_session_warned,
)
from .insight_state import (
    get_session_model as get_insight_session_model,
    set_session_model as set_insight_session_model,
    get_last_insight_turn,
    set_last_insight_turn,
)

__all__ = [
    "find_project_root",
    "get_claude_dir",
    "get_config_path",
    "get_state_path",
    "get_handoff_path",
    "load_config",
    "get_config_value",
    "get_session_model",
    "set_session_model",
    "is_session_prompted",
    "mark_session_prompted",
    "is_session_warned",
    "mark_session_warned",
    "get_insight_session_model",
    "set_insight_session_model",
    "get_last_insight_turn",
    "set_last_insight_turn",
]
