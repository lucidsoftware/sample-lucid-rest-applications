"""
Fishbone (Ishikawa / cause-and-effect) diagram implementation of
CreateDocumentBase.

Produces a single-page Lucidchart document laid out as a classic
fishbone: a horizontal arrow points to the problem on the right;
diagonal ribs branch off the spine, alternating up and down, each
labeled with a category and a list of contributing causes.

Layout is fully deterministic geometry — no auto-layout — because the
fishbone shape is the diagram's whole point.

Input:

    generator.create_document(
        title="Why are deploys failing?",
        problem="Production deploy failures",
        categories=[
            {"label": "People",      "causes": ["Insufficient training",
                                                 "Comms gaps"]},
            {"label": "Process",     "causes": ["No rollback plan",
                                                 "Manual deploys",
                                                 "Skipped reviews"]},
            {"label": "Tools",       "causes": ["Stale CI",
                                                 "No staging parity"]},
            {"label": "Environment", "causes": ["Flaky network",
                                                 "Resource contention"]},
        ],
    )

`problem` is a single string rendered in the head box. `categories` is
a list of `{"label", "causes"}` dicts; `causes` is a list of strings
(may be empty). Categories alternate above (even indices) and below
(odd indices) the spine, in input order.
"""

import math
from typing import Any

from ..base import CreateDocumentBase


class FishboneGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    HEAD_WIDTH = 220
    HEAD_HEIGHT = 100
    CATEGORY_WIDTH = 200
    CATEGORY_ROW_HEIGHT = 36

    SPINE_LENGTH = 1000
    RIB_LENGTH = 220
    RIB_ANGLE_DEGREES = 60  # measured from spine (horizontal)
    ANCHOR_BUFFER_LEFT = 120  # spine x distance before first rib anchor
    ANCHOR_BUFFER_RIGHT = 240  # spine x distance after last rib anchor (head clearance)

    LEFT_MARGIN = 80
    OUTER_MARGIN = 80  # vertical clearance above topmost / below bottommost shape

    HEAD_FILL = "#FEE2E2"
    HEAD_STROKE = "#DC2626"
    CATEGORY_HEADER_FILL = "#DBEAFE"
    SPINE_COLOR = "#374151"
    SPINE_WIDTH = 3
    LINE_COLOR = "#6B7280"
    LINE_WIDTH = 2

    def generate_document_content_json(
        self,
        *,
        problem: str,
        categories: list[dict[str, Any]],
        page_title: str = "Fishbone",
    ) -> dict[str, Any]:
        if not categories:
            raise ValueError("at least one category is required")

        angle_rad = math.radians(self.RIB_ANGLE_DEGREES)
        rib_dx = self.RIB_LENGTH * math.cos(angle_rad)
        rib_dy = self.RIB_LENGTH * math.sin(angle_rad)

        category_box_heights = [self._category_box_height(category) for category in categories]
        max_category_height = max(category_box_heights)
        spine_y = self.OUTER_MARGIN + max_category_height + rib_dy
        spine_start_x = self.LEFT_MARGIN
        spine_end_x = spine_start_x + self.SPINE_LENGTH
        head_left_x = spine_end_x - self.HEAD_WIDTH

        anchors = self._compute_anchors(spine_start_x, spine_end_x, len(categories))

        shapes: list[dict[str, Any]] = [self._build_head(problem, head_left_x, spine_y)]
        lines: list[dict[str, Any]] = [self._build_spine(spine_start_x, spine_y, head_left_x)]

        for index, category in enumerate(categories):
            anchor_x = anchors[index]
            direction = -1 if index % 2 == 0 else 1  # -1 = above (smaller y), +1 = below
            rib_end_x = anchor_x - rib_dx
            rib_end_y = spine_y + direction * rib_dy
            box_height = category_box_heights[index]
            category_id = f"category-{index}"

            shapes.append(self._build_category_box(category, category_id, rib_end_x, rib_end_y, box_height, direction))
            lines.append(self._build_rib(category_id, anchor_x, spine_y, direction, index))

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

    def _category_box_height(self, category: dict[str, Any]) -> float:
        # 1 header row for the label + 1 row per cause.
        return (1 + len(category.get("causes", []))) * self.CATEGORY_ROW_HEIGHT

    def _compute_anchors(self, spine_start_x: float, spine_end_x: float, count: int) -> list[float]:
        first = spine_start_x + self.ANCHOR_BUFFER_LEFT
        last = spine_end_x - self.ANCHOR_BUFFER_RIGHT
        if count == 1:
            return [(first + last) / 2]
        step = (last - first) / (count - 1)
        return [first + index * step for index in range(count)]

    def _build_head(self, problem: str, head_left_x: float, spine_y: float) -> dict[str, Any]:
        return {
            "id": "_head",
            "type": "rectangle",
            "boundingBox": {
                "x": head_left_x,
                "y": spine_y - self.HEAD_HEIGHT / 2,
                "w": self.HEAD_WIDTH,
                "h": self.HEAD_HEIGHT,
            },
            "text": problem,
            "style": {
                "fill": {"type": "color", "color": self.HEAD_FILL},
                "stroke": {"color": self.HEAD_STROKE, "width": 2, "style": "solid"},
            },
        }

    def _build_spine(self, spine_start_x: float, spine_y: float, head_left_x: float) -> dict[str, Any]:
        return {
            "id": "_spine",
            "lineType": "straight",
            "endpoint1": {
                "type": "positionEndpoint",
                "style": "none",
                "position": {"x": spine_start_x, "y": spine_y},
            },
            "endpoint2": {
                "type": "positionEndpoint",
                "style": "arrow",
                "position": {"x": head_left_x, "y": spine_y},
            },
            "stroke": {
                "color": self.SPINE_COLOR,
                "width": self.SPINE_WIDTH,
                "style": "solid",
            },
        }

    def _build_category_box(
        self,
        category: dict[str, Any],
        category_id: str,
        rib_end_x: float,
        rib_end_y: float,
        box_height: float,
        direction: int,
    ) -> dict[str, Any]:
        # Box's edge nearest the spine sits exactly at rib_end_y; the box
        # extends away from the spine. Direction -1 means "above"
        # (smaller y), so the box's BOTTOM is at rib_end_y; +1 means
        # "below", so its TOP is at rib_end_y.
        box_y = rib_end_y - box_height if direction == -1 else rib_end_y
        causes = category.get("causes", [])
        cells: list[dict[str, Any]] = [
            {
                "xPosition": 0,
                "yPosition": 0,
                "text": category["label"],
                "style": {"fill": {"type": "color", "color": self.CATEGORY_HEADER_FILL}},
            }
        ]
        for index, cause in enumerate(causes):
            cells.append({"xPosition": 0, "yPosition": index + 1, "text": cause})
        return {
            "id": category_id,
            "type": "table",
            "boundingBox": {
                "x": rib_end_x - self.CATEGORY_WIDTH / 2,
                "y": box_y,
                "w": self.CATEGORY_WIDTH,
                "h": box_height,
            },
            "rowCount": 1 + len(causes),
            "colCount": 1,
            "cells": cells,
        }

    def _build_rib(
        self,
        category_id: str,
        anchor_x: float,
        spine_y: float,
        direction: int,
        index: int,
    ) -> dict[str, Any]:
        # The rib enters the box at its near-spine edge, centered. For
        # categories above (direction = -1) that's bottom-center (0.5, 1);
        # for below (direction = +1) that's top-center (0.5, 0).
        category_edge = {"x": 0.5, "y": 1 if direction == -1 else 0}
        return {
            "id": f"rib-{index}",
            "lineType": "straight",
            "endpoint1": {
                "type": "shapeEndpoint",
                "style": "none",
                "shapeId": category_id,
                "position": category_edge,
            },
            "endpoint2": {
                "type": "positionEndpoint",
                "style": "none",
                "position": {"x": anchor_x, "y": spine_y},
            },
            "stroke": {
                "color": self.LINE_COLOR,
                "width": self.LINE_WIDTH,
                "style": "solid",
            },
        }
