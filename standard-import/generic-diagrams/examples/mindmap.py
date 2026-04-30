#!/usr/bin/env python3
"""
Example: create a radial mindmap Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/mindmap.py

The example builds a "Computer Science" mindmap with several top-level
branches; the generator splits them between the left and right halves
and assigns each branch a palette color that propagates to its
descendants.
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.mindmap import MindmapGenerator


def main() -> None:
    generator = MindmapGenerator()  # reads LUCID_API_KEY from env

    tree = {
        "id": "root",
        "label": "Computer Science",
        "children": [
            {
                "id": "algo",
                "label": "Algorithms",
                "children": [
                    {"id": "algo-sort", "label": "Sorting"},
                    {"id": "algo-search", "label": "Searching"},
                    {"id": "algo-graph", "label": "Graph"},
                    {"id": "algo-dp", "label": "Dynamic programming"},
                ],
            },
            {
                "id": "ds",
                "label": "Data Structures",
                "children": [
                    {"id": "ds-array", "label": "Arrays"},
                    {"id": "ds-linked", "label": "Linked lists"},
                    {"id": "ds-tree", "label": "Trees"},
                    {"id": "ds-hash", "label": "Hash tables"},
                ],
            },
            {
                "id": "lang",
                "label": "Languages",
                "children": [
                    {"id": "lang-py", "label": "Python"},
                    {"id": "lang-ts", "label": "TypeScript"},
                    {"id": "lang-rust", "label": "Rust"},
                    {"id": "lang-go", "label": "Go"},
                ],
            },
            {
                "id": "db",
                "label": "Databases",
                "children": [
                    {"id": "db-rel", "label": "Relational"},
                    {"id": "db-doc", "label": "Document"},
                    {"id": "db-kv", "label": "Key-value"},
                    {"id": "db-graph", "label": "Graph"},
                ],
            },
            {
                "id": "sec",
                "label": "Security",
                "children": [
                    {"id": "sec-crypto", "label": "Cryptography"},
                    {"id": "sec-authz", "label": "AuthZ"},
                    {"id": "sec-authn", "label": "AuthN"},
                ],
            },
            {
                "id": "ai",
                "label": "AI / ML",
                "children": [
                    {"id": "ai-cls", "label": "Classification"},
                    {"id": "ai-reg", "label": "Regression"},
                    {"id": "ai-llm", "label": "LLMs"},
                ],
            },
        ],
    }

    try:
        response = generator.create_document(
            title="Computer Science mindmap",
            tree=tree,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
