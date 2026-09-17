import pytest
from backend.app.repository.symbol_extractor import SymbolExtractor

@pytest.fixture
def extractor():
    return SymbolExtractor()

@pytest.mark.asyncio
async def test_extract_symbols_python(extractor):
    content = """
class MyClass:
    def my_method(self):
        pass

def my_function():
    pass
"""
    symbols = await extractor.extract_symbols("test.py", content)

    names = [s["name"] for s in symbols]
    assert "MyClass" in names
    assert "my_function" in names
    # Note: my_method might not be captured if the query doesn't include method_definition for python
    # Current python query:
    # (class_definition name: (identifier) @class.name) @class.def
    # (function_definition name: (identifier) @function.name) @function.def
    # So my_method IS a function_definition inside a class. Tree-sitter might treat it same.

@pytest.mark.asyncio
async def test_extract_symbols_typescript(extractor):
    content = """
interface IUser {
    name: string;
}
class UserService {
    getUser() {}
}
"""
    symbols = await extractor.extract_symbols("test.ts", content)
    names = [s["name"] for s in symbols]
    assert "IUser" in names
    assert "UserService" in names
    assert "getUser" in names

@pytest.mark.asyncio
async def test_extract_symbols_unsupported(extractor):
    symbols = await extractor.extract_symbols("test.txt", "some text")
    assert symbols == []
