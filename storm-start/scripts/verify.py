#!/usr/bin/env python3
"""Structural checks for an eventstorm.yaml. Structure only: the semantics are out of scope.

Usage:
    verify.py <eventstorm.yaml> [--close <big-picture|process|design>]
    verify.py --list

Without --close: always-on checks, plus the level gates of every level already marked `cerrado`.
With --close L: additionally runs the gates for L, i.e. "may this level be closed now?".
--list prints every check: when it runs, when it fails, and which session fixes it. This file is
the only list of checks; documents point here instead of copying it.

Exit codes: 0 = all checks pass, 1 = at least one check failed, or malformed YAML (an `error:`
message, no report), 2 = usage / IO / missing dependency.
Deterministic: same file in, same report out.
"""

import argparse
import re
import sys

import stormlib as sl

SUPPORTED = {
    "$schema", "$id", "$defs", "title", "description", "$ref", "type", "const", "enum",
    "required", "properties", "additionalProperties", "items", "minItems", "minLength",
    "pattern", "allOf", "if", "then", "else", "not",
}
TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "null": lambda v: v is None,
}


class SchemaError(Exception):
    pass


def _same(a, b):
    return type(a) is type(b) and a == b


def _resolve(ref, root):
    if not ref.startswith("#/"):
        raise SchemaError(f"only local $ref is supported, got {ref}")
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def validate(inst, schema, path, root, errors):
    """Subset of JSON Schema draft 2020-12. Unknown keywords abort instead of being ignored."""
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise SchemaError(f"unsupported schema keyword(s) {sorted(unknown)} at {path or '<root>'}")
    if "$ref" in schema:
        validate(inst, _resolve(schema["$ref"], root), path, root, errors)
    if "type" in schema and not TYPES[schema["type"]](inst):
        errors.append((path, f"must be {schema['type']}, got {type(inst).__name__}"))
        return
    if "const" in schema and not _same(inst, schema["const"]):
        errors.append((path, f"must be {schema['const']!r}, got {inst!r}"))
    if "enum" in schema and not any(_same(inst, e) for e in schema["enum"]):
        errors.append((path, f"must be one of {schema['enum']}, got {inst!r}"))
    if isinstance(inst, dict):
        for key in schema.get("required", []):
            if key not in inst:
                errors.append((path, f"missing required field '{key}'"))
        props = schema.get("properties", {})
        for key, val in inst.items():
            sub = f"{path}.{key}" if path else str(key)
            if key in props:
                validate(val, props[key], sub, root, errors)
            elif schema.get("additionalProperties") is False:
                errors.append((path, f"unknown field '{key}'"))
            elif isinstance(schema.get("additionalProperties"), dict):
                validate(val, schema["additionalProperties"], sub, root, errors)
    if isinstance(inst, list):
        if len(inst) < schema.get("minItems", 0):
            errors.append((path, f"needs at least {schema['minItems']} item(s)"))
        if "items" in schema:
            for i, val in enumerate(inst):
                validate(val, schema["items"], f"{path}[{i}]", root, errors)
    if isinstance(inst, str):
        if len(inst) < schema.get("minLength", 0):
            errors.append((path, "must not be empty"))
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            errors.append((path, f"{inst!r} does not match {schema['pattern']}"))
    for sub in schema.get("allOf", []):
        validate(inst, sub, path, root, errors)
    if "if" in schema:
        probe = []
        validate(inst, schema["if"], path, root, probe)
        branch = schema.get("then") if not probe else schema.get("else")
        if branch is not None:
            validate(inst, branch, path, root, errors)
    if "not" in schema:
        probe = []
        validate(inst, schema["not"], path, root, probe)
        if not probe:
            banned = schema["not"].get("required")
            msg = f"must not have {banned}" if banned else "matches a forbidden shape"
            errors.append((path, msg))



# ---------------------------------------------------------------- structural checks
# Each check returns a list of "problem" strings. Order here is the order of the report.

MANDATORY_BLOCKING = "conflicto-entre-voces"


