"""Validate control files and observing blocks with the schemas of numina"""
import pathlib
import sys

import yaml
from numina.schemas import SchemaValidationError, validate

status = 0
for name in sys.argv[1:]:
    path = pathlib.Path(name)
    kind = "control" if path.name == "control.yaml" else "oblock"
    try:
        docs = [doc for doc in yaml.safe_load_all(path.read_text()) if doc is not None]
        if kind == "oblock" and not all(isinstance(d, dict) and "instrument" in d for d in docs):
            continue  # not an observing block
        for idx, doc in enumerate(docs, start=1):
            validate(doc, kind, source=f"{name} (document {idx})")
    except (SchemaValidationError, yaml.YAMLError) as error:
        print(error)
        status = 1
sys.exit(status)
