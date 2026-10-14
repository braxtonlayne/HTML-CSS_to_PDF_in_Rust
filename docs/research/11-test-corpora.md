# 11 — Test corpora and golden-reference strategy

Date: 2026-10-14 · Topic slug: `testcorpora` · Author: Phase-0 research agent

Scope: concrete corpora recto can test against (WPT, WeasyPrint, paged-media engines, real-world templates, fuzzing seeds), and how to produce/compare golden references for a PDF-emitting engine deterministically in CI. All counts below were computed from the clones listed here (scripts in `/tmp/claude-0/src/testcorpora/scripts/`); they are heuristic file scans, not `wpt manifest` output, so expect ±5 %.

## Sources inspected

| Name | Version / tag | Commit SHA (HEAD inspected) | License | Last commit | Maintenance |
|---|---|---|---|---|---|
| web-platform-tests/wpt (sparse) | master | `80d213ac479dcf94dcfe21b75cf279633e89a7ac` | BSD-3-Clause (`LICENSE.md`) | 2026-10-14 | very active |
| Kozea/WeasyPrint | 70.0 (`weasyprint/__init__.py` VERSION) | `3c5f1ceb0cf10ec10542a05a3eb3d49b25067e54` | BSD-3-Clause (`LICENSE`) | 2026-10-14 | active |
| pagedjs/pagedjs | 0.5.0-beta.2 (`package.json`) | `677cdc1e537365e1b3c03c550e2463360164d3fc` | MIT (`LICENSE.md`) | 2026-10-06 | active |
| vivliostyle/vivliostyle.js | core 2.45.2 | `7646a9e488d4c610e62b472feacbfd3d4d79fdf4` | AGPL-3.0 (`LICENSE`) | 2026-10-14 | active |
| danfickle/openhtmltopdf | (last upstream) | `780ba564839f1ad5abfa5df12e4aebb9dd6782d2` | LGPL-2.1+ (`LICENSE`) | 2022-04-01 | abandoned upstream |
| openhtmltopdf/openhtmltopdf (maintained fork, sparse) | — | `7853e9328e32e7322da64bd38f30ad52392a205f` | LGPL-2.1+ | 2026-10-09 | active |
| zopyx/print-css-rocks | — | `7d97ac55e6d7095f08981b444f69cac4856e92bf` | **no repo license file** (fonts OFL) | 2026-06-30 | slow |
| html5lib/html5lib-tests | — | `c777c408b61078ea2eb4acefc2535f54dbc8b28a` | MIT (`LICENSE`) | 2026-10-01 | maintained (tree tests moved to WPT) |
| linebender/resvg | 0.48.1 (`crates/resvg/Cargo.toml`) | `77b12f4951a7b75d759c42e8c9497cff7c839c3c` | Apache-2.0 OR MIT | 2026-10-09 | active |
| LaurenzV/hayro | 0.8.0 (index: latest 0.8.0) | `9c58d13a608d603856800a3c9d6b9e821f85d1d0` | Apache-2.0 OR MIT | 2026-10-14 | very active, self-described "experimental" |
| DioxusLabs/blitz (sparse `wpt/`) | — | `e72650a6e67941852fddf025295cfee30c39ea32` | Apache-2.0 OR MIT (workspace) | 2026-10-13 | active (precedent: Rust WPT runner) |
| harfbuzz/harfbuzz (sparse `test/`) | — | `9df939b153d88956a22dfb30a9868d1ffebf696f` | MIT-style "Old MIT" (`COPYING`) | 2026-10-13 | very active |
| googlefonts/fontations (sparse `fuzz/`) | — | `cbb2f9240c350829448d4e5d6feba7439a43d461` | Apache-2.0 OR MIT | 2026-10-13 | very active |
| image-rs/image (sparse `tests/images`) | — | `075e65d618a323e5cb48c1d8710a2eca25d690c6` | Apache-2.0 OR MIT | 2026-09-15 | active |
| image-rs/image-png (sparse `tests`) | — | `b2f10c6a7e3127d4aaf231f3eae731a33e6eb0bc` | Apache-2.0 OR MIT; PngSuite own license | 2026-09-23 | active |
| kornelski/dssim | 3.5.1 | `0e44c9b7fe91a5265c8e463436c28512186fe9cd` | **AGPL-3.0** (`Cargo.toml`) | 2026-09-24 | active |
| ChrisRega/image-compare | 0.5.0 | `1bcd98373007f8eb6c89974fb0695f44268cffc3` | MIT | 2025-08-18 | slow |
| jihchi/dify | 0.8.0 | `0e5f1fa546d7cd134cbb12cb019f337d36a3a053` | MIT | 2026-01-04 | slow |
| ajrcarey/pdfium-render | 0.9.4 | `ea2961cb8ac777bb1a06dddb8efd272d34d74f18` | MIT OR Apache-2.0 (needs external pdfium lib) | 2026-10-08 | active |
| messense/mupdf-rs | 0.8.0 | `537d50556ee8e4abf2435f81357dfef3c145d883` | **AGPL-3.0** | 2026-09-14 | active |
| veraPDF/veraPDF-library | — | `79f7c2d712b44bccbccc9fe67d5668d9ce058ae9` | GPL-3.0+ / MPL-2.0 dual (`LICENSE.GPL`, `LICENSE.MPL`) | 2026-10-12 | active (Java) |
| veraPDF/veraPDF-corpus | — | `bb75f4f0073d9350dfd058c0162a367e6fadf25e` | CC-BY-4.0 (`README.md`) | 2026-09-16 | active |
| qpdf/qpdf | — | `4eba95899886e851cc41d76886483b347612f2a8` | Apache-2.0 (`LICENSE.txt`) | 2026-09-26 | active (C++) |
| pdfcpu/pdfcpu | — | `b41a41d5323f6119ff6a183ad3f287eb4a20a617` | Apache-2.0 (`LICENSE.txt`) | 2026-10-11 | active (Go) |
| poppler `pdftoppm` (local binary) | 24.02.0 | — | GPL-2/3 | — | system tool |
| Real-world templates (18 repos) | see §4 table | SHAs in §4 | mixed | — | — |

crates.io index (2026-10-14): `hayro 0.8.0` (MSRV 1.92), `pdfium-render 0.9.4`, `mupdf 0.8.0`, `dssim 3.5.1`, `image-compare 0.5.0`, `dify 0.8.0`, `lopdf 0.45.0`, `insta 1.49.0`, `libtest-mimic 0.8.2`, `datatest-stable 0.3.3`, `resvg 0.48.1`, `vello_cpu 0.3.0`, `tiny-skia 0.12.0`, `image 0.25.10`, `html5ever 0.40.1`, `oxipng 10.2.1`, `qpdf 0.3.7` (bindings), `pdf-extract 0.12.1`, `pdf_oxide 0.3.78`.

---

## 1. Web Platform Tests

### 1.1 How WPT defines reftests / print reftests (verified in docs + runner source)