def check_schema(doc, _ctx):
    schema = sl.load_json(sl.SCHEMA_PATH)
    errors = []
    validate(doc, schema, "", schema, errors)
    return [f"{_with_id(doc, p) or '<root>'}: {m}" for p, m in errors]


def _with_id(doc, path):
    """events[4].status -> events[4] (ev-prestamo-vencido).status, so the reader finds the element."""
    m = re.match(r"^([a-z_]+)\[(\d+)\]", path)
    if not m:
        return path
    items = doc.get(m.group(1))
    i = int(m.group(2))
    if isinstance(items, list) and i < len(items) and isinstance(items[i], dict) and items[i].get("id"):
        return f"{m.group(0)} ({items[i]['id']}){path[m.end():]}"
    return path


def _all_elements(doc):
    for sp in doc.get("speakers") or []:
        yield "speakers", sp
    for section in sl.SECTIONS:
        for el in doc.get(section) or []:
            yield section, el


def _items(doc, section):
    return [el for el in doc.get(section) or [] if isinstance(el, dict)]


def _section(ctx, ident):
    return ctx["index"].get(ident, (None,))[0] if isinstance(ident, str) else None


def _name(el):
    return f"{el.get('id')} '{sl.label_of(el)}'"


def _open_refs(doc):
    return {r for h in _items(doc, "hotspots") if h.get("resolution") == "abierto" for r in h.get("refs") or []}


def check_unique_ids(doc, _ctx):
    seen, out = {}, []
    for section, el in _all_elements(doc):
        if not isinstance(el, dict) or "id" not in el:
            continue
        ident = el["id"]
        owner = sl.section_of(ident)
        if owner and owner != section:
            out.append(f"{ident}: prefix says {owner}, but it lives in {section}")
        if ident in seen:
            out.append(f"{ident}: duplicated (in {seen[ident]} and {section})")
        seen.setdefault(ident, section)
    return out


def _refs_of(section, el):
    """Every (field, id) an element points to. Single place that knows which fields are references."""
    single = ["speaker", "actor", "then", "bounded_context", "resolved_by", "decision", "to_speaker",
              "failure_of", "raised_by", "supersedes"]
    multi = ["triggered_by", "results_in", "when", "built_from", "informs", "handles", "emits",
             "refs", "steps", "invariants", "speakers"]
    for key in single:
        if isinstance(el.get(key), str):
            yield key, el[key]
    for key in multi:
        for val in el.get(key) or []:
            if isinstance(val, str):
                yield key, val
    for nested in ("positions", "edge_cases", "exclusions", "validations"):
        for item in el.get(nested) or []:
            if isinstance(item, dict) and isinstance(item.get("speaker"), str):
                yield f"{nested}.speaker", item["speaker"]
    for key, said in [("alternatives_asked", el.get("alternatives_asked")), ("delay", el.get("delay"))] + [
            (f"none_said.{k}", v) for k, v in (el.get("none_said") or {}).items()]:
        if isinstance(said, dict) and isinstance(said.get("speaker"), str):
            yield f"{key}.speaker", said["speaker"]
    if isinstance(el.get("code_name"), dict) and isinstance(el["code_name"].get("decision"), str):
        yield "code_name.decision", el["code_name"]["decision"]
    for way, path in (el.get("failure_paths") or {}).items():
        if isinstance(path, str):
            yield f"failure_paths.{way}", path
        elif isinstance(path, dict) and isinstance(path.get("speaker"), str):
            yield f"failure_paths.{way}.speaker", path["speaker"]
    for field, hs in sl.unknowns(el):
        yield f"{field}.desconocido", hs


