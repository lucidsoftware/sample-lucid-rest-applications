#!/usr/bin/env python3
"""
Example: create a UML sequence diagram Lucid document.

Set LUCID_API_KEY in your environment, then run:

    python3 documentcreation/examples/sequence.py

The example walks through an e-commerce checkout: customer → web app →
order service → inventory / payments / database. Messages render as
horizontal arrows between actor lifelines, ordered top-to-bottom in
input order. `call` messages are solid; `return` messages are dashed
with an open arrow. A self-message ("Validate card") renders as a
U-shaped loop back to the same lifeline.
"""

import sys
from pathlib import Path

# Make the parent `documentcreation` package importable when this file
# is executed directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from documentcreation.base import CreateDocumentError
from documentcreation.implementations.sequence import SequenceGenerator


def main() -> None:
    generator = SequenceGenerator()  # reads LUCID_API_KEY from env

    actors = [
        {"id": "customer", "label": "Customer"},
        {"id": "web", "label": "Web App"},
        {"id": "orders", "label": "Order Service"},
        {"id": "inventory", "label": "Inventory Service"},
        {"id": "payments", "label": "Payment Service"},
        {"id": "db", "label": "Database"},
    ]
    messages = [
        {"from": "customer", "to": "web", "label": 'Click "Place order"'},
        {"from": "web", "to": "orders", "label": "POST /orders"},
        {"from": "orders", "to": "inventory", "label": "Reserve items"},
        {"from": "inventory", "to": "db", "label": "SELECT stock"},
        {"from": "db", "to": "inventory", "label": "Stock rows", "type": "return"},
        {"from": "inventory", "to": "db", "label": "UPDATE stock -N"},
        {"from": "db", "to": "inventory", "label": "OK", "type": "return"},
        {"from": "inventory", "to": "orders", "label": "reservationId", "type": "return"},
        {"from": "orders", "to": "payments", "label": "Charge $total"},
        {"from": "payments", "to": "payments", "label": "Validate card"},
        {"from": "payments", "to": "db", "label": "INSERT transaction"},
        {"from": "db", "to": "payments", "label": "OK", "type": "return"},
        {"from": "payments", "to": "orders", "label": "transactionId", "type": "return"},
        {"from": "orders", "to": "db", "label": "INSERT order"},
        {"from": "db", "to": "orders", "label": "orderId", "type": "return"},
        {"from": "orders", "to": "web", "label": "201 Created", "type": "return"},
        {"from": "web", "to": "customer", "label": 'Show "Order placed"'},
    ]

    try:
        response = generator.create_document(
            title="Checkout sequence",
            actors=actors,
            messages=messages,
        )
    except CreateDocumentError as error:
        print(f"create_document failed: {error}", file=sys.stderr)
        sys.exit(1)

    print(response["editUrl"])


if __name__ == "__main__":
    main()
