"""Shared helpers for render.py and verify.py. Python 3 stdlib + PyYAML only."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
SCHEMA_PATH = os.path.join(ASSETS, "eventstorm.schema.json")
PALETTE_PATH = os.path.join(ASSETS, "palette.json")

LEVELS = ["big-picture", "process", "design"]

# id prefix -> section of eventstorm.yaml that owns it
PREFIX_SECTION = {
    "ev": "events",
    "cmd": "commands",
    "act": "actors",
    "pol": "policies",
    "rm": "read_models",
    "ext": "external_systems",
    "agg": "aggregates",
    "hs": "hotspots",
    "op": "opportunities",
    "bc": "bounded_contexts",
    "fl": "flows",
    "gl": "glossary",
    "inv": "invariants",
    "dec": "decisions",
    "oq": "open_questions",
    "sp": "speakers",
}
SECTIONS = [s for s in PREFIX_SECTION.values() if s != "speakers"]

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 1, 2


def die(msg, code=EXIT_USAGE):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _yaml():
    try:
        import yaml  # noqa: WPS433
    except ImportError:
        die(
            "PyYAML is not installed. Install it with `python3 -m pip install pyyaml` "
            "(the only dependency outside the standard library)."
        )
    return yaml


def load_yaml(path):
    """Load YAML with dates kept as strings, so the output never depends on the parser's types."""
    yaml = _yaml()

    class Loader(yaml.SafeLoader):
        pass

    Loader.yaml_implicit_resolvers = {
        ch: [(tag, rx) for tag, rx in rs if tag != "tag:yaml.org,2002:timestamp"]
        for ch, rs in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    if not os.path.isfile(path):
        die(f"file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        try:
            data = yaml.load(fh, Loader=Loader)  # noqa: S506 - SafeLoader subclass
        except yaml.YAMLError as exc:
            die(f"{path} is not valid YAML: {exc}", EXIT_FAIL)
    if not isinstance(data, dict):
        die(f"{path}: top level must be a mapping", EXIT_FAIL)
    return data


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def section_of(ident):
    if not isinstance(ident, str) or "-" not in ident:
        return None
    return PREFIX_SECTION.get(ident.split("-", 1)[0])


def index(doc):
    """id -> (section, element). Duplicates are reported by verify.py, first one wins here."""
    idx = {}
    for sp in doc.get("speakers") or []:
        if isinstance(sp, dict) and "id" in sp:
            idx.setdefault(sp["id"], ("speakers", sp))
    for section in SECTIONS:
        for el in doc.get(section) or []:
            if isinstance(el, dict) and "id" in el:
                idx.setdefault(el["id"], (section, el))
    return idx


def unknown(value):
    """{desconocido: hs-id} -> hs-id; anything else -> None."""
    return value.get("desconocido") if isinstance(value, dict) else None


def unknowns(el):
    """Every (field, hs-id) where an element records a "no sé". Single place that knows where it may appear."""
    keys = ("actor", "informed_by", "then", "mode", "failure_mode", "bounded_context")
    out = [(key, unknown(el.get(key))) for key in keys if unknown(el.get(key))]
    out += [(f"triggered_by[{i}]", unknown(t)) for i, t in enumerate(el.get("triggered_by") or []) if unknown(t)]
    out += [(f"failure_paths.{way}", unknown(p)) for way, p in (el.get("failure_paths") or {}).items() if unknown(p)]
    return out


def label_of(el):
    for key in ("name", "term", "statement", "question"):
        if isinstance(el, dict) and el.get(key):
            return str(el[key])
    return "?"