def check_refs(doc, ctx):
    idx, out = ctx["index"], []
    for section, el in _all_elements(doc):
        if not isinstance(el, dict):
            continue
        for field, ref in _refs_of(section, el):
            if ref not in idx:
                out.append(f"{el.get('id', section)}.{field} -> {ref}: no such id")
    for exc in (doc.get("domain") or {}).get("scope", {}).get("excludes") or []:
        if isinstance(exc, dict) and exc.get("speaker") not in idx:
            out.append(f"domain.scope.excludes '{exc.get('what')}' -> {exc.get('speaker')}: no such speaker")
    for slot, pq in ((doc.get("session") or {}).get("pending_questions") or {}).items():
        for key in ("about", "to_speaker"):
            if isinstance(pq, dict) and pq.get(key) and pq[key] not in idx:
                out.append(f"session.pending_questions.{slot}.{key} -> {pq[key]}: no such id")
    return out


def check_session(doc, _ctx):
    session, out = doc.get("session") or {}, []
    levels = session.get("levels") or {}
    cur = session.get("current_level")
    if cur in levels and (levels[cur] or {}).get("state") == "pendiente":
        out.append(f"current_level is {cur} but its state is 'pendiente'")
    defaults = [s.get("id") for s in doc.get("speakers") or [] if isinstance(s, dict) and s.get("default")]
    if len(defaults) > 1:
        out.append(f"more than one default speaker: {defaults}")
    return out


def _opposed(doc, ctx, h):
    """A case recorded in two referenced glossary entries with verdicts es and no-es."""
    verdicts = {}
    for ref in h.get("refs") or []:
        if _section(ctx, ref) != "glossary":
            continue
        for case in ctx["index"][ref][1].get("edge_cases") or []:
            if isinstance(case, dict) and case.get("verdict") in ("es", "no-es"):
                key = str(case.get("case", "")).strip().casefold()
                verdicts.setdefault(key, set()).add((ref, case["verdict"]))
    return sorted(k for k, v in verdicts.items() if {vd for _r, vd in v} == {"es", "no-es"})


def check_hotspot_rules(doc, ctx):
    """Severity and level are set by rule (socratic-protocol.md "Severity", "Hotspot level")."""
    session = doc.get("session") or {}
    cur = session.get("current_level")
    closed = {lv for lv, st in (session.get("levels") or {}).items() if isinstance(st, dict) and st.get("state") == "cerrado"}
    out = []
    for h in _items(doc, "hotspots"):
        if (h.get("resolution") == "abierto" and h.get("severity") == "bloqueante"
                and h.get("level") in closed and h.get("level") != cur):
            out.append(f"{h.get('id')}: open and bloqueante at level '{h.get('level')}', which is cerrado; "
                       f"a new hotspot takes the level in course ({cur})")
        kind, sev = h.get("type"), h.get("severity")
        mandatory = kind == MANDATORY_BLOCKING
        if kind == "frontera-candidata":
            if h.get("level") != "design":
                out.append(f"{h.get('id')}: frontera-candidata at level '{h.get('level')}'; design resolves it")
            cases = _opposed(doc, ctx, h)
            mandatory = bool(cases)
            reason = f"its cases got opposite verdicts ({'; '.join(cases)})"
        else:
            reason = "it is a conflicto-entre-voces"
        if mandatory and sev != "bloqueante":
            out.append(f"{h.get('id')}: marked {sev}, but {reason}: always bloqueante, no voice can lower it")
        if sev == "bloqueante" and not mandatory and not h.get("raised_by"):
            out.append(f"{h.get('id')}: bloqueante by no rule and no raised_by (which voice raised it?)")
    return out


def check_decisions(doc, ctx):
    out = []
    for d in _items(doc, "decisions"):
        if not d.get("alternatives_rejected") and not d.get("alternatives_asked"):
            out.append(f"{d.get('id')}: no alternatives_rejected and no alternatives_asked "
                       f"(record that alternatives were asked for)")
        sup = d.get("supersedes")
        if sup == d.get("id"):
            out.append(f"{d.get('id')}: supersedes itself")
        elif _section(ctx, sup) == "decisions" and ctx["index"][sup][1].get("level") != d.get("level"):
            out.append(f"{d.get('id')}: supersedes {sup}, a decision of another level")
    return out


