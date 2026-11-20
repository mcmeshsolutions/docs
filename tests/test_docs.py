import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def resolve_json_pointer(doc: dict, pointer: str):
    if not pointer.startswith("#/"):
        raise ValueError(f"Unsupported external or relative $ref: {pointer}")
    parts = pointer[2:].split("/")
    cur = doc
    for raw in parts:
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            raise KeyError(f"Unresolved $ref pointer: {pointer}")
    return cur


def iter_refs(node):
    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str):
            yield node["$ref"]
        for v in node.values():
            yield from iter_refs(v)
    elif isinstance(node, list):
        for item in node:
            yield from iter_refs(item)


class DocsValidationTests(unittest.TestCase):
    def test_openapi_spec_valid_and_refs_resolve(self):
        spec_path = ROOT / "openapi.json"
        self.assertTrue(spec_path.is_file(), "openapi.json must exist")
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

        self.assertIn("openapi", spec)
        self.assertRegex(spec["openapi"], r"^3\.[01]\.", f"Unexpected OpenAPI version: {spec['openapi']}")
        self.assertIn("info", spec)
        self.assertTrue(spec["info"].get("title"))
        self.assertTrue(spec["info"].get("version"))

        paths = spec.get("paths", {})
        self.assertGreater(len(paths), 0, "openapi.json must define at least one path")

        http_methods = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
        for route, item in paths.items():
            self.assertTrue(route.startswith("/"), f"Route must start with '/': {route}")
            ops = {k: v for k, v in item.items() if k.lower() in http_methods}
            self.assertGreater(len(ops), 0, f"Path {route} has no HTTP operations")
            for method, op in ops.items():
                self.assertIn("responses", op, f"{method.upper()} {route} missing responses")
                self.assertGreater(len(op["responses"]), 0, f"{method.upper()} {route} has empty responses")

        for ref in iter_refs(spec):
            resolve_json_pointer(spec, ref)

    def test_compat_json_schema_valid(self):
        schema_path = ROOT / "mcmesh_compat.schema.json"
        self.assertTrue(schema_path.is_file(), "mcmesh_compat.schema.json must exist")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertIn("$schema", schema)
        self.assertEqual(schema.get("type"), "object")
        self.assertIn("properties", schema)
        self.assertGreater(len(schema["properties"]), 0)

    def test_markdown_relative_links_resolve(self):
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for md_path in sorted(ROOT.glob("*.md")):
            text = md_path.read_text(encoding="utf-8")
            self.assertRegex(text, r"(?m)^#\s+\S", f"{md_path.name} should contain a top-level markdown heading")
            for target in link_re.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                rel = target.split("#", 1)[0]
                if not rel:
                    continue
                resolved = (md_path.parent / rel).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"Broken relative link in {md_path.name}: {target}",
                )

    def test_html_docs_valid(self):
        for html_name in ("marketing.html", "marketing-strategy.html"):
            html_path = ROOT / html_name
            self.assertTrue(html_path.is_file(), f"{html_name} must exist")
            content = html_path.read_text(encoding="utf-8")
            self.assertRegex(content, r"(?is)<title>[^<]+</title>")
            self.assertIn("<style>", content.lower(), f"{html_name} missing <style> block")


if __name__ == "__main__":
    unittest.main()
