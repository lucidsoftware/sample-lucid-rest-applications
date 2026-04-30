"""
Gantt chart implementation of CreateDocumentBase.

Produces a single-page Lucidchart document laid out as a Gantt chart:
each task is a horizontal bar in its own row, positioned by start and
end date against a shared time axis. A label column on the left shows
the task name; bars on the right are placed proportionally to their
date range.

Layout is fully deterministic — no auto-layout — because the visual
meaning of the diagram is the time axis itself; letting the renderer
move things would break it.

Input:

    tasks = [
        {"id": "research", "label": "Research",
         "start": "2026-01-01", "end": "2026-01-15"},
        {"id": "design",   "label": "Design",
         "start": "2026-01-16", "end": "2026-02-01",
         "dependsOn": ["research"]},
        {"id": "build",    "label": "Build",
         "start": "2026-02-02", "end": "2026-03-15",
         "dependsOn": ["design"]},
    ]

Each task needs `id`, `label`, `start`, and `end`. Dates are ISO date
strings (`YYYY-MM-DD`). `dependsOn` is an optional list of task ids
that must precede this task; the graph is validated for unknown ids
but no dependency arrows are drawn — routing them cleanly across rows
without crossing bars requires a CSP solver, and the Gantt's primary
visual is the time axis itself, so keeping the bars uncluttered is
worth more than the arrows. Wire the field through if your downstream
tooling needs it.

Tasks render in input order, top to bottom. Sort the input list ahead
of time if you want a different ordering (e.g. by start date).
"""

from datetime import date
from typing import Any

from ..base import CreateDocumentBase


class GanttChartGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    LABEL_COLUMN_WIDTH = 220
    PIXELS_PER_DAY = 12
    ROW_HEIGHT = 44
    ROW_GAP = 6
    HEADER_HEIGHT = 50
    LEFT_MARGIN = 80
    TOP_MARGIN = 80
    BAR_FILL = "#3B82F6"
    BAR_STROKE = "#1D4ED8"
    BAR_TEXT = "#FFFFFF"
    HEADER_FILL = "#E5E7EB"
    LABEL_FILL = "#F3F4F6"

    def generate_document_content_json(
        self,
        *,
        tasks: list[dict[str, Any]],
        page_title: str = "Gantt Chart",
    ) -> dict[str, Any]:
        self._validate(tasks)
        if not tasks:
            return self._empty_page(page_title)

        parsed = [self._parse_task(task) for task in tasks]
        min_start = min(task["start_date"] for task in parsed)
        max_end = max(task["end_date"] for task in parsed)
        total_days = (max_end - min_start).days + 1

        timeline_x = self.LEFT_MARGIN + self.LABEL_COLUMN_WIDTH
        timeline_w = total_days * self.PIXELS_PER_DAY

        shapes = self._build_header(timeline_x, timeline_w, min_start, max_end)
        shapes.extend(self._build_rows(parsed, min_start, timeline_x))

        return {
            "version": 1,
            "pages": [
                {
                    "id": "page1",
                    "title": page_title,
                    "shapes": shapes,
                    "lines": [],
                }
            ],
        }

    def _empty_page(self, page_title: str) -> dict[str, Any]:
        return {
            "version": 1,
            "pages": [{"id": "page1", "title": page_title, "shapes": [], "lines": []}],
        }

    @staticmethod
    def _validate(tasks: list[dict[str, Any]]) -> None:
        ids = [task["id"] for task in tasks]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate task ids")
        valid = set(ids)
        for task in tasks:
            for dep in task.get("dependsOn", []):
                if dep not in valid:
                    raise ValueError(f"task {task['id']} depends on unknown task: {dep}")
            start = date.fromisoformat(task["start"])
            end = date.fromisoformat(task["end"])
            if end < start:
                raise ValueError(f"task {task['id']} has end before start")

    @staticmethod
    def _parse_task(task: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": task["id"],
            "label": task["label"],
            "start_date": date.fromisoformat(task["start"]),
            "end_date": date.fromisoformat(task["end"]),
            "dependsOn": list(task.get("dependsOn", [])),
        }

    def _build_header(
        self,
        timeline_x: float,
        timeline_w: float,
        min_start: date,
        max_end: date,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "_label_header",
                "type": "rectangle",
                "boundingBox": {
                    "x": self.LEFT_MARGIN,
                    "y": self.TOP_MARGIN,
                    "w": self.LABEL_COLUMN_WIDTH,
                    "h": self.HEADER_HEIGHT,
                },
                "text": "Task",
                "style": {"fill": {"type": "color", "color": self.HEADER_FILL}},
            },
            {
                "id": "_timeline_header",
                "type": "rectangle",
                "boundingBox": {
                    "x": timeline_x,
                    "y": self.TOP_MARGIN,
                    "w": timeline_w,
                    "h": self.HEADER_HEIGHT,
                },
                "text": f"{min_start.isoformat()}    →    {max_end.isoformat()}",
                "style": {"fill": {"type": "color", "color": self.HEADER_FILL}},
            },
        ]

    def _build_rows(
        self,
        parsed: list[dict[str, Any]],
        min_start: date,
        timeline_x: float,
    ) -> list[dict[str, Any]]:
        shapes: list[dict[str, Any]] = []
        for index, task in enumerate(parsed):
            row_y = self.TOP_MARGIN + self.HEADER_HEIGHT + index * (self.ROW_HEIGHT + self.ROW_GAP)
            shapes.append(
                {
                    "id": f"label-{task['id']}",
                    "type": "rectangle",
                    "boundingBox": {
                        "x": self.LEFT_MARGIN,
                        "y": row_y,
                        "w": self.LABEL_COLUMN_WIDTH,
                        "h": self.ROW_HEIGHT,
                    },
                    "text": task["label"],
                    "style": {"fill": {"type": "color", "color": self.LABEL_FILL}},
                }
            )

            offset_days = (task["start_date"] - min_start).days
            duration_days = (task["end_date"] - task["start_date"]).days + 1
            bar_x = timeline_x + offset_days * self.PIXELS_PER_DAY
            bar_w = duration_days * self.PIXELS_PER_DAY
            shapes.append(
                {
                    "id": task["id"],
                    "type": "rectangle",
                    "boundingBox": {
                        "x": bar_x,
                        "y": row_y,
                        "w": bar_w,
                        "h": self.ROW_HEIGHT,
                    },
                    "text": task["label"],
                    "style": {
                        "fill": {"type": "color", "color": self.BAR_FILL},
                        "stroke": {"color": self.BAR_STROKE, "width": 1, "style": "solid"},
                        "textColor": self.BAR_TEXT,
                    },
                }
            )
        return shapes
