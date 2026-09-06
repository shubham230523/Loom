from enum import Enum
from typing import Optional, Dict
from backend.app.config import settings

class TaskType(str, Enum):
    REPO_ANALYSIS = "repo_analysis"
    ISSUE_ANALYSIS = "issue_analysis"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    TESTING = "testing"
    CODE_REVIEW = "code_review"
    PR_GENERATION = "pr_generation"

class ModelRouter:
    def __init__(self):
        # Default mapping of task types to setting keys
        self._task_setting_map = {
            TaskType.REPO_ANALYSIS: "MODEL_REPO_ANALYSIS",
            TaskType.ISSUE_ANALYSIS: "MODEL_ISSUE_ANALYSIS",
            TaskType.PLANNING: "MODEL_PLANNING",
            TaskType.IMPLEMENTATION: "MODEL_IMPLEMENTATION",
            TaskType.DEBUGGING: "MODEL_DEBUGGING",
            TaskType.TESTING: "MODEL_TESTING",
            TaskType.CODE_REVIEW: "MODEL_CODE_REVIEW",
            TaskType.PR_GENERATION: "MODEL_PR_GENERATION",
        }

    def get_model_for_task(self, task: TaskType) -> str:
        """
        Returns the appropriate model name for a given task type.
        Prioritizes specific task overrides, then fallbacks to AGENT_MODEL, then DEFAULT_MODEL.
        """
        setting_key = self._task_setting_map.get(task)
        if setting_key:
            model = getattr(settings, setting_key, None)
            if model:
                return model

        # Fallbacks
        return settings.AGENT_MODEL or settings.DEFAULT_MODEL

model_router = ModelRouter()
