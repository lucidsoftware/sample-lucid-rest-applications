"""
Base class for scripts that programmatically generate Lucid documents
through the Lucid REST API's POST /documents endpoint.

A subclass represents a *kind* of document (e.g. a flowchart, a
swim-lane diagram). It implements `generate_document_content_json` to
turn caller-supplied data into Lucid Standard JSON. A single subclass
instance is reused across many `create_document` calls, each of which
takes the per-document metadata (title, parent, team, ...) and the
content-specific kwargs.

Typical use:

    class FlowchartGenerator(CreateDocumentBase):
        def generate_document_content_json(self, *, nodes, edges):
            return {...}

    generator = FlowchartGenerator(api_key=...)
    generator.create_document(title="Onboarding", nodes=[...], edges=[...])
    generator.create_document(title="Renewal", parent={...}, nodes=[...], edges=[...])
"""

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any


class CreateDocumentError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"Lucid REST API returned {status}: {body}")
        self.status = status
        self.body = body


class CreateDocumentBase(ABC):
    HOST = "https://api.lucid.co"

    # Subclasses may override to target a different product (e.g. "lucidspark").
    DEFAULT_PRODUCT = "lucidchart"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("LUCID_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required: pass api_key=... or set LUCID_API_KEY")

    @abstractmethod
    def generate_document_content_json(self, **kwargs: Any) -> dict[str, Any]:
        """Return the Lucid Standard JSON content for one document.

        Subclasses define their own keyword arguments for the data that
        varies per document. Callers pass those through `create_document`.
        """

    def create_document(
        self,
        title: str,
        *,
        product: str | None = None,
        parent: dict[str, Any] | None = None,
        team: str | None = None,
        **content_kwargs: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "title": title,
            "product": product or self.DEFAULT_PRODUCT,
            "content": self.generate_document_content_json(**content_kwargs),
        }
        if parent is not None:
            body["parent"] = parent
        if team is not None:
            body["team"] = team

        request = urllib.request.Request(
            f"{self.HOST}/v1/documents",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise CreateDocumentError(error.code, error.read().decode("utf-8")) from error
