#!/usr/bin/env python3
"""
Example: create a UML class diagram Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/umlclassdiagram.py

The example models a small Animal hierarchy: Dog and Cat extend an
abstract Animal and realize a Pettable interface; Owner aggregates
Animals and depends on Collar; Dog composes Collar. Each class
becomes a `table` shape with header / attributes / methods sections;
relationships are smart lines whose endpoint styles encode UML
semantics (inheritance, realization, association, aggregation,
composition, dependency).
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.umlclassdiagram import UMLClassDiagramGenerator


def main() -> None:
    generator = UMLClassDiagramGenerator()  # reads LUCID_API_KEY from env

    classes = [
        {
            "id": "animal",
            "name": "Animal",
            "stereotype": "abstract",
            "attributes": [
                {"name": "name", "type": "String", "visibility": "+"},
                {"name": "age", "type": "int", "visibility": "-"},
            ],
            "methods": [
                {"name": "makeSound", "parameters": [], "returnType": "void", "visibility": "public", "abstract": True},
                {
                    "name": "eat",
                    "parameters": [{"name": "food", "type": "String"}],
                    "returnType": "void",
                    "visibility": "public",
                },
            ],
        },
        {
            "id": "dog",
            "name": "Dog",
            "attributes": [
                {"name": "breed", "type": "String", "visibility": "private"},
            ],
            "methods": [
                {"name": "makeSound", "parameters": [], "returnType": "void", "visibility": "public"},
                {
                    "name": "fetch",
                    "parameters": [{"name": "item", "type": "String"}],
                    "returnType": "boolean",
                    "visibility": "public",
                },
            ],
        },
        {
            "id": "cat",
            "name": "Cat",
            "attributes": [
                {"name": "indoor", "type": "boolean", "visibility": "private"},
            ],
            "methods": [
                {"name": "makeSound", "parameters": [], "returnType": "void", "visibility": "public"},
            ],
        },
        {
            "id": "pettable",
            "name": "Pettable",
            "stereotype": "interface",
            "attributes": [],
            "methods": [
                {"name": "pet", "parameters": [], "returnType": "void", "visibility": "public", "abstract": True},
            ],
        },
        {
            "id": "owner",
            "name": "Owner",
            "attributes": [
                {"name": "name", "type": "String", "visibility": "+"},
                {"name": "address", "type": "String", "visibility": "-"},
            ],
            "methods": [
                {"name": "feedAll", "parameters": [], "returnType": "void", "visibility": "public"},
            ],
        },
        {
            "id": "collar",
            "name": "Collar",
            "attributes": [
                {"name": "color", "type": "String", "visibility": "public"},
            ],
            "methods": [],
        },
    ]

    relationships = [
        {"from": "dog", "to": "animal", "type": "inheritance"},
        {"from": "cat", "to": "animal", "type": "inheritance"},
        {"from": "dog", "to": "pettable", "type": "realization"},
        {"from": "cat", "to": "pettable", "type": "realization"},
        {
            "from": "owner",
            "to": "animal",
            "type": "aggregation",
            "fromMultiplicity": "1",
            "toMultiplicity": "*",
            "label": "owns",
        },
        {"from": "dog", "to": "collar", "type": "composition", "fromMultiplicity": "1", "toMultiplicity": "1"},
        {"from": "owner", "to": "collar", "type": "dependency", "label": "buys"},
    ]

    try:
        response = generator.create_document(
            title="UML class diagram - Animal hierarchy",
            classes=classes,
            relationships=relationships,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
