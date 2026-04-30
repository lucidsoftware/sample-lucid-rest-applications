#!/usr/bin/env python3
"""
Example: create a flowchart Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/flowchart.py

This builds a moderately complex order-fulfillment flow with branches,
convergence points, and a payment-retry loop, then POSTs it to the
Lucid REST API and prints the editUrl of the new document.
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.flowchart import FlowchartGenerator


def main() -> None:
    generator = FlowchartGenerator()  # reads LUCID_API_KEY from env

    nodes = [
        {"id": "received", "label": "Order received", "shape": "terminator"},
        {"id": "validate", "label": "Validate order", "shape": "process"},
        {"id": "valid", "label": "Valid?", "shape": "decision"},
        {"id": "reject", "label": "Reject order", "shape": "process"},
        {"id": "check_stock", "label": "Check inventory", "shape": "process"},
        {"id": "in_stock", "label": "In stock?", "shape": "decision"},
        {"id": "backorder", "label": "Create backorder", "shape": "process"},
        {"id": "notify_back", "label": "Notify customer", "shape": "process"},
        {"id": "charge", "label": "Charge card", "shape": "process"},
        {"id": "charge_ok", "label": "Charge succeeded?", "shape": "decision"},
        {"id": "retry_charge", "label": "Retry payment", "shape": "process"},
        {"id": "max_retries", "label": "Max retries?", "shape": "decision"},
        {"id": "fail_pay", "label": "Payment failed", "shape": "process"},
        {"id": "pick", "label": "Pick items", "shape": "process"},
        {"id": "pack", "label": "Pack items", "shape": "process"},
        {"id": "ship", "label": "Ship", "shape": "process"},
        {"id": "confirm", "label": "Send confirmation", "shape": "process"},
        {"id": "complete", "label": "Complete", "shape": "terminator"},
        {"id": "cancelled", "label": "Cancelled", "shape": "terminator"},
    ]
    edges = [
        {"from": "received", "to": "validate"},
        {"from": "validate", "to": "valid"},
        {"from": "valid", "to": "reject", "label": "no"},
        {"from": "reject", "to": "cancelled"},
        {"from": "valid", "to": "check_stock", "label": "yes"},
        {"from": "check_stock", "to": "in_stock"},
        {"from": "in_stock", "to": "backorder", "label": "no"},
        {"from": "backorder", "to": "notify_back"},
        {"from": "notify_back", "to": "complete"},
        {"from": "in_stock", "to": "charge", "label": "yes"},
        {"from": "charge", "to": "charge_ok"},
        {"from": "charge_ok", "to": "retry_charge", "label": "no"},
        {"from": "retry_charge", "to": "max_retries"},
        {"from": "max_retries", "to": "fail_pay", "label": "yes"},
        {"from": "fail_pay", "to": "cancelled"},
        {"from": "max_retries", "to": "charge", "label": "no"},
        {"from": "charge_ok", "to": "pick", "label": "yes"},
        {"from": "pick", "to": "pack"},
        {"from": "pack", "to": "ship"},
        {"from": "ship", "to": "confirm"},
        {"from": "confirm", "to": "complete"},
    ]

    try:
        response = generator.create_document(
            title="Order fulfillment",
            nodes=nodes,
            edges=edges,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
