#!/usr/bin/env python3
"""Render eventstorm.yaml into a self-contained eventstorm.html (light and dark mode).

Usage:
    render.py <eventstorm.yaml> [-o <out.html>]

Default output: eventstorm.html next to the YAML. Sticky colors and board marks come ONLY from
assets/palette.json. Flows are grouped by lane, each failure flow under the principal it breaks.
Deterministic: no clock, no randomness; the only date shown is session.updated from the YAML.
Does not validate: run verify.py for that. Unknown ids are drawn as broken references, not hidden.
Exit codes: 0 = written, 1 = malformed YAML (an `error:` message, no report), 2 = usage / IO / missing dependency.
"""

import argparse
import html
import os
import sys

import stormlib as sl

STICKY_SECTIONS = [
    "actors", "commands", "aggregates", "events", "policies", "read_models",
    "external_systems", "hotspots", "opportunities",
]
LEVEL_LABEL = {"big-picture": "Big Picture", "process": "Process", "design": "Design"}
STATE_LABEL = {"pendiente": "pendiente", "abierto": "en curso", "cerrado": "cerrado"}
SLOT_LABEL = {"start": "inicio", **LEVEL_LABEL}
FIELD_LABEL = {"actor": "quién da la orden", "informed_by": "qué mira para decidir", "then": "qué orden sigue",
               "mode": "si es automática o manual", "triggered_by": "qué lo dispara",
               "failure_paths.rechazo": "si se rechaza", "failure_paths.error": "si falla",
               "failure_paths.demora": "si llega tarde", "failure_mode": "de qué forma sale mal",
               "bounded_context": "a qué área pertenece"}


def esc(value):
    return html.escape(str(value), quote=True)


def css(palette):
    ink = palette["ink"]
    rules = []
    for section, spec in palette["kinds"].items():
        border = f"border-color:{spec['border']};border-style:solid;" if spec.get("border") else ""
        rules.append(
            f".k-{section}{{background:{spec['fill']};color:{spec.get('ink', ink)};"
            f"--sticky-ink:{spec.get('ink', ink)};{border}}}"
        )
        if spec.get("size") == "small":
            rules.append(f".k-{section}{{width:7.5rem;min-height:4.5rem;font-size:.82rem}}")
    for status, spec in palette["status"].items():
        style = spec.get("border_style", "none")
        if style != "none":
            rules.append(f'.s-{status}{{border:3px {style} var(--sticky-ink)}}')
    marks = palette["marks"]
    rules.append(f".sticky.pivot{{border-left:9px solid {marks['pivotal']['color']}}}")
    rules.append(f".failure{{border-left:4px solid {marks['failure']['color']};margin:10px 0 0 28px;padding-left:12px}}")
    rules.append(f".failure>h4{{color:{marks['failure']['color']}}}")
    return "\n".join(rules)