def check_unknowns(doc, ctx):
    """Every "no sé" points to an open hotspot the process level (or earlier) can resolve."""
    out = []
    for _s, el in _all_elements(doc):
        if not isinstance(el, dict):
            continue
        for field, hs in sl.unknowns(el):
            if _section(ctx, hs) != "hotspots":
                out.append(f"{_name(el)}: {field} is desconocido, but {hs} is not a hotspot")
                continue
            h = ctx["index"][hs][1]
            if h.get("resolution") != "abierto":
                out.append(f"{_name(el)}: {field} -> {hs}, which is resolved; write the answer in place of the unknown")
            if field == "bounded_context":
                if h.get("type") != "frontera-candidata":
                    out.append(f"{_name(el)}: bounded_context -> {hs}, a {h.get('type')}; an undecided area points "
                               f"to the open frontera-candidata that has not decided it")
            elif h.get("level") == "design":
                out.append(f"{_name(el)}: {field} -> {hs} at level design; a process field needs a big-picture "
                           f"or process hotspot")
    return out


def check_triggers(doc, ctx):
    """triggered_by points to a command that lists the event, an external system, a time or an unknown."""
    out = []
    for ev in _items(doc, "events"):
        for trig in ev.get("triggered_by") or []:
            if not isinstance(trig, str):
                continue
            section = _section(ctx, trig)
            if section == "policies":
                then = ctx["index"][trig][1].get("then", "?")
                out.append(f"{_name(ev)}: triggered_by -> {trig} is a policy. A policy issues its command "
                           f"({then}); point triggered_by to the command that produces the event")
            elif section == "commands":
                if ev.get("id") not in (ctx["index"][trig][1].get("results_in") or []):
                    out.append(f"{_name(ev)}: triggered_by -> {trig}, but {trig}.results_in does not list it")
            elif section is not None and section != "external_systems":
                out.append(f"{_name(ev)}: triggered_by -> {trig} is in {section}, "
                           f"not a command, an external system or a time")
    return out


def check_policies(doc, ctx):
    out = []
    for pol in _items(doc, "policies"):
        if not pol.get("when") or not pol.get("then"):
            out.append(f"{_name(pol)}: not of the form 'cada vez que <evento>, entonces <comando>'")
            continue
        for ev in pol["when"]:
            if _section(ctx, ev) != "events":
                out.append(f"{_name(pol)}: when -> {ev} is not an event")
        if not sl.unknown(pol["then"]) and _section(ctx, pol["then"]) != "commands":
            out.append(f"{_name(pol)}: then -> {pol['then']} is not a command")
    return out


def check_commands(doc, ctx):
    out = []
    for cmd in _items(doc, "commands"):
        if not sl.unknown(cmd.get("actor")) and _section(ctx, cmd.get("actor")) != "actors":
            out.append(f"{_name(cmd)}: no actor")
        results = cmd.get("results_in") or []
        if not [r for r in results if _section(ctx, r) == "events"]:
            out.append(f"{_name(cmd)}: no resulting event")
        for way, path in (cmd.get("failure_paths") or {}).items():
            if isinstance(path, str) and path not in results:
                out.append(f"{_name(cmd)}: failure_paths.{way} -> {path} is not in its results_in")
            if isinstance(path, str) and _section(ctx, path) == "events" and ctx["index"][path][1].get("failure_mode"):
                out.append(f"{_name(cmd)}: failure_paths.{way} -> {path}, whose failure_mode is desconocido; "
                           f"keep one of the two")
        readers = [rm.get("id") for rm in _items(doc, "read_models") if cmd.get("id") in (rm.get("informs") or [])]
        if sl.unknown(cmd.get("informed_by")) and readers:
            out.append(f"{_name(cmd)}: informed_by is desconocido, but {', '.join(readers)} informs it")
    return out


def check_flows(doc, ctx):
    """failure_of links a camino de falla to its principal flow, and only that."""
    out = []
    for fl in _items(doc, "flows"):
        target = fl.get("failure_of")
        if not target:
            continue
        if fl.get("kind") != "falla":
            out.append(f"{_name(fl)}: has failure_of but kind is '{fl.get('kind')}', not 'falla'")
        if target == fl.get("id"):
            out.append(f"{_name(fl)}: failure_of points to itself")
        elif _section(ctx, target) == "flows" and ctx["index"][target][1].get("kind") != "principal":
            out.append(f"{_name(fl)}: failure_of -> {target}, which is not a principal flow")
    return out


