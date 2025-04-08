annotation_schema = {
    "type": "object",
    "properties": {
        "id": {"type": ["string", "null"]},
        "product": {"type": ["string", "null"]},
        "gain": {"type": ["number", "null"]},
        "exposure": {"type": ["number", "null"]},
        "annotations": {"type": ["array", "null"]},
    },
    "required": [
        "id",
        "product",
        "gain",
        "exposure",
        "annotations",
    ],
}