- **Reftest**: test file contains `<link rel="match"|"mismatch" href=...>`; passes if test and reference render pixel-identical "within a 800x600 window" (`docs/writing-tests/reftests.md` ~L20–30). `class="reftest-wait"` on root delays the screenshot until JS removes it (reftests.md L74–94) — irrelevant/unsupportable for recto (no JS) → such tests are SKIP.
- **Fuzzy**: `<meta name=fuzzy content="maxDifference=A-B;totalPixels=C-D">`, names optional, ranges inclusive, optional `ref-url:` prefix per reference (reftests.md L100–160). `maxDifference` = max abs per-channel delta over R,G,B; `totalPixels` = count of differing pixels. For print reftests "any fuzzy specifier applies to each image comparison performed i.e. separately for each page" (`docs/writing-tests/print-reftests.md`).
- **Print reftest**: filename has `-print` immediately before the extension (`bar-print.html`, **not** `bar-print-001.html`), or file lives under a directory named `print` (`print-reftests.md`). Default page box **12.7 cm × 7.62 cm (5in × 3in), margin 12.7 mm (0.5in)**. Output is paginated and compared page by page; `<meta name=reftest-pages content="-2,4,6-">` restricts pages.
- **How the official runner does print reftests** (`tools/wptrunner/wptrunner/executors/executorwebdriver.py` L540–560 `render_as_pdf`, L1460–1500 `WebDriverPrintRefTestExecutor._render`): WebDriver `print()` with page width/height and 0.5in margins, `background=True`, `shrink_to_fit=False` → base64 PDF → `print_pdf_runner.html` renders each page with **pdf.js at scale 96/72** onto a canvas → PNG per page → compared like screenshots. Both test and reference go through PDF. **This is exactly the pipeline a PDF-only engine needs** — the official semantics already are "render to PDF, rasterize at 96 dpi, compare".
- Test enumeration: `docs/running-tests/custom-runner.md` strongly recommends using `wpt manifest` (MANIFEST.json) as the canonical test-type classifier rather than re-implementing the rules. Vivliostyle downloads the prebuilt manifest from the latest WPT GitHub release (`vivliostyle.js/scripts/download-wpt-manifest.mjs` L87: `api.github.com/repos/web-platform-tests/wpt/releases/latest`).
- Expectations: wptrunner uses per-test `.ini` metadata (`tools/wptrunner/wptrunner/manifestexpected.py`: `expected` list prop L309, `fuzzy` prop L123/L305) — `[test.html]\n  expected: FAIL`. recto does not need wptrunner itself; mimic the format or use a flat TOML (see §1.5).
- **Ahem**: most layout tests rely on `/fonts/ahem.css` → `fonts/Ahem.ttf` (`docs/writing-tests/ahem.md`): square em, ascent+descent = 1em, baseline 0.8em, `X` = full em box, `p`/`É` partial boxes. recto's test harness MUST resolve `/fonts/…` absolute URLs to the WPT checkout root (a per-test "document root" mapping, which also exercises recto's file-access sandbox: root = WPT checkout).

### 1.2 Counts per directory (scan of the sparse checkout)

Columns: test files (excluding `-ref`/`-notref`, `reference/`, `support/`, `resources/`), reftests (has `rel=match|mismatch`), print-reftests (WPT naming rule), reftests whose test file has no `<script>` at all, testharness.js tests (JS; unusable without a JS engine, but see §1.4), visual (neither — old CSS2.1 "self-describing" tests), `flags=paged`, inline fuzzy meta, Ahem use.

| dir | files | reftests | print-reftests | reftests w/o `<script>` | testharness | visual | paged flag | fuzzy | Ahem |
|---|---|---|---|---|---|---|---|---|---|
| css/css-page | 278 | 224 | 217 | 217 | 23 | 31 | 20 | 0 | 13 |
| ↳ css-page/margin-boxes | 38 | 38 | 37 | 36 | 0 | 0 | 0 | 0 | 11 |
| css/css-break | 1268 | 1103 | 64 | 1070 | 48 | 117 | 6 | 6 | 25 |
| ↳ css-break/table | 164 | 135 | 13 | 133 | 8 | 21 | 0 | 1 | 0 |
| ↳ css-break/flexbox | 330 | 318 | 27 | 317 | 0 | 12 | 0 | 0 | 4 |
| ↳ css-break/grid | 188 | 183 | 1 | 180 | 0 | 5 | 0 | 0 | 0 |
| css/css-gcpm | 20 | 0 | 0 | 0 | 0 | 20 | 20 | 0 | 0 |
| css/css-multicol | 723 | 468 | 4 | 405 | 94 | 161 | 1 | 1 | 133 |
| css/css-tables | 345 | 170 | 4 | 140 | 137 | 38 | 2 | 2 | 10 |
| css/css-text | 1918 | 1491 | 0 | 1384 | 366 | 61 | 0 | 7 | 598 |
| css/css-fonts | 566 | 378 | 2 | 339 | 172 | 16 | 0 | 3 | 53 |
| css/css-flexbox | 1454 | 1013 | 3 | 947 | 376 | 65 | 13 | 18 | 46 |
| css/css-content | 78 | 63 | 0 | 52 | 9 | 6 | 0 | 3 | 1 |
| css/css-lists | 227 | 171 | 0 | 143 | 37 | 19 | 0 | 3 | 2 |
| css/css-counter-styles | 263 | 248 | 0 | 224 | 11 | 4 | 0 | 3 | 6 |
| css/css-position | 389 | 251 | 3 | 132 | 115 | 23 | 0 | 3 | 43 |
| css/printing | 32 | 32 | 26 | 25 | 0 | 0 | 0 | 1 | 0 |
| css/CSS2/pagination | 103 | 43 | 43 | 43 | 0 | 60 | 102 | 0 | 0 |
| css/CSS2/page-box | 36 | 0 | 0 | 0 | 0 | 36 | 36 | 0 | 0 |
| css/CSS2/floats | 145 | 108 | 0 | 100 | 18 | 19 | 0 | 0 | 0 |
| css/CSS2/margin-padding-clear | 739 | 682 | 0 | 682 | 0 | 57 | 1 | 0 | 125 |
| css/CSS2/normal-flow | 858 | 747 | 0 | 694 | 24 | 87 | 0 | 1 | 116 |
| css/CSS2/linebox | 250 | 191 | 0 | 191 | 7 | 52 | 0 | 0 | 140 |
| css/CSS2/tables | 1139 | 372 | 0 | 250 | 2 | 765 | 2 | 0 | 19 |
| css/CSS2/visudet | 40 | 38 | 0 | 37 | 0 | 2 | 0 | 1 | 0 |
| css/CSS2/visuren | 57 | 34 | 0 | 26 | 0 | 23 | 0 | 0 | 2 |
| css/CSS2/generated-content | 316 | 226 | 0 | 205 | 0 | 90 | 0 | 0 | 0 |
| css/CSS2/text | 570 | 409 | 0 | 387 | 0 | 161 | 0 | 0 | 308 |
| css/CSS2/fonts | 324 | 160 | 0 | 159 | 0 | 164 | 0 | 0 | 89 |
| css/CSS2/backgrounds | 625 | 339 | 0 | 336 | 0 | 286 | 1 | 4 | 8 |
| css/CSS2/borders | 762 | 506 | 0 | 504 | 1 | 255 | 0 | 0 | 53 |
| css/CSS2/positioning | 578 | 520 | 0 | 513 | 8 | 50 | 4 | 0 | 70 |
| css/CSS2/abspos | 33 | 29 | 0 | 25 | 4 | 0 | 0 | 0 | 0 |
| css/CSS2/box-display | 139 | 120 | 0 | 86 | 0 | 19 | 2 | 0 | 59 |
| css/CSS2/lists | 286 | 156 | 0 | 155 | 0 | 130 | 0 | 0 | 1 |
| css/CSS2/colors | 22 | 19 | 0 | 19 | 0 | 3 | 0 | 0 | 2 |
| `print/` (top level) | crashtests only | 0 | — | — | — | — | — | — | — |
| infrastructure/reftest | 49 files | runner self-tests incl. `reftest_match-print.html`, `reftest_mismatch-num-pages-print.html`, `reftest_mismatch_page_margins-print.html`, `reftest_fuzzy_1.html` | | | | | | | |

Whole-repo print reftests (`git ls-tree`, `-print.<ext>` non-ref): **425**, of which 26 are `*crash*-print`: css/css-page 225, css/css-break 64, css/CSS2/pagination 43, css/printing 26, html/rendering 9, infrastructure/reftest 8, css/css-cascade 7, svg/layout 6, css/css-multicol 5, css/css-tables 4, others ≤3.

Print-reftest families in css/css-page (count): monolithic-overflow 31, page-size 14, margin-boxes/dimensions 14, margin-boxes/content 13, page-box 12, fixedpos 11, page-name-propagated 9, page-margin 8, page-background 6, page-name-siblings 5, basic-pagination 5, pseudo-first-margin 4, page-name-{orthogonal-writing,img,flex,canvas,and-break} 4 each, layers 4, body-background 4, page-orientation-* 5, page-rule-specificity 3, media-queries 3, margin-boxes/{paint-order,auto-margins} 3 each, page-left-right 2, …

**Critical structural fact**: of 1101 css-break reftests, **1036 (94 %) use multicol (`column-count`/`column-width`/`columns`) as the fragmentainer**; only 62 are print reftests and 3 are neither (`scripts/dep.py`). Same for css-break/table: 122/135 via multicol. So recto's fragmentation code only becomes testable against css-break if multicol columns and pages share one fragmentainer abstraction.

