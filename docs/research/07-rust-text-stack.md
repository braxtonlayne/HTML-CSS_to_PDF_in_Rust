# 07 — Rust text stack: shaping, line breaking, bidi, hyphenation, fonts

Date: 2026-10-14 · Topic slug: `text` · Author: Phase-0 research agent

Scope: choose the shaper, segmenter/line-breaker, bidi, hyphenation, font parsing/subsetting and font
database for recto, and decide whether to adopt `parley` (or `cosmic-text`) as the inline layout engine
or build recto's own inline formatting context on top of lower-level crates. Every API claim below
cites a file in the source tree inspected at the stated tag. Anything I could not check is marked
**UNVERIFIED**.

## Sources inspected

Versions are the latest non-yanked entries in the crates.io sparse index on 2026-10-14. Clones are under
`/tmp/claude-0/src/text/`.

| Crate / repo | Version (index) | Tag inspected | Commit SHA | License | Last commit (tag / repo HEAD) | Maintenance |
|---|---|---|---|---|---|---|
| parley (+ parley_engine, parley_data, parlance) | parley 0.12.0, parley_engine 0.12.0, parlance 0.1.1 | `v0.12.0` | `6e1143dda817360dd3a2a64f9133c6e5dfabd881` | Apache-2.0 OR MIT | 2026-10-09 / 2026-10-14 | Very active (Linebender, used by Blitz/Xilem). Breaking API changes in every 0.x release |
| fontique | 0.12.0 | `v0.12.0` (same repo) | same | Apache-2.0 OR MIT | same | Active |
| cosmic-text | 0.19.0 | `0.19.0` | `c24886c2471e5606587c46090cd25dbbf209186b` | MIT OR Apache-2.0 | 2026-04-22 / 2026-09-30 | Active (System76/COSMIC), GUI/editor-oriented |
| harfrust | 0.14.0 | `0.14.0` | `3fbac46c3943bffb7519e38fa1eabe963a6579c7` | MIT | 2026-10-03 / 2026-10-12 | Very active (HarfBuzz org + Google Fonts) |
| rustybuzz | 0.20.1 | `v0.20.1` | `8c52723ff75e91a33ae36e527baed871097e64bf` | MIT | 2024-11-12 / 2026-07-26 | **Archived/deprecated**: HEAD README says "not developed further, unmaintained, and archived … switch to HarfRust" (commit `9faca96`) |
| swash | 0.2.10 | HEAD (no 0.2.10 tag; HEAD commit is "Bump version number to 0.2.10") | `7773843df0d63cd468db61a29c152b5e7a99d4ab` | Apache-2.0 OR MIT | 2026-07-17 | Maintenance-only (skrifa bumps) |
| fontations: skrifa / read-fonts / write-fonts / skera | 0.48.0 / 0.45.0 / 0.54.0 / 0.8.0 | `skrifa-v0.48.0` = `read-fonts-v0.45.0` = `write-fonts-v0.54.0` = `skera-v0.8.0` | `0e939934004776b1982982428a7ce748e61b0310` | MIT OR Apache-2.0 | 2026-10-02 / 2026-10-13 | Very active (Google Fonts; Chrome uses skrifa) |
| subsetter (typst) | 0.2.6 | `v0.2.6` | `c3f23c67bc0190587f639bda84dc0005ca3f54d5` | MIT OR Apache-2.0 | 2026-06-04 / 2026-07-23 | Active, narrow scope (PDF embedding) |
| fontdb | 0.24.0 | `v0.24.0` | `ecb707e6096b59146b750f66a32c125a43515192` | MIT | 2026-07-29 | Maintained |
| ttf-parser | 0.25.1 | not cloned (read via index only) | — | MIT OR Apache-2.0 | — | Being superseded by read-fonts in the ecosystem (rustybuzz archived; fontdb 0.24 vendors its own parser, `src/ttf_parser/`) |
| unicode-bidi | 0.3.18 | `v0.3.18` | `580b9c6c68fdb689916017e61d5052be3ed349b5` | MIT OR Apache-2.0 | 2024-12-16 / 2026-09-15 | Maintained (servo). 0.3.18 tables = Unicode 16.0 (`src/char_data/tables.rs:8`); HEAD has 17.0 unreleased |
| unicode-linebreak | 0.1.5 | `v0.1.5` | `829adeed3c07ed160c1c721b61806eb902a4c1f0` | Apache-2.0 | 2023-07-25 | Stale. Unicode 15.0 (`src/lib.rs:27`), no tailoring |
| icu4x (icu_segmenter, icu_properties, data crates) | 2.3.0 (segmenter, properties), icu_provider 2.3.1 | HEAD (workspace version 2.3.0, `Cargo.toml:111`) — sparse checkout | `bb3e1f9a0c966f7334aa400066f520f64f3dc3d6` | Unicode-3.0 | 2026-10-14 | Very active (Unicode Consortium) |
| hypher | 0.1.8 | `v0.1.8` | `d81cc506416bffef2a75ee2dc969d4b41bc36613` | MIT OR Apache-2.0 (code); patterns individually licensed | 2026-09-17 | Active (typst) |
| hyphenation | 0.8.4 | `v0.8.4` | `0caea24164b37e78a8aae68c3e6a70b78fcdb06e` | Apache-2.0/MIT (code); patterns individually licensed | 2021-08-19 / 2024-01-24 | Dormant; depends on `bincode 1.3.3`, flagged unmaintained by RUSTSEC-2025-0141 |
| typst | 0.15.1 (tag) | `v0.15.1` | `9dfd3a08500b7896045f907433cf7b4b02434fad` | Apache-2.0 | 2026-07-17 / 2026-10-09 | Very active; production paged engine |
| CSS Fonts 4 / CSS Text 3–4 spec text | — | csswg-drafts HEAD (sparse) | `1c249b342ee7a0dfe0fcf7f7dc75272b1e794d52` | W3C | 2026-10-14 | — |

Web sources (used only for things not on GitHub):
- RUSTSEC-2025-0141 (bincode unmaintained, published 2025-12-16): https://rustsec.org/advisories/RUSTSEC-2025-0141 , https://osv.dev/vulnerability/RUSTSEC-2025-0141

---

## 1. Shapers

### 1.1 harfrust 0.14.0 (recommended)

- A port of HarfBuzz shaping to Rust, built on `read-fonts`. README: "Matches HarfBuzz v14.5.1". `HARFBUZZ.md`
  reports results against HarfBuzz's own test suites as of 2026-08-24: `shape+aots 800/800`,
  `shape+text-rendering-tests 437/437`, `shape+in-house 5012/5021`.
