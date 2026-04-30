"""
Entity-relationship diagram implementation of CreateDocumentBase.

Each entity is rendered as a Lucid `table` shape: row 0 is a merged
header containing the entity name; subsequent rows list attributes as
`(name [(key)], type)` pairs. Relationships are smart lines whose
endpoint styles encode cardinality (one, many, zeroOrMore, etc.).

Layout uses Fruchterman-Reingold force-directed placement: pairwise
repulsion plus attraction along edges, cooled over a fixed iteration
count from a deterministic seed. ER diagrams have no inherent flow
direction, so this objective ("related entities sit close, unrelated
entities spread apart") tends to produce readable layouts without the
caller having to specify positions.

Input:

    entities = [
        {
            "id": "user",
            "name": "User",
            "attributes": [
                {"name": "id",      "type": "uuid",      "key": "PK"},
                {"name": "email",   "type": "varchar"},
                {"name": "name",    "type": "varchar"},
            ],
        },
        ...
    ]
    relationships = [
        {
            "from": "user", "to": "post",
            "fromCardinality": "one", "toCardinality": "many",
            "label": "writes",
        },
        ...
    ]

Cardinality accepts the Standard Import endpoint styles directly
(`one`, `many`, `zeroOrOne`, `zeroOrMore`, `oneOrMore`, `exactlyOne`)
plus a few aliases (`1`, `n`, `*`, `0..1`, `1..*`, `0..*`).

Limitations: force-directed is non-deterministic across seeds and can
land in unfortunate local minima for densely-connected schemas. The
seed is fixed (LAYOUT_SEED) so a given input always produces the same
output, but the result may not be globally optimal.
"""

import math
import random
from typing import Any

from ..base import CreateDocumentBase

_CARDINALITY_ALIASES = {
    "one": "one",
    "many": "many",
    "zeroOrOne": "zeroOrOne",
    "zeroOrMore": "zeroOrMore",
    "oneOrMore": "oneOrMore",
    "exactlyOne": "exactlyOne",
    "1": "one",
    "n": "many",
    "*": "many",
    "0..1": "zeroOrOne",
    "1..*": "oneOrMore",
    "0..*": "zeroOrMore",
}


class ERDiagramGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    ENTITY_WIDTH = 280
    ROW_HEIGHT = 36
    HEADER_FILL = "#DBEAFE"

    LINE_WIDTH = 2
    LINE_COLOR = "#374151"

    LAYOUT_ITERATIONS = 250
    LAYOUT_SEED = 42

    # Wrap all entities in an invisible rectangleContainer with assistedLayout
    # so Lucid re-tidies positions on import. The force-directed positions
    # serve as a starting hint that the layout engine refines.
    USE_ASSISTED_LAYOUT = True
    LAYOUT_CONTAINER_PADDING = 120

    DEFAULT_FROM_CARDINALITY = "one"
    DEFAULT_TO_CARDINALITY = "many"

    def generate_document_content_json(
        self,
        *,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        page_title: str = "ER Diagram",
    ) -> dict[str, Any]:
        self._validate(entities, relationships)

        heights = {entity["id"]: self.ROW_HEIGHT * (1 + len(entity.get("attributes", []))) for entity in entities}

        positions = self._force_directed_layout(entities, relationships, heights)

        shapes: list[dict[str, Any]] = []
        if self.USE_ASSISTED_LAYOUT and entities:
            shapes.append(self._build_layout_container(entities, positions, heights))

        shapes.extend(
            self._build_entity_table(entity, positions[entity["id"]], heights[entity["id"]]) for entity in entities
        )
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
    def _validate(entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> None:
        ids = [entity["id"] for entity in entities]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate entity ids")
        valid = set(ids)
        for relationship in relationships:
            if relationship["from"] not in valid:
                raise ValueError(f"relationship references unknown entity: {relationship['from']}")
            if relationship["to"] not in valid:
                raise ValueError(f"relationship references unknown entity: {relationship['to']}")

    def _force_directed_layout(
        self,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        heights: dict[str, float],
    ) -> dict[str, tuple[float, float]]:
        node_count = len(entities)
        if node_count == 0:
            return {}

        avg_height = sum(heights.values()) / node_count
        cell_size = math.sqrt(self.ENTITY_WIDTH * avg_height) * 2
        canvas = max(800.0, math.sqrt(node_count) * cell_size)

        rng = random.Random(self.LAYOUT_SEED)
        ids = [entity["id"] for entity in entities]

        # Seed positions on a jittered circle so the algorithm has a
        # reasonable starting point but isn't perfectly symmetric.
        center = canvas / 2
        radius = canvas * 0.3
        positions: dict[str, list[float]] = {}
        for index, entity_id in enumerate(ids):
            angle = 2 * math.pi * index / node_count
            jitter_x = rng.uniform(-radius * 0.05, radius * 0.05)
            jitter_y = rng.uniform(-radius * 0.05, radius * 0.05)
            positions[entity_id] = [
                center + radius * math.cos(angle) + jitter_x,
                center + radius * math.sin(angle) + jitter_y,
            ]

        if node_count == 1:
            entity_id = ids[0]
            return {entity_id: (positions[entity_id][0], positions[entity_id][1])}

        edges = [
            (relationship["from"], relationship["to"])
            for relationship in relationships
            if relationship["from"] != relationship["to"]
        ]

        # Fruchterman-Reingold spring constant: ideal edge length scales with
        # canvas size and inversely with sqrt(n).
        k = math.sqrt((canvas * canvas) / node_count)
        temperature = canvas * 0.1
        cooling = temperature / self.LAYOUT_ITERATIONS

        for _ in range(self.LAYOUT_ITERATIONS):
            displacement = {entity_id: [0.0, 0.0] for entity_id in ids}

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

            for entity_id in ids:
                dx, dy = displacement[entity_id]
                magnitude = math.sqrt(dx * dx + dy * dy) or 0.01
                limit = min(magnitude, temperature)
                positions[entity_id][0] += (dx / magnitude) * limit
                positions[entity_id][1] += (dy / magnitude) * limit

            temperature -= cooling

        return {entity_id: (xs[0], xs[1]) for entity_id, xs in positions.items()}

    def _build_layout_container(
        self,
        entities: list[dict[str, Any]],
        positions: dict[str, tuple[float, float]],
        heights: dict[str, float],
    ) -> dict[str, Any]:
        """An invisible rectangleContainer with assistedLayout=true, sized to
        enclose every entity. Lucid's assisted layout will neaten the
        positions on import; the force-directed layout serves as a hint."""
        min_x = min(positions[entity["id"]][0] - self.ENTITY_WIDTH / 2 for entity in entities)
        max_x = max(positions[entity["id"]][0] + self.ENTITY_WIDTH / 2 for entity in entities)
        min_y = min(positions[entity["id"]][1] - heights[entity["id"]] / 2 for entity in entities)
        max_y = max(positions[entity["id"]][1] + heights[entity["id"]] / 2 for entity in entities)
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

    def _build_entity_table(
        self,
        entity: dict[str, Any],
        position: tuple[float, float],
        height: float,
    ) -> dict[str, Any]:
        x_center, y_center = position
        attrs = entity.get("attributes", [])
        row_count = 1 + len(attrs)

        cells: list[dict[str, Any]] = [
            {
                "xPosition": 0,
                "yPosition": 0,
                "text": entity["name"],
                "mergeCellsRight": 1,
                "style": {"fill": {"type": "color", "color": self.HEADER_FILL}},
            }
        ]
        for index, attr in enumerate(attrs):
            label = attr["name"]
            key = attr.get("key")
            if key:
                label = f"{label} ({key})"
            cells.append({"xPosition": 0, "yPosition": index + 1, "text": label})
            cells.append(
                {
                    "xPosition": 1,
                    "yPosition": index + 1,
                    "text": attr.get("type", ""),
                }
            )

        return {
            "id": entity["id"],
            "type": "table",
            "boundingBox": {
                "x": x_center - self.ENTITY_WIDTH / 2,
                "y": y_center - height / 2,
                "w": self.ENTITY_WIDTH,
                "h": height,
            },
            "rowCount": row_count,
            "colCount": 2,
            "cells": cells,
        }

    def _build_relationship_line(self, relationship: dict[str, Any], index: int) -> dict[str, Any]:
        from_style = self._cardinality_style(relationship.get("fromCardinality", self.DEFAULT_FROM_CARDINALITY))
        to_style = self._cardinality_style(relationship.get("toCardinality", self.DEFAULT_TO_CARDINALITY))
        # Omitting `position` on both endpoints turns this into a smart line,
        # so attachment points adjust to the chosen layout automatically.
        line: dict[str, Any] = {
            "id": f"rel-{index}",
            "lineType": "elbow",
            "endpoint1": {
                "type": "shapeEndpoint",
                "style": from_style,
                "shapeId": relationship["from"],
            },
            "endpoint2": {
                "type": "shapeEndpoint",
                "style": to_style,
                "shapeId": relationship["to"],
            },
            "stroke": {
                "color": self.LINE_COLOR,
                "width": self.LINE_WIDTH,
                "style": "solid",
            },
        }
        if "label" in relationship:
            line["text"] = [{"text": relationship["label"], "position": 0.5, "side": "middle"}]
        return line

    @staticmethod
    def _cardinality_style(cardinality: str) -> str:
        style = _CARDINALITY_ALIASES.get(cardinality)
        if style is None:
            raise ValueError(f"unsupported cardinality: {cardinality}")
        return style
