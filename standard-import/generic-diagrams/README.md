# Document creation examples

Example Python scripts that programmatically build Lucid documents via the
Lucid REST API's `POST /documents` endpoint. Each example takes a typed
description of a diagram (graph, tree, etc.), turns it into Lucid Standard
JSON, and POSTs it to create a real document in your account.

These examples are intended as starting points — copy a generator into your
own codebase and adapt it, or subclass `CreateDocumentBase` directly to
support a new diagram type.

## Layout

```
documentcreation/
├── base.py                  # CreateDocumentBase — auth, HTTP, request assembly
├── implementations/         # one file per diagram type
│   ├── erdiagram.py         # ERDiagramGenerator:        entities + relationships
│   ├── fishbone.py          # FishboneGenerator:         problem + categories of causes
│   ├── flowchart.py         # FlowchartGenerator:        nodes + edges
│   ├── gantt.py             # GanttChartGenerator:       dated tasks + dependencies
│   ├── mindmap.py           # MindmapGenerator:          recursive tree
│   ├── sequence.py          # SequenceGenerator:         actors + messages
│   ├── swimlane.py          # SwimlaneGenerator:         lanes + tasks + edges
│   └── umlclassdiagram.py   # UMLClassDiagramGenerator:  classes + relationships
└── examples/                # runnable example scripts, one per implementation
```

## Prerequisites

- Python 3.10+ (uses the `X | Y` union type syntax).
- A Lucid REST API key with permission to create documents. Pass it to the
  generator's constructor or set the `LUCID_API_KEY` environment variable.

## Quick start

```python
from documentcreation.implementations.flowchart import FlowchartGenerator

generator = FlowchartGenerator(api_key="your-key")
response = generator.create_document(
    title="Onboarding flow",
    nodes=[
        {"id": "start",  "label": "Start",        "shape": "terminator"},
        {"id": "verify", "label": "Verify email", "shape": "process"},
        {"id": "done",   "label": "Done",         "shape": "terminator"},
    ],
    edges=[
        {"from": "start",  "to": "verify"},
        {"from": "verify", "to": "done"},
    ],
)
print(response["editUrl"])
```

`create_document` returns the JSON body returned by the API, which includes
the new `documentId`, `editUrl`, and `viewUrl`.

A single generator instance is reusable; call `create_document` many times
to produce many documents from the same generator.

## Running the examples

The `examples/` directory has one runnable script per implementation, each
with a realistic input and a single `create_document` call. Set
`LUCID_API_KEY` and run any of them directly:

```bash
export LUCID_API_KEY=your-key
python3 documentcreation/examples/flowchart.py
python3 documentcreation/examples/erdiagram.py
python3 documentcreation/examples/sequence.py
# ...etc.
```

Each script prints the `editUrl` of the new document on success.

### Per-document metadata

Pass these to `create_document(...)` alongside the diagram-specific kwargs:

| Argument  | Type     | Purpose                                                       |
| --------- | -------- | ------------------------------------------------------------- |
| `title`   | `str`    | Document title (required, 1–300 chars).                       |
| `product` | `str`    | `"lucidchart"` or `"lucidspark"`. Defaults per generator.     |
| `parent`  | `dict`   | Parent folder reference (see Lucid REST API documentation).   |
| `team`    | `str`    | User-managed group ID to share the document with on creation. |

## Available implementations

### `FlowchartGenerator`

Turns a `nodes` list and an `edges` list into a flowchart. Layout is
delegated to Lucid's auto-layout engine via a `dataBackedShapes` entry of
type `assistedLayout`: shapes are emitted with placeholder positions and
repositioned server-side on import.

Per-call kwargs:

- `nodes` — list of `{"id", "label", "shape"}`. `shape` defaults to
  `"process"`; common values are `"process"`, `"decision"`, `"terminator"`,
  `"data"`, `"document"`.
- `edges` — list of `{"from", "to", "label"}`. `label` is optional.
- `page_title` — optional page tab title.

### `MindmapGenerator`

Turns a recursive tree dict into a radial (bidirectional) mindmap. Top-level
branches are split between left and right halves with a greedy leaf-count
balancer; each branch is assigned a palette color that is inherited by all
descendants and applied to both fills and the connecting lines.

Per-call kwargs:

- `tree` — `{"id", "label", "children": [...]}` recursively.
- `page_title` — optional page tab title.

### `ERDiagramGenerator`

Turns entities + relationships into an ER diagram. Each entity becomes a
`table` shape with a header row plus one row per attribute; relationships
are smart lines whose endpoint styles encode cardinality. Layout uses
Fruchterman-Reingold force-directed placement seeded deterministically,
then wrapped in an invisible `rectangleContainer` with `assistedLayout`
so Lucid refines the positions on import.

Per-call kwargs:

- `entities` — list of `{"id", "name", "attributes": [{"name", "type", "key"}, ...]}`.
  `key` is optional and rendered as a parenthesized suffix on the attribute name.
- `relationships` — list of `{"from", "to", "fromCardinality", "toCardinality", "label"}`.
  Cardinality accepts `one`, `many`, `zeroOrOne`, `zeroOrMore`, `oneOrMore`,
  `exactlyOne`, plus aliases (`1`, `n`, `*`, `0..1`, `1..*`, `0..*`).
