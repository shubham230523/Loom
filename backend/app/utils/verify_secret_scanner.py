from backend.app.security.secret_scanner import secret_scanner
from backend.app.utils.logging import logger

def verify_secret_scanner():
    logger.info("Verifying SecretScanner...")

    # 1. Test clean text
    clean_diff = """
+ def hello():
+     print("world")
    """
    assert len(secret_scanner.scan_text(clean_diff)) == 0

    # 2. Test with OpenAI key
    dirty_diff = """
+ sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKL
    """
    findings = secret_scanner.scan_text(dirty_diff)
    logger.info(f"Findings for OpenAI key: {findings}")
    assert len(findings) >= 1
    # Check if any finding has masked preview
    assert any("sk-" in f["preview"] and "*" in f["preview"] for f in findings)

    # 3. Test with AWS key
    aws_diff = """
+ AKIA1234567890ABCDEF
    """
    findings = secret_scanner.scan_text(aws_diff)
    logger.info(f"Findings for AWS key: {findings}")
    assert len(findings) >= 1

    # 4. Test with Private Key
    pk_diff = """
+ -----BEGIN RSA PRIVATE KEY-----
    """
    findings = secret_scanner.scan_text(pk_diff)
    logger.info(f"Findings for Private key: {findings}")
    assert len(findings) >= 1

    logger.info("SecretScanner verification successful.")
    return True

if __name__ == "__main__":
    if verify_secret_scanner():
        print("Verification PASSED")
    else:
        exit(1)
