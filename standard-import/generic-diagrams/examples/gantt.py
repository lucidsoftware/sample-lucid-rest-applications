#!/usr/bin/env python3
"""
Example: create a Gantt chart Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/gantt.py

The example lays out a quarter-long product launch plan: discovery,
spec, design, implementation, QA, docs, launch. Each task is rendered
as a bar positioned by its start and end dates against a shared time
axis. `dependsOn` is validated for unknown ids but no dependency
arrows are drawn.
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.gantt import GanttChartGenerator


def main() -> None:
    generator = GanttChartGenerator()  # reads LUCID_API_KEY from env

    tasks = [
        {"id": "research", "label": "Discovery research", "start": "2026-01-05", "end": "2026-01-23"},
        {"id": "spec", "label": "Tech spec", "start": "2026-01-26", "end": "2026-02-06", "dependsOn": ["research"]},
        {"id": "design", "label": "UX design", "start": "2026-01-26", "end": "2026-02-13", "dependsOn": ["research"]},
        {
            "id": "backend",
            "label": "Backend implementation",
            "start": "2026-02-09",
            "end": "2026-03-13",
            "dependsOn": ["spec"],
        },
        {
            "id": "frontend",
            "label": "Frontend implementation",
            "start": "2026-02-16",
            "end": "2026-03-20",
            "dependsOn": ["design", "spec"],
        },
        {
            "id": "qa",
            "label": "QA & bug fixes",
            "start": "2026-03-16",
            "end": "2026-04-03",
            "dependsOn": ["backend", "frontend"],
        },
        {"id": "docs", "label": "Customer docs", "start": "2026-03-23", "end": "2026-04-03", "dependsOn": ["frontend"]},
        {"id": "launch", "label": "Launch", "start": "2026-04-06", "end": "2026-04-10", "dependsOn": ["qa", "docs"]},
    ]

    try:
        response = generator.create_document(
            title="Q1 launch plan",
            tasks=tasks,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