BASE_CSS = """
:root{--bg:#f6f4ef;--fg:#1f1d1a;--muted:#6b665d;--card:#ffffff;--line:#d9d4c9;--accent:#e8246f;--lane:#ece8df}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15161a;--fg:#e9e6df;--muted:#a09a8f;--card:#202127;--line:#34363e;--accent:#ff5c9a;--lane:#1c1d22}}
:root[data-theme="dark"]{--bg:#15161a;--fg:#e9e6df;--muted:#a09a8f;--card:#202127;--line:#34363e;--accent:#ff5c9a;--lane:#1c1d22}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.7rem;margin:0 0 4px}
h2{font-size:1.2rem;margin:40px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:1rem;margin:20px 0 8px}
.muted{color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.chip{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:.85rem;background:var(--card)}
.chip.cerrado{border-color:#3aa76d}.chip.abierto{border-color:var(--accent)}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.card ul{margin:6px 0 0;padding-left:18px}
.lane{list-style:none;display:flex;gap:26px;overflow-x:auto;padding:14px 12px 18px;margin:0;background:var(--lane);border-radius:10px}
.lane>li{position:relative;flex:0 0 auto}
.lane>li+li::before{content:"\\2192";position:absolute;left:-20px;top:40%;color:var(--muted)}
.board{display:flex;flex-wrap:wrap;gap:12px}
.sticky{width:10.5rem;min-height:6.5rem;padding:8px 10px;border-radius:3px;box-shadow:0 1px 3px rgba(0,0,0,.25);display:flex;flex-direction:column;gap:3px;position:relative}
.sticky .kind{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;opacity:.8}
.sticky .name{font-weight:600;line-height:1.25}
.sticky .meta{font-size:.72rem;opacity:.85;margin-top:auto}
.sticky .id{font-family:ui-monospace,Menlo,monospace;font-size:.66rem;opacity:.7}
.badge{display:inline-block;font-size:.66rem;padding:0 6px;border-radius:999px;background:rgba(0,0,0,.12)}
.badge.unknown{background:var(--accent);color:#fff}
.heat{position:absolute;top:-8px;right:-8px;background:var(--accent);color:#fff;border-radius:999px;min-width:22px;height:22px;font-size:.75rem;display:flex;align-items:center;justify-content:center;font-weight:700;box-shadow:0 0 0 2px var(--bg)}
.broken{background:transparent;border:2px dashed var(--accent);color:var(--fg)}
.hot{border-left:6px solid var(--accent)}
.hot.nb{border-left-color:var(--muted)}
.voices{margin:8px 0 0;padding-left:0;list-style:none}
.voices li{padding:4px 8px;border-left:3px solid var(--line);margin-top:4px}
.decision{background:#ffffff;color:#1d1b16;border:2px solid #1d1b16}
.decision .muted{color:#5a554c}
table{border-collapse:collapse;width:100%;font-size:.9rem}
.table-wrap{overflow-x:auto}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font-weight:600;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:10px}
.legend .sticky{width:9rem;min-height:4.5rem}
h4{font-size:.92rem;margin:12px 0 6px}
.flow{margin-bottom:18px}
details summary{cursor:pointer;color:var(--muted)}
"""