- `page_title` — optional page tab title.

### `UMLClassDiagramGenerator`

Turns classes + relationships into a UML class diagram. Each class becomes
a `table` shape with a header row, an optional attributes section, and an
optional methods section. Relationships are smart lines whose endpoint
styles encode UML semantics (inheritance, realization, association,
aggregation, composition, dependency). Layout uses the same
Fruchterman-Reingold + assistedLayout-container approach as
`ERDiagramGenerator`.

Per-call kwargs:

- `classes` — list of `{"id", "name", "stereotype", "attributes", "methods"}`.
  `stereotype` is optional and renders as `«stereotype»` above the class name.
  Each attribute is `{"name", "type", "visibility"}`; each method is
  `{"name", "parameters", "returnType", "visibility", "abstract"}`.
  Visibility accepts the UML symbols (`+`, `-`, `#`, `~`) or the spelled-out
  aliases (`public`, `private`, `protected`, `package`).
- `relationships` — list of `{"from", "to", "type", "fromMultiplicity", "toMultiplicity", "label"}`.
  `type` defaults to `association`.
- `page_title` — optional page tab title.

### `SequenceGenerator`

Turns actors + messages into a UML sequence diagram. Actors are headers
across the top with dashed vertical lifelines; messages are drawn as
horizontal arrows between lifelines, ordered top-to-bottom in input order.
A `call` message is solid with a filled arrow; a `return` message is
dashed with an open arrow. Self-messages render as a U-shaped loop back
to the same lifeline.

Per-call kwargs:

- `actors` — list of `{"id", "label"}`.
- `messages` — list of `{"from", "to", "label", "type"}`. `type` defaults
  to `call`; `return` renders dashed with an open arrow.
- `page_title` — optional page tab title.

### `SwimlaneGenerator`

Turns lanes + tasks + edges into a vertical-lane swimlane diagram. Tasks
are placed in their lane and stacked top-to-bottom in dependency order
(longest-path topological rank within each lane). The container itself
is a `swimLanes` shape with `assistedLayout` so Lucid routes the lines
on import.

Per-call kwargs:

- `lanes` — list of `{"id", "title", "headerFill", "laneFill"}`. Fills are
  optional and accept any hex color.
- `tasks` — list of `{"id", "label", "lane", "shape"}`. `lane` references
  a lane id; `shape` defaults to `process`.
- `edges` — list of `{"from", "to", "label"}`. `label` is optional.
- `page_title` — optional page tab title.

### `GanttChartGenerator`

Turns a list of dated tasks into a Gantt chart. A label column on the
left names each task; bars on the right are placed proportionally to
their start/end dates against a shared time axis. Layout is fully
deterministic (no auto-layout) because the time axis is the diagram's
load-bearing visual.

Per-call kwargs:

- `tasks` — list of `{"id", "label", "start", "end", "dependsOn"}`. Dates
  are ISO date strings (`YYYY-MM-DD`). `dependsOn` is optional and
  validated for unknown ids; dependency arrows are not drawn (routing
  them across rows without crossing bars is ill-defined).
- `page_title` — optional page tab title.

### `FishboneGenerator`

Turns a single `problem` string and a list of `categories` into a
classic Ishikawa (cause-and-effect) fishbone: a horizontal arrow
points to the problem on the right, and diagonal ribs branch off the
spine alternating up and down, each labeled with a category and a
list of contributing causes. Layout is fully deterministic geometry
— no auto-layout — because the fishbone shape is the diagram's
purpose.

Per-call kwargs:

- `problem` — single string rendered in the head box on the right.
- `categories` — list of `{"label", "causes"}`. `causes` is a list of
  strings (may be empty). Categories alternate above and below the
  spine in input order.
- `page_title` — optional page tab title.

## Adding a new diagram type

Subclass `CreateDocumentBase` and implement `generate_document_content_json`.
The kwargs you accept on that method become the per-document kwargs callers
pass to `create_document`.

```python
from typing import Any
from ..base import CreateDocumentBase

class OrgChartGenerator(CreateDocumentBase):
    DEFAULT_PRODUCT = "lucidchart"  # or "lucidspark"

    def generate_document_content_json(
        self, *, employees: list[dict[str, Any]],
    ) -> dict[str, Any]:
        # Lay out employees, build the Standard Import dict, and return it.
        return {
            "version": 1,
            "pages": [{"id": "page1", "title": "Org chart", "shapes": [...], "lines": [...]}],
        }
```

The output of `generate_document_content_json` must be valid Lucid Standard
JSON; consult the public REST API documentation for the full schema
(supported shape types, line endpoint formats, page settings, etc.).

## Error handling

`create_document` raises `CreateDocumentError` (defined in `base.py`) when
the API returns a non-2xx response. The exception exposes:

- `error.status` — HTTP status code.
- `error.body` — raw response body (typically a JSON error envelope).

Wrap calls in a `try`/`except CreateDocumentError` to handle validation
failures, rate limiting, or auth errors as your script needs.
