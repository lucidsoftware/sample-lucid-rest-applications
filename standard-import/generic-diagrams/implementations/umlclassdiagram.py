"""
UML class-diagram implementation of CreateDocumentBase.

Each class is rendered as a Lucid `table` shape with three sections:
the header row holds the class name (and optional stereotype, e.g.
`<<interface>>`); the attributes section lists fields formatted as
`<visibility> name: Type`; the methods section lists operations
formatted as `<visibility> name(params): ReturnType`. Sections are
separated visually by a section-header row whose label is `attributes`
or `methods`.

Relationships are smart lines whose endpoint styles encode UML
semantics:

    inheritance / generalization → generalization at the parent (`to`)
    realization / implements     → generalization at the parent (`to`), dashed line
    association                  → arrow         at `to`
    aggregation                  → aggregation   at the whole (`to`)
    composition                  → composition   at the whole (`to`)
    dependency                   → arrow         at `to`, dashed line

Layout uses Fruchterman-Reingold force-directed placement (same
algorithm as `ERDiagramGenerator`): pairwise repulsion plus attraction
along edges, cooled over a fixed iteration count from a deterministic
seed. Class diagrams have no inherent flow direction, so this objective
("related classes sit close, unrelated classes spread apart") tends to
produce readable layouts without the caller having to specify
positions. The force-directed positions are then wrapped in an
invisible `rectangleContainer` with `assistedLayout: true` so Lucid's
auto-layout engine refines them on import.

Input:

    classes = [
        {
            "id": "animal",
            "name": "Animal",
            "stereotype": "abstract",          # optional
            "attributes": [
                {"name": "name", "type": "String", "visibility": "+"},
                {"name": "age",  "type": "int",    "visibility": "-"},
            ],
            "methods": [
                {
                    "name": "makeSound",
                    "parameters": [{"name": "volume", "type": "int"}],
                    "returnType": "void",
                    "visibility": "+",
                    "abstract": True,
                },
            ],
        },
        ...
    ]
    relationships = [
        {
            "from": "dog", "to": "animal",
            "type": "inheritance",
            "fromMultiplicity": "*",          # optional
            "toMultiplicity": "1",            # optional
            "label": "extends",               # optional
        },
        ...
    ]

Visibility accepts the UML symbols directly (`+`, `-`, `#`, `~`) or
the spelled-out aliases (`public`, `private`, `protected`, `package`).
Defaults to `+` for attributes and methods when omitted.
"""

import math
import random
from typing import Any

from ..base import CreateDocumentBase

_VISIBILITY_ALIASES = {
    "+": "+",
    "-": "-",
    "#": "#",
    "~": "~",
    "public": "+",
    "private": "-",
    "protected": "#",
    "package": "~",
}

_RELATIONSHIP_STYLES: dict[str, dict[str, str]] = {
    "inheritance": {"toStyle": "generalization", "fromStyle": "none", "lineStyle": "solid"},
    "generalization": {"toStyle": "generalization", "fromStyle": "none", "lineStyle": "solid"},
    "realization": {"toStyle": "generalization", "fromStyle": "none", "lineStyle": "dashed"},
    "implementation": {"toStyle": "generalization", "fromStyle": "none", "lineStyle": "dashed"},
    "association": {"toStyle": "arrow", "fromStyle": "none", "lineStyle": "solid"},
    "aggregation": {"toStyle": "aggregation", "fromStyle": "none", "lineStyle": "solid"},
    "composition": {"toStyle": "composition", "fromStyle": "none", "lineStyle": "solid"},
    "dependency": {"toStyle": "arrow", "fromStyle": "none", "lineStyle": "dashed"},
}


class UMLClassDiagramGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    CLASS_WIDTH = 280
    ROW_HEIGHT = 30
    HEADER_FILL = "#DBEAFE"
    SECTION_FILL = "#F3F4F6"

    LINE_WIDTH = 2
    LINE_COLOR = "#374151"

    LAYOUT_ITERATIONS = 250
    LAYOUT_SEED = 42

    # Wrap all classes in an invisible rectangleContainer with assistedLayout
    # so Lucid re-tidies positions on import. The force-directed positions
    # serve as a starting hint that the layout engine refines.
    USE_ASSISTED_LAYOUT = True
    LAYOUT_CONTAINER_PADDING = 120

    DEFAULT_RELATIONSHIP_TYPE = "association"
    DEFAULT_VISIBILITY = "+"

    def generate_document_content_json(
        self,
        *,
        classes: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        page_title: str = "UML Class Diagram",
    ) -> dict[str, Any]:
        self._validate(classes, relationships)

        row_counts = {cls["id"]: self._row_count(cls) for cls in classes}
        heights = {cls_id: self.ROW_HEIGHT * count for cls_id, count in row_counts.items()}

        positions = self._force_directed_layout(classes, relationships, heights)

        shapes: list[dict[str, Any]] = []
        if self.USE_ASSISTED_LAYOUT and classes:
            shapes.append(self._build_layout_container(classes, positions, heights))

        shapes.extend(self._build_class_table(cls, positions[cls["id"]], heights[cls["id"]]) for cls in classes)
        lines = [self._build_relationship_line(relationship, index) for index, relationship in enumerate(relationships)]

        return {
            "version": 1,
            "pages": [
                {
                    "id": "page1",
                    "title": page_title,
                    "shapes": shapes,
                    "lines": lines,
                }
            ],
        }

    @staticmethod
    def _validate(classes: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> None:
        ids = [cls["id"] for cls in classes]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate class ids")
        valid = set(ids)
        for relationship in relationships:
            if relationship["from"] not in valid:
                raise ValueError(f"relationship references unknown class: {relationship['from']}")
            if relationship["to"] not in valid:
                raise ValueError(f"relationship references unknown class: {relationship['to']}")

    @staticmethod
    def _row_count(cls: dict[str, Any]) -> int:
        # Header + attributes-section header (if any attrs) + attribute rows +
        # methods-section header (if any methods) + method rows. A class with
        # no attributes and no methods still gets a one-row header.
        rows = 1
        attrs = cls.get("attributes", [])
        methods = cls.get("methods", [])
        if attrs:
            rows += 1 + len(attrs)
        if methods:
            rows += 1 + len(methods)
        return rows

    def _force_directed_layout(
        self,
        classes: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        heights: dict[str, float],
    ) -> dict[str, tuple[float, float]]:
        node_count = len(classes)
        if node_count == 0:
            return {}

        avg_height = sum(heights.values()) / node_count
        cell_size = math.sqrt(self.CLASS_WIDTH * avg_height) * 2
        canvas = max(800.0, math.sqrt(node_count) * cell_size)

        rng = random.Random(self.LAYOUT_SEED)
        ids = [cls["id"] for cls in classes]

        center = canvas / 2
        radius = canvas * 0.3
        positions: dict[str, list[float]] = {}
        for index, class_id in enumerate(ids):
            angle = 2 * math.pi * index / node_count
            jitter_x = rng.uniform(-radius * 0.05, radius * 0.05)
            jitter_y = rng.uniform(-radius * 0.05, radius * 0.05)
            positions[class_id] = [
                center + radius * math.cos(angle) + jitter_x,
                center + radius * math.sin(angle) + jitter_y,
            ]

        if node_count == 1:
            class_id = ids[0]
            return {class_id: (positions[class_id][0], positions[class_id][1])}

        edges = [
            (relationship["from"], relationship["to"])
            for relationship in relationships
            if relationship["from"] != relationship["to"]
        ]

        k = math.sqrt((canvas * canvas) / node_count)
        temperature = canvas * 0.1
        cooling = temperature / self.LAYOUT_ITERATIONS

        for _ in range(self.LAYOUT_ITERATIONS):
            displacement = {class_id: [0.0, 0.0] for class_id in ids}

            for index, source in enumerate(ids):
                for target in ids[index + 1 :]:
                    sx, sy = positions[source]
                    tx, ty = positions[target]
                    dx = sx - tx
                    dy = sy - ty
                    distance = math.sqrt(dx * dx + dy * dy) or 0.01
                    force = (k * k) / distance
                    fx = (dx / distance) * force
                    fy = (dy / distance) * force
                    displacement[source][0] += fx
                    displacement[source][1] += fy
                    displacement[target][0] -= fx
                    displacement[target][1] -= fy

            for source, target in edges:
                sx, sy = positions[source]
                tx, ty = positions[target]
                dx = sx - tx
                dy = sy - ty
                distance = math.sqrt(dx * dx + dy * dy) or 0.01
                force = (distance * distance) / k
                fx = (dx / distance) * force
                fy = (dy / distance) * force
                displacement[source][0] -= fx
                displacement[source][1] -= fy
                displacement[target][0] += fx
                displacement[target][1] += fy

            for class_id in ids:
                dx, dy = displacement[class_id]
                magnitude = math.sqrt(dx * dx + dy * dy) or 0.01
                limit = min(magnitude, temperature)
                positions[class_id][0] += (dx / magnitude) * limit
                positions[class_id][1] += (dy / magnitude) * limit

            temperature -= cooling

        return {class_id: (xs[0], xs[1]) for class_id, xs in positions.items()}

    def _build_layout_container(
        self,
        classes: list[dict[str, Any]],
        positions: dict[str, tuple[float, float]],
        heights: dict[str, float],
    ) -> dict[str, Any]:
        """An invisible rectangleContainer with assistedLayout=true, sized to
        enclose every class. Lucid's assisted layout will neaten the
        positions on import; the force-directed layout serves as a hint."""
        min_x = min(positions[cls["id"]][0] - self.CLASS_WIDTH / 2 for cls in classes)
        max_x = max(positions[cls["id"]][0] + self.CLASS_WIDTH / 2 for cls in classes)
        min_y = min(positions[cls["id"]][1] - heights[cls["id"]] / 2 for cls in classes)
        max_y = max(positions[cls["id"]][1] + heights[cls["id"]] / 2 for cls in classes)
        padding = self.LAYOUT_CONTAINER_PADDING
        return {
            "id": "_layout_container",
            "type": "rectangleContainer",
            "boundingBox": {
                "x": min_x - padding,
                "y": min_y - padding,
                "w": (max_x - min_x) + 2 * padding,
                "h": (max_y - min_y) + 2 * padding,
            },
            "assistedLayout": True,
            "opacity": 0,
        }

    def _build_class_table(
        self,
        cls: dict[str, Any],
        position: tuple[float, float],
        height: float,
    ) -> dict[str, Any]:
        x_center, y_center = position
        attrs = cls.get("attributes", [])
        methods = cls.get("methods", [])

        header_text = cls["name"]
        stereotype = cls.get("stereotype")
        if stereotype:
            header_text = f"«{stereotype}»\n{cls['name']}"

        cells: list[dict[str, Any]] = [
            {
                "xPosition": 0,
                "yPosition": 0,
                "text": header_text,
                "style": {"fill": {"type": "color", "color": self.HEADER_FILL}},
            }
        ]

        row = 1
        if attrs:
            cells.append(
                {
                    "xPosition": 0,
                    "yPosition": row,
                    "text": "attributes",
                    "style": {"fill": {"type": "color", "color": self.SECTION_FILL}},
                }
            )
            row += 1
            for attr in attrs:
                cells.append(
                    {
                        "xPosition": 0,
                        "yPosition": row,
                        "text": self._format_attribute(attr),
                    }
                )
                row += 1

        if methods:
            cells.append(
                {
                    "xPosition": 0,
                    "yPosition": row,
                    "text": "methods",
                    "style": {"fill": {"type": "color", "color": self.SECTION_FILL}},
                }
            )
            row += 1
            for method in methods:
                cells.append(
                    {
                        "xPosition": 0,
                        "yPosition": row,
                        "text": self._format_method(method),
                    }
                )
                row += 1

        return {
            "id": cls["id"],
            "type": "table",
            "boundingBox": {
                "x": x_center - self.CLASS_WIDTH / 2,
                "y": y_center - height / 2,
                "w": self.CLASS_WIDTH,
                "h": height,
            },
            "rowCount": row,
            "colCount": 1,
            "cells": cells,
        }

    def _format_attribute(self, attr: dict[str, Any]) -> str:
        visibility = self._visibility_symbol(attr.get("visibility", self.DEFAULT_VISIBILITY))
        type_part = f": {attr['type']}" if attr.get("type") else ""
        return f"{visibility} {attr['name']}{type_part}"

    def _format_method(self, method: dict[str, Any]) -> str:
        visibility = self._visibility_symbol(method.get("visibility", self.DEFAULT_VISIBILITY))
        params = ", ".join(
            f"{p['name']}: {p['type']}" if p.get("type") else p["name"] for p in method.get("parameters", [])
        )
        return_part = f": {method['returnType']}" if method.get("returnType") else ""
        signature = f"{visibility} {method['name']}({params}){return_part}"
        # Italicize abstract methods by convention; the renderer treats this
        # as plain text but the surrounding underscores read as the standard
        # textual marker for abstract operations.
        if method.get("abstract"):
            signature = f"_{signature}_"
        return signature

    @staticmethod
    def _visibility_symbol(visibility: str) -> str:
        symbol = _VISIBILITY_ALIASES.get(visibility)
        if symbol is None:
            raise ValueError(f"unsupported visibility: {visibility}")
        return symbol

    def _build_relationship_line(self, relationship: dict[str, Any], index: int) -> dict[str, Any]:
        relationship_type = relationship.get("type", self.DEFAULT_RELATIONSHIP_TYPE)
        styles = _RELATIONSHIP_STYLES.get(relationship_type)
        if styles is None:
            raise ValueError(f"unsupported relationship type: {relationship_type}")

        endpoint1: dict[str, Any] = {
            "type": "shapeEndpoint",
            "style": styles["fromStyle"],
            "shapeId": relationship["from"],
        }
        endpoint2: dict[str, Any] = {
            "type": "shapeEndpoint",
            "style": styles["toStyle"],
            "shapeId": relationship["to"],
        }

        line: dict[str, Any] = {
            "id": f"rel-{index}",
            "lineType": "elbow",
            "endpoint1": endpoint1,
            "endpoint2": endpoint2,
            "stroke": {
                "color": self.LINE_COLOR,
                "width": self.LINE_WIDTH,
                "style": styles["lineStyle"],
            },
        }

        text_labels: list[dict[str, Any]] = []
        if "label" in relationship:
            text_labels.append({"text": relationship["label"], "position": 0.5, "side": "middle"})
        if "fromMultiplicity" in relationship:
            text_labels.append(
                {
                    "text": str(relationship["fromMultiplicity"]),
                    "position": 0.05,
                    "side": "middle",
                }
            )
        if "toMultiplicity" in relationship:
            text_labels.append(
                {
                    "text": str(relationship["toMultiplicity"]),
                    "position": 0.95,
                    "side": "middle",
                }
            )
        if text_labels:
            line["text"] = text_labels

        return line
