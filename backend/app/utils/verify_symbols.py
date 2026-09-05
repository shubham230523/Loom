import asyncio
import sys
from backend.app.repository import symbol_extractor
from backend.app.utils.logging import logger

async def verify_symbol_extraction():
    # 1. Test Python extraction
    py_code = """
class MyClass:
    def my_method(self):
        pass

def top_level_func():
    pass
"""
    py_symbols = await symbol_extractor.extract_symbols("test.py", py_code)
    logger.info(f"Python symbols: {py_symbols}")

    names = [s["name"] for s in py_symbols]
    assert "MyClass" in names
    assert "my_method" in names
    assert "top_level_func" in names

    # 2. Test TypeScript extraction
    ts_code = """
interface User {
    id: string;
}

class UserService {
    getUser(id: string): User {
        return { id };
    }
}

function helper() {}
"""
    ts_symbols = await symbol_extractor.extract_symbols("test.ts", ts_code)
    logger.info(f"TypeScript symbols: {ts_symbols}")

    names = [s["name"] for s in ts_symbols]
    assert "User" in names
    assert "UserService" in names
    assert "getUser" in names
    assert "helper" in names

    logger.info("Symbol extraction verification successful.")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_symbol_extraction())
    if not success:
        sys.exit(1)