def check_sources(doc, _ctx):
    """Material enters only as a registered source: every fuente provenance names a domain.sources path."""
    registered = {s.get("path") for s in (doc.get("domain") or {}).get("sources") or [] if isinstance(s, dict)}
    out = []
    for _s, el in _all_elements(doc):
        prov = el.get("provenance") if isinstance(el, dict) else None
        if isinstance(prov, dict) and prov.get("kind") == "fuente" and prov.get("source") not in registered:
            out.append(f"{el.get('id')}: provenance source '{prov.get('source')}' is not in domain.sources")
    return out


def check_glossary_terms(doc, _ctx):
    known = {str(t.get("term", "")).casefold() for t in _items(doc, "glossary")}
    out = []
    for _s, el in _all_elements(doc):
        if not isinstance(el, dict):
            continue
        for term in el.get("terms") or []:
            if isinstance(term, str) and term.casefold() not in known:
                out.append(f"{el.get('id')}: uses '{term}', which is not in the glossary")
    return out


def check_term_decisions(doc, ctx):
    """A plain yes confirms a term; a term someone chose between meanings for carries that decision."""
    out = []
    for h in _items(doc, "hotspots"):
        if h.get("type") not in ("frontera-candidata", MANDATORY_BLOCKING) or h.get("resolution") != "resuelto":
            continue
        for ref in h.get("refs") or []:
            if _section(ctx, ref) == "glossary" and not ctx["index"][ref][1].get("decision"):
                out.append(f"{ref}: its meaning was chosen in {h.get('id')} (resolved by "
                           f"{h.get('resolved_by')}), but the term has no decision")
    return out


def check_unified_verdicts(doc, ctx):
    """R1: a unification needs one verdict per separating case. A conflict is always resolved by one reading."""
    out = []
    for h in _items(doc, "hotspots"):
        kind = h.get("type")
        if kind not in ("frontera-candidata", MANDATORY_BLOCKING) or h.get("resolution") != "resuelto":
            continue
        dec = h.get("resolved_by")
        outcome = ctx["index"][dec][1].get("outcome") if _section(ctx, dec) == "decisions" else None
        if kind == "frontera-candidata" and not outcome:
            out.append(f"{h.get('id')}: resolved by {dec}, which has no outcome (unificar or separar)")
        if kind == MANDATORY_BLOCKING or outcome == "unificar":
            for case in _opposed(doc, ctx, h):
                out.append(f"{h.get('id')}: resolved by unifying ({dec}), but the case '{case}' still has "
                           f"opposite verdicts; ask it again to each voice")
    return out


def check_homonyms(doc, _ctx):
    """Same word, two contexts = candidate boundary. It must be visible as a frontera-candidata hotspot."""
    by_term = {}
    for t in _items(doc, "glossary"):
        by_term.setdefault(str(t.get("term", "")).casefold(), []).append(t)
    boundaries = [set(h.get("refs") or []) for h in _items(doc, "hotspots")
                  if h.get("type") == "frontera-candidata"]
    out = []
    for term, entries in sorted(by_term.items()):
        contexts = {e.get("context") for e in entries}
        if len(contexts) < 2:
            continue
        ids = {e.get("id") for e in entries}
        if not any(ids <= refs for refs in boundaries):
            out.append(
                f"'{term}' appears in {len(contexts)} contexts ({', '.join(sorted(map(str, contexts)))}) "
                f"with no frontera-candidata hotspot referencing {sorted(ids)}"
            )
    return out


def check_disputed(doc, _ctx):
    open_refs = _open_refs(doc)
    return [
        f"{el.get('id')}: status 'disputado' but no open hotspot references it"
        for _s, el in _all_elements(doc)
        if isinstance(el, dict) and el.get("status") == "disputado" and el.get("id") not in open_refs
    ]


