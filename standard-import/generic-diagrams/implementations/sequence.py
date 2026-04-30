"""
Sequence diagram implementation of CreateDocumentBase.

Produces a single-page Lucidchart document with the standard UML sequence
diagram layout: actors arrayed left-to-right at the top, each with a
dashed vertical lifeline; messages drawn as horizontal arrows between
lifelines, ordered top-to-bottom in input order.

Layout:
- Each actor gets a header rectangle in column `i`.
- A dashed vertical lifeline runs from the bottom of each header down past
  the last message.
- The k-th message is at y = (first message y) + k * MESSAGE_VERTICAL_GAP.
- A "call" message is a solid line ending in a filled arrow; a "return"
  message is a dashed line ending in an open arrow.

Input:

    generator.create_document(
        title="Login flow",
        actors=[
            {"id": "user",    "label": "User"},
            {"id": "browser", "label": "Browser"},
            {"id": "api",     "label": "Auth API"},
            {"id": "db",      "label": "Database"},
        ],
        messages=[
            {"from": "user",    "to": "browser", "label": "Click login"},
            {"from": "browser", "to": "api",     "label": "POST /login"},
            {"from": "api",     "to": "db",      "label": "Lookup user"},
            {"from": "db",      "to": "api",     "label": "User record",  "type": "return"},
            {"from": "api",     "to": "browser", "label": "JWT token",    "type": "return"},
            {"from": "browser", "to": "user",    "label": "Redirect home"},
        ],
    )

Each actor needs `id` and `label`. Each message needs `from` and `to`
(both actor ids); `label` and `type` are optional. `type` defaults to
`"call"`; `"return"` renders dashed with an open arrow.

v1 limitations:
- No activations, frames (alt/loop/par), or notes.
- Self-messages are drawn as a U-shaped loop using three line segments
  (out, down, back) since Standard Import lines don't expose waypoints.
"""

from typing import Any

from ..base import CreateDocumentBase


class SequenceGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"

    ACTOR_WIDTH = 160
    ACTOR_HEIGHT = 60
    COLUMN_GAP = 80
    MESSAGE_VERTICAL_GAP = 60
    HEADER_TO_FIRST_MESSAGE = 80
    BOTTOM_PADDING = 60
    LEFT_MARGIN = 80
    TOP_MARGIN = 80
    LINE_WIDTH = 2
    LIFELINE_COLOR = "#9CA3AF"
    LIFELINE_WIDTH = 1
    SELF_MESSAGE_STUB = 60
    SELF_MESSAGE_RETURN_OFFSET = 30

    def generate_document_content_json(
        self,
        *,
        actors: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        page_title: str = "Sequence",
    ) -> dict[str, Any]:
        self._validate(actors, messages)

        actor_index = {actor["id"]: i for i, actor in enumerate(actors)}
        column_step = self.ACTOR_WIDTH + self.COLUMN_GAP

        def actor_x_center(actor_id: str) -> float:
            return self.LEFT_MARGIN + actor_index[actor_id] * column_step + self.ACTOR_WIDTH / 2

        first_message_y = self.TOP_MARGIN + self.ACTOR_HEIGHT + self.HEADER_TO_FIRST_MESSAGE
        last_message_y = first_message_y + max(0, len(messages) - 1) * self.MESSAGE_VERTICAL_GAP
        lifeline_bottom_y = last_message_y + self.BOTTOM_PADDING

        shapes: list[dict[str, Any]] = []
        for i, actor in enumerate(actors):
            shapes.append(
                {
                    "id": actor["id"],
                    "type": "rectangle",
                    "boundingBox": {
                        "x": self.LEFT_MARGIN + i * column_step,
                        "y": self.TOP_MARGIN,
                        "w": self.ACTOR_WIDTH,
                        "h": self.ACTOR_HEIGHT,
                    },
                    "text": actor["label"],
                }
            )

        lines: list[dict[str, Any]] = []
        for actor in actors:
            x = actor_x_center(actor["id"])
            lines.append(
                {
                    "id": f"lifeline-{actor['id']}",
                    "lineType": "straight",
                    "endpoint1": {
                        "type": "positionEndpoint",
                        "style": "none",
                        "position": {"x": x, "y": self.TOP_MARGIN + self.ACTOR_HEIGHT},
                    },
                    "endpoint2": {
                        "type": "positionEndpoint",
                        "style": "none",
                        "position": {"x": x, "y": lifeline_bottom_y},
                    },
                    "stroke": {
                        "color": self.LIFELINE_COLOR,
                        "width": self.LIFELINE_WIDTH,
                        "style": "dashed",
                    },
                }
            )

        for i, message in enumerate(messages):
            y = first_message_y + i * self.MESSAGE_VERTICAL_GAP
            from_x = actor_x_center(message["from"])

            is_return = message.get("type") == "return"
            arrow_style = "openArrow" if is_return else "arrow"
            stroke_style = "dashed" if is_return else "solid"
            stroke = {
                "color": "#000000",
                "width": self.LINE_WIDTH,
                "style": stroke_style,
            }

            if message["from"] == message["to"]:
                lines.extend(self._build_self_message(message, i, from_x, y, arrow_style, stroke))
            else:
                to_x = actor_x_center(message["to"])
                line: dict[str, Any] = {
                    "id": f"message-{i}",
                    "lineType": "straight",
                    "endpoint1": {
                        "type": "positionEndpoint",
                        "style": "none",
                        "position": {"x": from_x, "y": y},
                    },
                    "endpoint2": {
                        "type": "positionEndpoint",
                        "style": arrow_style,
                        "position": {"x": to_x, "y": y},
                    },
                    "stroke": stroke,
                }
                if "label" in message:
                    line["text"] = [{"text": message["label"], "position": 0.5, "side": "top"}]
                lines.append(line)

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

    def _build_self_message(
        self,
        message: dict[str, Any],
        index: int,
        from_x: float,
        y: float,
        arrow_style: str,
        stroke: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Render a self-message as a U-shaped loop: a horizontal stub
        out from the lifeline, a short vertical drop, and a horizontal
        return back to the lifeline with the arrow head."""
        stub_x = from_x + self.SELF_MESSAGE_STUB
        return_y = y + self.SELF_MESSAGE_RETURN_OFFSET
        outbound: dict[str, Any] = {
            "id": f"message-{index}-out",
            "lineType": "straight",
            "endpoint1": {
                "type": "positionEndpoint",
                "style": "none",
                "position": {"x": from_x, "y": y},
            },
            "endpoint2": {
                "type": "positionEndpoint",
                "style": "none",
                "position": {"x": stub_x, "y": y},
            },
            "stroke": stroke,
        }
        if "label" in message:
            outbound["text"] = [{"text": message["label"], "position": 0.5, "side": "top"}]
        connector: dict[str, Any] = {
            "id": f"message-{index}-down",
            "lineType": "straight",
            "endpoint1": {
                "type": "positionEndpoint",
                "style": "none",
                "position": {"x": stub_x, "y": y},
            },
            "endpoint2": {
                "type": "positionEndpoint",
                "style": "none",
                "position": {"x": stub_x, "y": return_y},
            },
            "stroke": stroke,
        }
        inbound: dict[str, Any] = {
            "id": f"message-{index}-back",
            "lineType": "straight",
            "endpoint1": {
                "type": "positionEndpoint",
                "style": "none",
                "position": {"x": stub_x, "y": return_y},
            },
            "endpoint2": {
                "type": "positionEndpoint",
                "style": arrow_style,
                "position": {"x": from_x, "y": return_y},
            },
            "stroke": stroke,
        }
        return [outbound, connector, inbound]

    @staticmethod
    def _validate(actors: list[dict[str, Any]], messages: list[dict[str, Any]]) -> None:
        actor_ids = [actor["id"] for actor in actors]
        if len(set(actor_ids)) != len(actor_ids):
            raise ValueError("duplicate actor ids")
        valid = set(actor_ids)
        for message in messages:
            if message["from"] not in valid:
                raise ValueError(f"message references unknown actor: {message['from']}")
            if message["to"] not in valid:
                raise ValueError(f"message references unknown actor: {message['to']}")
