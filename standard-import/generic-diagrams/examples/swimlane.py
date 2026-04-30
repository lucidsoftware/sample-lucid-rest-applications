#!/usr/bin/env python3
"""
Example: create a swimlane Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/swimlane.py

The example models an expense-approval flow that hops between three
lanes (Employee, Manager, Finance). Each task lives in its lane;
edges connect tasks across lanes, and the swimLanes container has
assistedLayout enabled so Lucid routes the lines on import.
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.swimlane import SwimlaneGenerator


def main() -> None:
    generator = SwimlaneGenerator()  # reads LUCID_API_KEY from env

    lanes = [
        {"id": "employee", "title": "Employee"},
        {"id": "manager", "title": "Manager"},
        {"id": "finance", "title": "Finance"},
    ]
    tasks = [
        {"id": "submit", "label": "Submit expense", "lane": "employee", "shape": "terminator"},
        {"id": "review", "label": "Review report", "lane": "manager", "shape": "process"},
        {"id": "decide", "label": "Approve?", "lane": "manager", "shape": "decision"},
        {"id": "pay", "label": "Issue payment", "lane": "finance", "shape": "process"},
        {"id": "notify", "label": "Send receipt", "lane": "finance", "shape": "process"},
        {"id": "done", "label": "Reimbursed", "lane": "employee", "shape": "terminator"},
    ]
    edges = [
        {"from": "submit", "to": "review"},
        {"from": "review", "to": "decide"},
        {"from": "decide", "to": "submit", "label": "revise"},
        {"from": "decide", "to": "pay", "label": "yes"},
        {"from": "pay", "to": "notify"},
        {"from": "notify", "to": "done"},
    ]

    try:
        response = generator.create_document(
            title="Expense approval swimlane",
            lanes=lanes,
            tasks=tasks,
            edges=edges,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
