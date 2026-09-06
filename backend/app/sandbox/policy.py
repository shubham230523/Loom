from pydantic import BaseModel, Field
from typing import List, Set
import re

class SecurityPolicy(BaseModel):
    """
    Defines the permitted execution policy for a repository sandbox.
    """
    allowed_commands: Set[str] = Field(
        default_factory=lambda: {
            "ls", "pwd", "cat", "mkdir", "rm", "cp", "mv", "grep", "find", "echo",
            "git", "python", "pip", "pytest", "unittest",
            "npm", "node", "npx", "yarn", "pnpm", "jest", "vitest",
            "go", "cargo", "rustc",
            "gradle", "gradlew", "mvn", "mvnw"
        },
        description="Base set of permitted executable names"
    )

    blocked_patterns: List[str] = Field(
        default_factory=lambda: [
            r"ssh", r"curl", r"wget", r"netcat", r"nc", r"nmap",
            r"sudo", r"su", r"chown", r"chmod\s+777",
            r"docker", r"kubectl", r"/etc/passwd", r"/etc/shadow",
            r"rm\s+-rf\s+/", r"rm\s+--no-preserve-root"
        ],
        description="Regex patterns that are always blocked even if the command is in the allowed set"
    )

    def is_command_permitted(self, command: str) -> bool:
        """
        Validates if a full command string is permitted under this policy.
        """
        # 1. Check blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False

        # 2. Check executable name
        # Simple extraction of the first word (the executable)
        parts = command.strip().split()
        if not parts:
            return False

        executable = parts[0]
        # Strip path if provided (e.g. /usr/bin/python -> python)
        executable = executable.split("/")[-1].split("\\")[-1]
        # Handle wrappers (e.g. ./gradlew -> gradlew)
        if executable.startswith("."):
            executable = executable.lstrip("./")

        return executable in self.allowed_commands

# Default global policy
default_policy = SecurityPolicy()
