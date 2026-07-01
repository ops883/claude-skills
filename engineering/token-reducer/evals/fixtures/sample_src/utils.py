"""General-purpose utility helpers (eval distractor file)."""
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2))


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def flatten(nested):
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result