class Renderer:
    def __init__(self, doc, palette):
        self.doc = doc
        self.pal = palette
        self.idx = sl.index(doc)
        self.speakers = {s.get("id"): s for s in doc.get("speakers") or [] if isinstance(s, dict)}
        self.heat = {}
        for h in doc.get("hotspots") or []:
            if isinstance(h, dict) and h.get("resolution") == "abierto":
                for ref in h.get("refs") or []:
                    self.heat[ref] = self.heat.get(ref, 0) + 1

    # ------------------------------------------------------------------ helpers
    def items(self, section):
        return [e for e in self.doc.get(section) or [] if isinstance(e, dict)]

    def who(self, sp_id):
        sp = self.speakers.get(sp_id)
        return esc(sp.get("name", sp_id)) if sp else esc(sp_id or "sin autor")

    def ref_label(self, ident):
        hit = self.idx.get(ident)
        if not hit:
            return f'<span class="badge">{esc(ident)} ?</span>'
        return f"{esc(sl.label_of(hit[1]))} <span class=\"id\">{esc(ident)}</span>"

    def sticky(self, ident):
        hit = self.idx.get(ident)
        if not hit:
            return (f'<div class="sticky broken"><span class="kind">referencia rota</span>'
                    f'<span class="name">{esc(ident)}</span></div>')
        section, el = hit
        spec = self.pal["kinds"].get(section, {})
        status = el.get("status", "")
        badge = "" if status == "confirmado" else f'<span class="badge">{esc(self.pal["status"].get(status, {}).get("label", status))}</span>'
        heat = self.heat.get(ident, 0)
        heat_html = f'<span class="heat" title="puntos calientes abiertos">{heat}</span>' if heat else ""
        author = self.who(el["speaker"]) if el.get("speaker") else ""
        if sl.unknowns(el):
            badge += ' <span class="badge unknown">? no se sabe</span>'
        kind = esc(spec.get("label", section))
        delay = el.get("delay") if section == "policies" else None
        if isinstance(delay, dict) and delay.get("words"):
            badge += f' <span class="badge">plazo: {esc(delay["words"])}</span>'
        pivot = ""
        if section == "events" and el.get("pivotal"):
            pivot = " pivot"
            kind += f' · {esc(self.pal["marks"]["pivotal"]["label"].lower())}'
        elif section == "policies" and el.get("mode"):
            kind += " · modo desconocido" if isinstance(el["mode"], dict) else f" · {esc(el['mode'])}"
        elif section == "events" and el.get("failure"):
            kind += f' · {esc(self.pal["marks"]["failure"]["label"].lower())}'
        elif section == "actors" and el.get("kind") and el["kind"] != "persona":
            kind += f" · {esc(el['kind'])}"
        return (
            f'<div class="sticky k-{section} s-{esc(status)}{pivot}" title="{esc(sl.label_of(el))}">{heat_html}'
            f'<span class="kind">{kind}</span>'
            f'<span class="name">{esc(sl.label_of(el))}</span>'
            f'<span class="meta">{badge} {author}</span>'
            f'<span class="id">{esc(ident)}</span></div>'
        )

    def invariant_items(self, ids):
        return "".join(
            f"<li>{esc(self.idx[i][1].get('statement'))} <span class=\"id\">{esc(i)}</span></li>"
            if self.idx.get(i, (None,))[0] == "invariants" else f"<li>{self.ref_label(i)}</li>"
            for i in ids or []
        )

    # ------------------------------------------------------------------ sections
    def header(self):
        d = self.doc.get("domain") or {}
        s = self.doc.get("session") or {}
        scope = d.get("scope") or {}
        levels = s.get("levels") or {}
        chips = "".join(
            f'<span class="chip {esc((levels.get(lv) or {}).get("state", ""))}">{LEVEL_LABEL[lv]}: '
            f'{esc(STATE_LABEL.get((levels.get(lv) or {}).get("state", ""), "?"))}</span>'
            for lv in sl.LEVELS
        )
        voices = "".join(
            f'<span class="chip">{esc(sp.get("name"))}{" · " + esc(sp["role"]) if sp.get("role") else ""}</span>'
            for sp in self.speakers.values()
        )
        inc = "".join(f"<li>{esc(x)}</li>" for x in scope.get("includes") or [])
        exc = "".join(
            f"<li>{esc(x.get('what'))} <span class=\"muted\">— {esc(x.get('why'))} ({self.who(x.get('speaker'))})</span></li>"
            for x in scope.get("excludes") or [] if isinstance(x, dict)
        )
        slots = s.get("pending_questions") or {}
        pend = "".join(
            f'<div class="card hot"><strong>Pregunta pendiente · {esc(SLOT_LABEL.get(slot, slot))}</strong><br>'
            f'{esc(pq.get("text"))}'
            f'{" <span class=muted>→ " + self.who(pq.get("to_speaker")) + "</span>" if pq.get("to_speaker") else ""}</div>'
            for slot in SLOT_LABEL if isinstance(pq := slots.get(slot), dict) and pq.get("text")
        )
        return (
            f"<header><h1>{esc(d.get('name', 'Event Storming'))}</h1>"
            f"<div class=\"muted\">Nivel actual: {esc(LEVEL_LABEL.get(s.get('current_level'), '?'))}"
            f" · actualizado {esc(s.get('updated', '?'))} · esquema {esc(self.doc.get('schema_version', '?'))}</div>"
            f"<div class=\"chips\">{chips}</div><div class=\"chips\">{voices}</div>"
            f"<div class=\"cols\"><div class=\"card\"><strong>Qué entra</strong><ul>{inc}</ul></div>"
            f"<div class=\"card\"><strong>Qué queda fuera</strong><ul>{exc or '<li class=muted>nada registrado</li>'}</ul></div></div>"
            f"{pend}</header>"
        )

    def hotspot_card(self, h):
        nb = "" if h.get("severity") == "bloqueante" else " nb"
        refs = ", ".join(self.ref_label(r) for r in h.get("refs") or [])
        voices = "".join(
            f"<li><strong>{self.who(p.get('speaker'))}:</strong> {esc(p.get('says'))}</li>"
            for p in h.get("positions") or [] if isinstance(p, dict)
        )
        resolved = (f"<div class=\"muted\">Resuelto por {self.ref_label(h['resolved_by'])}</div>"
                    if h.get("resolved_by") else "")
        if h.get("raised_by"):
            resolved += f"<div class=\"muted\">Bloquea porque lo pidió {self.who(h['raised_by'])}</div>"
        status = h.get("status", "")
        hyp = (f' <span class="badge">{esc(self.pal["status"][status]["label"])}</span>'
               if status == "hipótesis-sin-autor" else "")
        return (
            f'<div class="card hot{nb}"><div class="muted">{esc(h.get("type"))} · {esc(h.get("severity"))}'
            f' · {esc(LEVEL_LABEL.get(h.get("level"), h.get("level")))} · <span class="id">{esc(h.get("id"))}</span></div>'
            f'<strong>{esc(h.get("question"))}</strong>{hyp}'
            f'{"<ul class=voices>" + voices + "</ul>" if voices else ""}'
            f'{"<div class=muted>Sobre: " + refs + "</div>" if refs else ""}{resolved}</div>'
        )

    def hotspots(self):
        hs = self.items("hotspots")
        order = {"bloqueante": 0, "no-bloqueante": 1}
        open_ = sorted(
            (h for h in hs if h.get("resolution") == "abierto"),
            key=lambda h: (order.get(h.get("severity"), 2), sl.LEVELS.index(h["level"]) if h.get("level") in sl.LEVELS else 9),
        )
        done = [h for h in hs if h.get("resolution") != "abierto"]
        body = "".join(self.hotspot_card(h) for h in open_) or '<p class="muted">Ninguno abierto.</p>'
        closed = (f"<details><summary>{len(done)} resuelto(s)</summary><div class=\"cols\">"
                  f"{''.join(self.hotspot_card(h) for h in done)}</div></details>" if done else "")
        return f'<section><h2>Puntos calientes abiertos</h2><div class="cols">{body}</div>{closed}</section>'

    def flow_block(self, fl, heading, failures=""):
        status = fl.get("status", "")
        tag = "" if status == "confirmado" else f' <span class="badge">{esc(self.pal["status"].get(status, {}).get("label", status))}</span>'
        if fl.get("kind") == "falla":  # the kind marks a camino de falla; its name is the voice's, unprefixed
            tag = f' <span class="badge">{esc(self.pal["marks"]["failure"]["label"])}</span>' + tag
        walked = [LEVEL_LABEL[lv] for lv in ("big-picture", "process") if (fl.get("walked") or {}).get(lv)]
        walked_html = f' <span class="badge">recorrido: {esc(" · ".join(walked))}</span>' if walked else ""
        steps = "".join(f"<li>{self.sticky(step)}</li>" for step in fl.get("steps") or [])
        said = fl.get("none_said") or {}
        none = "".join(
            f'<div class="muted">{label}: “{esc(said[key].get("words"))}” ({self.who(said[key].get("speaker"))})</div>'
            for key, label in (("pivot", "Sin evento pivote"), ("failure", "Sin camino de falla"))
            if isinstance(said.get(key), dict)
        )
        return (f'<div class="flow"><{heading}>{esc(fl.get("name"))}{tag}{walked_html} '
                f'<span class="id muted">{esc(fl.get("id"))}</span></{heading}>'
                f'<ol class="lane">{steps}</ol>{none}{failures}</div>')

    def flows(self):
        flows = self.items("flows")
        principal = {fl["id"] for fl in flows if fl.get("kind") == "principal" and fl.get("id")}
        failures_of = {}
        for fl in flows:
            if fl.get("kind") == "falla" and fl.get("failure_of") in principal:
                failures_of.setdefault(fl["failure_of"], []).append(fl)
        attached = {fl.get("id") for group in failures_of.values() for fl in group}
        by_lane = {}
        for fl in flows:
            if fl.get("id") in attached:
                continue
            by_lane.setdefault(fl.get("lane") or "", []).append(fl)
        out = []
        for lane in sorted(by_lane, key=lambda k: (k == "", list(by_lane).index(k))):
            blocks = []
            for fl in by_lane[lane]:
                fails = "".join(
                    f'<div class="failure">{self.flow_block(f, "h4")}</div>' for f in failures_of.get(fl.get("id"), [])
                )
                if fl.get("kind") == "falla":
                    blocks.append(f'<div class="failure"><h4>Sin flujo principal</h4>'
                                  f'{self.flow_block(fl, "h4")}</div>')
                else:
                    blocks.append(self.flow_block(fl, "h3", fails))
            title = f"Carril: {esc(lane)}" if lane else "Sin carril"
            out.append(f'<h3 class="muted">{title}</h3>{"".join(blocks)}')
        return f'<section><h2>Flujos</h2>{"".join(out) or "<p class=muted>Todavía no hay flujos.</p>"}</section>'

    def loose(self):
        in_flow = {s for fl in self.items("flows") for s in fl.get("steps") or []}
        blocks = []
        for section in STICKY_SECTIONS:
            if section == "hotspots":
                continue
            rest = [e["id"] for e in self.items(section) if e.get("id") and e["id"] not in in_flow]
            if rest:
                label = self.pal["kinds"].get(section, {}).get("label", section)
                blocks.append(f"<h3>{esc(label)}</h3><div class=\"board\">{''.join(self.sticky(i) for i in rest)}</div>")
        return f"<section><h2>Fuera de los flujos</h2>{''.join(blocks)}</section>" if blocks else ""

    def unknown_rows(self):
        """One row per hotspot, with every element whose "no sé" it holds: several may share one."""
        covered = {}
        for section in STICKY_SECTIONS:
            for el in self.items(section):
                for field, hs in sl.unknowns(el):
                    covered.setdefault(hs, []).append(
                        f"<li>{self.ref_label(el.get('id'))} · {esc(FIELD_LABEL.get(field.split('[')[0], field))}</li>")
        for h in self.items("hotspots"):
            if h.get("type") == "desconocido" and h.get("resolution") == "abierto" and h.get("id") not in covered:
                covered[h["id"]] = [f"<li>{self.ref_label(r)}</li>" for r in h.get("refs") or []]
        order = [h.get("id") for h in self.items("hotspots")]
        rows = [
            f"<tr><td>{self.ref_label(hs)}</td><td><ul>{''.join(items)}</ul></td></tr>"
            for hs, items in sorted(covered.items(), key=lambda kv: (order.index(kv[0]) if kv[0] in order else len(order), kv[0]))
        ]
        if not rows:
            return ""
        head = "<tr><th>Punto caliente</th><th>Qué no se sabe, y dónde</th></tr>"
        return (f'<section><h2>Lo que no se sabe</h2><div class="table-wrap"><table>{head}{"".join(rows)}'
                f'</table></div></section>')

    def contexts(self):
        bcs, aggs = self.items("bounded_contexts"), self.items("aggregates")
        if not bcs and not aggs:
            return ""
        cards = []
        undecided = [a for a in aggs if not isinstance(a.get("bounded_context"), str)]
        for bc in bcs + [{"id": None, "name": "Área sin decidir"}]:
            mine = [a for a in aggs if a.get("bounded_context") == bc.get("id")] if bc.get("id") else undecided
            if bc.get("id") is None and not mine:
                continue
            agg_html = "".join(
                f"<div style=\"margin-top:10px\">{self.sticky(a['id'])}<ul>"
                + self.invariant_items(a.get("invariants"))
                + "</ul>"
                + (f"<div class=\"muted\">Área: no se sabe → {self.ref_label(sl.unknown(a['bounded_context']))}</div>"
                   if sl.unknown(a.get("bounded_context")) else "")
                + "</div>"
                for a in mine
            )
            status = bc.get("status")
            tag = f' <span class="badge">{esc(status)}</span>' if status and status != "confirmado" else ""
            cards.append(f'<div class="card"><strong>{esc(bc.get("name"))}</strong>{tag}'
                         f'<div class="muted">{esc(bc.get("purpose", ""))}</div>{agg_html}</div>')
        return f'<section><h2>Contextos y agregados</h2><div class="cols">{"".join(cards)}</div></section>'

    def glossary(self):
        rows = []
        for t in self.items("glossary"):
            cases = "".join(
                f"<li><strong>{esc(c.get('verdict'))}</strong>: {esc(c.get('case'))}"
                f"{' — ' + esc(c['why']) if c.get('why') else ''}</li>"
                for c in t.get("edge_cases") or [] if isinstance(c, dict)
            )
            invs = self.invariant_items(t.get("invariants"))
            invs += "".join(
                f"<li>validación: {esc(v.get('words'))} <span class=\"muted\">({self.who(v.get('speaker'))})</span></li>"
                for v in t.get("validations") or [] if isinstance(v, dict)
            )
            excl = "".join(f"<li>{esc(x.get('what'))}</li>" for x in t.get("exclusions") or [] if isinstance(x, dict))
            meta = t.get("metaphor") or {}
            code = t.get("code_name") or {}
            status = t.get("status", "")
            decision = self.ref_label(t["decision"]) if t.get("decision") else ""
            rows.append(
                f"<tr><td><strong>{esc(t.get('term'))}</strong><br><span class=\"id\">{esc(t.get('id'))}</span>"
                f"<br><span class=\"badge\">{esc(status)}</span></td>"
                f"<td>{esc(t.get('context'))}{'<br>' + self.ref_label(t['bounded_context']) if t.get('bounded_context') else ''}</td>"
                f"<td>{esc(t.get('in_their_words', ''))}{'<ul>' + invs + '</ul>' if invs else ''}</td>"
                f"<td>{'<ul>' + cases + '</ul>' if cases else ''}</td>"
                f"<td>{esc(meta.get('kind', ''))}{': ' + esc(meta['text']) if meta.get('text') else ''}</td>"
                f"<td>{'<ul>' + excl + '</ul>' if excl else ''}</td>"
                f"<td>{decision}{'<br>código: <code>' + esc(code.get('value')) + '</code>' if code.get('value') else ''}</td></tr>"
            )
        if not rows:
            return ""
        head = "<tr><th>Término</th><th>Contexto</th><th>En sus palabras · invariantes</th><th>Casos límite</th><th>Metáfora</th><th>Deja fuera</th><th>Decisión</th></tr>"
        return f'<section><h2>Glosario</h2><div class="table-wrap"><table>{head}{"".join(rows)}</table></div></section>'

    def invariants(self):
        users = {}
        for section in ("glossary", "aggregates"):
            for el in self.items(section):
                for inv in el.get("invariants") or []:
                    users.setdefault(inv, []).append(el["id"])
        rows = []
        for inv in self.items("invariants"):
            status = inv.get("status", "")
            used = ", ".join(self.ref_label(u) for u in users.get(inv.get("id"), []))
            rows.append(
                f"<tr><td>{esc(inv.get('statement'))}<br><span class=\"id\">{esc(inv.get('id'))}</span></td>"
                f"<td><span class=\"badge\">{esc(self.pal['status'].get(status, {}).get('label', status))}</span></td>"
                f"<td>{self.who(inv.get('speaker')) if inv.get('speaker') else 'sin autor'}</td>"
                f"<td>{used or '<span class=muted>nadie la usa todavía</span>'}</td></tr>"
            )
        if not rows:
            return ""
        head = "<tr><th>Regla</th><th>Estado</th><th>Dijo</th><th>La usan</th></tr>"
        return f'<section><h2>Invariantes</h2><div class="table-wrap"><table>{head}{"".join(rows)}</table></div></section>'

    def decisions(self):
        cards = []
        replaced = {d.get("supersedes"): d.get("id") for d in self.items("decisions") if d.get("supersedes")}
        for d in self.items("decisions"):
            alts = "".join(
                f"<li>{esc(a.get('option'))} <span class=\"muted\">— {esc(a.get('why_not'))}</span></li>"
                for a in d.get("alternatives_rejected") or [] if isinstance(a, dict)
            )
            if alts:
                alts = f"<div>Descartado:</div><ul>{alts}</ul>"
            else:
                asked = d.get("alternatives_asked") or {}
                alts = ('<div><span class="badge unknown">sin alternativas consideradas</span></div>'
                        + (f'<div class="muted">Se preguntó: “{esc(asked.get("words"))}” ({self.who(asked.get("speaker"))})</div>'
                           if asked else ""))
            links = ""
            if d.get("supersedes"):
                links += f'<div class="muted">Reemplaza a {self.ref_label(d["supersedes"])}</div>'
            if d.get("id") in replaced:
                links += f'<div class="muted">Reemplazada por {self.ref_label(replaced[d["id"]])}</div>'
            authors = ", ".join(self.who(sp) for sp in d.get("speakers") or [])
            cards.append(
                f'<div class="card decision"><div class="muted">{esc(LEVEL_LABEL.get(d.get("level"), ""))}'
                f' · {esc(d.get("decided_on", ""))} · <span class="id">{esc(d.get("id"))}</span></div>'
                f'<strong>{esc(d.get("statement"))}</strong><div>Decidió: {authors or "sin autor"}</div>'
                f'<div class="muted">Por qué: {esc(d.get("why"))}</div>{alts}{links}</div>'
            )
        return f'<section><h2>Decisiones</h2><div class="cols">{"".join(cards)}</div></section>' if cards else ""

    def open_questions(self):
        items = "".join(
            f"<li>{esc(q.get('question'))} <span class=\"muted\">({esc(LEVEL_LABEL.get(q.get('level'), ''))}"
            f"{' → ' + self.who(q['to_speaker']) if q.get('to_speaker') else ''}"
            f"{' → ' + esc(q['target']) if q.get('target') else ''})</span></li>"
            for q in self.items("open_questions")
        )
        return f"<section><h2>Preguntas abiertas</h2><ul>{items}</ul></section>" if items else ""

    def legend(self):
        kinds = "".join(
            f'<div class="sticky k-{s}"><span class="name">{esc(k["label"])}</span>'
            f'<span class="meta">{esc(k["meaning"])}</span></div>'
            for s, k in self.pal["kinds"].items()
        )
        stats = "".join(
            f'<div class="sticky k-events s-{s}"><span class="name">{esc(k["label"])}</span>'
            f'<span class="meta">{esc(k["meaning"])}</span></div>'
            for s, k in self.pal["status"].items()
        )
        marks = self.pal["marks"]
        mark_html = (
            f'<div class="sticky k-events pivot"><span class="name">{esc(marks["pivotal"]["label"])}</span>'
            f'<span class="meta">{esc(marks["pivotal"]["meaning"])}</span></div>'
            f'<div class="failure"><h4>{esc(marks["failure"]["label"])}</h4>'
            f'<span class="muted">{esc(marks["failure"]["meaning"])}</span></div>'
        )
        return (f'<section><h2>Leyenda</h2><div class="legend">{kinds}</div><h3>Estado</h3>'
                f'<div class="legend">{stats}</div><h3>Marcas</h3><div class="legend">{mark_html}</div></section>')

    def page(self):
        title = esc((self.doc.get("domain") or {}).get("name", "Event Storming"))
        body = "".join([self.header(), self.hotspots(), self.unknown_rows(), self.flows(), self.loose(), self.contexts(),
                        self.invariants(), self.glossary(), self.decisions(), self.open_questions(),
                        self.legend()])
        return (
            "<!doctype html>\n<html lang=\"es\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{title} · Event Storming</title><style>{BASE_CSS}{css(self.pal)}</style></head>"
            f"<body><main>{body}</main></body></html>\n"
        )


def main():
    ap = argparse.ArgumentParser(description="Render eventstorm.yaml to a self-contained HTML page")
    ap.add_argument("file")
    ap.add_argument("-o", "--out", help="output path (default: eventstorm.html next to the YAML)")
    args = ap.parse_args()
    doc = sl.load_yaml(args.file)
    palette = sl.load_json(sl.PALETTE_PATH)
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.file)), "eventstorm.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(Renderer(doc, palette).page())
    print(f"rendered: {out}")
    return sl.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