def check_blocking_hotspots(doc, ctx):
    if not ctx["gates"]:
        return []
    top = max(sl.LEVELS.index(g) for g in ctx["gates"])
    out = []
    for h in _items(doc, "hotspots"):
        if h.get("level") not in sl.LEVELS:
            continue
        if (h.get("resolution") == "abierto" and h.get("severity") == "bloqueante"
                and sl.LEVELS.index(h["level"]) <= top):
            out.append(f"{h.get('id')} [{h['level']}] {h.get('type')}: {h.get('question')}")
    return out


def check_big_picture_close(doc, ctx):
    if "big-picture" not in ctx["gates"]:
        return []
    events, flows, open_refs = _items(doc, "events"), _items(doc, "flows"), _open_refs(doc)
    out = []
    if not any(ev.get("status") == "confirmado" for ev in events):
        out.append("no confirmed event")
    placed = set()
    for fl in flows:
        steps = fl.get("steps") or []
        placed.update(steps)
        if not [s for s in steps if _section(ctx, s) == "events"]:
            out.append(f"{_name(fl)}: no event in its steps")
        if fl.get("kind") == "falla" and not fl.get("failure_of"):
            out.append(f"{_name(fl)}: kind 'falla' without failure_of (which principal flow does it break?)")
    for ev in events:
        if ev.get("status") == "confirmado" and ev.get("id") not in placed | open_refs:
            out.append(f"{_name(ev)}: confirmed but in no flow and in no open hotspot")
    failed = {fl.get("failure_of") for fl in flows if fl.get("kind") == "falla"}
    for fl in flows:
        if fl.get("kind") != "principal" or not (fl.get("walked") or {}).get("big-picture"):
            continue
        said = fl.get("none_said") or {}
        pivots = [s for s in fl.get("steps") or []
                  if _section(ctx, s) == "events" and ctx["index"][s][1].get("pivotal")]
        if not pivots and "pivot" not in said:
            out.append(f"{_name(fl)}: walked, but no pivotal event and no none_said.pivot")
        if fl.get("id") not in failed | open_refs and "failure" not in said:
            out.append(f"{_name(fl)}: walked, but no camino de falla, no none_said.failure and no open hotspot")
    return out


def _current(doc, level):
    """Decisions of a level that no later decision supersedes."""
    superseded = {d.get("supersedes") for d in _items(doc, "decisions")}
    return [d for d in _items(doc, "decisions") if d.get("level") == level and d.get("id") not in superseded]


def chosen_flows(doc, ctx):
    """Flujo elegido = a flow in refs of a current (not superseded) `level: process` decision."""
    return sorted({r for d in _current(doc, "process") for r in d.get("refs") or [] if _section(ctx, r) == "flows"})


def _process_scope(doc, ctx):
    """Events, commands and policies of the flujos elegidos and of their caminos de falla."""
    chosen = set(chosen_flows(doc, ctx))
    flows = [fl for fl in _items(doc, "flows") if fl.get("id") in chosen or fl.get("failure_of") in chosen]
    steps = {s for fl in flows for s in fl.get("steps") or []}
    events = {s for s in steps if _section(ctx, s) == "events"}
    commands = [c for c in _items(doc, "commands")
                if c.get("id") in steps or events & set(c.get("results_in") or [])]
    policies = [p for p in _items(doc, "policies") if p.get("id") in steps or events & set(p.get("when") or [])]
    return events, commands, policies


def check_chosen_flows(doc, ctx):
    if "process" not in ctx["gates"]:
        return []
    chosen = chosen_flows(doc, ctx)
    out = [] if chosen else ["no flujo elegido: no current 'level: process' decision references a flow"]
    for fid in chosen:
        if not (ctx["index"][fid][1].get("walked") or {}).get("process"):
            out.append(f"{fid}: chosen for process but walked.process is not true")
    return out


