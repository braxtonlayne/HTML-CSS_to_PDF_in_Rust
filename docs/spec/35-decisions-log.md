# 35 — Decisions log (ADRs)

Status: living. Format per entry: **Status** (Accepted / Proposed / Superseded), **Context**, **Decision**, **Alternatives considered**, **Consequences**. Evidence references use R-numbers from `research/00-SYNTHESIS.md`. The project owner reviews this log. Decisions were made without asking, per the brief. Reverse any of them by superseding the entry, never by editing it silently.

Index: 0001 name · 0002 layout engine · 0003 break-token contract · 0004 Au units · 0005 inline layout · 0006 PDF backend · 0007 HTML parser/DOM · 0008 cascade · 0009 SVG · 0010 images · 0011 duplicate fontations · 0012 two-phase finalization · 0013 forward references · 0014 fonts · 0015 tagging default · 0016 grid · 0017 multicol · 0018 SVG text · 0019 footnotes · 0020 page floats · 0021 table header repetition · 0022 form controls · 0023 encryption · 0024 page defaults · 0025 barcodes · 0026 MathML · 0027 letter-spacing · 0028 template engine · 0029 fetcher policy · 0030 server isolation · 0031 bindings · 0032 options schema · 0033 test rasterizer · 0034 MSRV · 0035 hyphenation languages · 0036 HTTP client · 0037 CLI parsing · 0038 determinism · 0039 writing modes · 0040 default media · 0041 error codes · 0042 server stack · 0043 licenses · 0044 background PDFs · 0045 fixed/sticky · 0046 effects scope.

---

## ADR-0001 — Working name "recto"
**Status:** Accepted. **Context:** The brief uses the placeholder `{{PROJECT_NAME}}`. Docs, crates and commands need a concrete name. "recto" is the right-hand page of a spread, the crate name is unclaimed on crates.io (sparse index 404, checked 2026-10-14), and it is short to type. **Decision:** Use `recto` everywhere (binary, crates `recto-*`, npm `@recto/pdf`, PyPI `recto`). **Alternatives:** `folio`, `quire`, `vellum`, `verso`, `colophon` (taken on crates.io); `pressmark`, `leafpress`, `pagecraft` (free but longer or worse). **Consequences:** The name is not trademark-cleared. Renaming is a mechanical search and replace. Package-name availability on npm, PyPI, NuGet and Maven is UNVERIFIED (BND verification items).

## ADR-0002 — Own fragmenting layout engine; taffy only for flex/grid
**Status:** Accepted. **Context:** R06 verified taffy 0.15.0 has no fragmentation concept: block layout gives children unlimited height (`block.rs:1090`), results are one box in and one box out, and it has no inline layout or tables. Slicing a long canvas into pages (fulgur) needs 10.5k lines, still lacks nested-table fragmentation and caused a DoS. **Decision:** Write block, inline, table, float, abspos, multicol and page layout ourselves around break tokens. Use taffy (exact minor pin, adapter of about 500 lines) for flex and grid item placement within a fragment. Port taffy's margin-collapsing and float-slot logic as code, not calls. **Alternatives:** (a) lay out on one canvas, then slice; (b) re-run taffy per page with a height limit; (d) write flex and grid ourselves too; (e) adopt Blitz/Servo layout (no pagination either, plus heavy dependency trees). **Consequences:** About 18–23k lines of layout we maintain. Streaming, determinism and correct breaking become possible. Taffy API churn is isolated. Vendoring `flexbox.rs` stays possible (MIT).

## ADR-0003 — Break-token layout contract and streaming page loop
**Status:** Accepted. **Context:** WeasyPrint uses nested resume indices and abort-and-rollback (R01). Typst passes all regions up front and calls this a compatibility shim (R06 §3). Chromium LayoutNG and Azul use on-demand break tokens. **Decision:** `layout(node, ConstraintSpace, Option<&BreakToken>) -> LayoutResult` with immutable tokens, side effects returned as values, best-break rewind by appeal class, and a progress assertion on every fragmentainer. **Alternatives:** WeasyPrint-style mutable boxes with manual rollback; Typst all-regions-upfront. **Consequences:** Pages can be emitted as they finish. Re-layout of one page is cheap. Cached layouts must key on the token.

