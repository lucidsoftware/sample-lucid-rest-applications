#!/usr/bin/env python3
"""
Example: create an entity-relationship diagram Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/erdiagram.py

The example builds a small blog schema: users write posts and
comments, posts have tags and reactions. Each entity becomes a `table`
shape with a header row plus one row per attribute; relationships are
smart lines whose endpoint styles encode cardinality.
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.erdiagram import ERDiagramGenerator


def main() -> None:
    generator = ERDiagramGenerator()  # reads LUCID_API_KEY from env

    entities = [
        {
            "id": "user",
            "name": "User",
            "attributes": [
                {"name": "id", "type": "uuid", "key": "PK"},
                {"name": "email", "type": "varchar"},
                {"name": "name", "type": "varchar"},
                {"name": "created_at", "type": "timestamp"},
            ],
        },
        {
            "id": "post",
            "name": "Post",
            "attributes": [
                {"name": "id", "type": "uuid", "key": "PK"},
                {"name": "user_id", "type": "uuid", "key": "FK"},
                {"name": "title", "type": "varchar"},
                {"name": "body", "type": "text"},
                {"name": "published_at", "type": "timestamp"},
            ],
        },
        {
            "id": "comment",
            "name": "Comment",
            "attributes": [
                {"name": "id", "type": "uuid", "key": "PK"},
                {"name": "post_id", "type": "uuid", "key": "FK"},
                {"name": "user_id", "type": "uuid", "key": "FK"},
                {"name": "body", "type": "text"},
                {"name": "created_at", "type": "timestamp"},
            ],
        },
        {
            "id": "tag",
            "name": "Tag",
            "attributes": [
                {"name": "id", "type": "uuid", "key": "PK"},
                {"name": "name", "type": "varchar"},
            ],
        },
        {
            "id": "post_tag",
            "name": "PostTag",
            "attributes": [
                {"name": "post_id", "type": "uuid", "key": "PK,FK"},
                {"name": "tag_id", "type": "uuid", "key": "PK,FK"},
            ],
        },
        {
            "id": "reaction",
            "name": "Reaction",
            "attributes": [
                {"name": "id", "type": "uuid", "key": "PK"},
                {"name": "post_id", "type": "uuid", "key": "FK"},
                {"name": "user_id", "type": "uuid", "key": "FK"},
                {"name": "kind", "type": "varchar"},
            ],
        },
    ]

    relationships = [
        {"from": "user", "to": "post", "fromCardinality": "one", "toCardinality": "many", "label": "writes"},
        {"from": "user", "to": "comment", "fromCardinality": "one", "toCardinality": "many", "label": "authors"},
        {"from": "post", "to": "comment", "fromCardinality": "one", "toCardinality": "many", "label": "has"},
        {"from": "post", "to": "post_tag", "fromCardinality": "one", "toCardinality": "many"},
        {"from": "tag", "to": "post_tag", "fromCardinality": "one", "toCardinality": "many"},
        {"from": "user", "to": "reaction", "fromCardinality": "one", "toCardinality": "many"},
        {"from": "post", "to": "reaction", "fromCardinality": "one", "toCardinality": "many"},
    ]

    try:
        response = generator.create_document(
            title="Blog ER diagram",
            entities=entities,
            relationships=relationships,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