def check_event_triggers(doc, ctx):
    if not ctx["gates"] & {"process", "design"}:
        return []
    events, _c, _p = _process_scope(doc, ctx)
    return [f"{_name(ev)}: in a flujo elegido, no trigger (command, external system, time or desconocido)"
            for ev in _items(doc, "events") if ev.get("id") in events and not ev.get("triggered_by")]


def check_process_close(doc, ctx):
    if "process" not in ctx["gates"]:
        return []
    _e, commands, policies = _process_scope(doc, ctx)
    out = []
    for cmd in commands:
        missing = [w for w in ("rechazo", "error", "demora") if w not in (cmd.get("failure_paths") or {})]
        if missing:
            out.append(f"{_name(cmd)}: failure_paths without {', '.join(missing)}")
    for pol in policies:
        if not pol.get("mode"):
            out.append(f"{_name(pol)}: no mode (automática, manual or desconocido)")
    return out


def check_design_close(doc, ctx):
    if "design" not in ctx["gates"]:
        return []
    out = [f"{_name(agg)}: no invariant" for agg in _items(doc, "aggregates") if not agg.get("invariants")]
    handled = {c for agg in _items(doc, "aggregates") for c in agg.get("handles") or []}
    design_refs = {r for h in _items(doc, "hotspots") if h.get("resolution") == "abierto"
                   and h.get("level") == "design" for r in h.get("refs") or []}
    for cmd in _items(doc, "commands"):
        if (cmd.get("status") != "hipótesis-sin-autor" and cmd.get("id") not in handled
                and cmd.get("id") not in design_refs):
            out.append(f"{_name(cmd)}: no aggregate handles it and no open design hotspot references it")
    if not _items(doc, "bounded_contexts"):
        out.append("no bounded context: every domain has at least one")
    return out


# (name, function, when it runs, fails when, session that fixes it). "gated" = runs only for levels
# already `cerrado` plus the --close level. "flujo elegido scope" = the flows of the current
# `level: process` decisions plus their caminos de falla.
CHECKS = [
    ("schema", check_schema, "always",
     "the YAML breaks the schema; later checks are skipped", "the session that wrote the element"),
    ("unique-ids", check_unique_ids, "always",
     "an id repeats, or its prefix does not match its section", "the session that wrote the element"),
    ("refs", check_refs, "always",
     "an id field points to nothing", "the session that wrote the element"),
    ("session", check_session, "always",
     "current_level is pendiente, or several default voices", "/storm-start"),
    ("hotspot-rules", check_hotspot_rules, "always",
     "a conflicto-entre-voces, or a frontera-candidata whose cases got opposite verdicts, is not "
     "bloqueante; a frontera-candidata is not at level design; a bloqueante by no rule has no raised_by; "
     "an open bloqueante sits at a cerrado level other than current_level",
     "the session that wrote the hotspot"),
    ("decisions", check_decisions, "always",
     "a decision has neither alternatives_rejected nor alternatives_asked; supersedes points to itself "
     "or to another level", "the session that wrote the decision"),
    ("unknowns", check_unknowns, "always",
     "a desconocido points to no hotspot or to a resolved one; a process field points to a design "
     "hotspot; an aggregate's bounded_context points to anything but a frontera-candidata",
     "the session that wrote the element"),
    ("triggers", check_triggers, "always",
     "triggered_by points to a policy or to anything but a command that lists the event, "
     "an external system, a time or a desconocido", "/storm-process"),
    ("policies", check_policies, "always",
     "a policy is not when events -> then command", "/storm-process"),
    ("commands", check_commands, "always",
     "a command lacks an actor or a resulting event; a failure event is not in results_in, or has "
     "failure_mode desconocido; informed_by is desconocido while a read model informs it",
     "/storm-process"),
    ("flows", check_flows, "always",
     "failure_of sits on a principal flow, points to itself or to another failure flow",
     "/storm-big-picture"),
    ("sources", check_sources, "always",
     "a fuente provenance names material not registered in domain.sources",
     "the session that read the material"),
    ("glossary-terms", check_glossary_terms, "always",
     "a terms entry is not a glossary term", "the session that used the term"),
    ("term-decisions", check_term_decisions, "always",
     "a term referenced by a resolved frontera-candidata or conflicto-entre-voces has no decision",
     "the session that resolved the hotspot"),
    ("unified-verdicts", check_unified_verdicts, "always",
     "a resolved frontera-candidata's decision has no outcome; a frontera resolved by unificar, or a "
     "resolved conflicto-entre-voces, keeps a separating case with opposite verdicts",
     "the session that resolved the hotspot"),
    ("homonym-boundary", check_homonyms, "always",
     "one term in two contexts without a frontera-candidata hotspot", "/storm-big-picture"),
    ("disputed-has-hotspot", check_disputed, "always",
     "a disputado element has no open hotspot", "the session that marked it"),
    ("blocking-hotspots", check_blocking_hotspots, "gated",
     "a bloqueante hotspot is open at or below the gated level", "/storm-<the hotspot's level>"),
    ("big-picture-close", check_big_picture_close, "gated, big-picture",
     "no confirmed event; a flow without events; a confirmed event in no flow and no open hotspot; a "
     "falla flow without failure_of; a walked principal flow without a pivot or none_said.pivot, or "
     "without a camino de falla, none_said.failure or an open hotspot", "/storm-big-picture"),
    ("chosen-flows", check_chosen_flows, "gated, process",
     "no flujo elegido (no current level: process decision references a flow); a flujo elegido "
     "without walked.process", "/storm-process"),
    ("event-triggers", check_event_triggers, "gated, process+",
     "an event in the flujo elegido scope has no triggered_by", "/storm-process"),
    ("process-close", check_process_close, "gated, process",
     "a command in the flujo elegido scope without its three failure_paths; a policy there without mode",
     "/storm-process"),
    ("design-close", check_design_close, "gated, design",
     "an aggregate without invariants; a command no aggregate handles and no open design hotspot "
     "references; no bounded context", "/storm-design"),
]


