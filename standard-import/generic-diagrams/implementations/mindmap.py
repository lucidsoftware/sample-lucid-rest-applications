"""
Mindmap implementation of CreateDocumentBase.

Produces a single-page Lucidchart document laid out as a radial mindmap:
the root sits in the centre and top-level branches radiate outward to the
right and left. Each side is laid out as an independent horizontal tree
where each subtree occupies a vertical band proportional to its leaf
count; the two sides are vertically centred on the root.

Aesthetic choices:
- Root has a distinct dark fill with light text and is sized larger.
- Each top-level branch is assigned a color from PALETTE; that color is
  inherited by all descendants of the branch (both fills and the lines
  connecting them).
- Lines are curved and colored to match the subtree they lead into.

Input is a recursive `tree` dict:

    {
        "id": "root",
        "label": "Mindmap topic",
        "children": [
            {"id": "a", "label": "Branch A", "children": [
                {"id": "a1", "label": "Leaf A1"},
                {"id": "a2", "label": "Leaf A2"},
            ]},
            {"id": "b", "label": "Branch B"},
        ],
    }

Each node must have a unique `id` and a `label`; `children` is optional.
"""

from typing import Any

from ..base import CreateDocumentBase

_DEFAULT_PALETTE = [
    {"fill": "#DBEAFE", "stroke": "#2563EB", "text": "#1E3A8A"},  # blue
    {"fill": "#DCFCE7", "stroke": "#16A34A", "text": "#14532D"},  # green
    {"fill": "#FED7AA", "stroke": "#EA580C", "text": "#7C2D12"},  # orange
    {"fill": "#E9D5FF", "stroke": "#7C3AED", "text": "#4C1D95"},  # purple
    {"fill": "#FCE7F3", "stroke": "#DB2777", "text": "#831843"},  # pink
    {"fill": "#CFFAFE", "stroke": "#0891B2", "text": "#164E63"},  # cyan
    {"fill": "#FEF3C7", "stroke": "#D97706", "text": "#78350F"},  # yellow
    {"fill": "#FEE2E2", "stroke": "#DC2626", "text": "#7F1D1D"},  # red
]

_DEFAULT_ROOT_STYLE = {
    "fill": "#1F2937",
    "stroke": "#111827",
    "text": "#FFFFFF",
}


class MindmapGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    NODE_WIDTH = 180
    NODE_HEIGHT = 60
    ROOT_WIDTH = 220
    ROOT_HEIGHT = 80
    LEVEL_GAP = 80  # horizontal spacing between depth columns
    LEAF_GAP = 30  # vertical spacing between leaf slots
    LEFT_MARGIN = 100
    TOP_MARGIN = 100
    NODE_STROKE_WIDTH = 1
    LINE_WIDTH = 3
    NODE_SHAPE = "terminator"
    ROOT_SHAPE = "terminator"

    PALETTE = _DEFAULT_PALETTE
    ROOT_STYLE = _DEFAULT_ROOT_STYLE

    def generate_document_content_json(
        self,
        *,
        tree: dict[str, Any],
        page_title: str = "Mindmap",
    ) -> dict[str, Any]:
        side_for = self._assign_sides(tree)
        palette_index_for = self._assign_palettes(tree)

        right_positions, right_count = self._layout_one_side(tree, side_for, "right")
        left_positions, left_count = self._layout_one_side(tree, side_for, "left")

        pixel_positions = self._compute_pixel_positions(
            root_id=tree["id"],
            right_positions=right_positions,
            left_positions=left_positions,
            right_count=right_count,
            left_count=left_count,
        )

        shapes: list[dict[str, Any]] = []
        lines: list[dict[str, Any]] = []
        self._emit(
            tree,
            pixel_positions=pixel_positions,
            side_for=side_for,
            palette_index_for=palette_index_for,
            shapes=shapes,
            lines=lines,
            edge_counter=[0],
        )

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

    def _assign_sides(self, tree: dict[str, Any]) -> dict[str, str]:
        """Greedy split of top-level branches: each branch goes to whichever side
        currently has fewer leaves."""
        side_for: dict[str, str] = {tree["id"]: "root"}
        right_leaves = 0
        left_leaves = 0
        for branch in tree.get("children", []):
            leaves = self._count_leaves(branch)
            if right_leaves <= left_leaves:
                side = "right"
                right_leaves += leaves
            else:
                side = "left"
                left_leaves += leaves
            self._propagate(branch, side, side_for)
        return side_for

    def _count_leaves(self, node: dict[str, Any]) -> int:
        children = node.get("children", [])
        if not children:
            return 1
        return sum(self._count_leaves(child) for child in children)

    def _propagate(self, node: dict[str, Any], value: Any, target: dict[str, Any]) -> None:
        target[node["id"]] = value
        for child in node.get("children", []):
            self._propagate(child, value, target)

    def _assign_palettes(self, tree: dict[str, Any]) -> dict[str, int | None]:
        palette_index_for: dict[str, int | None] = {tree["id"]: None}
        for index, branch in enumerate(tree.get("children", [])):
            self._propagate(branch, index % len(self.PALETTE), palette_index_for)
        return palette_index_for

    def _layout_one_side(
        self,
        tree: dict[str, Any],
        side_for: dict[str, str],
        target_side: str,
    ) -> tuple[dict[str, tuple[int, float]], int]:
        positions: dict[str, tuple[int, float]] = {}
        leaf_counter = [0]
        for branch in tree.get("children", []):
            if side_for[branch["id"]] == target_side:
                self._assign_positions(branch, depth=1, positions=positions, leaf_counter=leaf_counter)
        return positions, leaf_counter[0]

    def _assign_positions(
        self,
        node: dict[str, Any],
        depth: int,
        positions: dict[str, tuple[int, float]],
        leaf_counter: list[int],
    ) -> tuple[float, float]:
        children = node.get("children", [])
        if not children:
            slot = float(leaf_counter[0])
            leaf_counter[0] += 1
            positions[node["id"]] = (depth, slot)
            return slot, slot

        spans = [self._assign_positions(child, depth + 1, positions, leaf_counter) for child in children]
        min_y = min(span[0] for span in spans)
        max_y = max(span[1] for span in spans)
        positions[node["id"]] = (depth, (min_y + max_y) / 2)
        return min_y, max_y

    def _compute_pixel_positions(
        self,
        *,
        root_id: str,
        right_positions: dict[str, tuple[int, float]],
        left_positions: dict[str, tuple[int, float]],
        right_count: int,
        left_count: int,
    ) -> dict[str, tuple[float, float]]:
        x_step = self.NODE_WIDTH + self.LEVEL_GAP
        y_step = self.NODE_HEIGHT + self.LEAF_GAP

        left_max_depth = max((d for d, _ in left_positions.values()), default=0)

        root_x_center = self.LEFT_MARGIN + left_max_depth * x_step + self.NODE_WIDTH / 2
        max_count = max(right_count, left_count, 1)
        canvas_center_y = self.TOP_MARGIN + (max_count - 1) / 2 * y_step + self.NODE_HEIGHT / 2

        positions: dict[str, tuple[float, float]] = {
            root_id: (
                root_x_center - self.ROOT_WIDTH / 2,
                canvas_center_y - self.ROOT_HEIGHT / 2,
            ),
        }

        for side_positions, side_count, x_sign in (
            (right_positions, right_count, +1),
            (left_positions, left_count, -1),
        ):
            if side_count == 0:
                continue
            side_y_offset = canvas_center_y - (side_count - 1) / 2 * y_step
            for node_id, (depth, slot) in side_positions.items():
                x_center = root_x_center + x_sign * depth * x_step
                y_center = side_y_offset + slot * y_step
                positions[node_id] = (
                    x_center - self.NODE_WIDTH / 2,
                    y_center - self.NODE_HEIGHT / 2,
                )

        return positions

    def _emit(
        self,
        node: dict[str, Any],
        *,
        pixel_positions: dict[str, tuple[float, float]],
        side_for: dict[str, str],
        palette_index_for: dict[str, int | None],
        shapes: list[dict[str, Any]],
        lines: list[dict[str, Any]],
        edge_counter: list[int],
    ) -> None:
        palette_index = palette_index_for[node["id"]]
        is_root = palette_index is None

        style = self.ROOT_STYLE if is_root else self.PALETTE[palette_index]
        width = self.ROOT_WIDTH if is_root else self.NODE_WIDTH
        height = self.ROOT_HEIGHT if is_root else self.NODE_HEIGHT
        x, y = pixel_positions[node["id"]]

        shapes.append(
            {
                "id": node["id"],
                "type": self.ROOT_SHAPE if is_root else self.NODE_SHAPE,
                "boundingBox": {"x": x, "y": y, "w": width, "h": height},
                "text": node["label"],
                "style": {
                    "fill": {"type": "color", "color": style["fill"]},
                    "stroke": {
                        "color": style["stroke"],
                        "width": self.NODE_STROKE_WIDTH,
                        "style": "solid",
                    },
                    "textColor": style["text"],
                },
            }
        )

        for child in node.get("children", []):
            child_side = side_for[child["id"]]
            child_palette_index = palette_index_for[child["id"]]
            child_style = self.PALETTE[child_palette_index] if child_palette_index is not None else self.ROOT_STYLE
            if child_side == "right":
                source_pos = {"x": 1, "y": 0.5}
                target_pos = {"x": 0, "y": 0.5}
            else:
                source_pos = {"x": 0, "y": 0.5}
                target_pos = {"x": 1, "y": 0.5}

            lines.append(
                {
                    "id": f"edge-{edge_counter[0]}",
                    "lineType": "curved",
                    "endpoint1": {
                        "type": "shapeEndpoint",
                        "style": "none",
                        "shapeId": node["id"],
                        "position": source_pos,
                    },
                    "endpoint2": {
                        "type": "shapeEndpoint",
                        "style": "none",
                        "shapeId": child["id"],
                        "position": target_pos,
                    },
                    "stroke": {
                        "color": child_style["stroke"],
                        "width": self.LINE_WIDTH,
                        "style": "solid",
                    },
                }
            )
            edge_counter[0] += 1
            self._emit(
                child,
                pixel_positions=pixel_positions,
                side_for=side_for,
                palette_index_for=palette_index_for,
                shapes=shapes,
                lines=lines,
                edge_counter=edge_counter,
            )