- README "Major changes": no font-size property ("Shaping is always using UnitsPerEm. You should scale the
  result manually"), no system/ICU integration, no Graphite, and "Malformed fonts will cause an error"
  where HarfBuzz falls back to a dummy shaper. **recto must catch `ShapeError` and fall back to a
  nominal-glyph (cmap + hmtx) "dumb" shaping path for corrupt fonts.**
- Performance: README says "less than 25% slower than HarfBuzz on most common fonts".
- Deps (`harfrust/Cargo.toml`): `read-fonts 0.45`, `bitflags`, `bytemuck`, `smallvec`. Optional `icu`
  (`icu_properties =2.2.0`, `icu_normalizer`) and `libm`/`spin` for `no_std`. **No hashing or HashMap
  in the crate** (grep of `harfrust/src` finds no `HashMap`/`hashbrown`), `#![forbid(unsafe_code)]`
  (`src/lib.rs:10`), and `no_std` with `default-features = false` (`src/lib.rs:8`). Deterministic and
  WASM-friendly.
- API at 0.14 (`src/lib.rs`, `src/shape.rs`, `src/shaper_font.rs`, `src/plan.rs`):
  - `harfrust::Font` re-exports `read_fonts::model::Font` (`src/lib.rs` `pub mod font { pub use read_fonts::model::*; }`;
    struct at `read-fonts/src/model/font.rs:52`).
  - `ShaperFont::new(&Font)` with `set_scale`/`with_scale`, `set_font_funcs` (pluggable `FontFuncs` for
    advances, extents and nominal glyphs, `src/shaper_font.rs:43–263`).
  - `ShapePlan::new(...)` / builder with `.language()`, `.features()` (`src/plan.rs:56,121–139`). Plans should be
    cached per (font, script, direction, language, features); parley does exactly this (`parley_engine/src/shape/cache.rs:95–166`).
  - `pub fn shape(font: &ShaperFont, buffer: &mut Buffer, options: ShapeOptions) -> Result<(), ShapeError>` (`src/shape.rs:10`).
  - `GlyphFlags::UNSAFE_TO_BREAK`, `UNSAFE_TO_CONCAT` (needs `BufferFlags::PRODUCE_UNSAFE_TO_CONCAT`),
    `SAFE_TO_INSERT_TATWEEL` (`src/buffer.rs:175–256`). These are what make "shape once per paragraph, reshape
    only at line edges" possible (see Typst §5.3).
- The API churns: 0.12 → 0.14 within months (parley 0.12 still pins `harfrust ^0.12.0`, see §2.9). Expect to
  update call sites at each bump. HarfBuzz itself can be built with HarfRust as a shaper (`HARFBUZZ.md`), so
  it has strong upstream backing. Chrome's adoption is **UNVERIFIED**.

### 1.2 rustybuzz 0.20.1: rejected

Archived. HEAD commit `9faca96` "Deprecate in preference to HarfRust", and the README says "This project
is not developed further, unmaintained, and archived". It is based on `ttf-parser`, a second font-parsing
stack next to read-fonts/skrifa. Typst still uses it at v0.15.1 and at HEAD (`Cargo.toml:110/112`
`rustybuzz = "0.20"`). recto must not start on it.

### 1.3 swash 0.2.10: not as the shaper

Swash has its own shaper (not a HarfBuzz port) plus scaling/rasterization (README "Goals"). It caps
`skrifa >=0.31.1, <=0.44` (index), so it cannot share a single fontations version with harfrust 0.14
(read-fonts 0.45 / skrifa 0.48) and would pull a duplicate fontations tree. recto writes vector glyphs into
the PDF and does not rasterize, so swash brings nothing. Rejected.

### 1.4 Font parsing: skrifa 0.48 / read-fonts 0.45

- `skrifa::metrics::Metrics::new(&font_ref, Size, &location)` supplies ascent, descent, leading,
  underline, strikeout, x-height and cap-height. Line-metric source selection (`skrifa/src/metrics.rs:64–67,143–174`):
  OS/2 typo metrics if `USE_TYPO_METRICS` is set; otherwise hhea; if hhea is zero, OS/2 typo, and Win metrics
  as a last resort. This matches Blink/FreeType behaviour for `line-height: normal`. parley uses it unchanged
  (`parley_engine/src/shape/shaped_text.rs:77–148`).
- skrifa also gives outlines (for SVG/Type3 fallback, synthetic oblique and bold), variation locations and
  charmaps. It is the single parsing stack recto should use everywhere.

---

## 2. parley 0.12.0 + fontique 0.12.0

### 2.1 Crate structure (new in 0.12)

From the workspace `Cargo.toml` and `CHANGELOG.md` "## [0.12.0] - 2026-10-09":
- `parley_engine`: low-level analysis and shaping. "Layout decisions, such as where to break lines and how
  to align or stack them, are left to the caller." It was introduced explicitly "for … typesetters implementing their own
  line-breaking algorithms".
- `parley`: the web-style layout on top of `parley_engine`.
- `parley_data`: baked ICU4X-derived composite property trie (`parley_data/README.md`).
- `parlance`: shared vocabulary types (FontWeight, Language, LineBreak, OverflowWrap, WordBreak, …).
- `fontique`: font collection, matching and fallback.

### 2.2 Builders and styles

- `LayoutContext::{ranged_builder, tree_builder, style_run_builder}` → `RangedBuilder`, `TreeBuilder`,
  `StyleRunBuilder` (`parley/src/lib.rs:7–17`, `parley/src/builder.rs`).
  `ranged_builder(fcx, text, scale, quantize: bool)` (`parley/src/context.rs:96–102`). **`quantize` rounds
  ascent, descent and leading to whole pixels** (`style/mod.rs:90–94`). recto must pass `false`.
- `StyleProperty` variants (`parley/src/style/mod.rs:227–280`): FontFamily, FontSize, FontWidth, FontStyle,
  FontWeight, FontVariations, FontFeatures, Locale, Brush, Underline(+Offset/Size/Brush),
  Strikethrough(+…), LineHeight, VerticalAlign, WordSpacing, LetterSpacing, WordBreak, LineBreak,
  OverflowWrap, TextWrapMode, WhiteSpaceCollapse.
- **Missing compared with CSS inline formatting:** no padding, border or margin on inline spans (non-atomic
  inline boxes), no `box-decoration-break`, no `text-transform`, no `tab-size`, no `hyphens`, no
  `font-synthesis` control, no `font-size-adjust`, no `::first-line` or `::first-letter`, no `text-align-last`
  beyond `AlignmentOptions::last_line_alignment`, no `text-justify`, no `hanging-punctuation`.
- `LineHeight::{MetricsRelative(f32), FontSizeRelative(f32), Absolute(f32)}`. `NORMAL = MetricsRelative(1.0)`
  (`style/mod.rs:49–71`).
- `VerticalAlign { alignment: AlignmentBaseline, shift: BaselineShift }` covers the CSS 2 keywords
  (baseline/sub/super/text-top/text-bottom/middle/top/bottom/length), `style/mod.rs:109–205`. Percentages
  must be resolved by the caller.
- `WhiteSpaceCollapse::{Collapse, Preserve, PreserveBreaks, BreakSpaces}`. **Only `TreeBuilder` collapses**;
  ranged builders expect pre-transformed text (`style/mod.rs:28–44`).
- Text indent: `Layout::set_text_indent(amount, IndentOptions { each_line, hanging })` (`layout/layout.rs:199`,
  `layout/mod.rs:100–160`). Percentages are resolved by the caller.

### 2.3 Shaping backend: harfrust (verified)

`parley_engine/Cargo.toml` depends on `harfrust` (workspace `harfrust = "0.12.0"`) and `skrifa 0.44`. Swash is
used only by `examples/swash_render`. Shaping plans are cached per
(font, direction, script, language, features) (`parley_engine/src/shape/cache.rs:95–166`).

### 2.4 Bidi, segmentation, line-break opportunities

- **Bidi:** parley has its own resolver, `parley_engine/src/bidi.rs` (915 lines, `BidiResolver`), and does
  not use `unicode-bidi`.
- **Line breaking, word and grapheme:** `icu_segmenter` 2.3 (`parley_engine/src/analysis.rs:21–26,104–162`).
  `LineSegmenter::new_for_non_complex_scripts` is the default. With feature `complex-scripts`, it uses
  `LineSegmenter::new_dictionary` plus `WordSegmenter::new_dictionary`. CSS `line-break`/`word-break` map
  to ICU `LineBreakOptions`, and there is a pluggable `LineBreakOverrideFn` with a `CHROMIUM_LINE_BREAK_OVERRIDE`
  table (`parley/src/lib.rs` re-exports from `parley_engine::break_overrides`). The repo has a
  browser-recording harness that compares line breaks with real browsers (`parley_tests/linebreaking_browser_recorder`).
- Properties come from `parley_data` (a baked composite trie) plus `icu_properties` and `icu_normalizer` compiled data.

### 2.5 Line breaking API: resumable, with variable width per line

This is parley's strongest feature for recto (`parley/src/layout/line_break.rs`, 2057 lines):
- `Layout::break_all_lines(Option<f32>)` (`layout.rs:210`) is the simple path. `Layout::break_lines() -> BreakLines` (`layout.rs:205`) is the incremental path.
- `BreakLines::break_next() -> Option<YieldData>` (`line_break.rs:1028`) yields once per line.
  `YieldData::{LineBreak(LineBreakData), MaxHeightExceeded(MaxHeightBreakData), InlineBoxBreak(BoxBreakData)}`
  (`:517–541`). `LineBreakData` carries `reason`, `metrics: LineMetrics`, `line_y_start` and `line_y_end` (`:544–556`).
- `BreakerState` (`:587–633`) is `Clone` and lets the caller set the following between lines:
  `set_line_max_advance` (per-line width; must stay ≤ `layout_max_advance`, asserted at `:1029–1032`),
  `set_line_x` (left offset, for a float on the left), `set_line_y`, and `set_line_max_height`, which makes the breaker yield
  `MaxHeightExceeded` so the caller can move the line down past a float whose band is too short (`:524–532`).
- `InlineBoxKind::CustomOutOfFlow` makes the breaker yield `InlineBoxBreak` at the box's position "to implement
  … CSS's `float`" (`parley/src/inline_box.rs:44–61`, `line_break.rs:1076–1086`).
- `BreakLines::revert_to(BreakerState)` and `revert()` (`:996–1012`) allow checkpoint and retry. For pagination,
  recto can save a state per line, and on a page break or widows/orphans adjustment revert to line *k*,
  change the width (for example a different `@page` width), and continue.
- `break_next_with_length(max_chars)` (`:1302`) breaks by character count.
- **Answer to the brief:** yes, parley can break lines with a varying available width per line, and yes,
  breaking is resumable and checkpointable. All lines still live in one `Layout` object, with a continuous
  y coordinate (f64) that the caller re-bases per fragment.

### 2.6 Inline boxes, alignment, justification, spacing

- `InlineBox { id, kind, index (byte offset), width, height, baseline: Option<f32>, vertical_align }` (`inline_box.rs:7–27`)
  represents atomic inlines (inline-block, img, inline-table) only.
- `Alignment::{Start, End, Left, Center, Right, Justify}` plus `AlignmentOptions { align_when_overflowing, last_line_alignment }`
  (`layout/alignment.rs:8–52`). Justification spreads free space evenly over word-separator opportunities
  (`alignment.rs:126–143`, `line.justification.amount_per_opportunity`). There is no inter-character
  justification (CJK) and no shrink.
- Letter and word spacing are styles. "Applying letter spacing now stops optional ligatures from forming"
  (CHANGELOG 0.12).

### 2.7 Hyphenation: none

No `hyphens` property, and no dictionary hyphenation anywhere in `parley`, `parley_engine` or `parlance`
(grep "hyphen" finds only tests and a UAX#14 break-override test). The soft hyphen U+00AD is shaped as a zero-advance
cluster (`parley_engine/src/shape/shaped_text.rs:667–700`) and creates a break opportunity, but the
line breaker never inserts a visible hyphen glyph at a SHY break (`line_break.rs` has no hyphen handling).
That is incorrect for `hyphens: manual` (the CSS default).

### 2.8 Reshaping at line breaks: not implemented

`parley_engine/README.md` says: "Correct reshaping of lines is in progress; in the meantime you can break text at
`Atom` or `ShapedCluster` boundaries." The CHANGELOG says "Work is underway to support reshaping of lines, e.g., when a
break falls within a ligature or splits a word in a cursive script." No `unsafe_to_break` handling exists in
`parley_engine/src/shape/` (grep). Hyphenation inside a word (Arabic-script joining, ligatures across
the hyphen point, kerning against the hyphen) requires reshaping, so parley cannot host hyphenation properly
today.

### 2.9 Fonts in parley/fontique

- `FontContext { collection: fontique::Collection, source_cache: SourceCache }` (`parley/src/font.rs`).
- `Collection::new(CollectionOptions)`, `load_system_fonts()`, `load_fonts_from_paths(paths)` (std),
  `register_fonts(Blob, Option<FontInfoOverride>)`, `set_generic_families`, `set_fallbacks(FallbackKey, …)`, `query(&mut SourceCache) -> Query`
  (`fontique/src/collection/mod.rs:81–234`).
- The matching algorithm is "the CSS font matching algorithm" (`fontique/src/matching.rs:4`, `match_font`), but the
  module is private (`mod matching;` in `lib.rs`) and not reusable directly.
- Per-cluster fallback in parley (`parley/src/shape/mod.rs:305–450`) works like this. The family list comes from the style. Emoji clusters
  append `GenericFamily::Emoji`. The query is filtered by charmap coverage of the whole cluster, and the best-coverage
  font wins. Script and language fallbacks come from `FallbackKey(script, lang)`. If nothing at all matches, a "last
  resort" font is any face from sans-serif, serif or monospace generics (`any_font`, `:452`).
- **System discovery on Linux = libfontconfig via FFI** (`fontique/Cargo.toml`: `system` feature pulls
  `yeslogic-fontconfig-sys` for linux/freebsd; `src/backend/mod.rs` selects `fontconfig.rs`). With
  `fontconfig-dlopen` it dlopens at runtime. **Neither works in a fully static musl binary in a `scratch` image.**
  The first needs a static libfontconfig plus expat and freetype linked in; the second relies on `dlopen`,
  which is non-functional in static musl (general musl behaviour, **UNVERIFIED** for this crate specifically).
  Without the `system` feature, fontique uses a dummy backend (`backend/mod.rs` "Dummy system font backend
  for targets like wasm32"). `load_fonts_from_paths` still works and is pure Rust plus `memmap2` (`scan.rs:64–167`).
- **Determinism hazards in fontique:**
  1. `scan_path_impl` iterates `std::fs::read_dir` without sorting (`scan.rs:159`), so face order within a family
     depends on filesystem order.
  2. `FamilyId` and `SourceId` come from process-global atomic counters (`family.rs:22`, `source.rs:26`), so IDs depend on
     the order of registration across threads in server mode.
  3. `hashbrown` is configured with `default-hasher` (workspace `Cargo.toml`). `register_fonts` returns families
     in HashMap iteration order (`collection/mod.rs:728–753`), which only matters for multi-family TTCs.
     Lookups are otherwise keyed. The hasher's per-process seeding is **UNVERIFIED**.
  4. Memory-maps font files (`scan.rs:164`, `unsafe { Mmap::map }`). A file that changes under the process is UB-adjacent.
- **Dependency version skew:** parley 0.12 pins `harfrust ^0.12` → `read-fonts ^0.41`, `skrifa ^0.44`, and fontique uses
  `read-fonts ^0.41` (index). Current versions are harfrust 0.14, read-fonts 0.45 and skrifa 0.48. A recto that also uses
  current skrifa (for outlines/metrics) or `subsetter` (skrifa 0.42/read-fonts 0.39) would link 2–3
  copies of read-fonts.

### 2.10 Rendering iteration

`Layout::lines()` → `Line::items()` → `PositionedLayoutItem::{GlyphRun, InlineBox}`. `GlyphRun::{run, style,
style_index, baseline, offset, advance, glyphs, positioned_glyphs}` (`layout/line.rs:298–337`), with
`Glyph { id: u32, x: f32, y: f32, advance: f32 }` (`parley_engine/src/glyph.rs:7–12`). Clusters expose text
ranges and ligature start/continuation (CHANGELOG 0.12), which is enough for ToUnicode/ActualText mapping.
Coordinates are **f32**, while `line_y` is f64 (`line_break.rs:604–606`, "f32 causes test failures due to accumulated error").

### 2.11 Size, WASM, determinism summary for parley

- Deps (index): fontique, harfrust, hashbrown, icu_locale_core, icu_normalizer, icu_properties, icu_segmenter
  (`compiled_data`), parley_data (baked), parley_emoji, skrifa, smallvec, plus platform FFI crates under
  `system`.
- ICU data cost without `complex-scripts` is roughly 30 KB of line rules, 12 KB grapheme and 18 KB word (see §4.2), plus property tries.
  With `complex-scripts` it adds the line dictionary for SE-Asian scripts (2.07 MB) and the word dictionary (CJ, 4.0 MB).
- WASM: `no_std` capable (`#![no_std]` in `parley/src/lib.rs`, std/libm features), with the dummy font backend on wasm32.

---

## 3. cosmic-text 0.19.0

- A GUI/editor text engine (`Buffer`, `BufferLine`, `ShapeLine`, `LayoutLine`, editor with `vi` feature). Default
  features are `std`, `swash` and `fontconfig` (`Cargo.toml [features]`).
- Shaping: `harfrust ^0.5.0` (index), which is an old harfrust nine minor versions behind, with `skrifa ^0.40`. Line breaking:
  `unicode_linebreak::linebreaks` (`src/shape.rs:970`), so Unicode 15 with no CSS tailoring. Bidi: `unicode-bidi`.
  Fonts: `fontdb ^0.23` (HEAD bumped to 0.24 on 2026-09-20, unreleased).
- Wrapping: `enum Wrap { None, Glyph, Word, WordOrGlyph }` (`src/layout.rs:128–137`), and `Align { Left, Right, Center,
  Justified, End }` (`:152–158`). There is one `width_opt: Option<f32>` per layout call (`ShapeLine::layout`, `src/shape.rs:1570–1584`):
  **no per-line width, no resumable breaking, no inline boxes, no hyphenation, no word-spacing** (`Attrs` at
  `src/attrs.rs:286–299` has color, family, stretch, style, weight, metrics, letter_spacing, features and decoration).
- Tabs are handled as `tab_width × space advance` (`src/shape.rs:1413`). Ellipsis is supported.
- Determinism: uses `rustc-hash` FxHashMap (deterministic). Fallback lists are per platform (`src/font/fallback/{unix,macos,windows,other}.rs`).
- **Verdict:** unsuitable for paged CSS layout. It lacks floats, fragmentation, inline boxes and CSS break tailoring, and its
  dependency versions lag. Rejected.

---

## 4. Lower-level building blocks

### 4.1 Bidi

| Option | Notes |
|---|---|
| `unicode-bidi 0.3.18` | UAX#9 with `BidiInfo`/`ParagraphBidiInfo`, reordering of lines (`visual_runs`). Unicode 16.0 tables at the tag (Unicode 17 on HEAD, unreleased). Deps: none required (optional serde/smallvec/flame). Used by Typst (`Cargo.toml:137`) and cosmic-text. `no_std` capable. |
| parley_engine's `BidiResolver` | Not public (`pub(crate) struct BidiResolver`, `parley_engine/src/bidi.rs:12`). |
| ICU4X | `icu_properties` exposes `BidiClass` and has an optional `unicode-bidi` integration feature (index: `icu_properties` optional dep `unicode-bidi`). A standalone ICU4X UBA implementation is **UNVERIFIED** (not found in the sparse checkout). |

Recommendation: `unicode-bidi` 0.3.18, with `BidiClass` sourced from the same Unicode version as the
segmenter if possible (via the `icu_properties` integration). Keep the bidi pass behind an internal trait so it can be swapped.

### 4.2 Line-break opportunities (UAX#14) and segmentation (UAX#29)

`icu_segmenter 2.3.0` (`components/segmenter/src/line.rs`):
- `LineBreakOptions { strictness: Option<LineBreakStrictness>, word_option: Option<LineBreakWordOption>, content_locale }`
  (`line.rs:80–97`). `LineBreakStrictness::{Loose, Normal, Strict}` maps to CSS `line-break`, and
  `LineBreakWordOption::{Normal, BreakAll, KeepAll}` maps to CSS `word-break` (`line.rs:27–74`). `line-break: anywhere` and
  `overflow-wrap: anywhere/break-word` are handled by the line builder, not the segmenter.
- Constructors (`line.rs:333–600`): `new_for_non_complex_scripts` (const, rules only), `new_auto` = `new_lstm`
  (LSTM for Khmer, Lao, Myanmar and Thai), and `new_dictionary` (dictionary for those scripts). Chinese and Japanese line breaking is rule-based
  (UAX#14 ID class) and needs **no** dictionary. The dictionaries matter for word segmentation and SE-Asian line breaking.
- Baked data sizes from `provider/data/segmenter/fingerprints.csv` at HEAD (binary payload sizes):

| Data marker | Size |
|---|---|
| `segmenter/break/line/v1` / `v2` / `v3` | 19.9 KB / 30.6 KB / 26.6 KB |
| `segmenter/break/grapheme/cluster/v1` / `v2` | 10.5 KB / 12.4 KB |
| `segmenter/break/word/v2` | 18.5 KB |
| `segmenter/lstm/auto/v1` (Thai/Lao/Khmer/Burmese LSTM) | **621 KB** |
| `segmenter/dictionary/extended/v2` (SE-Asian dictionaries) | **2.07 MB** |
| `segmenter/dictionary/auto/v2` (Chinese/Japanese word dictionary) | **4.01 MB** |

- Typst uses `LineSegmenter::new_lstm(...)` (`typst-layout/src/inline/linebreak.rs:38–39`), roughly +621 KB, plus a custom CJ
  blob from `typst_assets::icu::ICU_CJ_SEGMENT` that overrides curly quotes QU→OP/CP (`:41–58`).
- `unicode-linebreak 0.1.5` has Unicode 15.0, only `linebreaks(&str)` and `break_property(u32)`
  (`src/lib.rs:41,89`), no strictness or word-break tailoring, and no commits since 2023-07. Rejected.

**Recommendation:** use `icu_segmenter` with `compiled_data`. Default build: `new_for_non_complex_scripts` plus
grapheme. Cargo feature `complex-scripts`: `new_lstm` (+~0.6 MB), with dictionary mode not used. This keeps the default
binary small and still handles Thai and friends when enabled. Pin the ICU4X minor version, because data and
behaviour change between versions and byte-identical output across recto versions is a goal.

### 4.3 Grapheme clusters

Use `icu_segmenter::GraphemeClusterSegmenter` (const-constructible, as parley does at
`parley_engine/src/analysis.rs:104–106`). That gives one Unicode version for all segmentation. `unicode-segmentation 1.13.3`
is an acceptable alternative (no deps) but adds a second Unicode-version source.

### 4.4 Hyphenation

| | hypher 0.1.8 | hyphenation 0.8.4 |
|---|---|---|
| Algorithm | Liang patterns compiled at build time to finite automata that run directly on embedded bytes (README) | Knuth–Liang, `fst` + `bincode` serialized dictionaries |
| Deps | **none**, `no_std`, no unsafe (README "Features") | `bincode 1.3.3` (RUSTSEC-2025-0141 unmaintained), `fst`, `serde`, `hyphenation_commons`; embedding via `pocket-resources` |
| Languages | 48 behind per-language features (`Cargo.toml [features] full = [...]`) | 82 dictionary files (`dictionaries/`, 3.0 MB on disk) |
| Size | ~1.1 MiB for all languages (README). English 27 KiB, German 201 KiB, Hungarian 346 KiB, Norwegian 153 KiB | en-us 92 KB, de-1996 200 KB (`dictionaries/*.bincode`) |
| Load time | 0 (README benchmark table) | Deserialization at load (151 µs for English per hypher README benchmark) |
| API | `hyphenate(word, Lang) -> Syllables`, `hyphenate_bounded(word, lang, left_min, right_min)` (`src/lib.rs:88,112`), `Lang::hyphenation_character()` | `Standard::from_embedded(Language)`, `hyphenate` (**UNVERIFIED** names; not read) |
| Maintenance | Active (2026-09) | Dormant (last tag 2021) |

**Pattern licensing.** hypher's README claims "only patterns that are available under permissive licenses
… LPPL, MPL, MIT, BSD-3". Reading the headers of `patterns/*.tex` gives MIT ×22, LPPL ×16,
custom "copying permitted" ×3 (en-us, no, sa), BSD-like ×1 (bg), MPL ×1 (hu), BSD-3 ×1 (pt), Unlicense ×1 (gl),
LPPL in prose ×1 (ca), and **GPL-2.0-or-later ×1: `hyph-sk.tex` (Slovak), lines 14–18**. It is compiled into
`tries/sk.bin` (`tests/generate.rs:50`) and enabled by the default `full` feature. So hypher's default
feature set embeds a GPL-licensed pattern. **recto must use `default-features = false` and an explicit
language list that excludes `slovak`** (or get a legal opinion). LPPL patterns embedded in a binary are generally
accepted (Typst ships them), but recto's NOTICE file must reproduce each pattern's copyright line.
The hyphenation crate ships the same hyph-utf8 sources (`patterns/hyph-sk.*`), so it has the same issue.

**Recommendation:** hypher, with an explicit language feature list and per-language opt-in at build time. Implement
`hyphenate-limit-chars` and `-lines` and `-zone` (CSS Text 4) in recto's breaker using `hyphenate_bounded`.
The hyphen glyph comes from `Lang::hyphenation_character()` or `hyphenate-character`, shaped with the run's font
(Typst `ShapedText::hyphen`, `line.rs:163`).

### 4.5 Subsetting (for PDF embedding)

| | typst `subsetter` 0.2.6 | fontations `skera` 0.8.0 (formerly `klippa`) |
|---|---|---|
| Purpose | "subsetting a font with the purpose of including it in a PDF file" only (README "Scope"). Output is not a general-purpose font; `cmap` removed; you must write CIDFontType0/2 and use remapped GID as CID (`src/lib.rs` docs) | General-purpose HarfBuzz-`hb-subset` port |
| Outlines | glyf, **CFF (SID→CID conversion)**, CFF2 only via `subset_with_variations` (converted to TrueType) (`src/lib.rs:108–140`) | glyf/loca, gvar, COLR/CPAL, CBDT/CBLC, sbix, GSUB/GPOS, HVAR/VVAR…; **no CFF/CFF2 module** (`skera/src/` listing; `fn subset` table match at `lib.rs:1213–1425` has no CFF arm) |
| Variable fonts | Instancing via `subset_with_variations(data, index, &[(Tag, f32)], &GlyphRemapper)` (feature `variable-fonts`, default) | Instancing marked TODO in places (`lib.rs:845,1183,1208`) |
| Deps | `rustc-hash` only. With `variable-fonts`: `skrifa ^0.42`, `write-fonts ^0.48`, `kurbo` (index), which is **older fontations** than harfrust 0.14 | `skrifa 0.48`, `write-fonts 0.54`, `hashbrown`, `thiserror` (and `clap` only with `cli`) |
| Size | ~4.9 kLoC | ~30 kLoC |

Note: the crates.io crate named `klippa` (0.2.6, deps `geo-types`, `log`) is an **unrelated polygon-clipping crate**.
The fontations subsetter was renamed `klippa` → `skera` (git log `98e4fe13 "[subset] rename klippa to skera"`).

**Recommendation:** typst `subsetter` with `default-features = false` (no fontations dependency, so no version
skew) for static fonts, glyf and CFF. For variable fonts, enable `variable-fonts` only if the fontations versions line up
(they currently do not: read-fonts 0.39 vs 0.45). Otherwise instance by drawing outlines through skrifa into a
synthesized glyf subset, or embed Type3. This is a decision for the PDF-writer research doc. skera is a later option if it
gains CFF support. Typst's PDF stack (krilla) is the reference user of `subsetter`.

### 4.6 Font databases

- `fontdb 0.24.0`: pure Rust. `load_system_fonts()` scans fixed directories (`/usr/share/fonts/`, `/usr/local/share/fonts/`,
  `~/.fonts`, `~/.local/share/fonts`, `src/lib.rs:479–494`). With the `fontconfig` feature it **parses fontconfig XML
  in pure Rust** (`fontconfig-parser`) to get `<dir>` entries and generic aliases (`:505–585`), with no libfontconfig. It
  also vendors its own TrueType name/OS2 parser (`src/ttf_parser/`) and has `query(&Query)` CSS-like matching (`:663`).
  Directory traversal is unsorted `read_dir` (`:363`), so it is non-deterministic across filesystems. IDs are
  `slotmap` keys (insertion order).
- Typst wraps fontdb (`typst-kit/src/fonts.rs:168–199`) but also ships embedded fonts (`embedded()`, `:129–135`,
  feature `embedded-fonts`) and keeps fonts in insertion order in `FontBook`. Fallback is a coverage scan over all faces
  scored by similarity (`typst-library/src/text/font/book.rs:94–135`, `select_fallback`).
- fontique: see §2.9.

---

## 5. How Typst does inline text (v0.15.1)

Files: `crates/typst-layout/src/inline/{collect,prepare,shaping,linebreak,line,finalize,box,deco}.rs` (4579 lines).

1. **Collect** inline content into one string, with boxes and spacing as items (`collect.rs`). **Prepare** runs bidi (`unicode-bidi`) and
   shapes each bidi/script/style run once with rustybuzz (`prepare.rs`, `shaping.rs:786–1110`).
2. **Font fallback per segment** (`shaping.rs:900–990`): it iterates the style's families, takes the first font covering the text, then
   `book.select_fallback(like, variant, text)` if enabled. Uncovered parts are re-shaped recursively with the
   next font, and "tofus" are emitted when nothing covers the text. Families already used "with unlimited coverage" are excluded from re-use (`:853–857`).
3. **Reshape at line boundaries** (`shaping.rs:546–680`): `reshape(text_range)` reuses the glyph slice if both ends are
   `safe_to_break` (derived from `!info.unsafe_to_break()`, `:1101`). Otherwise it reshapes that substring. This is the
   standard HarfBuzz technique, and it is what parley lacks today.
4. **Breakpoints** (`linebreak.rs:693–782`): from ICU `LineSegmenter` (LSTM; a CJ-specific segmenter for zh/ja), plus
   `hyphenations()` via `hypher::hyphenate(word, lang)`. Breaks before Glue/WJ/ZWJ are filtered, and the
   `Breakpoint::Hyphen(l, r)` carries the character counts on each side (`:784–825`). There are special URL break rules (`linebreak_link`).
5. **Line breaking** (`linebreak.rs:151–160`): `Linebreaks::Simple` (greedy first-fit, `:163–208`) or `Linebreaks::Optimized`
   (Knuth–Plass, `:210–530`). The optimized mode first runs an approximate K-P on cumulative arrays to get an upper cost bound, then
   runs exact K-P with pruning. Cost (`:627–683`): `(1 + 100|r|³ + penalties)²`, with `DEFAULT_HYPH_COST = 135`, `DEFAULT_RUNT_COST = 100`,
   extra hyphen cost near word edges (+15% per char below 5), and an extra cost for consecutive dashes.
6. **Line building** (`line.rs`): trims, adds the hyphen glyph (`ShapedText::hyphen`, `:141–166`), repeats the hyphen at the next line start for some languages
   (`should_repeat_hyphen`), and justifies with stretch and shrink, including CJK.
7. **Width is a single `Abs` per paragraph** (`linebreak(engine, p, width)`, `:152`). Typst has no floats wrapping text, so
   there are no per-line widths. Page fragmentation happens later, in flow layout, by distributing finished line frames.

Lessons for recto: (a) shape once, reshape only the line edges using unsafe-to-break; (b) hyphenation and
K-P fit on top of a breakpoint stream; (c) K-P assumes known line widths, so with floats (width depends on y,
which depends on earlier line heights) recto should use greedy breaking (what browsers do) and offer K-P only
as an opt-in for paragraphs with no float interaction (`text-wrap: pretty`); (d) embedded fonts make output machine-independent.

---

## 6. Requirements check: parley as-is vs our own inline layout

| recto requirement (CSS) | parley 0.12 | Own IFC on harfrust + icu + unicode-bidi + hypher |
|---|---|---|
| Per-line available width (floats) | **Yes** (`set_line_max_advance`, `set_line_x`, `MaxHeightExceeded`, `CustomOutOfFlow` yields) | Must build. Parley's design is the template |
| Resumable / checkpointable breaking (pages, orphans/widows) | **Yes** (`BreakerState: Clone`, `revert_to`) | Must build (straightforward: the state is indices + x + a line-box accumulator) |
| Non-atomic inline boxes with padding/border/margin, split across lines, `box-decoration-break` | **No** (only atomic `InlineBox`). It could be emulated by zero-height inline boxes at span edges, but then the span's start/end edges are not tied to break decisions | Native: inline-start/end edges are items with widths that attach to the first/last fragment |
| `vertical-align`, line-height strut, CSS 2 §10.8 line box | **Yes** (0.12, `VerticalAlign`, strut via root span `reset_line` `line_break.rs:865–877`) | Must build (port the model) |
| `text-indent` incl. `each-line`/`hanging` | Yes | Build (trivial) |
| `::first-line` (restyle → different shaping on line 1) | No (one style set per Layout; needs a second Layout and re-break) | Build: reshape the first line's range with first-line styles, then re-measure |
| `white-space` modes, hanging spaces | Yes (TreeBuilder collapses; CSS Text 4 hanging) | Build (collapsing is done in recto's box-tree builder anyway) |
| Tab stops / `tab-size` | No (tab is just whitespace) | Build |
| Justification | Inter-word stretch only | Build: inter-word plus inter-character for CJK, `text-justify` |
| `hyphens: manual` (visible hyphen at SHY) | **No** | Build (hyphen glyph insertion + reshape) |
| `hyphens: auto` | **No** | hypher |
| `overflow-wrap`, `word-break`, `line-break` | Yes (ICU options + override table) | icu_segmenter options + emergency-break logic |
| Correct shaping across break (ligatures, Arabic joining, kerning) | **No** (breaks at atom boundaries without reshaping) | Reshape with `UNSAFE_TO_BREAK` |
| Bidi with inline boxes, `unicode-bidi`/`direction` per element | Base direction per layout; embedding controls via text | Build: insert isolates/embeddings per CSS `unicode-bidi` |
| Deterministic font discovery | No (read_dir order, global atomic IDs, libfontconfig on Linux) | Own DB with sorted scan and stable IDs |
| Static musl binary with system fonts | No with `system` (fontconfig FFI). Yes without `system` + `load_fonts_from_paths` | Yes |
| Glyph→text cluster map for ToUnicode/ActualText/tagged PDF | Yes (clusters with text ranges) | harfrust `GlyphInfo.cluster` |
| Dependency hygiene | Pins harfrust 0.12/read-fonts 0.41 (two versions behind). Breaking API every release | We choose versions. One fontations version |
| Effort | Integration of ~weeks, but blocked on hyphenation/reshape/inline-edges, which needs forking | Estimated 6–10 kLoC for the IFC (parley's line_break.rs is 2057 lines; Typst inline is 4579 lines) |

---

## Findings that affect recto's design

1. **Shaper = harfrust 0.14** (HarfBuzz 14.5.1 parity, 800/800 AOTS and 437/437 text-rendering tests; pure Rust, `no_std`, no HashMap,
   `forbid(unsafe_code)`). rustybuzz is archived, and swash's shaper is not HarfBuzz-conformant and caps skrifa at 0.44.
2. **Single fontations version** (read-fonts 0.45 / skrifa 0.48 / write-fonts 0.54) must be a hard rule enforced with
   `cargo deny`'s duplicate-version check. parley 0.12 (read-fonts 0.41), subsetter 0.2.6 with `variable-fonts` (0.39)
   and swash (≤ skrifa 0.44) all violate it today.
3. harfrust **errors on malformed fonts** instead of falling back. recto needs a cmap+hmtx nominal-glyph fallback
   shaping path and must log a warning, not fail the document.
4. **parley's resumable breaker (`BreakerState`, per-line width/x/y, `MaxHeightExceeded`, `CustomOutOfFlow`, `revert_to`) is
   the right architecture** for floats and fragmentation. Copy that design, not necessarily the code.
5. **parley cannot be used as-is.** Its missing pieces are blockers for documents: no reshaping at line breaks
   (`parley_engine/README.md`), no visible hyphen at U+00AD, no `hyphens:auto`, no inline padding/border/margin, no tab
   stops, no `::first-line`, Linux system fonts via libfontconfig FFI, non-deterministic font IDs and scan order, and pixel quantization by default.
   Fixing these means forking roughly half of `parley/src/layout` and pinning an older harfrust.
6. **Line-break opportunities: `icu_segmenter` 2.3** (CSS `line-break`/`word-break` map directly to `LineBreakOptions`).
   Default `new_for_non_complex_scripts` costs about 30 KB of line data and 12 KB of grapheme data. A `complex-scripts` cargo feature uses `new_lstm`
   (+621 KB). Never enable `dictionary/auto` (4.0 MB) or `extended` (2.07 MB) by default. `unicode-linebreak` (Unicode 15,
   untailorable, stale) is rejected.
7. Add a recto-side **break-override hook** like parley's `LineBreakOverrideFn` / Typst's CJ quote override, so we
   can match Chromium on known UAX#14 vs browser differences (parley ships `CHROMIUM_LINE_BREAK_OVERRIDE`).
8. **Bidi: `unicode-bidi` 0.3.18** (Unicode 16). Unicode versions may then differ between bidi (16) and ICU
   segmenter/properties (2.3 is newer). Document the versions, and pin everything for reproducibility.
9. **Hyphenation: hypher 0.1.8, `default-features = false`, explicit language list WITHOUT `slovak`.**
   `patterns/hyph-sk.tex` is GPL-2.0-or-later (lines 14–18) and is compiled into `tries/sk.bin` under the default `full`
   feature, which contradicts the README's "permissive" claim. All 48 languages take about 1.1 MiB, and an en+de+fr+es+it+nl+pt+pl set
   takes roughly 330 KiB (README table). The `hyphenation` crate is rejected: dormant, bincode is RUSTSEC-2025-0141, and it needs runtime deserialization.
10. Reshape at line edges using `UNSAFE_TO_BREAK` (Typst `reshape`, `shaping.rs:546–680`). Set
    `BufferFlags::PRODUCE_UNSAFE_TO_CONCAT` if we want to concatenate shaped pieces (e.g. after `::first-line` restyle).
11. **Line-breaking strategy:** greedy, CSS-conformant breaking by default (needed with floats, because width depends on y).
    Knuth–Plass (Typst cost model: `(1+100|r|³+penalties)²`, hyphen 135, runt 100) is an opt-in for `text-wrap: pretty`
    and only for paragraphs whose lines all have known widths (no float overlap). Fall back to greedy otherwise.
12. **Subsetting: typst `subsetter` 0.2.6 with `default-features = false`.** It handles glyf and CFF, requires CID-keyed
    embedding (GID=CID, recto writes its own ToUnicode), and has only `rustc-hash` as a dependency. The fontations
    `skera` 0.8 has **no CFF support**, and the crates.io `klippa` is an unrelated crate.
    Variable-font instancing for PDF remains an open item (subsetter's `variable-fonts` drags in old fontations).
13. **Vertical metrics:** use skrifa `Metrics` (USE_TYPO_METRICS → OS/2 typo, else hhea, else typo/win). This matches
    browsers for `line-height: normal`. Keep f32 in font units ×size, but accumulate block positions in f64 or fixed-point
    (parley notes f32 accumulation errors, `line_break.rs:604–606`). Consider integer layout units (e.g. 1/64 pt) for
    byte-determinism across platforms.
14. **No pixel quantization anywhere** in the PDF path (parley's `quantize` flag rounds metrics).
15. **Font discovery must not use fontconfig FFI.** Scan directories in pure Rust and optionally parse
    `/etc/fonts/fonts.conf` `<dir>` entries the way fontdb does (pure Rust, `fontconfig-parser`). Sort every directory listing.
    Without explicit opt-in (`--system-fonts`), recto should **not** read system fonts at all: secure-by-default and
    deterministic output.
16. **Determinism rules for the font DB:** stable face IDs are the index into a vector sorted by
    (source priority, canonical path bytes or @font-face order, face index). Do not use global atomic counters or HashMap
    iteration, so fallback order is fixed by configuration. Font identity in caches is a content hash (e.g. BLAKE3 of the bytes)
    rather than a path. The PDF subset tag is derived from that hash plus the glyph set.
17. **Bundled fonts:** the single static binary must render correctly in `scratch`. Bundle a small default
    set behind a cargo feature (default on): metric-compatible Liberation Sans/Serif/Mono (Arial/Times/Courier substitutes
    that invoice templates assume) and a symbol/emoji fallback (e.g. Noto Sans Symbols 2, monochrome). Offer an optional
    `fonts-cjk` feature (Noto Sans CJK, very large). Typst does the same (`typst-kit` `embedded()`). Exact sizes and license
    texts are **UNVERIFIED** here; they belong in the fonts/licensing research doc.
18. **WASM:** harfrust, skrifa, icu_segmenter (compiled data), unicode-bidi, hypher and subsetter are all `no_std`/wasm-capable.
    Keep filesystem scanning behind a `std`/`fs` feature, as fontdb and fontique do.

## Recommendation

### Stack

| Layer | Choice | Version | Feature flags |
|---|---|---|---|
| Font parsing, metrics, outlines, variations | skrifa / read-fonts | 0.48 / 0.45 | `std` |
| Shaping | harfrust | 0.14 | default (`std`); not `icu` (keeps one copy of Unicode data; harfrust has its own `src/unicode`) |
| Line-break opportunities, graphemes | icu_segmenter | 2.3 | `compiled_data`; `auto` only under recto feature `complex-scripts` (LSTM) |
| Unicode properties (script, gc, emoji, east-asian-width, line-break class) | icu_properties | 2.3 | `compiled_data` |
| Bidi | unicode-bidi | 0.3.18 | default |
| Hyphenation | hypher | 0.1.8 | `default-features = false, features = ["alloc", "english", "german", "french", "spanish", "italian", "dutch", "portuguese", "polish", "danish", "swedish", "norwegian", "finnish", "czech", …]` (**never `slovak`/`full`**) |
| Subsetting | subsetter | 0.2.6 | `default-features = false` |
| Optional system font config parsing | fontconfig-parser (as fontdb does) | ~0.5 (fontdb's dep, **UNVERIFIED** exact) | behind `system-fonts` |

### Inline layout: build recto's own IFC (`recto-inline`), modelled on parley's breaker and Typst's shaping

Do not depend on parley or cosmic-text. Build the inline formatting context in-house and borrow designs:

1. **Item stream (from the box tree):** text runs with computed style; inline-start/inline-end edges of
   non-atomic inline boxes (margin+border+padding widths, plus a reference to the box for background painting);
   atomic inlines (`InlineBox`-like: width, height, baseline, vertical-align); floats and abs-pos placeholders
   (yield points, like parley's `CustomOutOfFlow`); forced breaks; tabs. Text is concatenated into one paragraph
   string with object-replacement characters (U+FFFC) for atomics, as both parley and Typst do.
2. **Analysis:** bidi levels per paragraph (unicode-bidi, with CSS `unicode-bidi`/`direction` mapped to isolates/embeddings),
   script itemization (icu_properties Script + Script_Extensions), break opportunities (icu_segmenter with per-range
   `LineBreakOptions` from `line-break`/`word-break`), hyphenation opportunities (hypher, per `lang`, lazily per word, only if
   `hyphens:auto`), and SHY opportunities (`hyphens:manual`).
3. **Shaping:** itemize by (font after fallback, bidi level, script, language, size, features, variations, letter-spacing-disables-ligatures).
   Shape once with harfrust and a cached `ShapePlan`. Keep `GlyphInfo.cluster` and the unsafe-to-break flags.
4. **Font fallback:** per grapheme cluster, following CSS Fonts 4 §"Cluster matching" (`css-fonts-4/Overview.bs:4757`).
   Walk the `font-family` list. At each family, select the face via the §"Matching font styles" width → style → weight narrowing
   (`Overview.bs:4349–4600`; summarized under "Matching" in the Font database design below). Require full-cluster coverage, then base-char coverage,
   then the configured fallback chain (by script/lang), then bundled last-resort fonts, then .notdef. Cache per
   (family-list id, style, codepoint).
5. **Line breaker (greedy, resumable):** a parley-style `BreakerState` (cursor indices, x, line-box accumulator with
   strut / inline-box ascent+descent per CSS 2 §10.8, saved last-opportunity and emergency-opportunity states).
   Per line, the caller supplies `(x_offset, available_width)` from the float/exclusion manager at the current y.
   If the line's height grows past the band (`MaxHeightExceeded` equivalent), the caller moves the line down and retries.
   The state is `Clone` so fragmentation can checkpoint every line and re-break after a page or column width change.
   Orphans and widows are handled by the fragmentation layer by choosing among already-built line boxes (no re-break
   needed unless the width changes).
6. **Line finalization:** reshape the first and last clusters if they are unsafe-to-break at the line edge. Insert the hyphen glyph
   (`hyphenate-character` or the language default) and reshape the word fragment. Trim and hang whitespace (CSS Text 4).
   Apply bidi reordering per line (L2), text-indent, tab stops (measure to the next multiple of `tab-size` × space advance from the
   line start), `text-align`/`text-align-last` and justification (inter-word, and inter-character for CJK/`text-justify`).
   Then place inline box edges and backgrounds.
7. **Optional `text-wrap: pretty` / `balance`:** Typst-style Knuth–Plass over the breakpoint stream when all line widths
   are known up front. Greedy otherwise.
8. **Output to the painter:** glyph runs (font id, size, variations, synthesis, positioned glyph ids, cluster→text
   mapping for ToUnicode/ActualText), decoration spans, inline-box fragments with edges, and an f64/fixed-point block position.

Rough size: 6–10 kLoC (parley `line_break.rs` 2057 + `alignment`/`whitespace` ≈ 300 lines; Typst inline 4579 lines). The
expensive parts (shaping, segmentation, bidi, hyphenation data) are in mature crates.

### Font database design (`recto-fonts`)

- **Sources, in priority order:** (1) `@font-face` faces from the document (only from the allowed input dir or `data:` URIs; no network
  unless explicitly enabled). (2) User-configured font dirs (`--font-dir`). (3) Bundled fonts (compiled in, behind cargo
  features). (4) System fonts, only with `--system-fonts`: scan `/usr/share/fonts`, `/usr/local/share/fonts`, `~/.local/share/fonts`,
  `~/.fonts` and, optionally, `<dir>` entries parsed from `/etc/fonts/fonts.conf` (pure Rust). On macOS scan `/System/Library/Fonts`,
  `/Library/Fonts`, `~/Library/Fonts`; on Windows `%WINDIR%\Fonts` and `%LOCALAPPDATA%\Microsoft\Windows\Fonts`. No CoreText,
  DirectWrite or fontconfig FFI.
- **Scanning:** read files (no mmap by default, to avoid UB when files change; mmap could be a server-mode opt-in), sort directory
  entries by byte path, recurse with a depth limit, and accept `.ttf/.otf/.ttc/.otc` (and WOFF/WOFF2 for `@font-face`, decompressed
  in-process; WOFF2 needs a Brotli decoder, **UNVERIFIED** crate choice). Parse names with read-fonts: typographic family (ID 16) → family (ID 1),
  all localized names for matching (`localized-name-matching`, `Overview.bs:4286`), PostScript and full names for `local()`.
  Store width/style/weight ranges, from `fvar` axes when variable.
- **Identity and order:** `FaceId(u32)` = index into the final sorted face vector. Sort key: (source priority, family-name casefold,
  then for @font-face the declaration order, otherwise path bytes, then face index). Content hash per blob. Never use process-global
  counters or HashMap iteration in anything that affects output.
- **Matching:** implement CSS Fonts 4 §5 exactly. The family lookup checks `@font-face` families first, and a family defined by
  `@font-face` with no valid faces does **not** fall through to a platform font of the same name (`Overview.bs` step 3).
  Narrowing is width → style (italic/oblique tables incl. the 11deg threshold) → weight (400–500 special case) (`Overview.bs:4349–4600`).
  Composite faces apply `unicode-range` (step 4 note). Synthesis (bold via outline emboldening, oblique via shear)
  follows `font-synthesis`. Generic families map to a fixed, configurable table (no fontconfig alias resolution unless system
  fonts are enabled). Cluster matching follows `Overview.bs:4757+`.
- **Fallback chain:** a deterministic per-script list (configurable; defaults to bundled fonts), then a last-resort font that covers
  everything with visible .notdef boxes, and a warning in the report that lists uncovered code points.

## Open questions / UNVERIFIED items

1. Whether hashbrown 0.17's `default-hasher` (used by parley and fontique) seeds randomly per process: **UNVERIFIED**. It does not change the
   recommendation, since we do not adopt fontique.
2. fontique `fontconfig-dlopen` in a static-musl binary: assumed non-functional (static musl `dlopen` cannot load shared objects).
   **UNVERIFIED** by building, since builds are impossible in this environment.
3. Measured binary-size deltas (harfrust code size, icu compiled data actually linked, hypher subset) are **UNVERIFIED**. The figures
   above are data-payload sizes from `fingerprints.csv` and the hypher README, not linked-binary measurements. Measure in Phase 1 with
   `cargo bloat`.
4. Whether `unicode-bidi` 0.3.18 can take BidiClass from icu_properties 2.3 (the `icu_properties` optional dep `unicode-bidi`
   suggests an integration) to unify the Unicode version: **UNVERIFIED**.
5. Variable-font embedding in PDF: subsetter's `variable-fonts` instancing pulls skrifa 0.42/write-fonts 0.48 (version skew).
   Options: wait for subsetter to bump, use skera once it supports CFF2/instancing, or instance glyf ourselves via
   skrifa outlines. Defer to the PDF-writer research doc.
6. The hyphenation crate's exact API names were not read (it is rejected anyway).
7. Chrome adopting harfrust/skrifa (marketing claim in the ecosystem): **UNVERIFIED**, and irrelevant to the decision.
8. Bundled font selection, sizes and licenses (Liberation is OFL-1.1? Noto is OFL-1.1) need verification in a separate doc. **UNVERIFIED**.
9. WOFF2 decoding crate choice (Brotli, pure Rust) is not researched here.
10. Blitz (linebender) uses parley's `CustomOutOfFlow` for CSS floats in production: inferred from the `inline_box.rs` docs, **UNVERIFIED**.
11. ICU4X data sizes were read at icu4x HEAD `bb3e1f9` (workspace version 2.3.0). The 2.3.0 release data could differ slightly.