def list_checks():
    print("check | runs | fails when | fixed in")
    for name, _fn, runs, fails, fixed in CHECKS:
        print(f"{name} | {runs} | {fails} | {fixed}")
    return sl.EXIT_OK


def main():
    ap = argparse.ArgumentParser(description="Structural checks for eventstorm.yaml")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--close", choices=sl.LEVELS, help="also gate this level: may it be closed now?")
    ap.add_argument("--list", action="store_true", help="print every check and the session that fixes it")
    args = ap.parse_args()
    if args.list:
        return list_checks()
    if not args.file:
        ap.error("the file argument is required (or use --list)")

    doc = sl.load_yaml(args.file)
    levels = (doc.get("session") or {}).get("levels") or {}
    gates = {lv for lv in sl.LEVELS if isinstance(levels.get(lv), dict) and levels[lv].get("state") == "cerrado"}
    if args.close:
        gates.add(args.close)
    ctx = {"index": sl.index(doc), "gates": gates}

    cur = (doc.get("session") or {}).get("current_level", "?")
    print(f"verify: {args.file} (schema {doc.get('schema_version', '?')}, current level: {cur})")
    print(f"gated levels: {', '.join(lv for lv in sl.LEVELS if lv in gates) or 'none'}")
    failed = 0
    problems = 0
    for name, fn, _runs, _fails, fixed in CHECKS:
        try:
            found = fn(doc, ctx)
        except SchemaError as exc:
            print(f"error: schema file is outside the supported subset: {exc}", file=sys.stderr)
            return sl.EXIT_USAGE
        if found:
            failed += 1
            problems += len(found)
            print(f"  FAIL {name}  (fixed in: {fixed})")
            for line in found:
                print(f"       - {line}")
        else:
            print(f"  PASS {name}")
        if name == "schema" and found:
            print("  (remaining checks skipped: fix the schema errors first)")
            break
    if failed:
        print(f"RESULT: FAIL — {failed} check(s), {problems} problem(s)")
        return sl.EXIT_FAIL
    print("RESULT: PASS")
    return sl.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