css-gcpm (20), CSS2/page-box (36) and 60 of CSS2/pagination are old `flags=paged` **visual** tests without references (self-describing "you should see…"): usable only as human-verified golden images in recto's own snapshot store.

### 1.3 Running WPT reftests in a non-browser engine

Pipeline per (test, reference) pair, mirroring wptrunner's print path:

1. Parse test → find `rel=match|mismatch` (may chain: references can themselves have `rel=match`; wptrunner handles chains — follow at most N levels), `meta name=fuzzy`, `meta name=reftest-pages`, `class="reftest-wait"` (→ SKIP), `<script>` (→ SKIP unless it's only a no-op like `testharness`-less helper; simplest: SKIP if any `<script>` other than known inert ones).
2. Render **both** with recto to PDF:
   - print reftest: page size 5in×3in, margins 0.5in unless the test's `@page` overrides (equivalent to WebDriver `print(page={w,h}, margin=0.5in)`).
   - screen reftest: one page of 800×600 CSS px, margin 0, background painted, no pagination (`--page-size 800px 600px --margin 0` and "don't fragment" or very tall page cropped to 600px). Note that WPT screen reftests assume the viewport is the ICB (800×600) — recto needs a "viewport = page area" mode; tests that overflow 600px compare only the visible 800×600 area.
3. Rasterize each PDF page at **96 dpi** (scale 96/72, same as `print_pdf_runner.html`), sRGB, opaque white background, in-process (hayro) — see §6.
4. Compare page count first (mismatch ⇒ FAIL; this is what `reftest_mismatch-num-pages-print.html` exercises), then per page: compute (maxDifference, differingPixels); PASS for `match` iff within fuzzy ranges (default exact 0;0), for `mismatch` iff outside.
5. Emit status PASS/FAIL/SKIP/CRASH/TIMEOUT; on FAIL write test/ref/diff PNG triptych.

Because test **and** reference go through the same rasterizer, rasterizer anti-aliasing artefacts cancel unless geometry differs — so the rasterizer need not be "correct", only deterministic and consistent. This is why WPT tolerates pdf.js.

Precedent in Rust: Blitz's runner (`blitz/wpt/runner/src/test_runners/`): `fuzzy.rs` parses `<meta name=fuzzy>` (regex + `FuzzyRange`, tests at L148–189) and `fuzzy_buffer_diff` (L114) computes `(max_difference, differing_pixels)`; `ref_test.rs` L186–204 uses fuzzy when declared, else `dify::diff::get_results(..., 0.1, true, …)` (pixelmatch-style YIQ threshold). Caveat: Blitz checks only the upper bound of fuzzy ranges (L193–194); WPT says ranges are inclusive both ends. `wpt/runner/timeout-quarantine.txt` is their skip list with a reason column (`css/... animation-events`). Vivliostyle also runs WPT reftests (`scripts/layout-regression.mjs` mode `wpt-reftest`, `--wpt-path-prefix css/css-break/`, uses `pixelmatch`, fuzzy metadata handling L156–224) and has a triage YAML (`scripts/layout-regression-triage.yaml`).

testharness.js tests: ~1,900 in the selected dirs; all need JS (`getComputedStyle`, `offsetTop`, `check-layout-th.js`). Not runnable. Some `check-layout-th.js` tests (`data-expected-width/height/offset-x/y` attributes, common in css-flexbox/css-tables) could be converted mechanically to layout-tree assertions via recto's debug box-tree dump (**UNVERIFIED** count; grep `data-expected-` to size it in M2).

### 1.4 Proposed curated WPT subsets per milestone

Approximate counts are reftests without `<script>`; expect 20–40 % SKIP after manual triage (Ahem baseline issues, writing-modes, `vertical-*`, ruby, form controls, tentative).

| Milestone | Globs | ≈ tests | Why |
|---|---|---|---|
| M1 block/inline/box | `css/CSS2/normal-flow/**`, `css/CSS2/margin-padding-clear/**`, `css/CSS2/visudet/**`, `css/CSS2/visuren/**`, `css/CSS2/box-display/**`, `css/CSS2/borders/**`, `css/CSS2/backgrounds/**`, `css/CSS2/colors/**` (exclude `*-vrl-*`, `*-vlr-*`, `*-v{l,r}r*`, `*tentative*`) | ~2,500 | core box model, cheap, mostly Ahem |
| M1 text basics | `css/CSS2/linebox/**`, `css/CSS2/text/**`, `css/CSS2/fonts/**` | ~740 | line boxes, text-indent/align, font shorthand |
| M2 floats/positioning | `css/CSS2/floats/**`, `css/CSS2/floats-clear/**`, `css/CSS2/positioning/**`, `css/CSS2/abspos/**`, `css/css-position/**` (excl. `sticky`, `position-fallback`, `anchor`) | ~800 | |
| M2 generated content/lists | `css/CSS2/generated-content/**`, `css/CSS2/lists/**`, `css/css-lists/**`, `css/css-content/**`, `css/css-counter-styles/**` | ~780 | counters → page counters & target-counter later |
| M3 tables | `css/CSS2/tables/**` (reftests only), `css/css-tables/**` (reftests only) | ~390 | invoices are tables |
| M3 paged media (core for recto) | `css/css-page/**/*-print.*`, `css/css-page/margin-boxes/**`, `css/CSS2/pagination/*-print.*`, `css/printing/*-print.*` (excl. `*crash*`, `animation*`, `input-*`, `select-*`), `infrastructure/reftest/*-print.html` | ~300 | the headline feature; must be ≥ 90 % PASS for v1 |
| M3 fragmentation (print only) | `css/css-break/**/*-print.*`, `css/css-break/table/*-print.*`, `css/css-break/flexbox/*-print.*` | ~64 | breaks, orphans/widows in pages |
| M4 flex | `css/css-flexbox/**` (reftests, excl. `*-vert-*`, `*-vlr*`, `*-vrl*`, `align-content-*` with scripts) | ~950 | |
| M4 fragmentation via multicol | `css/css-break/**` (non-print) + `css/css-multicol/**` | ~1,500 | only once multicol shares fragmentainer engine |
| M5 text/fonts deep | `css/css-text/**`, `css/css-fonts/**` (excl. `font-loading`, `variations/*` until supported) | ~1,700 | i18n, white-space, line-break, hyphens |
| GCPM (golden-image only) | `css/css-gcpm/*.html`, `css/CSS2/page-box/*`, `css/CSS2/pagination/` visual tests | ~116 | no refs; snapshot after manual verification |
| HTML parser | `html/syntax/parsing/resources/*.dat` (62 files, **1,968** `#data` cases) | 1,968 | tree-construction (moved here from html5lib-tests) |

### 1.5 Expectations manifest

Store in-repo `tests/wpt/expectations.toml` (one entry per non-PASS test; absent = PASS expected), plus `tests/wpt/WPT_COMMIT` (pin like Blitz `wpt/WPT_COMMIT` = `cd1d8aa5bfeb…`) and `tests/wpt/include.toml` (the globs above).

```toml
# status ∈ PASS | FAIL | SKIP | CRASH | TIMEOUT; reason required for SKIP/FAIL
["css/css-page/margin-boxes/content-001-print.html"]
status = "FAIL"
reason = "margin box auto-sizing (css-page-3 §6.3.2) not implemented"
bug = "recto#123"

["css/css-break/widows-orphans-005.html"]
status = "SKIP"
reason = "multicol fragmentainer"
```

Rules: CI fails on *unexpected* results in either direction (FAIL→PASS forces the file to be updated, like wptrunner "unexpected PASS"); a `--update-expectations` flag rewrites the file; an optional per-test `fuzzy = "0-2;0-40"` override (wptrunner's `.ini` supports `fuzzy` too). Totals per directory are written to `tests/wpt/summary.json` to chart progress.

---

## 2. WeasyPrint test suite

License: **BSD-3-Clause**, `LICENSE` (“Copyright (c) 2011-2021, Simon Sapin and contributors”) — compatible with recto (MIT/Apache) provided the copyright notice + disclaimer are retained in ported tests (keep a `tests/ported/weasyprint/LICENSE` and per-file attribution).

### 2.1 Structure (`tests/`) and counts (`^def test_` functions; 275 `@pytest.mark.parametrize` decorators expand this considerably)

| path | test fns | style |
|---|---|---|
| `tests/test_api.py` | 68 | Python API, CLI, `write_png` with `resolution=192` etc. — not portable |
| `tests/test_boxes.py` | 49 | box-tree construction (anonymous boxes, table fix-up) |
| `tests/test_pdf.py` | 56 | PDF structure: bookmarks_1..15, links, relative links, anchors, embedded images/attachments, metadata/RDF, PDF/A attachments, ICC output intent, **tags** (`test_pdf_tags_inline_table`, `…_split_table_with_caption`, `…_nested_lists_order`, `…_table_headers`), forms, `test_pdf_ua_2_namespace_type`, bleed |
| `tests/test_text.py` | 78 | line breaking, hyphenation, letter/word-spacing, text-indent, tab-size (via `render_pages`) |
| `tests/test_fonts.py`, `test_unicode.py`, `test_url.py`, `test_html.py`, `test_stacking.py`, `test_acid2.py` | 8+1+2+22+3+1 | |
| `tests/css/` (14 files) | 251 | parsing/validation/expanders (81 in `test_validation.py`, 46 expanders), counters 25, variables 39, math 20, target 8, pages 3, layers, nesting |
| `tests/layout/` (16 files) | 569 | `render_pages()` then assert box positions: block 35, column 40, flex 103, float 37, footnotes 25, grid 54, image 24, inline 48, page 57, position 21, table 109, … |
| `tests/draw/` (24 files) | 393 | `assert_pixels`: absolute 25, background 24, box 41, column 4, float 35, footnote 11+10, gradient 28, image 34, leader 18, note 14, table 41, text 49, transform 14, whitespace 9, … |
| `tests/draw/svg/` (13 files) | 212 | SVG painting via assert_pixels |
| **total** | **1,714** | |

Resources (`tests/resources/`): `weasyprint.otf/.woff/.otb` (custom test font, Ahem-like), `tests_ua.css` (minimal UA sheet: `@font-face { src: url(weasyprint.otf); font-family: weasyprint }`, `body { orphans: 1; widows: 1 }`, bookmark-level for h1–h5), `pattern.png/.gif/.svg`, `blue.jpg`, `cmyk*.jpg`, `cmyk.icc`, `acid2-test.html` + reference, `really-a-png.svg`/`really-a-svg.png` (content sniffing), `dangerous.eps`, `doc1.html` (+UTF-16BE variant), `latin1-test.css`/`utf8-test.css` (charset), `mini_ua.css`, `user.css`.

### 2.2 The `assert_pixels` approach (verified)

- `tests/draw/__init__.py` L14 `PIXELS_BY_CHAR`: `_` white, `R` red, `B` blue, `G` lime, `K` black, `V` (191,0,64) etc. (and lowercase blends such as `s` = 50 % red on white, `a` = red after lossy JPEG); `z` = don't-care (None).
- `parse_pixels` (L41) strips `#` comments, requires equal line widths, maps chars → RGB. `assert_pixels(name, expected, html)` (L52) renders HTML and checks size, then pixels; on failure writes `results/<name>.png` and `<name>.expected.png`.
- Tests use tiny pages: e.g. `test_float.py`: `@page { size: 10px 5px }` and a 10×5 char grid; `test_page.py::test_nth_page` uses `@page { size: 1px 1px }` and 10 pages, each page = one pixel row (`'_R_R_R_R_R'`). Multi-page output is stacked vertically (`conftest.py` concatenates per-page PNGs).
- **Rasterization** (`tests/conftest.py` `document_write_png`, top of file): writes PDF with `zoom=4/30`, then Ghostscript `gs -sDEVICE=png16m -dTextAlphaBits=1 -dGraphicsAlphaBits=1 -r{96/zoom} -dUsePDFX3Profile` (i.e. **anti-aliasing off**, 720 dpi of a 4/30-scaled PDF ⇒ exactly 1 CSS px = 1 device pixel). Docstring notes Ghostscript is AGPL. `FakeHTML.write_pdf` forces `uncompressed_pdf=True` (testing_utils.py L45–60).
- Why it works: geometry is chosen on integer px with solid colours and AA off, so exact equality is achievable across machines. Colours are pure primaries so a human can read the expected grid.

### 2.3 What to port and how

- **Draw tests (605 incl. SVG)** → recto `assert_pixels!` macro with identical char grid semantics. Port mechanically: a script parses the Python AST for `assert_pixels('''grid''', '''html''')` literals (plus parametrize tuples) and emits `tests/ported/weasyprint/draw/<file>/<test>.toml` `{ html, pixels, source = "WeasyPrint 3c5f1ce tests/draw/test_float.py::test_float" }`. Needs: (a) recto UA test stylesheet equivalent to `tests_ua.css`; (b) `weasyprint.otf` test font (BSD, bundled with the test, not the binary); (c) rasterizer with AA disabled (hayro: **UNVERIFIED** whether it has an AA-off switch; alternative: render at 8× and box-downsample + threshold, or pick test colours so AA edges fall on pixel boundaries — integer geometry means no partial coverage except for text/curves).
- **Layout tests (569)** assert `position_x/y`, `width`, `height`, children structure on WeasyPrint's box tree. Portable as **data**, not code: extract HTML + expected numbers into recto's layout-dump assertions (`recto debug --dump-layout json`), mapping WeasyPrint box kinds (BlockBox/LineBox/TextBox/TableCellBox) to recto fragments. Semi-manual (asserts are arbitrary Python); start with `layout/test_page.py` (57), `test_table.py` (109), `test_float.py` (37), `test_block.py` (35), `test_footnotes.py` (25), `test_column.py` (40).
- **test_pdf.py (56)**: port as PDF-structure tests (bookmarks outline tree, link annotations/rects, named dests, `/StructTreeRoot` shape for tables/lists, metadata). Use `lopdf` to inspect.
- `css/` parsing tests are mostly WeasyPrint-API-specific; the expanders/validation cases are useful as data for recto's CSS parser (shorthand expansion expected outputs).
- Not portable: `test_api.py`, logging-based assertions, font-config specifics, Pango-specific line-breaking results (ICU/Pango differences) — treat text-position expectations as approximate.

---

## 3. Other paged-media corpora

| Corpus | Location | Size | License | Format of expectation | Usefulness for recto |
|---|---|---|---|---|---|
| **Paged.js specs** | `pagedjs/specs/` | 34 dirs, 123 HTML, 110 `*.spec.js`, 233 PNG snapshots (`__image_snapshots__`) | MIT | Jest+Puppeteer; DOM assertions (e.g. `named-page.spec.js`: "should render 8 pages", page N has class `pagedjs_chapter_page`) + image snapshots of Chrome output | HTML inputs + **page counts** + "which page gets named page X" are directly portable assertions; PNGs are Chrome+paged.js renders → loose reference only. Dirs: breaks (20 html, 70 png), named-page 11, notes 11, splits 7, string 7, target 7, page-rules 6, page-selector 6, counters 5, tables 5, margin-boxes 4, widows-orphans, position-fixed, generate-content, bleed/marks/custom-bleeds |
| **Vivliostyle test files** | `packages/core/test/files/` | 190 entries, 453 HTML/XHTML, `file-list.js` with 442 `file:` entries (categories, `skipLayoutRegression`) | **AGPL-3.0** | layout-regression screenshots via Playwright+pixelmatch (`scripts/layout-regression.mjs`) | Do **not** vendor. Run from an external checkout in an optional CI job. Relevant files: `named-pages/`, `named-strings/`, `running-elements/`, `page_floats/`, `page_breaks/`, `footnotes/`, `nth-page/`, `target-counter-*.html`, `content-in-page-margin-box.html`, `counters-function-in-page-margin-box.html`, `crop-marks.html`, `page-size-math-functions.html`, `page-margin-box-images.html` |
| **openhtmltopdf visualtest** | `openhtmltopdf-examples/src/main/resources/visualtest/{html,expected}` | upstream 188 html / 154 expected PDFs; maintained fork 246 / 210 | LGPL-2.1+ (repo) (+ `LICENSE-W3C-TEST` for imported W3C tests) | expected **PDFs** produced by openhtmltopdf, compared with pdfcompare/PDFBox rasterization (`visualtest/VisualTester.java`) | Excellent paged-media regression topics: `running-*` (9), `page-margins-*` (5), `horiz-page-overflow-*` (10), `footnote/issue-364-*` (18), `issue-551-page-break-avoid-*`, `issue-771-leader-function`, `issue-792-target-counter-style`, `text/content-toc-example.html`, `text/content-page-numbers.html`, `bookmark-*` (6), `replaced-*-page-break-inside-{allow,avoid}`, `table-*`, **security**: `external-access-control.html`, `malicious-svg-{secure,insecure}-mode.html`, `svg-external-file-load-blocked.html`, `css-import-loop.html`, `issue-466/482-infinite-loop-*`, `issue-615-infinite-loop-break-word`. LGPL test data: keep in an external checkout or a separate `tests/corpora-lgpl/` git submodule (data files, not linked code — **UNVERIFIED legal view**; safest is to not vendor) |
| **print-css.rocks** | `lessons/lesson-*` (≈75 lessons) + `lessons/generated/<lesson>/{antennahouse,bfo,pagedjs,pdfreactor,prince,typeset,vivliostyle,weasyprint}.pdf` | 81 entries | **No license file** in repo (fonts OFL) → all rights reserved by default | multi-engine PDFs + `conversion.ini` per lesson with per-engine `status = OK/…` | Unique: the **same input rendered by 8 commercial/OSS engines**. Use as an external, non-vendored "consensus" corpus: rasterize recto output and compare against Prince/WeasyPrint PDFs with a coarse metric (SSIM) for triage, not pass/fail. Lessons map 1:1 to recto features: page-numbers, running-elements, named-pages, named-strings, page-areas, pagination, footnotes, cross-references, pdf-bookmarks, pdf-links, metadata-pdfua, archive-pdf, account-statement, tables, multi-columns, hyphenation, right-to-left, cmyk, blank-pages, chapter-numbering, flex, grid. `vdiff.py` uses `diff-pdf` |
| WeasyPrint samples | CourtBouillon/weasyprint-samples (book, invoice, letter, poster, report, ticket) | 6 docs + their WeasyPrint PDFs | "public domain" except fonts (OFL etc.) and book text (Madcats) (`README.rst` L31–37) | WeasyPrint-produced PDFs | Best **vendorable** end-to-end documents with a known-good reference PDF; report.html uses margin boxes ×12, `counter(page)`, columns, flex, `@font-face` |
| CSS-WG test fonts | `wpt/fonts/` (Ahem.ttf, `CSSTest/`, ahem-extra, noto, math…) | 32 entries | BSD-3 (repo); Ahem itself historically public domain (**UNVERIFIED**: no license text in `fonts/README.md`) | — | Bundle Ahem with the test harness |

---

## 4. Real-world templates

Feature counts = regex hits across the template's HTML/CSS files (`scripts/features.py`; `·` = 0). "Engine" = the renderer the project targets (verified from `composer.json`/source), which constrains CSS used: dompdf/mPDF templates are float/table-era CSS; Chrome-targeted ones use flex/grid.

| # | Template (repo @ SHA) | Kind | License | Engine targeted | files | flex | grid | @page | margin-box | counter(page) | float | abs | fixed | table | thead | page-break/break-* | @font-face | svg | img | transform | radius | calc/var | columns | script |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sparksuite/simple-html-invoice-template @7d74fe3 | invoice | MIT | browser | 1 | · | · | · | · | · | · | · | · | 3 | · | · | · | · | 1 | · | · | · | · | · |
| 2 | anvilco/html-pdf-invoice-template @bd45138 | invoice | MIT (`package.json`) | Chrome/Puppeteer (`generate-pdf.js`) | 3 | · | · | 1 | 2 | 2 | 1 | · | · | 3 | 2 | · | · | · | 2 | 1 | · | · | · | · |
| 3 | weasyprint-samples/invoice @6dc675b | invoice | public domain | WeasyPrint | 2 | 1 | · | 1 | 2 | · | · | 2 | · | 2 | 2 | · | 3 | · | · | 1 | · | 11 | · | · |
| 4 | weasyprint-samples/report | report | public domain | WeasyPrint | 2 | 9 | · | 5 | 12 | 1 | 6 | · | · | · | · | 3 | 5 | 5 | · | · | · | 16 | 3 | · |
| 5 | weasyprint-samples/ticket | ticket | public domain | WeasyPrint | 2 | 8 | · | 1 | · | · | · | 1 | · | · | · | · | 4 | · | · | 4 | 1 | 9 | 1 | · |
| 6 | weasyprint-samples/letter | letter | public domain | WeasyPrint | 2 | · | · | 1 | · | · | · | · | · | · | · | · | 2 | · | 1 | · | · | · | · | · |
| 7 | weasyprint-samples/book | book | public domain (text © Madcats) | WeasyPrint | 3 | 7 | · | 11 | 18 | 4 | 1 | 8 | · | · | · | 5 | 3 | · | 60 | · | 3 | · | · | · |
| 8 | ActiveCampaign/postmark-templates (basic/receipt, basic/invoice) @fa73527 | receipt, invoice (email HTML) | MIT | email clients | 2 | · | · | · | · | · | · | · | · | 22 | · | · | 2 | · | · | · | 5 | · | · | · |
| 9 | leemunroe/responsive-html-email-template @60b5b6d | transactional email | MIT | email clients | 1 | · | · | · | · | · | · | · | · | 5 | · | · | · | · | · | 1 | 4 | · | · | · |
| 10 | rbardini/jsonresume-theme-even @8231a31 | résumé | MIT | browser | 30 | 6 | 11 | · | · | · | · | 3 | · | · | · | · | 1 | · | 1 | · | 4 | 46 | 3 | 1 |
| 11 | invoiceninja pdf-designs (20 files) @f1ffa5f | invoice, statement, receipt, refund, delivery note | **Elastic-2.0** | headless Chrome (`beganovich/snappdf`) | 20 | 93 | **134** | 18 | · | · | 10 | 2 | **49** | 160 | 24 | 22 | · | · | 17 | 58 | 29 | 136 | 70 | · |
| 12 | kimai invoice renderer @a3bf6f9 | invoice, timesheet | AGPL-3.0 | **mPDF** | 4 | · | · | · | · | · | · | · | · | 12 | 4 | · | · | · | · | · | · | · | · | · |
| 13 | InvoicePlane pdf templates @32b92f8 | invoice, quote | MIT (code; trademark notice) | **mPDF** | 4 | · | · | · | · | · | · | · | · | 4 | 2 | · | · | · | · | · | · | · | · | · |
| 14 | crater invoice/estimate/payment @05d5ce2 | invoice | AGPL-3.0 | **dompdf** | 4 | · | · | · | · | · | 19 | 4 | · | 7 | · | 18 | · | · | 3 | 3 | · | · | · | · |
| 15 | crater reports | report | AGPL-3.0 | dompdf | 5 | · | · | · | · | · | · | · | · | 21 | · | · | · | · | · | · | · | · | · | · |
| 16 | InvoiceShelf pdf (crater fork) @650bd3b | invoice, estimate, statement, reports | AGPL-3.0 | dompdf | 23 | · | · | 1 | · | · | 45 | 10 | · | 36 | 14 | 40 | 1 | · | 9 | 19 | · | · | · | · |
| 17 | akaunting document templates @06dfa47 | invoice/bill (default, classic, modern) | **BSL-1.1** | dompdf | 4 | · | · | · | · | · | · | · | · | 3 | 3 | · | · | · | 6 | · | · | · | · | · |
| 18 | getlago/lago-api invoice templates (v1–v4 slim) @d0b73d4 | usage-based invoice | AGPL-3.0 | **Gotenberg/Chromium** (`app/services/utils/pdf_generator.rb` L34 `/forms/chromium/convert/html`) | 53 | 24 | · | · | · | · | 36 | · | · | · | · | 26 | 241 | · | · | · | 11 | 19 | · | · |
| 19 | LaravelDaily/laravel-invoices @67fd16b | invoice | GPL-3.0 | dompdf | 1 | · | · | · | · | · | · | · | · | 3 | 2 | · | · | · | 1 | 1 | · | · | · | 1 |
| 20 | frappe/erpnext print formats @e65a640 | invoice, vouchers, credit note, balance sheet | GPL-3.0 | wkhtmltopdf/Chrome (Frappe) (**UNVERIFIED**) | 13 | · | · | · | · | · | · | · | · | 20 | 2 | · | · | · | 1 | · | · | · | · | · |
| 21 | SolidInvoice templates (classic, compact, editorial, friendly, photographer) @6e40f06 | invoice | MIT | **mPDF** | 9 | · | · | 1 | · | · | · | · | · | 32 | 6 | · | · | · | · | 33 | · | · | · | · |
| 22 | openedx/edx-platform `lms/templates/certificates` @ce074d1 | certificate | AGPL-3.0 | browser (web cert) | 15 | · | · | · | · | · | · | · | · | · | · | · | · | · | 9 | · | · | · | · | 6 |
| 23 | openhtmltopdf-templates arboshiki-invoice @780ba56 | invoice | LGPL (repo) | openhtmltopdf | 1 | · | · | 1 | 1 | 2 | 1 | · | · | 1 | 1 | 1 | · | · | 1 | · | · | · | · | · |
| 24 | openhtmltopdf-templates cafe-menu | menu/flyer | LGPL | openhtmltopdf | 1 | · | · | 1 | · | · | 1 | 1 | 1 | · | · | · | · | · | · | · | · | · | 1 | · |
| 25 | gotenberg test/integration/testdata (feature-rich-html, header-footer-html, pages-3/12-html, `ssrf-*-html`) @db150b7 | test fixtures | MIT | Chromium | ~25 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 5 |
| 26 | print-css-rocks lesson-account-statement | bank statement | none | multi-engine | 1 | · | · | 1 | 1 | 1 | · | · | · | 5 | 4 | · | · | · | 4 | · | · | · | · | · |

Observations that matter:

- **Tables everywhere** (every invoice family); `thead` repetition across pages needed by ≥ 9 families.
- **Invoice Ninja (the largest open-source invoicing product) uses `display: grid` in 18/20 designs** (134 hits) and `position: fixed` (49 hits) for `.repeating-header`/`.repeating-footer` and watermark (`clean.html` L260–306) — relying on Chrome's behaviour of repeating fixed-position boxes on every printed page (WPT `css/css-page/fixedpos-*-print.html`, 11 tests, cover this). Also `mix-blend-mode: multiply` and invalid unitless `@page { margin-top: 5 }` (clean.html L28–32) that Chrome ignores — recto must drop invalid declarations silently, like browsers.
- **Legacy-engine extensions** appear in templates for mPDF/dompdf: mPDF `<htmlpagefooter>`/`sethtmlpagefooter`/`{PAGENO}`/`{nbpg}` in kimai `default.pdf.twig`, `service-date.pdf.twig`, InvoicePlane `InvoicePlane.php`; dompdf `<script type="text/php">` page scripts in LaravelDaily `default.blade.php`. These will not render page numbers in recto; a documented migration (→ `@page { @bottom-right { content: counter(page) " / " counter(pages) } }`) or an opt-in compat shim is needed.
- dompdf-targeted templates are **float-heavy** (InvoiceShelf 45 floats, crater 19) and use `page-break-*` (40/18) — legacy `page-break-*` aliases must work.
- Chrome-targeted templates use **flex** (ninja 93, lago 24, weasyprint samples) and **CSS variables/calc** (ninja 136, jsonresume 46).
- **Margin boxes + counter(page)** appear only in templates written for paged-media engines (WeasyPrint samples, anvil, arboshiki, print-css-rocks). Chrome/dompdf users fake headers with `position: fixed`/mPDF tags → recto should support **both** idioms.
- Web fonts: Lago embeds many `@font-face`/Google Fonts links (241 hits) → offline-by-default means recto must surface a clear "blocked remote font" diagnostic and allow a local font dir.
- Vendorable without licence friction: #1–10, #13 (MIT, mind trademark), #21, #25. AGPL/GPL/Elastic/BSL templates (#11, 12, 14–20, 22) should be fetched at CI time from pinned SHAs (not committed); store only recto's outputs/metrics. Templates are server-side (Twig/Blade/Slim/Mako/Jinja): each needs a **pre-rendered static HTML snapshot** with sample data — generate once per template with the upstream project's demo data, keep the rendered HTML outside the repo if license requires.

Suggested "real-world smoke" set (v1 gate, 15 docs): sparksuite, anvil, weasyprint-samples ×6, postmark receipt+invoice, InvoicePlane, SolidInvoice classic, arboshiki, print-css-rocks account-statement, jsonresume-even; plus (external, non-vendored) invoiceninja `clean`/`modern`/`tidy_receipt`/`basic_statement`, kimai default (after migration), InvoiceShelf invoice1, Lago v4.

---

## 5. Fuzzing / robustness corpora

| Corpus | Location | Size | License | Use |
|---|---|---|---|---|
| html5lib tokenizer tests | `html5lib-tests/tokenizer/*.test` (15 files) | 6,827 cases | MIT | seed corpus for recto's HTML tokenizer fuzzing; html5ever already passes them (if recto uses html5ever, use as a smoke test only) |
| html5lib tree-construction | **moved to WPT** `html/syntax/parsing/resources/*.dat` (html5lib-tests `README.md`: "now solely maintained on web-platform-tests") | 62 files, 1,968 `#data` cases | BSD-3 | parser seeds + expected DOM trees |
| html5lib encoding / serializer | `encoding/` (5), `serializer/` (5) | — | MIT | charset sniffing seeds (`<meta charset>` prescan) |
| HarfBuzz fuzzing fonts | `harfbuzz/test/fuzzing/fonts/` | 525 files (crash reproducers, hash-named) | Old-MIT (`COPYING`) | font-parser/shaper robustness seeds — feed through recto's `@font-face` path (`data:` URL) |
| HarfBuzz shaping fonts | `test/shape/data/in-house/fonts/` 219, `test/api/fonts/` 213 | | Old-MIT | shaping edge cases, variable fonts, COLR/CBDT/sbix |
| fontations fuzz targets | `fontations/fuzz/fuzz_targets/` (fuzz_skrifa_outline, _charmap, _color, fuzz_name, …) | targets only, **no corpus in repo** (corpora live in OSS-Fuzz) | Apache-2.0/MIT | copy target structure if recto uses skrifa/read-fonts |
| PngSuite | `image-png/tests/pngsuite/` (177 files) + `pngsuite-extra`, `bugfixes`, `iccp`, `sbit`, `animated` | 177 | PngSuite: "Permission to use, copy, modify and distribute these images for any purpose and without fee is hereby granted" (`PngSuite.LICENSE`) | image decoding seeds; also a golden-image test: embed each PNG via `<img>` and rasterize |
| image-rs test images | `image/tests/images/{bmp,gif,jpg,png,tiff,webp,…}` | 192 files | Apache-2.0/MIT | JPEG/GIF/WebP seeds |
| resvg test suite | `resvg/crates/resvg/tests/tests/{filters 405, masking 93, paint-servers 154, painting 307, shapes 133, structure 264, text 386}` | **1,760 SVG + 1,760 reference PNG** | Apache-2.0/MIT | if recto embeds SVG via usvg→PDF (svg2pdf/krilla), run the same SVGs through recto and compare to resvg PNGs with fuzzy tolerance; text tests need resvg's `tests/fonts/` (Amiri, MPLUS1p, Noto…, OFL/Apache) |
| veraPDF corpus | `veraPDF-corpus` | 2,906 PDFs (PDF/A-1b 569, 2b 986, 4 485, UA-1 297, UA-2 138, Isartor 205, …) | CC-BY-4.0 | not for recto inputs; use to **validate the validator** (calibrate which checks recto's built-in PDF/UA/A self-checks must catch) |
| hayro test PDFs | `hayro-tests/manifest_{pdfjs 679, pdfbox 454, custom 301, pdfium 127, corpus 41}.json` | ~1,600 | various upstream | evidence of hayro's rendering coverage |
| Gotenberg SSRF fixtures | `gotenberg/test/integration/testdata/ssrf-{fetch,eventsource,websocket,websocket-tls,websocket-worker}-html` | 5 | MIT | negative tests for recto's network sandbox (must make **zero** requests) |
| openhtmltopdf security/loop tests | `external-access-control.html`, `malicious-svg-*`, `css-import-loop.html`, `issue-466/482-infinite-loop-*`, `issue-615-infinite-loop-break-word.html` | ~8 | LGPL | inputs for time/memory-cap and sandbox tests (reproduce scenario, don't vendor) |
| Vivliostyle loop regressions | `eal-zero-size-flow-partition.html`, `invalid-page-area.html` ("must not loop forever") | 2 | AGPL | scenario ideas only |

Fuzz harness: `cargo-fuzz` targets `html_to_pdf(bytes)`, `css_parse(bytes)`, `font_load(bytes)`, `image_decode(bytes)`, with structure-aware generation for CSS (grammar-based) and a dictionary of paged-media keywords (`@page`, `@top-center`, `break-before`, `string-set`, `target-counter`). Every fuzz crash → minimized repro added to `tests/crash/` (WPT-style crashtest: PASS = no panic, within caps).

---

## 6. Golden-image strategy

### 6.1 Rasterizer options

| Option | Lang / deps | License | Determinism | Verdict |
|---|---|---|---|---|
| **hayro 0.8.0** (`hayro/src/lib.rs` L230 `render(page, cache, interpreter_settings, render_settings, pixmap_settings) -> Pixmap`; `PixmapSettings { x_scale, y_scale, bg_color }` L203) | pure Rust; vello_cpu, kurbo, image, pic-scale (`hayro/Cargo.toml`) | Apache-2.0/MIT | Its own suite compares **exact** pixels (`hayro-tests/tests/mod.rs` L422 `is_pix_diff` = any channel differs) against stored PNGs, CI only on ubuntu-latest (`.github/workflows/ci.yml`) → deterministic per platform; cross-arch equality **UNVERIFIED** (default `simd` feature enables pic-scale NEON/SSE/AVX paths — disable `simd` in the test harness). README: "experimental, work-in-progress", handles 1400+ regression PDFs from pdf.js/PDFBox, missing knockout groups and non-embedded CID fonts (irrelevant for recto output) | **Primary.** In-process, `cargo test`-friendly, no system deps, MSRV 1.92. Pin exact version; regenerate goldens on bump |
| pdfium via pdfium-render 0.9.4 | Rust bindings, needs prebuilt `libpdfium` (dynamic `bind_to_library` or static link; README L82–113) | MIT/Apache (bindings), pdfium BSD-3 | Chrome's renderer — closest to what users see in Chrome; binary download from bblanchon/pdfium-binaries (**UNVERIFIED** availability in recto CI) | **Secondary/oracle** job: catches bugs where recto PDF is valid-for-hayro but renders wrong in real viewers |
| poppler `pdftoppm` 24.02 | C++ system binary | GPL | Verified here: same machine, two runs → identical SHA-256 per page (`-r 96 -png`, and with `-aa no -aaVector no`); 8-page WeasyPrint report in 1.78 s | Third oracle; used by many projects; version drift across distros changes AA → don't store goldens from it |
| MuPDF (`mupdf` crate 0.8.0 / `mutool draw`) | C | **AGPL-3.0** (mupdf-rs `Cargo.toml`) | good | avoid linking; CLI-only oracle at most |
| Ghostscript | C | AGPL | WeasyPrint uses it with AA off (§2.2) | avoid (license, external binary) |
| pdf.js | JS/Node | Apache-2.0 | what WPT uses (96/72 scale) | only if a Node job exists; not needed |

### 6.2 Image comparison

- **Exact / WPT-fuzzy** (default): per-page `(maxDifference, totalPixels)` exactly as WPT defines (implement ~40 lines, cf. Blitz `fuzzy.rs` L114). Deterministic, explainable, matches WPT semantics.
- **Perceptual** for real-world documents: `image-compare 0.5.0` (MIT; `rgba_hybrid_compare` hybrid.rs L102, `rgb_similarity_structure` SSIM lib.rs L168) → score threshold, e.g. ≥ 0.995; `dify 0.8.0` (MIT; pixelmatch-port `diff::get_results(left, right, threshold, detect_anti_aliased_pixels, …)` diff.rs L43) for AA-tolerant diffs and diff images. `dssim 3.5.1` is **AGPL-3.0** → only as an external CLI if at all.
- Always emit a triptych PNG (expected | diff | actual) on failure, like resvg (`tests/integration/main.rs` L168 `get_diff`, `DIFF_THRESHOLD = 1`) and hayro.
- Store goldens as PNG optimized with `oxipng` (10.2.1) to keep the repo small; or store **BLAKE3 hashes of raw RGBA** for very large suites (WPT doesn't need goldens: the reference file *is* the golden).

### 6.3 Non-visual checks

| Check | Tool | Notes |
|---|---|---|
| Byte determinism | recto itself | render twice (and in two threads/orders) → identical bytes; render on x86_64 and aarch64 in CI → identical bytes (recto's headline guarantee) |
| PDF syntax | `qpdf --check` (Apache-2.0, C++ CLI) | xref, streams, object structure; CI container installs qpdf |
| PDF syntax (2nd) | `pdfcpu validate` (Apache-2.0, Go) | stricter/lenient modes; single static binary |
| In-process structure assertions | `lopdf 0.45.0` (MIT) | outlines, link annotations & rects, `/Dests`, `/StructTreeRoot` (role tree shape for tables/lists/headings), `/Lang`, `/MarkInfo`, fonts embedded/subset, `/ViewerPreferences/DisplayDocTitle` |
| PDF/A + PDF/UA | **veraPDF** (Java ≥ 11, GPL-3+/MPL-2 dual) CLI in a dedicated CI job (`verapdf --flavour ua1 --format json`) | Java is fine in CI only; never a runtime dep. Calibrate with veraPDF-corpus (UA-1 297, UA-2 138 files) |
| Text extraction | `pdftotext -layout` (poppler) and/or `pdf-extract 0.12.1` / `pdf_oxide 0.3.78` | verifies ToUnicode/ActualText, reading order (tagged), ligature decomposition, hyphen soft-break handling; golden `.txt` per document |
| Layout dump | recto `--dump-layout json` | fragment tree with page index + border-box rects; snapshot via `insta 1.49.0` (`assert_json_snapshot!`) — robust to painting changes, fast, diffable in review |
| Page-level metadata | recto JSON report | page count, page sizes, named page per page, string-set values per page — cheap assertions ported from Paged.js specs ("should render 8 pages") |

### 6.4 Recommended harness architecture

```
tests/
  harness/            # crate `recto-test-harness` (libtest-mimic 0.8.2 custom runner)
    src/main.rs       # discovers cases from manifests, runs in parallel, filters, --update
    src/raster.rs     # hayro (default-features=false, features=["embed-fonts"]) → RGBA @96dpi, white bg
    src/compare.rs    # wpt_fuzzy(), perceptual() via image-compare, triptych writer
    src/wpt.rs        # rel=match/mismatch chains, meta fuzzy/reftest-pages, print vs screen mode
    src/pdfcheck.rs   # lopdf structure asserts; shells to qpdf/pdfcpu/verapdf if present (feature-gated)
  wpt/
    WPT_COMMIT  include.toml  expectations.toml  summary.json
  ported/weasyprint/{draw,layout,pdf}/*.toml   # + LICENSE (BSD-3) + source refs
  pixels/*.toml       # recto-native assert_pixels cases (WeasyPrint char grid)
  layout/*.html + insta snapshots
  docs/<name>/{input.html, assets/, expected/page-N.png, expected.txt, meta.toml}
  crash/*.html        # fuzz repros, PASS = no panic within caps
  fonts/ Ahem.ttf weasyprint.otf (test-only)
external corpora (fetched at pinned SHAs by `cargo xtask fetch-corpora`, gitignored):
  wpt (sparse), resvg tests, vivliostyle files, openhtmltopdf visualtest, print-css-rocks,
  AGPL/Elastic/BSL templates
```

Tiers in CI:
1. **PR, every push (<5 min)**: unit tests, `assert_pixels` (ported WeasyPrint draw + native), layout snapshots (insta), docs/ smoke set (15 docs, perceptual compare), determinism (double render, byte equality), `qpdf --check` on all produced PDFs, curated WPT M-current subset (~2–3k reftests; recto <100 ms per doc ⇒ seconds-to-minutes with rayon).
2. **Nightly**: full WPT include set with expectations diff and summary trend; resvg SVG suite; html5lib/WPT parser `.dat`; veraPDF UA/A on a tagged-PDF corpus; pdfium oracle comparison (flag disagreements between hayro and pdfium renders of the same recto PDF > threshold); x86_64 vs aarch64 byte-equality; fuzzing 30 min per target.
3. **Weekly / manual**: external template corpus (AGPL/Elastic etc.), print-css-rocks consensus comparison against Prince/WeasyPrint PDFs (report-only), Vivliostyle and openhtmltopdf inputs (crash/timeout/page-count only).

Golden update workflow: `cargo xtask goldens --update <filter>` regenerates, writes an HTML report of before/after triptychs; reviewers approve in PR. Goldens record `{recto_version, hayro_version, font_set_hash}`; a hayro bump regenerates all goldens in a dedicated PR.

---

## Findings that affect recto's design

1. **WPT print reftests already define "render to PDF → rasterize at 96/72 → compare per page"** (`executorwebdriver.py` L540–560, `print_pdf_runner.html`). recto can run ~300 paged-media reftests (css-page 217, CSS2/pagination 43, css/printing ~17 non-crash, infrastructure 8, css-break print 64) with zero adaptation beyond default page 5in×3in, margin 0.5in. Make these a v1 gate.
2. **94 % of css-break reftests fragment via multicol**, not pages. Design the fragmentation engine around a generic *fragmentainer* (page, column) from day one; otherwise ~1,000 of the most relevant break/orphans/widows/table-split tests are untestable. Even a minimal balanced-column multicol unlocks them.
3. recto needs a **"screen reftest" mode**: single 800×600px page, zero margin, ICB = page area, overflow clipped — to reuse ~10k non-print WPT reftests. Expose it as a hidden/test CLI flag or harness API, not a public feature.
4. The harness must map **absolute URLs `/fonts/ahem.css` → WPT root**, i.e. recto's resource loader needs a configurable document root that also acts as the sandbox root. Ahem.ttf must be loadable via `@font-face` from a local file.
5. Tests with `<script>`/`reftest-wait`/testharness.js are SKIP (no JS): roughly 5–50 % per dir (css-position 47 % of reftests have scripts). Provide a **layout-tree JSON dump** so `check-layout-th.js`-style (`data-expected-*`) and WeasyPrint layout tests can be ported as data.
6. Real templates rely on **Chrome's repeat-`position: fixed`-on-every-page** behaviour (Invoice Ninja 49 uses; WPT `fixedpos-*-print` ×11). Implement it — it's how the most-used invoicing app does headers/footers.
7. **Grid is not optional for Invoice Ninja**: 18/20 designs use `display: grid` (134 hits). Keep grid a stretch goal for v1 but plan it for v1.x; publish a compatibility matrix per template.
8. mPDF/dompdf templates carry **proprietary pagination markup** (`<htmlpagefooter>`, `{PAGENO}`, `<script type="text/php">`). Ship a migration guide and consider an opt-in shim mapping `{PAGENO}`/`{nbpg}` to `counter(page)`/`counter(pages)`.
9. Invalid CSS in the wild (unitless `@page` margins) must be dropped exactly as browsers do; legacy `page-break-*` aliases are heavily used (dompdf families).
10. **Use hayro (pure Rust, Apache/MIT) as the in-process golden rasterizer** with `simd` disabled; pin the version; pdfium (via pdfium-render) and poppler as nightly oracles only. Avoid AGPL tools (Ghostscript, MuPDF, dssim) in-tree.
11. WeasyPrint's char-grid `assert_pixels` (1-CSS-px = 1-device-px, AA off, solid primaries) is the best unit-level visual test format; adopt it verbatim (BSD-3 allows porting 605 draw tests with attribution). recto's rasterizer path needs a no-AA or integer-aligned mode for exact grids.
12. Paged.js specs give cheap, portable **structural** assertions (page counts, which pages carry named page X); recto should emit a machine-readable render report (page count, per-page size/name/strings) to assert against without rasterizing.
13. Security tests come for free from Gotenberg's SSRF fixtures and openhtmltopdf's external-access/malicious-SVG/loop tests — assert zero network I/O and bounded time/memory.
14. Determinism verification belongs in the harness: double-render byte equality on every test, cross-arch nightly. poppler on one machine was bit-stable; but goldens must come from the pinned in-process rasterizer, never a system tool.
15. License hygiene: vendor only BSD/MIT/Apache/public-domain/CC-BY material (WPT, WeasyPrint tests & samples, Paged.js specs, resvg, PngSuite, html5lib, veraPDF corpus with attribution). Fetch AGPL (Vivliostyle, kimai, crater, InvoiceShelf, lago, edx), LGPL (openhtmltopdf), Elastic (Invoice Ninja), BSL (Akaunting), GPL (erpnext, laravel-invoices) and unlicensed (print-css-rocks) corpora at CI time from pinned SHAs.

## Recommendation

- Build `recto-test-harness` on `libtest-mimic` with five case kinds: `wpt-reftest`, `pixels` (WeasyPrint grid), `layout-snapshot` (insta JSON), `doc-golden` (per-page PNG + perceptual compare + text + structure), `crash`.
- Rasterize with **hayro 0.8.x** at 96 dpi (`PixmapSettings { x_scale: 96/72, y_scale: 96/72, bg_color: WHITE }`), simd off; compare with WPT fuzzy semantics by default, `image-compare` SSIM for documents.
- Structure checks with `lopdf` in-process; `qpdf --check` on every produced PDF in CI; veraPDF nightly for tagged/UA/A outputs.
- WPT: pin `WPT_COMMIT`, sparse-fetch the dirs in §1.4, classify via the released `MANIFEST.json`, keep `expectations.toml` with unexpected-result-fails semantics. Milestone gates: M3 paged-media subset ≥ 90 % PASS; publish per-directory pass rates.
- Port WeasyPrint `tests/draw` + `tests/draw/svg` (605) first, then `layout/test_page.py`, `test_table.py`, `test_footnotes.py`, and `test_pdf.py` bookmarks/links/tags as structure tests.
- Real-world: vendor the 15-doc smoke set (§4), fetch external templates nightly; track a template-compat matrix in docs.

## Open questions / UNVERIFIED items

- **UNVERIFIED**: hayro output equality across x86_64/aarch64 and with/without `simd`; whether hayro/vello_cpu exposes an anti-aliasing-off mode (needed for exact WeasyPrint grids; fallback: supersample + threshold or integer-aligned geometry only).
- **UNVERIFIED**: Ahem.ttf license text (not present in `wpt/fonts/README.md`; historically public domain/CC0).
- **UNVERIFIED**: legal status of committing LGPL test HTML (openhtmltopdf) into an MIT/Apache repo — recommended not to vendor.
- print-css-rocks has **no license file**; treat as all-rights-reserved; confirm with author (zopyx) before any redistribution.
- Counts are regex scans, not `wpt manifest` output; references chains, `.any.js`, variants (`?variant`) and `-manual` were not resolved. Re-count with MANIFEST.json in M1.
- Count of `check-layout-th.js` / `data-expected-*` tests convertible to layout assertions not measured.
- frappe/erpnext rendering engine (wkhtmltopdf vs Chrome) not verified from source.
- pdfium prebuilt binary availability/pinning for CI (bblanchon/pdfium-binaries) not verified (network restricted here).
- Whether recto's "screen reftest" mode should clip at 600px or paginate (WPT semantics: viewport screenshot incl. scrollbars; scrollbars don't exist in recto — tests depending on overflow scrollbars should be SKIP).
