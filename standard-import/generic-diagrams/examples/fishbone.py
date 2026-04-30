#!/usr/bin/env python3
"""
Example: create an Ishikawa (fishbone) diagram Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/fishbone.py

The example walks through a "why are production deploys failing?"
root-cause analysis using the classic 6M categories (People, Process,
Tools, Environment, Inputs, Measurement). The problem renders in the
head box on the right; categories alternate above and below the
horizontal spine.
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.fishbone import FishboneGenerator


def main() -> None:
    generator = FishboneGenerator()  # reads LUCID_API_KEY from env

    categories = [
        {
            "label": "People",
            "causes": [
                "Insufficient on-call training",
                "Communication gaps between teams",
                "Burnout / fatigue",
            ],
        },
        {
            "label": "Process",
            "causes": [
                "No rollback plan",
                "Manual deploy steps",
                "Reviews skipped under deadline",
            ],
        },
        {
            "label": "Tools",
            "causes": [
                "Stale CI image",
                "No staging parity",
                "Slow build feedback",
            ],
        },
        {
            "label": "Environment",
            "causes": [
                "Flaky network",
                "Resource contention",
            ],
        },
        {
            "label": "Inputs",
            "causes": [
                "Schema drift in upstream API",
                "Unvalidated config changes",
            ],
        },
        {
            "label": "Measurement",
            "causes": [
                "Alert thresholds too lax",
                "Missing tracing on critical paths",
            ],
        },
    ]

    try:
        response = generator.create_document(
            title="Why are production deploys failing?",
            problem="Production deploy failures",
            categories=categories,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