## ADR-0004 — `Au(i32)` = 1/64 CSS px layout units
**Status:** Accepted. **Context:** Determinism across x86_64 and aarch64 and exact fit tests. Taffy uses `f32`, harfrust works in font units. **Decision:** All layout geometry is `Au`. f32 appears only at the taffy bridge, shaping scale conversion and the PDF writer boundary, always with round-half-even. **Alternatives:** f32/f64 (drift, `FIT_EPS` hacks as in Azul), 1/60 px (Servo's Au, inexact for powers of two), 1/64 pt. **Consequences:** Range ±33.5M px (about 8.9 km), plenty. Every f32 boundary needs a rounding test.

## ADR-0005 — Own inline layout on harfrust, icu_segmenter, unicode-bidi, hypher
**Status:** Accepted. **Context:** R07: parley has a resumable breaker but lacks reshaping at breaks, hyphenation, inline padding/border, tab stops and `::first-line`, depends on fontconfig FFI for Linux fonts, and has non-deterministic font IDs. cosmic-text wraps to one width and has no inline boxes. **Decision:** Build `recto-text`/inline layout modelled on parley's breaker state design and Typst's shaping and reshaping. **Alternatives:** parley (fork half of it), cosmic-text, Pango/HarfBuzz FFI (breaks the static binary). **Consequences:** 6–10k lines. Full control over floats, fragmentation and CSS text semantics.

## ADR-0006 — krilla as PDF backend behind an adapter
**Status:** Accepted. **Context:** R08: krilla 0.8.2 is the only Rust writer with tagging, PDF/A-1…4 and UA-1 enforcement, color glyphs, variable/CFF2 subsetting and deterministic output. It cannot stream (peak ≈ 2.1× output), and lacks custom XMP (#209), encryption and PDF/UA-2. **Decision:** Use krilla + krilla-svg, never exposing their types. Carry or upstream two patches: custom XMP and a streaming sink (M6). **Alternatives:** pdf-writer directly (about 15k lines to rebuild), printpdf (no tagging, non-deterministic IDs), lopdf (low-level, no layout helpers). **Consequences:** Memory is bounded by compressed output until the streaming patch lands; an output cap is mandatory. The MSRV rises to 1.92.

## ADR-0007 — html5ever with our own arena DOM
**Status:** Accepted. **Context:** R12: `markup5ever_rcdom` is test-only and unpublished; scraper lags the html5ever version. **Decision:** Implement `TreeSink` over an arena (`RefCell<Arena>`, `Handle = NodeId`), set `scripting_enabled: false`, sniff encodings ourselves, cap depth and node counts. **Alternatives:** scraper, tl, html5gum (tokenizer only), lol_html (not a DOM). **Consequences:** About 800 lines of glue; exact control of limits and source lines.

## ADR-0008 — Own cascade on cssparser + selectors
**Status:** Accepted. **Context:** R12: stylo cannot parse `@page` or paged-media properties outside its Gecko build and is huge; lightningcss lacks typed values for about half the needed properties and has no cascade. **Decision:** cssparser 0.38 + selectors 0.41 with our own property registry, cascade and computed values. **Alternatives:** stylo, lightningcss, raw-token handling of unknown properties. **Consequences:** We own the property table (spec 04). MPL-2.0 NOTICE entries are required.

## ADR-0009 — usvg sandboxed with krilla-svg
**Status:** Accepted. **Context:** R10/R12: usvg's default resolver reads arbitrary files, svgz decompression is uncapped, node limit is 1M. svg2pdf is unmaintained. **Decision:** Pre-parse with roxmltree (`allow_dtd: false`, node cap), replace both href resolvers, decompress svgz ourselves with a cap, feed fonts from our registry, then `Tree::from_xmltree`; draw through krilla-svg. **Alternatives:** resvg rasterization (loses vectors), svg2pdf, own SVG renderer. **Consequences:** The workspace usvg version follows krilla-svg (0.47.x, ADR-0011).

## ADR-0010 — Image formats and JPEG passthrough
**Status:** Accepted. **Decision:** `image` with PNG, JPEG, GIF (first frame), WebP, BMP only, explicit `Limits`, header-based size checks before decode, JPEG embedded as DCT without re-encoding where valid (Adobe CMYK inverted, arithmetic/lossless SOFs transcoded or rejected), EXIF orientation as a matrix. **Alternatives:** AVIF/HEIC (C dependencies), TIFF/ICO/HDR (attack surface, WeasyPrint CVE history). **Consequences:** Unsupported formats warn and render as missing.

## ADR-0011 — Two fontations lines; usvg follows krilla-svg
**Status:** Accepted. **Context:** krilla pins skrifa 0.42 and subsetter with older fontations; our text stack wants skrifa 0.48. **Decision:** Allow both inside the dependency graph, with `recto-pdf` as the only boundary where krilla's line is used. `deny.toml` carries an explicit skip-list. A CI test checks glyph-ID/advance agreement. **Alternatives:** Pin ourselves to krilla's older fontations (blocks harfrust 0.14), fork krilla now. **Consequences:** Larger binary by one set of font-parsing code; revisit when krilla updates.

## ADR-0012 — Two-phase finalization and streaming emission
**Status:** Accepted. **Context:** `counter(pages)`, forward `target-counter`, `string(last)`, `element(last)` need final page assignment (R05a F1). Margin boxes never affect body layout. **Decision:** Body pages are laid out and painted in order. When static analysis finds no page-total or forward dependence, margin boxes are rendered and each page is handed to the writer immediately. Otherwise body display lists are retained until the last page, then margin boxes are rendered and pages emitted. **Alternatives:** Always buffer all pages; patch the content stream afterwards with reserved width; two full layout runs. **Consequences:** Memory is compact display lists per page in the deferred case (still linear). Documents with "Page X of Y" use the deferred path, which is the common invoice case. Display lists must therefore be compact (PNT items).

## ADR-0013 — Bounded forward-reference relayout
**Status:** Accepted. **Decision:** Dependency analysis marks pages whose output depends on resolved values; after a pass, only pages from the first changed page onward are re-laid out; at most `max_layout_passes` (default 4); a width reservation for page-number text makes convergence likely; non-convergence yields `W_LAYOUT_NOT_CONVERGED` and uses the last pass. **Alternatives:** WeasyPrint's silent 8-loop cap; error on non-convergence. **Consequences:** Deterministic. A rare document may keep slightly wrong numbers, with a warning.

## ADR-0014 — Font sources, system fonts, bundled fonts
**Status:** Accepted. **Decision:** Priority: `@font-face` (allowed dir or `data:`), `--font-dir`, bundled, system. The CLI enables system fonts by default; `--reproducible`, the server and the library disable them. Discovery is pure Rust with sorted directories; no fontconfig/CoreText/DirectWrite. `FontId` = index into a sorted face vector; identity is a content hash. Bundled set: Liberation Sans/Serif/Mono + a monochrome symbol/emoji fallback (OFL-1.1; sizes UNVERIFIED), `fonts-cjk` optional. **Alternatives:** system fonts only (fails in scratch images), always-bundled-only (surprises desktop users). **Consequences:** Output on a desktop CLI may vary by machine unless `--reproducible` is set; the docs say so.

## ADR-0015 — Tagged PDF on by default
**Status:** Accepted. **Decision:** Tagging is on unless `--no-tagged`. Headings become outline entries and structure elements, tables become tagged tables, `alt` becomes `/Alt`, margin content becomes artifacts. PDF/UA and PDF/A are opt-in. **Alternatives:** Off by default (Prince), on only with PDF/UA. **Consequences:** A size and CPU cost (budget in PERF items); one structure element per DOM element across pages.

## ADR-0016 — CSS Grid: monolithic in M3, fragmentation in M6
**Status:** Accepted. **Context:** R11: 18 of 20 Invoice Ninja designs use grid; R04: Prince does not fragment grid. **Decision:** Use taffy grid, treating containers as monolithic (or `break-inside: avoid`) in M3, then break between rows in M6. **Alternatives:** Defer grid past 1.0; emulate with tables. **Consequences:** Oversized grids overflow the page until M6 and warn (`W_GRID_OVERFLOWS_PAGE`).

## ADR-0017 — Multi-column in v1 (basic); span and nesting deferred
**Status:** Accepted. **Decision:** `column-count/width/gap/rule`, `column-fill`, column breaks and continuation across pages in M6. `column-span: all` and nested multicol are deferred past 1.0. The fragmentation engine supports column fragmentainers from M1 (R11: 94% of css-break reftests use columns). **Alternatives:** Skip multicol; full spec support. **Consequences:** Spec 10 states this explicitly.

## ADR-0018 — SVG text via usvg's `text` feature for now
**Status:** Accepted. **Context:** usvg text pulls fontdb → ttf-parser (RUSTSEC-2026-0192, unmaintained). Logos and charts use SVG text. **Decision:** Enable it in v1 and track; replace with text-to-path through `recto-text` after 1.0. **Alternatives:** Disable SVG text (broken charts). **Consequences:** An unmaintained parser runs on untrusted fonts inside SVG; mitigations are the font allowlist (only registry fonts) and fuzzing.

## ADR-0019 — Footnotes in v1 (M6)
**Status:** Accepted. **Decision:** `float: footnote`, `::footnote-call/marker`, `footnote-display`, `footnote-policy: auto|line`, `@footnote` area, following the Prince/WeasyPrint model (no normative spec algorithm, R05a F13). **Alternatives:** Defer. **Consequences:** Needs the transactional side-effect model of ADR-0003.

## ADR-0020 — Page floats deferred
**Status:** Accepted. **Decision:** `float: top|bottom`, `float-reference`, `float-defer` are parsed and treated as `float: none` with a warning. **Alternatives:** Implement per css-page-floats-3 (Prince/Vivliostyle partial). **Consequences:** Figures flow with breaks.

## ADR-0021 — Table header/footer repetition rule
**Status:** Accepted. **Context:** css-tables-3 requires ≤ ¼ page each and `break-inside: avoid`; users expect Chrome/WeasyPrint behaviour. **Decision:** Repeat `table-header-group`/`table-footer-group` on every fragment when header + footer ≤ 50% of the fragmentainer block size; else drop the footer, then the header, with `W_TABLE_HEADER_NOT_REPEATED`. Never break right after a header or before a footer. **Alternatives:** Strict spec rule; always repeat. **Consequences:** The exact Chromium condition is UNVERIFIED (verification item).

## ADR-0022 — Form controls render statically
**Status:** Accepted. **Decision:** `<input>`, `<select>`, `<textarea>`, `<button>` render as styled boxes with their value text. No AcroForm in 1.0. **Alternatives:** Real fields (krilla forms unreleased, R08). **Consequences:** Revisit when krilla ships forms.

## ADR-0023 — PDF encryption deferred
**Status:** Accepted. **Decision:** Not in 1.0. Later as a krilla patch with deterministic IVs in `--reproducible` mode. Not combinable with PDF/A. **Alternatives:** lopdf post-process (non-deterministic, reparses everything); qpdf shell-out (dependency). **Consequences:** Users needing encryption post-process with qpdf for now.

## ADR-0024 — Page defaults and per-entry-point compat defaults
**Status:** Accepted. **Decision:** Native default `@page { size: A4; margin: 2cm }`; `--page-size letter` switches. Each compat layer has its own defaults table: wkhtmltopdf (A4, 10 mm, screen media, backgrounds on, smart shrinking), Puppeteer (Letter, margins 0, bare number = px), Playwright, Gotenberg (0.39 in margins), Chrome CLI (1 cm). **Alternatives:** One global default; locale detection. **Consequences:** Shims reproduce legacy pagination at the cost of a defaults table per entry point.

## ADR-0025 — Barcodes through a `recto-barcode:` URL scheme
**Status:** Accepted. **Decision:** `<img src="recto-barcode:qr?data=...">` generates SVG at the resource layer (QR via fast_qr, 1D via rxing, DataMatrix via datamatrix, per R13 §5). It does no I/O and is exempt from fetch policy but not from size limits. **Alternatives:** Custom elements, CSS functions, requiring users to pre-render. **Consequences:** Works in backgrounds and anywhere an image URL does.

## ADR-0026 — MathML deferred
**Status:** Accepted. **Decision:** Not rendered; the content is shown as inline text with `W_UNSUPPORTED_ELEMENT`. **Alternatives:** Render via an equation crate. **Consequences:** Users pre-render equations to SVG.

## ADR-0027 — Letter-spacing uses the browser model by default
**Status:** Accepted. **Context:** The CSS Text spec changed in Aug 2026 (half on each side, none at line edges); browser status UNVERIFIED. **Decision:** Default to the browser model (trailing spacing after each character unit, trimmed at line end); `-recto-letter-spacing-model: spec` opts into the new model. **Alternatives:** Spec model only. **Consequences:** Matches the output users diff against.

## ADR-0028 — minijinja for data mode
**Status:** Accepted. **Context:** R12 §5.7. **Decision:** minijinja 3.0 with fuel, recursion limit, forced HTML auto-escaping, no filesystem loader (includes come from the asset bundle VFS). **Alternatives:** tera, handlebars-rust, upon (no escaping by default), mustache (abandoned). **Consequences:** Jinja syntax familiar to Python users; no Handlebars syntax in 1.0.

## ADR-0029 — Single deny-by-default Fetcher; lenient CLI/library, strict server
**Status:** Accepted. **Context:** R10: the dominant bug class in WeasyPrint, dompdf and Gotenberg is a second fetch path that skips the policy. **Decision:** One `Fetcher`, non-`Default`-constructible, requiring a `Policy`. Every `ResourceKind` is checked, proven by a table-driven test. IP checks use resolved addresses with pinning and per-hop redirect checks. The CLI and library skip blocked resources with warnings; the server fails closed. **Alternatives:** Per-feature checks; deny-lists on URL strings. **Consequences:** Network code ships only with the `net` feature.

## ADR-0030 — Server isolation through supervisor and worker processes
**Status:** Accepted. **Context:** R10 §4.5: OOM and stack overflow abort the process on stable Rust. **Decision:** `recto serve` runs a supervisor that does fetching (broker) and HTTP; workers are separate processes with `RLIMIT_AS`, Landlock and seccomp, no network, killed at the deadline. **Alternatives:** Thread pool in one process. **Consequences:** IPC protocol and worker recycling to design (spec 19).

## ADR-0031 — Binding strategy
**Status:** Accepted. **Decision:** Native in-process: Rust, Node (napi-rs, optionalDependencies platform packages), Python (PyO3 abi3, maturin, GIL released), WASM, .NET (P/Invoke over a small C ABI). Thin HTTP/subprocess clients for Go, PHP, Ruby, Java. **Alternatives:** Native bindings for every language (PHP FFI and Java FFM limits, Go without cgo). **Consequences:** Four native packaging pipelines plus five thin clients (R09).

## ADR-0032 — One `RenderOptions` schema
**Status:** Accepted. **Decision:** A single serde struct, camelCase with snake_case aliases, JSON Schema via schemars, shared by CLI flags, server JSON, bindings and the C ABI. Compat layers translate into it. **Alternatives:** Per-surface option sets. **Consequences:** The schema is the stability surface; additions are minor-version changes.

## ADR-0033 — hayro as the test rasterizer; no AGPL tooling
**Status:** Accepted. **Decision:** Golden tests rasterize PDFs with hayro 0.8 (pure Rust, `simd` off) at 96 dpi and compare with WPT-style fuzzy rules and `image-compare`. pdfium and poppler are nightly cross-checks only. No Ghostscript/MuPDF. Cross-CPU determinism of hayro is UNVERIFIED (verification item). **Alternatives:** Ghostscript (WeasyPrint's choice, AGPL), pdfium binaries. **Consequences:** Rasterizer bugs can mask or fake diffs; the cross-checks mitigate.

## ADR-0034 — MSRV 1.92, edition 2024
**Status:** Accepted. **Context:** krilla 0.8.2 and hayro require 1.92. **Decision:** Pin 1.92 in `rust-toolchain.toml`; raise only with an ADR. **Consequences:** Excludes distro Rust older than that; irrelevant for binary users.

## ADR-0035 — Hyphenation language set excludes Slovak
**Status:** Accepted. **Context:** R07 F9: hypher's `hyph-sk.tex` is GPL-2.0-or-later and compiled by the default `full` feature. **Decision:** `default-features = false` with an explicit list (en, de, fr, es, it, nl, pt, pl, da, sv, nb, fi, cs, … see spec 14); never `slovak` or `full`. **Alternatives:** Ship GPL data; drop hypher. **Consequences:** Slovak users get no `hyphens: auto` until a permissive pattern set exists.

## ADR-0036 — ureq 3 for the `net` feature
**Status:** Accepted. **Context:** R13 §2: ureq's `unversioned::resolver::Resolver` + `Agent::with_parts` allows check-and-pin; ring by default (static musl friendly); reqwest defaults to aws-lc-rs. **Decision:** ureq `~3.4`, `proxy(None)`, `max_redirects(0)` with manual hop checks, body limits, per-phase timeouts. **Alternatives:** reqwest, hand-written HTTP/1.1 client (fallback). **Consequences:** Pin tightly because the API is "unversioned". `scratch` images need `/etc/resolv.conf`.

## ADR-0037 — clap for the main CLI; lexopt for the wkhtmltopdf shim
**Status:** Accepted. **Decision:** clap 4 derive for `recto`; a hand-written lexopt-based parser for the shim because wkhtmltopdf page options bind to the preceding `cover`/`toc`/`page` object. Dispatch by argv[0] stem. **Alternatives:** clap multicall for both. **Consequences:** Two parsers, with a shared mapping table.

## ADR-0038 — Determinism rules and `--reproducible`
**Status:** Accepted. **Decision:** No wall-clock reads; fixed-point layout; sorted collections; content-hash IDs; pinned compression; per-job single thread; `--reproducible` = no system fonts, fixed epoch (`SOURCE_DATE_EPOCH` or 0), document ID from the content hash. Double-render byte equality is asserted on every harness test. **Alternatives:** Best-effort determinism. **Consequences:** Cross-architecture CI hash matrix (DET items).

## ADR-0039 — Horizontal writing mode only
**Status:** Accepted. **Decision:** `writing-mode` other than `horizontal-tb` warns and is ignored. Bidi is supported. **Alternatives:** Vertical CJK. **Consequences:** Documents requiring vertical text are out of scope for 1.0.

## ADR-0040 — Default media type is `print`
**Status:** Accepted. **Decision:** Native `@media print`; `--media screen` switches; the wkhtmltopdf shim defaults to `screen`, Puppeteer entry to `print` unless `emulateMediaType`. **Alternatives:** Always screen (Chrome-like screen quirks). **Consequences:** Templates written for wkhtmltopdf need the shim.

## ADR-0041 — Stable error codes and exit classes
**Status:** Accepted. **Decision:** String codes `E_*`/`W_*`, never renamed; CLI exit classes 0/1/2/3/4/5/6/7/70; the wkhtmltopdf shim returns 0/1/2/3 per R02. **Alternatives:** Numeric-only codes. **Consequences:** Documented in `docs/user/errors.md`.

## ADR-0042 — axum + tokio + tower-http server stack
**Status:** Accepted. **Context:** R13 §1: axum caps bodies at 2 MiB silently; graceful shutdown waits forever; per-route concurrency limits don't compose. **Decision:** axum 0.8, `DefaultBodyLimit` set explicitly, `GlobalConcurrencyLimitLayer` + `LoadShedLayer`, outer shutdown timeout, SSE for live reload, no zstd. **Alternatives:** tiny_http, hyper alone. **Consequences:** Server feature adds a large dependency tree (size UNVERIFIED).

## ADR-0043 — License policy
**Status:** Accepted. **Decision:** Allowed: MIT, Apache-2.0, BSD-2/3, ISC, Zlib, Unicode-3.0, MPL-2.0, OFL-1.1 (fonts), CC0-1.0, BSL-1.0, NCSA (dev-only). No GPL/AGPL/LGPL in binaries or tests. Test data under AGPL/LGPL is fetched at CI time, never committed. **Consequences:** `cargo deny` enforces it; NOTICE file generated.

## ADR-0044 — Background/letterhead PDF import is opt-in
**Status:** Accepted. **Decision:** `--background-pdf` through krilla's `pdf` feature; rejected with PDF/A-2+ and PDF/UA profiles. **Consequences:** Adds hayro-write to opt-in builds only.

## ADR-0045 — `position: fixed` repeats on every page; `sticky` is `relative`
**Status:** Accepted. **Context:** CSS2 §9.6.1; wkhtmltopdf and Chrome templates rely on it. **Decision:** Fixed boxes are laid out per page against the page area; sticky is treated as relative. **Consequences:** Spec 09 defines interaction with margin boxes and breaks.

## ADR-0046 — Visual effects scope
**Status:** Accepted. **Decision:** Support 2D transforms, opacity, box-shadow, linear/radial/conic gradients, border-radius, blend modes. `filter`, `backdrop-filter` and 3D transforms warn and are ignored. **Alternatives:** Rasterize filters. **Consequences:** Filter-heavy templates need pre-rendering.

---

## Proposed (from spec drafting; the lead assigns numbers)

None yet. Entries drafted by spec agents under `## ADR proposals` are merged here during the consistency pass.
