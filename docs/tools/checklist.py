#!/usr/bin/env python3
"""Checklist validator and aggregator for the recto spec set.

Usage:
    python3 docs/tools/checklist.py check      # validate only (exit 1 on errors)
    python3 docs/tools/checklist.py generate   # validate, then regenerate
                                               # docs/MASTER-CHECKLIST.md and the
                                               # generated section of
                                               # docs/spec/34-roadmap-and-milestones.md
    python3 docs/tools/checklist.py stats      # print counts per milestone/prefix

Item grammar (see docs/spec/CONVENTIONS.md):

    - [ ] **LAY-017** Imperative one-line title.
          Acceptance: ...            (required, may continue on following lines)
          Tests: ...                 (required)
          Depends on: LAY-009, PAG-003 | none   (required)
          Milestone: M0..M6          (required)
          Spec ref: ...              (optional)

Continuation lines are indented by >= 6 spaces. A field may wrap onto further
indented lines; wrapped lines are appended to the previous field.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "spec"
MASTER = ROOT / "docs" / "MASTER-CHECKLIST.md"
ROADMAP = SPEC / "34-roadmap-and-milestones.md"

MILESTONES = {
    "M0": "Hello PDF",
    "M1": "Block text with page breaks",
    "M2": "Invoice-complete",
    "M3": "Report-complete: tables, images, TOC",
    "M4": "Server + bindings",
    "M5": "Accessibility + archival",
    "M6": "Polish, compat shims, 1.0",
}
PREFIXES = {
    "ARC", "DOM", "CSS", "BOX", "LAY", "FLX", "GRD", "TBL", "FLT", "POS", "COL",
    "PAG", "PGM", "GEN", "FTN", "TXT", "FNT", "IMG", "SVG", "PNT", "PDF", "ACC",
    "NET", "CLI", "CMP", "SRV", "API", "BND", "TPL", "SEC", "LIM", "DET", "PERF",
    "TST", "DBG", "DX", "DEP", "DOC",
}
REQUIRED = ("Acceptance", "Tests", "Depends on", "Milestone")
KNOWN_FIELDS = REQUIRED + ("Spec ref", "Notes")

ITEM_RE = re.compile(r"^- \[( |x|X)\] \*\*([A-Z]+)-(\d{3,4})\*\* (.+?)\s*$")
FIELD_RE = re.compile(r"^ {4,}([A-Z][A-Za-z ]+?):\s*(.*)$")
CONT_RE = re.compile(r"^ {6,}(\S.*)$")
ID_RE = re.compile(r"\b([A-Z]{2,4})-(\d{3,4})\b")
GEN_BEGIN = "<!-- BEGIN GENERATED: milestone-assignment -->"
GEN_END = "<!-- END GENERATED: milestone-assignment -->"


class Item:
    def __init__(self, ident, prefix, done, title, path, line):
        self.id = ident
        self.prefix = prefix
        self.done = done
        self.title = title
        self.path = path
        self.line = line
        self.fields: dict[str, str] = {}

    @property
    def deps(self) -> list[str]:
        raw = self.fields.get("Depends on", "").strip()
        if raw.lower().startswith("none") or not raw:
            return []
        return [f"{p}-{n}" for p, n in ID_RE.findall(raw)]

    @property
    def milestone(self) -> str:
        return self.fields.get("Milestone", "").strip().split()[0] if self.fields.get("Milestone") else ""


def parse() -> tuple[list[Item], list[str]]:
    items: list[Item] = []
    errors: list[str] = []
    for path in sorted(SPEC.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        cur: Item | None = None
        last_field: str | None = None
        in_code = False
        for no, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                if cur is not None and not line.startswith(" "):
                    cur = None
                continue
            if in_code:
                continue
            m = ITEM_RE.match(line)
            if m:
                done, prefix, num, title = m.groups()
                cur = Item(f"{prefix}-{num}", prefix, done != " ", title, path, no)
                items.append(cur)
                last_field = None
                continue
            if cur is None:
                if re.match(r"^\s*- \[[ xX]\]", line):
                    errors.append(f"{path.name}:{no}: malformed checklist item: {line.strip()[:80]}")
                continue
            if not line.strip():
                # blank line ends the item
                cur = None
                continue
            fm = FIELD_RE.match(line)
            if fm and fm.group(1) in KNOWN_FIELDS:
                last_field = fm.group(1)
                if last_field in cur.fields:
                    errors.append(f"{cur.id} ({path.name}:{no}): duplicate field {last_field}")
                cur.fields[last_field] = fm.group(2).strip()
                continue
            cm = CONT_RE.match(line)
            if cm and last_field:
                cur.fields[last_field] += " " + cm.group(1).strip()
                continue
            # any other non-indented line ends the item
            cur = None
    return items, errors


def validate(items: list[Item], errors: list[str]) -> list[str]:
    by_id: dict[str, Item] = {}
    for it in items:
        if it.id in by_id:
            o = by_id[it.id]
            errors.append(f"duplicate ID {it.id}: {o.path.name}:{o.line} and {it.path.name}:{it.line}")
        else:
            by_id[it.id] = it
        if it.prefix not in PREFIXES:
            errors.append(f"{it.id} ({it.path.name}:{it.line}): unknown prefix {it.prefix}")
        for f in REQUIRED:
            if not it.fields.get(f, "").strip():
                errors.append(f"{it.id} ({it.path.name}:{it.line}): missing field '{f}'")
        if it.milestone and it.milestone not in MILESTONES:
            errors.append(f"{it.id} ({it.path.name}:{it.line}): bad milestone '{it.milestone}'")
        if not it.title.endswith("."):
            errors.append(f"{it.id} ({it.path.name}:{it.line}): title must end with '.'")
    for it in items:
        for d in it.deps:
            if d == it.id:
                errors.append(f"{it.id}: depends on itself")
            elif d not in by_id:
                errors.append(f"{it.id} ({it.path.name}:{it.line}): unknown dependency {d}")
            else:
                dm, im = by_id[d].milestone, it.milestone
                if dm in MILESTONES and im in MILESTONES and dm > im:
                    errors.append(
                        f"{it.id} ({im}) depends on {d} ({dm}) from a later milestone")
    # cycle detection (iterative DFS)
    WHITE, GREY, BLACK = 0, 1, 2
    color = {i: WHITE for i in by_id}
    for start in by_id:
        if color[start] != WHITE:
            continue
        stack = [(start, iter(by_id[start].deps))]
        color[start] = GREY
        path = [start]
        while stack:
            node, it_deps = stack[-1]
            nxt = next(it_deps, None)
            if nxt is None:
                color[node] = BLACK
                stack.pop()
                path.pop()
                continue
            if nxt not in by_id:
                continue
            if color[nxt] == GREY:
                cyc = path[path.index(nxt):] + [nxt]
                errors.append("dependency cycle: " + " -> ".join(cyc))
            elif color[nxt] == WHITE:
                color[nxt] = GREY
                path.append(nxt)
                stack.append((nxt, iter(by_id[nxt].deps)))
    # dangling ID references in prose (IDs mentioned anywhere that do not exist)
    for path in sorted(list(SPEC.glob("*.md")) + [ROOT / "docs" / "README.md"]):
        if not path.exists():
            continue
        in_code = False
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            for p, n in ID_RE.findall(line):
                ident = f"{p}-{n}"
                if p in PREFIXES and ident not in by_id:
                    errors.append(f"{path.name}:{no}: reference to undefined ID {ident}")
    return errors


def topo_order(items: list[Item]) -> list[Item]:
    """Stable topological order: milestone, then doc order, respecting deps."""
    by_id = {i.id: i for i in items}
    index = {i.id: n for n, i in enumerate(items)}
    indeg = {i.id: 0 for i in items}
    rdeps = defaultdict(list)
    for i in items:
        for d in i.deps:
            if d in by_id:
                indeg[i.id] += 1
                rdeps[d].append(i.id)
    import heapq
    heap = [(by_id[i].milestone, index[i], i) for i in indeg if indeg[i] == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        _, _, i = heapq.heappop(heap)
        out.append(by_id[i])
        for r in rdeps[i]:
            indeg[r] -= 1
            if indeg[r] == 0:
                heapq.heappush(heap, (by_id[r].milestone, index[r], r))
    return out


def generate(items: list[Item]) -> None:
    ordered = topo_order(items)
    per_ms = defaultdict(list)
    for it in ordered:
        per_ms[it.milestone].append(it)
    total = len(items)
    done = sum(1 for i in items if i.done)
    out = [
        "# MASTER CHECKLIST",
        "",
        "<!-- GENERATED by docs/tools/checklist.py generate. Do not edit item text here;",
        "     edit the source document, then regenerate. Checking an item off: tick it in",
        "     BOTH the source document and here (or tick the source and regenerate). -->",
        "",
        "Single source of truth for implementation progress. Items are grouped by milestone",
        "and listed in a dependency-respecting order (every item appears after all of its",
        "dependencies). Implement top to bottom within a milestone.",
        "",
        f"**Total items: {total}** — done: {done}, open: {total - done}.",
        "",
        "| Milestone | Name | Items | Done |",
        "|---|---|---:|---:|",
    ]
    for ms, name in MILESTONES.items():
        lst = per_ms.get(ms, [])
        out.append(f"| {ms} | {name} | {len(lst)} | {sum(1 for i in lst if i.done)} |")
    out.append(f"| **Total** | | **{total}** | **{done}** |")
    out.append("")
    for ms, name in MILESTONES.items():
        lst = per_ms.get(ms, [])
        out.append(f"## {ms} — {name} ({len(lst)} items)")
        out.append("")
        for it in lst:
            mark = "x" if it.done else " "
            rel = it.path.relative_to(ROOT / "docs")
            deps = ", ".join(it.deps) if it.deps else "none"
            out.append(f"- [{mark}] **{it.id}** {it.title} — [{rel.name}]({rel.as_posix()}) · deps: {deps}")
        out.append("")
    MASTER.write_text("\n".join(out), encoding="utf-8")

    if ROADMAP.exists():
        text = ROADMAP.read_text(encoding="utf-8")
        if GEN_BEGIN in text and GEN_END in text:
            gen = [GEN_BEGIN, "", "| Milestone | Item count | Items |", "|---|---:|---|"]
            for ms in MILESTONES:
                lst = sorted(per_ms.get(ms, []), key=lambda i: (i.prefix, i.id))
                gen.append(f"| {ms} | {len(lst)} | {', '.join(i.id for i in lst)} |")
            gen += ["", "Per-prefix counts:", "", "| Prefix | " + " | ".join(MILESTONES) + " | Total |",
                    "|---|" + "---:|" * (len(MILESTONES) + 1)]
            counts = defaultdict(lambda: defaultdict(int))
            for it in items:
                counts[it.prefix][it.milestone] += 1
            for p in sorted(counts):
                row = [str(counts[p].get(m, 0)) for m in MILESTONES]
                gen.append(f"| {p} | " + " | ".join(row) + f" | {sum(counts[p].values())} |")
            gen += ["", GEN_END]
            pre, rest = text.split(GEN_BEGIN, 1)
            _, post = rest.split(GEN_END, 1)
            ROADMAP.write_text(pre + "\n".join(gen) + post, encoding="utf-8")


def stats(items: list[Item]) -> None:
    c = defaultdict(int)
    for it in items:
        c[it.milestone] += 1
    for m in MILESTONES:
        print(f"{m}: {c[m]}")
    print(f"total: {len(items)}")
    p = defaultdict(int)
    for it in items:
        p[it.prefix] += 1
    print(" ".join(f"{k}={v}" for k, v in sorted(p.items())))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    items, errors = parse()
    errors = validate(items, errors)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(items)} items, {len(errors)} errors")
    if cmd == "stats":
        stats(items)
    if errors:
        return 1
    if cmd == "generate":
        generate(items)
        print(f"wrote {MASTER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
