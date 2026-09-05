import os
from typing import List, Dict, Any, Optional
from tree_sitter_languages import get_language, get_parser
from backend.app.utils.logging import logger

class SymbolExtractor:
    def __init__(self):
        self.parsers = {}
        self.languages = {}
        self.queries = {}

        self._setup_python()
        self._setup_javascript()
        self._setup_typescript()

    def _setup_python(self):
        lang = get_language("python")
        self.languages["python"] = lang
        self.parsers["python"] = get_parser("python")
        self.queries["python"] = lang.query("""
            (class_definition name: (identifier) @class.name) @class.def
            (function_definition name: (identifier) @function.name) @function.def
        """)

    def _setup_javascript(self):
        lang = get_language("javascript")
        self.languages["javascript"] = lang
        self.parsers["javascript"] = get_parser("javascript")
        self.queries["javascript"] = lang.query("""
            (class_declaration name: (identifier) @class.name) @class.def
            (function_declaration name: (identifier) @function.name) @function.def
            (method_definition name: (property_identifier) @method.name) @method.def
            (arrow_function) @function.def
        """)

    def _setup_typescript(self):
        lang = get_language("typescript")
        self.languages["typescript"] = lang
        self.parsers["typescript"] = get_parser("typescript")
        self.queries["typescript"] = lang.query("""
            (class_declaration name: (type_identifier) @class.name) @class.def
            (function_declaration name: (identifier) @function.name) @function.def
            (method_definition name: (property_identifier) @method.name) @method.def
            (interface_declaration name: (type_identifier) @interface.name) @interface.def
        """)

    def _get_lang_from_ext(self, extension: str) -> Optional[str]:
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript"
        }
        return mapping.get(extension.lower())

    async def extract_symbols(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        ext = os.path.splitext(file_path)[1]
        lang_name = self._get_lang_from_ext(ext)

        if not lang_name or lang_name not in self.parsers:
            return []

        try:
            parser = self.parsers[lang_name]
            tree = parser.parse(bytes(content, "utf8"))
            query = self.queries[lang_name]
            captures = query.captures(tree.root_node)

            symbols = []

            # Map to store definitions and find their names
            defs = {}
            for node, tag in captures:
                if tag.endswith(".def"):
                    defs[node.id] = {"node": node, "tag": tag, "name": "unknown"}
                elif tag.endswith(".name"):
                    parent = node.parent
                    while parent and parent.id not in defs:
                        parent = parent.parent
                    if parent:
                        defs[parent.id]["name"] = content[node.start_byte:node.end_byte]

            for d in defs.values():
                node = d["node"]
                symbols.append({
                    "name": d["name"],
                    "type": d["tag"].split(".")[0],
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "start_column": node.start_point[1],
                    "end_column": node.end_point[1]
                })

            return symbols
        except Exception as e:
            logger.error(f"Failed to extract symbols from {file_path}: {str(e)}")
            return []

symbol_extractor = SymbolExtractor()
