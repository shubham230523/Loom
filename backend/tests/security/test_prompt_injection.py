import pytest
from backend.app.security.secret_scanner import secret_scanner

def test_secret_scanner_detects_openai_key():
    """Verify that OpenAI API keys are detected in diffs."""
    diff = "---\n+++ b/file.py\n+ OPENAI_KEY = \"sk-proj-123456789012345678901234567890123456789012345678\""
    findings = secret_scanner.scan_text(diff)
    assert len(findings) == 1
    assert "sk-" in findings[0]["preview"]

def test_secret_scanner_ignores_unrelated_text():
    """Verify no false positives on regular code."""
    diff = "---\n+++ b/file.py\n+ def calculate_score(val):\n+     return val * 10"
    findings = secret_scanner.scan_text(diff)
    assert len(findings) == 0

def test_secret_scanner_detects_github_token():
    """Verify that GitHub tokens are detected."""
    diff = "+ TOKEN = \"ghp_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890\""
    findings = secret_scanner.scan_text(diff)
    assert len(findings) == 1
