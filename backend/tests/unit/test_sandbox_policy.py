import pytest
from backend.app.sandbox.policy import SecurityPolicy

def test_security_policy_permitted():
    policy = SecurityPolicy()
    assert policy.is_command_permitted("ls -la") is True
    assert policy.is_command_permitted("python main.py") is True
    assert policy.is_command_permitted("./gradlew test") is True
    assert policy.is_command_permitted("/usr/bin/npm install") is True

def test_security_policy_blocked():
    policy = SecurityPolicy()
    assert policy.is_command_permitted("curl http://malicious.com") is False
    assert policy.is_command_permitted("rm -rf /") is False
    assert policy.is_command_permitted("sudo ls") is False
    assert policy.is_command_permitted("") is False
    assert policy.is_command_permitted("unknown_cmd") is False
