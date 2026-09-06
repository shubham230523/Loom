import re
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.utils.logging import logger

class SecretScanner:
    def __init__(self):
        self.patterns = [re.compile(p) for p in settings.SECRET_DETECTION_PATTERNS]

    def scan_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans a block of text (like a git diff) for potential secrets.
        Returns a list of findings with the pattern matched and a masked preview.
        """
        findings = []

        # We only scan added lines in a diff usually, but for safety we can scan the whole text
        # If it's a unified diff, we might want to focus on lines starting with '+'
        lines = text.split('\n')

        for i, line in enumerate(lines, 1):
            # Focus on additions in a diff
            if line.startswith('+') and not line.startswith('+++'):
                content = line[1:].strip()
                line_findings = []
                for pattern in self.patterns:
                    match = pattern.search(content)
                    if match:
                        matched_text = match.group(0)
                        # Mask for logging and UI
                        masked = matched_text[:4] + "*" * (len(matched_text) - 8) + matched_text[-4:] if len(matched_text) > 8 else "****"

                        line_findings.append({
                            "line": i,
                            "pattern": pattern.pattern,
                            "preview": masked,
                            "full_line": content[:100]
                        })

                # Only add if we have findings on this line
                if line_findings:
                    findings.extend(line_findings)

        return findings

secret_scanner = SecretScanner()
