"""
Swimlane implementation of CreateDocumentBase.

Produces a single-page Lucidchart document built around a `swimLanes`
container. Lanes run vertically (one per column); tasks are placed inside
their lane and connected by lines.

Layout pipeline:
1. Rank tasks via longest-path topological depth on the dependency graph
   (Kahn's algorithm). A task with no incoming edges is rank 0.
2. Within each lane, sort tasks by rank (ties broken by input order) and
   place them compactly at rows 0, 1, 2, ... — each lane reads top-to-
   bottom as a tidy linear sequence. Lanes do not align horizontally
   with each other; the diagram width is driven by the lane count, the
   height by the busiest lane.
3. Connect edges with elbow lines: same-lane edges enter/exit
   top/bottom; cross-lane edges enter/exit left/right so handoffs read
   as horizontal arrows between lanes.

Input is three lists:

    generator.create_document(
        title="Order fulfillment",
        lanes=[
            {"id": "sales",   "title": "Sales"},
            {"id": "ops",     "title": "Operations", "headerFill": "#...", "laneFill": "#..."},
            {"id": "finance", "title": "Finance"},
        ],
        tasks=[
            {"id": "received",  "label": "Order received",  "lane": "sales",   "shape": "terminator"},
            {"id": "validate",  "label": "Validate order",  "lane": "sales",   "shape": "process"},
            {"id": "fulfill",   "label": "Fulfill",         "lane": "ops",     "shape": "process"},
            {"id": "invoice",   "label": "Send invoice",    "lane": "finance", "shape": "process"},
        ],
        edges=[
            {"from": "received", "to": "validate"},
            {"from": "validate", "to": "fulfill"},
            {"from": "fulfill",  "to": "invoice"},
        ],
    )

Each lane needs `id` and `title`; `headerFill` and `laneFill` are
optional. Each task needs `id`, `label`, and `lane` (a lane id); `shape`
defaults to `process`. Each edge needs `from` and `to` (both task ids);
`label` is optional.
"""

from collections import deque
from typing import Any

from ..base import CreateDocumentBase

_DEFAULT_HEADER_FILL = "#635DFF"
_DEFAULT_LANE_FILL = "#F2F3F5"


class SwimlaneGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    LANE_WIDTH = 280
    TASK_WIDTH = 200
    TASK_HEIGHT = 60
    TASK_VERTICAL_GAP = 40
    TITLE_BAR_HEIGHT = 50
    LANE_TOP_PADDING = 100
    LANE_BOTTOM_PADDING = 80
    LEFT_MARGIN = 80
    TOP_MARGIN = 80
    LINE_WIDTH = 2
    SWIMLANES_ID = "swimlanes"

    def generate_document_content_json(
        self,
        *,
        lanes: list[dict[str, Any]],
        tasks: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        page_title: str = "Swimlane",
    ) -> dict[str, Any]:
        self._validate(lanes, tasks, edges)

        task_by_id = {task["id"]: task for task in tasks}
        lane_index = {lane["id"]: i for i, lane in enumerate(lanes)}

        rank_for = self._assign_ranks(tasks, edges)
        row_for = self._assign_rows(lanes, tasks, rank_for)
        max_row = max(row_for.values(), default=0) if row_for else 0

        container_w = self.LANE_WIDTH * len(lanes)
        rows_height = (max_row + 1) * self.TASK_HEIGHT + max_row * self.TASK_VERTICAL_GAP if tasks else 0
        container_h = self.TITLE_BAR_HEIGHT + self.LANE_TOP_PADDING + rows_height + self.LANE_BOTTOM_PADDING

        shapes: list[dict[str, Any]] = [self._build_swimlanes_shape(lanes, container_w, container_h)]
        shapes.extend(self._build_task_shape(t, lane_index, row_for) for t in tasks)

        lines = [self._build_line(edge, index, task_by_id, lane_index, row_for) for index, edge in enumerate(edges)]

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
    def _validate(
        lanes: list[dict[str, Any]],
        tasks: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> None:
        lane_ids = [lane["id"] for lane in lanes]
        if len(set(lane_ids)) != len(lane_ids):
            raise ValueError("duplicate lane ids")
        task_ids = [task["id"] for task in tasks]
        if len(set(task_ids)) != len(task_ids):
            raise ValueError("duplicate task ids")
        valid_lanes = set(lane_ids)
        valid_tasks = set(task_ids)
        for task in tasks:
            if task["lane"] not in valid_lanes:
                raise ValueError(f"task {task['id']} references unknown lane: {task['lane']}")
        for edge in edges:
            if edge["from"] not in valid_tasks:
                raise ValueError(f"edge references unknown task: {edge['from']}")
            if edge["to"] not in valid_tasks:
                raise ValueError(f"edge references unknown task: {edge['to']}")

    @staticmethod
    def _assign_ranks(tasks: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
        task_ids = [task["id"] for task in tasks]
        out_edges: dict[str, list[str]] = {tid: [] for tid in task_ids}
        in_degree: dict[str, int] = dict.fromkeys(task_ids, 0)
        for edge in edges:
            if edge["from"] == edge["to"]:
                continue
            out_edges[edge["from"]].append(edge["to"])
            in_degree[edge["to"]] += 1

        rank: dict[str, int] = {tid: 0 for tid in task_ids if in_degree[tid] == 0}
        queue = deque(rank.keys())
        while queue:
            node = queue.popleft()
            for downstream in out_edges[node]:
                rank[downstream] = max(rank.get(downstream, 0), rank[node] + 1)
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    queue.append(downstream)
        for tid in task_ids:
            rank.setdefault(tid, 0)
        return rank

    @staticmethod
    def _assign_rows(
        lanes: list[dict[str, Any]],
        tasks: list[dict[str, Any]],
        rank_for: dict[str, int],
    ) -> dict[str, int]:
        tasks_by_lane: dict[str, list[dict[str, Any]]] = {lane["id"]: [] for lane in lanes}
        input_order = {task["id"]: i for i, task in enumerate(tasks)}
        for task in tasks:
            tasks_by_lane[task["lane"]].append(task)

        row_for: dict[str, int] = {}
        for lane_tasks in tasks_by_lane.values():
            ordered = sorted(
                lane_tasks,
                key=lambda t: (rank_for[t["id"]], input_order[t["id"]]),
            )
            for row, task in enumerate(ordered):
                row_for[task["id"]] = row
        return row_for

    def _build_swimlanes_shape(self, lanes: list[dict[str, Any]], width: float, height: float) -> dict[str, Any]:
        return {
            "id": self.SWIMLANES_ID,
            "type": "swimLanes",
            "boundingBox": {
                "x": self.LEFT_MARGIN,
                "y": self.TOP_MARGIN,
                "w": width,
                "h": height,
            },
            "vertical": True,
            "assistedLayout": True,
            "titleBar": {
                "height": self.TITLE_BAR_HEIGHT,
                "verticalText": False,
            },
            "lanes": [
                {
                    "title": lane["title"],
                    "width": self.LANE_WIDTH,
                    "headerFill": lane.get("headerFill", _DEFAULT_HEADER_FILL),
                    "laneFill": lane.get("laneFill", _DEFAULT_LANE_FILL),
                }
                for lane in lanes
            ],
        }

    def _build_task_shape(
        self,
        task: dict[str, Any],
        lane_index: dict[str, int],
        row_for: dict[str, int],
    ) -> dict[str, Any]:
        col = lane_index[task["lane"]]
        row = row_for[task["id"]]
        x = self.LEFT_MARGIN + col * self.LANE_WIDTH + (self.LANE_WIDTH - self.TASK_WIDTH) / 2
        y = (
            self.TOP_MARGIN
            + self.TITLE_BAR_HEIGHT
            + self.LANE_TOP_PADDING
            + row * (self.TASK_HEIGHT + self.TASK_VERTICAL_GAP)
        )
        return {
            "id": task["id"],
            "type": task.get("shape", "process"),
            "boundingBox": {
                "x": x,
                "y": y,
                "w": self.TASK_WIDTH,
                "h": self.TASK_HEIGHT,
            },
            "text": task["label"],
        }

    def _build_line(
        self,
        edge: dict[str, Any],
        index: int,
        task_by_id: dict[str, dict[str, Any]],
        lane_index: dict[str, int],
        row_for: dict[str, int],
    ) -> dict[str, Any]:
        from_task = task_by_id[edge["from"]]
        to_task = task_by_id[edge["to"]]
        from_row = row_for[from_task["id"]]
        to_row = row_for[to_task["id"]]
        from_col = lane_index[from_task["lane"]]
        to_col = lane_index[to_task["lane"]]

        if from_col == to_col:
            if from_row <= to_row:
                from_pos, to_pos = {"x": 0.5, "y": 1}, {"x": 0.5, "y": 0}
            else:
                from_pos, to_pos = {"x": 0.5, "y": 0}, {"x": 0.5, "y": 1}
        elif from_col < to_col:
            from_pos, to_pos = {"x": 1, "y": 0.5}, {"x": 0, "y": 0.5}
        else:
            from_pos, to_pos = {"x": 0, "y": 0.5}, {"x": 1, "y": 0.5}

        line: dict[str, Any] = {
            "id": f"edge-{index}",
            "lineType": "elbow",
            "endpoint1": {
                "type": "shapeEndpoint",
                "style": "none",
                "shapeId": from_task["id"],
                "position": from_pos,
            },
            "endpoint2": {
                "type": "shapeEndpoint",
                "style": "arrow",
                "shapeId": to_task["id"],
                "position": to_pos,
            },
            "stroke": {
                "color": "#000000",
                "width": self.LINE_WIDTH,
                "style": "solid",
            },
        }
        if "label" in edge:
            line["text"] = [{"text": edge["label"], "position": 0.5, "side": "middle"}]
        return line
