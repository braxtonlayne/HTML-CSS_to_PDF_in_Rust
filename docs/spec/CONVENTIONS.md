# Spec conventions

Every document in `docs/spec/` follows these rules. `docs/tools/checklist.py check` enforces the mechanical ones; run it before every commit that touches the spec.

## 1. Checklist items

All implementable work is a checklist item. If something is not inside an item, an implementation session must not build it. Prose sections explain behavior and design. Items describe the work.

```
- [ ] **LAY-017** Implement `break-inside: avoid` for block boxes.
      Acceptance: a block with `break-inside: avoid` that does not fit on the current page moves entirely to the next page unless it is taller than one page, in which case it fragments at the top of a fresh page.
      Tests: tests/layout/pagination/break-inside-avoid-*.html (golden PDF raster + fragment-tree snapshot)
      Depends on: LAY-009, PAG-003
      Milestone: M1
      Spec ref: CSS Fragmentation 3 §3.1
```

Rules:

1. **ID**: `PREFIX-NNN`, globally unique, never reused, never renumbered. A deleted item stays in its document as `- [x] **ID** WITHDRAWN: <reason>.` with `Depends on: none` and the other required fields set to `n/a`. IDs do not have to be sequential. Document order is implementation order.
2. **Title**: one imperative sentence ending in `.`, naming the concrete deliverable.
3. **Acceptance** (required): observable, binary pass/fail criteria with concrete values. Do not write "handles edge cases", "works correctly" or "is fast". Write the inputs and the expected outputs.
4. **Tests** (required): the exact test file paths or globs plus the kind of check (see §4). Unit tests are named as `crate::module::tests::name`.
5. **Depends on** (required): a comma-separated list of IDs, or `none`. Every ID must exist. No cycles. A dependency's milestone must be ≤ the item's milestone.
6. **Milestone** (required): exactly one of `M0`–`M6` (see `34-roadmap-and-milestones.md`).
7. **Spec ref** (optional): the spec and section, the research doc section, or the ADR the item implements.
8. **Notes** (optional): implementation hints. This field is not part of acceptance.
9. **Scope**: one focused session, which is roughly ≤ 1 day of work and ≤ ~800 changed lines including tests. Split anything bigger.
10. Continuation lines are indented with exactly 6 spaces. A blank line ends the item.

## 2. ID prefixes and owning documents

| Prefix | Area | Owning document(s) |
|---|---|---|
| ARC | workspace, core types, pipeline glue, error model | 02 |
| DOM | HTML parsing, DOM arena | 03 |
| CSS | CSS parsing, cascade, computed values | 04, 04b |
| BOX | box tree generation | 05 |
| LAY | block & inline layout, fragment tree | 06, 06b |
| FLX | flex layout | 07 |
| GRD | grid layout | 07b |
| TBL | table layout | 08 |
| FLT | floats | 09 |
| POS | relative/absolute/fixed/sticky positioning | 09 |
| COL | multi-column | 10 |
| PAG | fragmentation & pagination engine | 11 |
| PGM | paged media (@page, margin boxes, page selection) | 12 |
| GEN | generated content, counters, running elements, cross-refs | 13 |
| FTN | footnotes | 13b |
| TXT | shaping, line breaking, bidi, hyphenation | 14 |
| FNT | font database, matching, loading, subsetting | 14b |
| IMG | raster images | 15 |
| SVG | SVG | 15 |
| NET | resource loading (fetchers, URL resolution, caches) | 23b |
| PNT | display list / painting (backgrounds, borders, effects) | 16b |
| PDF | PDF writer integration | 16 |
| ACC | tagging, PDF/UA, PDF/A | 17 |
| CLI | command line | 18 |
| CMP | compat shims (wkhtmltopdf, Puppeteer options) | 18b |
| SRV | HTTP server | 19 |
| API | Rust library API | 20 |
| BND | language bindings | 21 |
| TPL | templating & data mode | 22 |
| SEC | security controls | 23 |
| LIM | resource limits & sandboxing | 24 |
| DET | determinism | 25 |
| PERF | performance work & benchmarks | 26 |
| TST | test infrastructure | 27 |
| DBG | diagnostics & debugging | 28 |
| DX | developer experience | 29 |
| DEP | build, packaging, release | 30 |
| DOC | user-facing documentation | 31–33 |

## 3. Units, terms and notation

- Lengths inside the engine are `Au` (app units): `i32`, **1/64 CSS px**. 1 CSS px = 1/96 in = 0.75 pt. PDF user space is in pt. Conversion happens only in the PDF backend.
- "Page" means a PDF page. "Fragmentainer" means a page area or a column box.
- Terms are defined in `36-glossary.md`.
- Every CSS feature reference uses the property/at-rule name plus the spec section.

## 4. Test kinds and locations

| Kind | Location | Mechanism |
|---|---|---|
| Unit | `crates/<crate>/src/**` `#[cfg(test)]` | `cargo test` |
| Snapshot (box tree / fragment tree / computed style) | `tests/layout/<area>/<name>.html` + `<name>.snap` | `insta` snapshots of the `--explain` text dump (DBG items) |
| Render golden | `tests/render/<area>/<name>.html` + `goldens/<name>.p<N>.png` | render → rasterize PDF page N at 96 dpi with the pinned rasterizer → per-pixel diff with tolerance (TST items) |
| PDF structure | `tests/pdf/<area>/<name>.html` + `<name>.pdfcheck.toml` | assertions over the parsed output PDF (objects, tags, metadata) |
| WPT | `tests/wpt/` manifest + `expectations.toml` | reftest runner (TST items) |
| CLI | `tests/cli/<name>.toml` | `trycmd`-style transcript |
| Server | `tests/server/<name>.rs` | integration tests against an in-process server |
| Fuzz | `fuzz/fuzz_targets/<name>.rs` | `cargo fuzz`, with a CI smoke run |
| Bench | `benches/<name>.rs` + `bench/corpus/` | `criterion`/`divan` plus the CI regression gate |
| Compat | `tests/compat/<tool>/<name>.html` | compare against stored reference outputs from WeasyPrint/Chrome |

## 5. Writing rules

- Write for an implementer. State exact algorithms, data structures, signatures, error codes and defaults.
- Rust signatures in specs are normative unless marked *illustrative*.
- Every crate claim cites the research doc that verified it, e.g. `[R06 §3]` = `docs/research/06-*.md` section 3.
- Every nontrivial decision links an ADR: `[ADR-0012]` in `35-decisions-log.md`.
- Split any document longer than ~800 lines into `NNb-`, `NNc-` … parts.
