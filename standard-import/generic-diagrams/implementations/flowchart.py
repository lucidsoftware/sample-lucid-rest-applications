"""
Flowchart implementation of CreateDocumentBase.

Layout is delegated to Lucid's built-in AssistedLayoutGenerator (declared
as a `dataBackedShapes` entry of type `assistedLayout` in the Standard
Import). The script supplies shapes and connections with placeholder
positions; on import, Lucid's auto-layout engine repositions every listed
shape into a clean flowchart layout.

Example:

    generator = FlowchartGenerator(api_key=...)
    generator.create_document(
        title="Onboarding Flow",
        nodes=[
            {"id": "start",  "label": "Start",         "shape": "terminator"},
            {"id": "verify", "label": "Verify email",  "shape": "process"},
            {"id": "ok",     "label": "Verified?",     "shape": "decision"},
            {"id": "resend", "label": "Resend email",  "shape": "process"},
            {"id": "done",   "label": "Done",          "shape": "terminator"},
        ],
        edges=[
            {"from": "start",  "to": "verify"},
            {"from": "verify", "to": "ok"},
            {"from": "ok",     "to": "done",   "label": "yes"},
            {"from": "ok",     "to": "resend", "label": "no"},
            {"from": "resend", "to": "verify"},
        ],
    )
"""

from typing import Any

from ..base import CreateDocumentBase


class FlowchartGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    SHAPE_WIDTH = 200
    SHAPE_HEIGHT = 80
    INITIAL_X = 100
    INITIAL_Y = 100
    PLACEHOLDER_GAP = 40

    def generate_document_content_json(
        self,
        *,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        page_title: str = "Flowchart",
    ) -> dict[str, Any]:
        """Build Lucid Standard Import JSON for a flowchart.

        nodes: each item is a dict with keys:
            - id (str): unique id used in edges
            - label (str): visible text on the shape
            - shape (str, optional): flowchart shape type. Defaults to "process".
              Common values: "process", "decision", "terminator", "data", "document".
        edges: each item is a dict with keys:
            - from (str): source node id
            - to (str): target node id
            - label (str, optional): label drawn on the line

        Positions on the resulting shapes are placeholders — every shape
        is stacked in a single column at import time, then Lucid's
        auto-layout engine repositions them.
        """
        shapes = [self._build_shape(node, index) for index, node in enumerate(nodes)]
        lines = [self._build_line(edge, index) for index, edge in enumerate(edges)]
        return {
            "version": 1,
            "pages": [
                {
                    "id": "page1",
                    "title": page_title,
                    "shapes": shapes,
                    "lines": lines,
                    "dataBackedShapes": [
                        {
                            "type": "assistedLayout",
                            "id": "flowchart-layout",
                            "shapeIds": [node["id"] for node in nodes],
                        }
                    ],
                }
            ],
        }

    def _build_shape(self, node: dict[str, Any], index: int) -> dict[str, Any]:
        return {
            "id": node["id"],
            "type": node.get("shape", "process"),
            "boundingBox": {
                "x": self.INITIAL_X,
                "y": self.INITIAL_Y + index * (self.SHAPE_HEIGHT + self.PLACEHOLDER_GAP),
                "w": self.SHAPE_WIDTH,
                "h": self.SHAPE_HEIGHT,
            },
            "text": node["label"],
        }

    @staticmethod
    def _build_line(edge: dict[str, Any], index: int) -> dict[str, Any]:
        line: dict[str, Any] = {
            "id": f"edge-{index}",
            "lineType": "elbow",
            "endpoint1": {
                "type": "shapeEndpoint",
                "style": "none",
                "shapeId": edge["from"],
                "position": {"x": 0.5, "y": 1},
            },
            "endpoint2": {
                "type": "shapeEndpoint",
                "style": "arrow",
                "shapeId": edge["to"],
                "position": {"x": 0.5, "y": 0},
            },
            "stroke": {"color": "#000000", "width": 2, "style": "solid"},
        }
        if "label" in edge:
            line["text"] = [{"text": edge["label"], "position": 0.5, "side": "middle"}]
        return line
