# 04 — Paged-media feature catalog: Prince vs Paged.js vs Vivliostyle

Date: 2026-10-14 · Topic slug: `prince-pagedjs` · Author: Phase-0 research agent

Purpose: a "best in class" catalog of every paged-media feature recto may need, recording which of the three
reference engines supports it, with exact syntax and a source citation, then a ranked v1/later list and the
syntax (standard + vendor aliases) recto should accept. Ends with an architecture note on how Paged.js and
Vivliostyle fragment content.

## Sources inspected

| Name | Version / tag | Commit SHA | License | Last commit | Maintenance assessment |
|---|---|---|---|---|---|
| Paged.js (`pagedjs/pagedjs`) | `package.json` 0.5.0-beta.2 (HEAD of default branch, no tag at HEAD) | `677cdc1e537365e1b3c03c550e2463360164d3fc` | MIT | 2026-10-06 | Active but slow; still "beta" after years; polyfill running inside a browser |
| Vivliostyle.js (`vivliostyle/vivliostyle.js`, `packages/core`) | core 2.45.2 (CHANGELOG 2026-09-23) | `7646a9e488d4c610e62b472feacbfd3d4d79fdf4` | AGPL-3.0 | 2026-10-14 | Very active, monthly releases, strongest spec coverage of the JS engines |
| CSS specs (`w3c/csswg-drafts`, sparse: css-page-3, css-gcpm-3, css-page-floats-3, css-content-3) | ED HEAD | `1c249b342ee7a0dfe0fcf7f7dc75272b1e794d52` | W3C | 2026-10-14 | Editor's drafts, used only to pin standard syntax |
| Prince (YesLogic) | Prince 17 current (released Sep 2026 per https://www.princexml.com/download/ ); docs cited are https://www.princexml.com/doc/ (current) plus versioned /doc/11..15 | n/a (closed source) | Commercial | n/a | Mature (20 yrs), active; source not inspectable — all Prince claims come from WebSearch summaries of princexml.com pages and are cited by URL. Anything not confirmed is marked **UNVERIFIED**. |

Clones live in `/tmp/claude-0/src/prince-pagedjs/{pagedjs,vivliostyle.js,csswg-drafts}`.

Path abbreviations used below:
- `PJ:` = `pagedjs/src/` ; `PJm:` = `pagedjs/src/modules/paged-media/` ; `PJg:` = `pagedjs/src/modules/generated-content/` ; `PJc:` = `pagedjs/src/chunker/`
- `VS:` = `vivliostyle.js/packages/core/src/vivliostyle/`
- `SPEC page3:` = `csswg-drafts/css-page-3/Overview.bs`, `gcpm3:` = `css-gcpm-3/Overview.bs`, `pf3:` = `css-page-floats-3/Overview.bs`, `content3:` = `css-content-3/Overview.bs`
- `P:` = a princexml.com URL

Important framing: **neither Paged.js nor Vivliostyle produces PDF itself.** Both lay out paginated DOM in a
browser and rely on Chromium's print-to-PDF (via pagedjs-cli / vivliostyle-cli, not inspected). Therefore every
"PDF-level" feature (bookmarks, PDF/A, tagging, attachments, page labels, forms) and every "text-level" feature
(hyphenation, justification, fonts, images, SVG, MathML) is Chromium's, not theirs. Their own contribution is
pagination, page boxes, margin boxes and GCPM generated content. Prince is the only one of the three that is a
complete HTML→PDF engine like recto.

---

## 1. Feature catalog

Legend: **Y** = supported (cited), **P** = partial (limits stated), **N** = not supported (verified absence in
source, or documented absence), **B** = delegated to the browser (Chromium) — works only because the host browser
does it, **U** = UNVERIFIED.

### 1.1 `@page` selectors

| Feature | Standard syntax | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| Universal `@page {}` | `@page { … }` | Y | Y — stored under key `"*"`, `PJm:atpage.js:79-80` | Y |
| `:first` | `@page :first` | Y. **Since Prince 16 `:first` = first page of the *document*; group-relative is `:first-of-group`** (P: https://www.princexml.com/releases/16/ , https://www.princexml.com/doc/paged/) | Y — class `pagedjs_first_page`; `PJm:atpage.js:797-801`, selector built in `selectorsForPage` `:2400-2455` | Y — `IsFirstPageAction` `VS:css-page.ts:2906`, specificity +256 `:3266` |
| `:left` / `:right` | `@page :left` | Y (P: https://www.princexml.com/doc/paged/) | Y `PJm:atpage.js:786-796` | Y `VS:css-page.ts:3274-3281` (specificity +1) |
| `:recto` / `:verso` | not a page pseudo-class in css-page-3 (only `break-before: recto/verso`, `SPEC page3:590`) | U | N as selector (only as break values, `PJc:chunker.js:430-479`) | Y (non-standard extension) `VS:css-page.ts:3282-3289`, `IsRectoPageAction :2966` |
| `:blank` | `@page :blank` (`SPEC page3:582-621`) | Y (U for exact version) | Y `PJm:atpage.js:803-807`; blank pages inserted by `addPage(blank)` `PJc:chunker.js:654` | Y `IsBlankPageAction` `VS:css-page.ts:2921` |
| `:nth(An+B)` | `:nth( <an+b> [of <custom-ident>]? )` (`SPEC gcpm3:724`) | Y since 8.0; doc-relative since 16; `:nth-of-group()` for group-relative (P: https://www.princexml.com/releases/16/). A 2016 forum post said `:nth(odd/even)` failed — U today (P: https://www.princexml.com/forum/topic/1518/arbitrary-page-selectors) | P — rewritten to `.pagedjs_page:nth-of-type(An+B)` over *all* pages (`PJm:atpage.js:2440-2452`); hand-rolled An+B parser `getNth` `:1950-1975` (no `of <ident>`, fragile with negatives/`odd`/`even`) | Y including `of <page-type>` (group-relative) `VS:css-page.ts:3229-3256` |
| `:last` | not in spec | N — deliberately omitted (layout loops); workaround is two-pass JS (P: https://www.princexml.com/forum/topic/5012/alternative-to-page-last) | N | N |
| Named pages | `page: <custom-ident>` + `@page name {}` (`SPEC page3:2167`) | Y (P: https://www.princexml.com/doc/paged/) | Y — `page` decl turned into a forced break + `data-page` (`PJm:breaks.js:29-50`), classes `pagedjs_<name>_page` (`PJm:atpage.js:1987-2001`) | Y `tagSelector` → `CheckPageTypeAction`, specificity +65536 `VS:css-page.ts:3214-3219` |
| Named page `:first` | `@page chapter:first` | Y (now `:first-of-group` semantic, see above) | Y via `pagedjs_<name>_first_page` `PJm:atpage.js:2424-2430` | Y |
| Page groups | implicit per css-gcpm-3 §page-groups (`SPEC gcpm3:730-829`) | Y; explicit control `prince-page-group: start | auto` (alias `page-group`) (P: https://www.princexml.com/doc/css-props/ , added Prince 6.0 per https://www.princexml.com/releases/) | P — "first of named run" only (`!start.dataset.splitFrom`) | Y via `:nth(… of name)` |
| Specificity / cascade order of page rules | css-page-3 §cascade | Y | P — fixed insertion order `*`, `:left`, `:right`, `:first`, `:blank`, `nth`, named (`PJm:atpage.js:779-830`), relies on browser specificity of generated classes | Y (computed specificity values above) |

### 1.2 Page size, orientation, bleed, marks

| Feature | Standard syntax | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| `size` lengths | `size: 210mm 297mm` | Y | Y `getSize` `PJm:atpage.js:555-617` | Y grammar `VS:assets.ts:516` |
| Size keywords | spec list: `A5 A4 A3 B5 B4 JIS-B5 JIS-B4 letter legal ledger` (`SPEC page3:~1700-1803`) | Y (`size: Letter`, `size: A4` in docs/forum, P: https://www.princexml.com/doc/paged/); full keyword list U | P — `PJ:polisher/sizes.js`: A0–A10, B4, B5, letter, legal, ledger (no JIS-B*, no C*); also accepts quoted strings `"A4"` | Y superset: a0–a10, b0–b10, c0–c10, jis-b0–jis-b10, letter, legal, ledger (`VS:assets.ts:505-509`) |
| `portrait`/`landscape` | `size: A4 landscape` | Y | Y (`PJm:atpage.js:589-591`, width/height swapped `:960-980`) | Y |
| `page-orientation` (rotate PDF page) | `upright | rotate-left | rotate-right` (`SPEC page3:1884-1886`) | U | N | N (not in grammar) |
| `bleed` | `bleed: auto | <length>` (`SPEC page3:2010-2012`) | Y as `prince-bleed` (bleed only with marks in old versions; later allowed without) (P: https://www.princexml.com/doc/paged/ , https://www.princexml.com/forum/topic/2218/bleed-and-trim-help) — whether unprefixed `bleed` is accepted: U | Y incl. 1–4 values (non-standard) and per `:left/:right` bleed (`PJm:atpage.js:122-157`, `:233-243`); `auto` → 6pt when marks set (`:158-172`) | Y `bleed`, `auto`→6pt when crop (`VS:print.ts:258-269`) |
| `marks` | `marks: none | [crop || cross]` (`SPEC page3:1964-1966`) | Y + `prince-trim`, `prince-mark-length` (24pt), `prince-mark-offset`, `prince-mark-width` (0.1pt) (P: https://www.princexml.com/doc/properties/marks/) | Y — drawn as styled divs; tunables via CSS vars `--pagedjs-crop-color/-offset/-stroke`, `--pagedjs-cross-size` (`PJ:polisher/base.js:39-45,114+`) | Y + `crop-offset`, `crop-marks-line-color` (non-standard, `VS:assets.ts:517-518`) |
| `page-margin-safety` | `none | clamp | add` (`SPEC page3:2073-2075`, new) | U | N | N |
| Page `margin/padding/border` | in `@page` | Y | Y (CSS vars `PJm:atpage.js:882-955`) | Y (`propertiesAppliedToPartition` `VS:css-page.ts:628-660`) |
| Page background | `@page { background }` | Y | Y | Y |

### 1.3 Margin boxes (16)

| Feature | Prince | Paged.js | Vivliostyle |
|---|---|---|---|
| 16 boxes `@top-left-corner … @right-bottom` | Y; `@top`/`@bottom`/`@left`/`@right` accepted as synonyms of `-center`/`-middle` (P: https://www.princexml.com/doc/paged/) | Y — names list `PJm:atpage.js:350-374` (same synonym folding `:380-394`). Bug: list contains `"top-right-corner"` twice and a typo `"right-right-corner"`. | Y — `VS:css-page.ts:690-716+` |
| Spec width/height resolution (min/max-content distribution, §6.3 "margin box variable dimension computation") | Y (U for exactness) | **P — heuristic**: CSS grid `repeat(3,1fr)` default, then a post-layout fix-up using `nowrap` measurement and `minmax(16.66%,1fr) minmax(33%, X%)` (`PJm:atpage.js:2090-2200`). Not the spec algorithm. | **Y — spec algorithm** `distributeAutoMarginBoxSizes` with min/max/fit-content `VS:css-page.ts:1434-1630` |
| `content` in margin boxes incl. counters/strings/elements | Y | Y | Y |
| Vertical-align / text-align defaults per box | Y | Y via base.css grid (`PJ:polisher/base.js:267-370`) | Y `VS:css-page.ts:2176-2182` |

### 1.4 Counters

| Feature | Syntax | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| `counter(page)` | `content: counter(page)` | Y | Y — `.pagedjs_page { counter-increment: page var(--pagedjs-page-counter-increment) }` (`PJ:polisher/base.js:475`) | Y |
| `counter(pages)` | `content: counter(pages)` | Y (P: https://www.princexml.com/doc/gen-content/ — U for exact page) | Y — **post-hoc**: after all pages laid out sets `--pagedjs-page-count` and `counter-reset: pages var(--pagedjs-page-count)` (`PJc:chunker.js:298`, `PJ:polisher/base.js:491`). Works only because browser re-renders; layout that depends on the width of "pages" is never re-run. | Y — dedicated `pagesCounterExprs` (`VS:counters.ts:953`, `:670`) |
| `counter-reset: page N` on elements | `h1 { counter-reset: page 1 }` | Y | Y — converted to per-page rules (`PJm:counters.js:102-133`) | Y |
| `counter-increment: page` on content | css-page-3 page-based counters | Y | Y (`PJm:page-counter-increment.js`, CSS var `--pagedjs-page-counter-increment`) | Y |
| `counter-set` | | Y (U) | U (not handled explicitly in `PJm:counters.js`) | Y (`VS:counters.ts:1117`) |
| Page counter styles (`lower-roman`, `@counter-style`) | | Y | B (browser counters) | Y `VS:counter-style.ts` |
| Footnote counter | `counter(footnote)` | Y | Y (`footnote`, `footnote-marker` counters, `PJm:counters.js:241`) | Y (`VS:assets.ts:1355-1363`) |
| Counters across page boundary for lists (`<ol>` split) | | Y | Y special-case `PJm:lists.js` (start attr fix-up) | Y |

### 1.5 Running content: strings and elements

| Feature | Syntax (css-gcpm-3) | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| `string-set` | `string-set: [ <custom-ident> <content-list> ]# | none` (`SPEC gcpm3:64-65`) | Y (P: https://www.princexml.com/doc/gen-content/) | **P** — only `content()` or `attr()`, one function per identifier, no string concatenation, no `content(before/after/first-letter)` (`PJg:string-sets.js:52-84`, `:150-170`) | Y full `CONTENT_LIST` (`VS:assets.ts:654`) |
| `string(name, first|start|last|first-except)` | gcpm3 | Y; `first-except` documented (P: https://www.princexml.com/doc/gen-content/) | P — `first`, `last` correct; `start` is a geometric heuristic (element top == page-content top) (`PJg:string-sets.js:180-189`); `first-except` always `""` when set on page (`:191-193`) | Y (`VS:counters.ts:838-848`) |
| Running elements | `position: running(name)` + `content: element(name [, policy])` (`SPEC gcpm3:269,359-382`) | Y (P: https://www.princexml.com/doc/gen-content/) | P — **only `first` policy** ("Currently only supports 'first'" `PJg:running-headers.js:74`); `element()` renamed to `element-ident()` before csstree parse (`:247-250`) | Y incl. all four policies (`VS:assets.ts:300`, `VS:counters.ts:206,606,880`) |
| Prince alias for running | `prince-flow: static(name)` + `content: flow(name)` | Y legacy (U for current docs) | N | N |

### 1.6 Cross-references

| Feature | Syntax | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| `target-counter()` | `target-counter(attr(href url), page [, <counter-style>])` | Y; forum: use `attr(href url)` and inline anchors (P: https://www.princexml.com/forum/topic/4254/i-always-get-page-0-when-i-use-cross-referencing) | P — only `attr(...)` form (`PJg:target-counters.js:144-147`), page counter value recovered by reading computed `counter-reset/increment` strings of the target page (`:166-195`) | Y incl. `STRING | URI` and `ATTR` forms (`VS:assets.ts:289-290`) |
| `target-counters()` | `target-counters(attr(href url), section, ".")` | Y (P: https://www.princexml.com/doc/gen-content/) | **N** (no handler; only `target-counter`) | Y (`VS:assets.ts:291-292`) |
| `target-text()` | `target-text(attr(href url), content|before|after|first-letter)` | Y (U for which keywords) | P — `content/before/after/first-letter`, before/after only from the *last seen* ::before/::after rule (`PJg:target-text.js:40-75`, `:100-184`) | Y + `marker` (`VS:assets.ts:293-294`) |
| `leader()` | `leader(dotted | solid | space | <string>)` (`SPEC content3:758`) | Y (P: https://www.princexml.com/doc/gen-content/) | **N** (no occurrence in `PJ:`) | Y `visitFuncLeader` `VS:css-cascade.ts:4670-4743`, marks `data-viv-leader` `VS:counters.ts:1926-1930` |
| Internal links → PDF link annotations | `<a href="#id">` | Y | B | B |

### 1.7 Footnotes

| Feature | Syntax (css-gcpm-3) | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| `float: footnote` | gcpm3 `:470` | Y (P: https://www.princexml.com/doc/11/footnotes/) | Y `PJm:footnotes.js:50-64` | Y (footnote is a subclass of `PageFloat`, `VS:footnotes.ts:34`) |
| `@footnote` area in `@page` | `@page { @footnote { … } }` | Y | Y `replaceNotes` `PJm:atpage.js:409-425` | Y (`VS:assets.ts:895-901`) |
| `::footnote-call` / `::footnote-marker` | gcpm3 | Y (P: https://www.princexml.com/doc/11/footnotes/) | Y — rewritten to `[data-footnote-call]`/`[data-footnote-marker]` attribute selectors (`PJm:footnotes.js:102-160`) | Y (`VS:assets.ts:1355-1363`) |
| `footnote-display: block | inline | compact` | gcpm3 `:481-482` | Y block/inline/compact (P: https://www.princexml.com/doc/properties/footnote-display/) | P — stored; only `inline` has CSS (`PJ:polisher/base.js:470`); `compact` = block | Y (`VS:assets.ts:655`, `VS:semantic-footnote.ts:187`) |
| `footnote-policy: auto | line | block` | gcpm3 `:614-615` | P/U — Prince uses `prince-footnote-policy` (forum mentions `keep-with-line`, applied to the paragraph) — official doc not found → **UNVERIFIED** (P: https://www.princexml.com/forum/topic/2656/) | Y all three, geometric (`PJm:footnotes.js:320-350`) | P — `auto | line` (no `block`) (`VS:assets.ts:656`, `VS:footnotes.ts:264`) |
| Marker position | `footnote-style-position: inside | outside` (Prince ext.; CSS has `::footnote-marker` + `list-style-position`) | Y (P: https://www.princexml.com/doc/11/properties/footnote-style-position/) | N | N |
| Footnote body split across pages | | Y | Y — overflow in footnote area extracted and carried (`PJm:footnotes.js:509-540`) | Y |
| Semantic (EPUB/DPUB) footnotes `aside[role=doc-footnote]` | | U | N | Y (`VS:semantic-footnote.ts`, `VS:assets.ts:1369-1392`) |
| Sidenotes / margin notes | Prince: `float: prince-column-footnote`, `-prince-margin-note`? | U | N | N |

### 1.8 Page floats

| Feature | Syntax (css-page-floats-3) | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| `float: top | bottom` (block-start/end, snap-block) | `pf3:212-213` | Y — `float` is a shorthand of `-prince-float-reference` + `-prince-float-placement` (+ modifier); since Prince 14 `float: top` defaults to **column** reference; default placement `top-bottom` (P: https://www.princexml.com/howcome/2021/guides/float/ , https://www.princexml.com/doc/css-props/) | **N** | Y incl. `snap-block`, logical sides, `inside/outside` (`VS:assets.ts:523`, `VS:page-floats.ts:405-420,1710-1723`) |
| `float-reference: inline | column | region | page` | `pf3:115-116` | Y as `-prince-float-reference` (unprefixed alias U) | N | Y (`VS:page-floats.ts:62-70`) |
| `float-defer` | `<integer> | last | none` (`pf3:668-669`) | Y as `float-defer-page`, `float-defer-column` (P: https://www.princexml.com/doc/css-props/) | N | **N** (no `float-defer` in `VS:`; only `float-min-wrap-block`) |
| `clear: top|bottom|page|column|all|same` | `pf3:466-467` | U | N | Y (`VS:assets.ts:521`) |
| `float-offset` | `pf3:808` | U | N | N |
| Floats never placed before anchor page | | documented limitation (P: https://www.princexml.com/forum/topic/4819/) | — | — |

### 1.9 Fragmentation controls

| Feature | Prince | Paged.js | Vivliostyle |
|---|---|---|---|
| `break-before/after: page | left | right | recto | verso | avoid` + legacy `page-break-*` aliases | Y | Y — legacy normalized (`PJm:breaks.js:54-67`); left/right/recto/verso insert blank pages (`PJc:chunker.js:428-480`) | Y (`VS:assets.ts:348-350`) |
| `break-inside: avoid` | Y | Y but **only whole-element avoid**: if overflow found and ancestor has `break-inside: avoid`, whole container moves (`PJc:layout.js:496-510,1486-1500`); `avoid-page`/`avoid-column` U | Y (penalty-based `findAcceptableBreakPosition` `VS:layout.ts:3454-3463`) |
| `orphans` / `widows` | Y | **B** — works only because the page area is a CSS multicol container and Chromium applies widows/orphans at column breaks (`PJc:page.js:61-63`, `PJ:polisher/base.js:385-390`) | Y (`VS:layout.ts:2535,2605` line-break check points) |
| `box-decoration-break: slice|clone` | U | B | Y (U exact) |
| Table header/footer repeat on each page | Y | Y — `rebuildTableFromBreakToken`, `getAncestorTheadSizes` (`PJc:layout.js:452,904`) | Y + non-standard `repeat-on-break: auto|none|header|footer` (`VS:assets.ts:659`, `VS:repetitive-element.ts`) |
| Break inside table rows / rowspans | Y | P — `rowspanNeedsBreakAt` (`PJc:layout.js:1365`) | Y |
| Hyphen glyph added when a word is split at page end | n/a | Y (inserts U+2011 `PJc:layout.js:1725-1740`, `settings.hyphenGlyph`) | B |
| Fragmenting flex / grid across pages | **N in Prince**: flex "with the exception of page breaking/fragmentation" (Prince 12+), grid "limited to a single page with no fragmentation" (Prince 16) (P: https://www.princexml.com/doc/css-refs/ , https://www.princexml.com/releases/16/); Prince 17 changes U | B-ish — top-level children walked individually; flex/grid containers measured by Chromium | Y/P (browser layout per column) |

### 1.10 Bookmarks / outline

| Feature | Syntax | Prince | Paged.js | Vivliostyle |
|---|---|---|---|---|
| `bookmark-level` | `none | <integer [1,∞]>` (`SPEC content3:1337-1338`) | Y — `prince-bookmark-level` (`-prince-` and unprefixed aliases); UA sheet sets h1–h6 → 1–6 (P: https://www.princexml.com/doc/properties/prince-bookmark-level/ , https://www.princexml.com/doc/pdf-bookmarks/) | N in core (pagedjs-cli outline: U) | N in core (`grep -il bookmark VS:*.ts` = 0 hits; vivliostyle-cli builds outline from TOC: U) |
| `bookmark-label` | `<content-list>` (`content3:1371-1372`) | Y default `content()` (accepts `attr()`, counters) | N | N |
| `bookmark-state` | `open | closed` (`content3:1416-1417`) | Y default `open` | N | N |
| Bookmark from `display:none` element | — | N (workaround `visibility:hidden`) (P: https://www.princexml.com/forum/topic/5092/) | — | — |

### 1.11 PDF-specific features (Prince only; Paged.js/Vivliostyle = Chromium's PDF output = N)

| Feature | Prince syntax | Citation |
|---|---|---|
| PDF profiles | `--pdf-profile=` PDF/A-1a, PDF/A-1b, PDF/A-2a/2b, PDF/A-3a/3b, PDF/UA-1, PDF/X-1a, PDF/X-3, PDF/X-4 (PDF/A-3b → PDF 1.7, PDF/UA-1 → ISO 14289-1 on 1.7, PDF/X-4 → ISO 15930-7:2008 on 1.6). Exact full list in current version U. | https://www.princexml.com/doc/prince-output/ , https://www.princexml.com/doc/command-line/ |
| Fail-safes | `--fail-pdf-profile-error`, `--fail-pdf-tag-error` (Prince 14) | https://www.princexml.com/releases/14/ |
| Tagged PDF | **off by default**; on via `--tagged-pdf`, `prince-pdf-tagged`, or automatically for PDF/A-*a and PDF/UA-1 | https://www.princexml.com/doc/prince-output/ |
| Tag overrides | `-prince-pdf-tag-type: auto | <PDF tag> | none`, `prince-alt-text: auto | none | <string>` (Prince 13), acronym expansion | https://www.princexml.com/releases/13/ , https://www.princexml.com/doc/13/css-props/ |
| File attachments | `--attach=FILE`, `--attach-data/-source/-alternative/-supplement/-unspecified` set AFRelationship (needed for ZUGFeRD/Factur-X invoices on PDF/A-3); HTML `<link rel="attachment">` U | https://www.princexml.com/doc/prince-output/ |
| XMP | `--pdf-xmp=FILE`, `prince-pdf-xmp: <url>` (data: URL ok), `--pdf-xmp-metadata` | https://www.princexml.com/doc/prince-output/ , https://princexml.com/doc/properties/prince-pdf-page-layout |
| Page labels | `@page { prince-pdf-page-label: auto | <content> }` e.g. `counter(page, lower-roman)` (Prince 8.0) | https://www.princexml.com/doc/css-props/ , https://www.princexml.com/doc/15/prince-output/ |
| Viewer prefs | `@prince-pdf { prince-pdf-page-layout: single-page … two-column-right; prince-pdf-page-mode: auto | show-attachments | show-bookmarks | fullscreen; prince-pdf-open-action: none | [print || zoom(...) || command(ident)] }`; `prince-pdf-paper-tray` (syntax U) | https://www.princexml.com/doc/css-at-rules/ , https://www.princexml.com/doc/13/css-props/ |
| Link/destination control | `prince-pdf-destination`, `prince-pdf-link-type` (names only; syntax **UNVERIFIED**) | https://www.princexml.com/doc/css-props/ |
| Forms | `--pdf-forms` + `-prince-pdf-form: auto | enable | disable`, `-prince-pdf-form-field-font-size`, `<input type="prince-pdf-signature">` | https://www.princexml.com/doc/prince-output/ |
| DPI control | `--pdf-dpi` / `pdf-dpi` JSON job option (2026 roadmap, release U) | https://www.princexml.com/roadmap/ |
| Encryption/permissions | `--encrypt`, `--user-password`… (**UNVERIFIED** — not in fetched results) | — |
| Colour: CMYK, output intents for PDF/X | `cmyk()` colour, `--pdf-output-intent` (**UNVERIFIED**) | — |

Vivliostyle has a CMYK store (`VS:cmyk-store.ts`) for its CLI's press-ready path (not inspected further).

### 1.12 Layout modules

| Feature | Prince | Paged.js | Vivliostyle |
|---|---|---|---|
| Multicol `columns`, `column-fill: auto | balance` | Y (P: https://www.princexml.com/doc/css-props/) | B (but conflicts: page area itself is multicol) | B + own handling `VS:columns.ts` |
| `column-span: all` | Y since 8.1; `column-span: <integer>` for column floats (Prince ext.); `none` = 1 since 13.2 (P: https://www.princexml.com/releases/) | B | Y `VS:layout.ts:2305-2336` |
| Flexbox | Y since 12, no fragmentation, no `visibility:collapse`, no vertical WM; `gap` since 16 (P: https://www.princexml.com/doc/css-refs/ , https://www.princexml.com/releases/16/) | B | B |
| Grid | Y since 16, single page only, no baseline alignment / auto-fit collapsing / fit-content (P: https://www.princexml.com/releases/16/ , https://www.princexml.com/forum/topic/5099/) | B | B |
| Tables (auto/fixed, rowspan, thead/tfoot repeat) | Y | B + chunker re-insertion of thead | B + repeat-on-break |
| `position: fixed` → repeat on every page | Y (repeats on every page — U) | Y — converted to `absolute` and cloned to every page (`PJm:position-fixed.js:41-90`) | U |
| Change bars | **N native**; two-pass via undocumented box-tracking API (P: https://www.princexml.com/forum/topic/3516/changebars) | N | N |
| Line numbering | **N native** (roadmap TODO; workaround `prince-script()`) (P: https://www.princexml.com/roadmap/ , https://www.princexml.com/forum/topic/4318/) | N | N |
| Baseline grid | P — `-prince-baseline-grid: auto | new | none` only pads boxes to whole grid lines; no true snapping (P: https://www.princexml.com/doc/11/text-formatting/) | N | N |

### 1.13 Text

| Feature | Prince | Paged.js | Vivliostyle |
|---|---|---|---|
| `hyphens: auto` (language from `lang`) | Y (own dictionaries) (P: http://www.princexml.com/doc/properties/hyphens/) | B | B |
| `hyphenate-limit-lines` | Y `-prince-hyphenate-lines` (alias `hyphenate-lines`, `prince-hyphenate-limit-lines` since 12) (P: https://www.princexml.com/doc/10/properties/prince-hyphenate-lines/ , https://www.princexml.com/releases/12/) | B | B (passthrough list `VS:css-cascade.ts:80-81` contains `hyphenate-limit-chars`, `hyphenate-limit-last`) |
| `hyphenate-limit-chars` | P — `-prince-hyphenate-before/-after` (min letters before/after); `hyphenate-limit-chars` itself **UNVERIFIED** | B (Chromium supports `hyphenate-limit-chars` since 109 — U) | B |
| `hyphenate-character` | U | B (+ own U+2011 at page split) | B (`VS:assets.ts:368`) |
| `text-justify` | P — `text-justify: auto | prince-cjk` (alias `-prince-text-justify`, Prince 8.1) (P: https://www.princexml.com/doc/11/properties/prince-text-justify/) | B | B (`VS:assets.ts:530`) |
| Line-breaking heuristics | `prince-linebreak-magic: auto | none` (P: https://www.princexml.com/doc/11/properties/prince-linebreak-magic/) | B | B |
| CJK text-spacing, ruby, emphasis | Y (U breadth) | B | Y — `text-spacing-trim`, `text-autospace`, ruby (`VS:assets.ts:525-545`, `VS:text-polyfill.ts`, `VS:ruby-emphasis.ts`) |
| `text-align-last`, `hanging-punctuation` | U | B | Y/B (`VS:assets.ts:531,546`) |

### 1.14 Replaced content, fonts, scripting

| Feature | Prince | Paged.js | Vivliostyle |
|---|---|---|---|
| Image formats | JPEG, PNG, TIFF, GIF, WebP, AVIF (WebP+AVIF since 15); BMP → error (P: https://www.princexml.com/doc/graphics/ , https://www.princexml.com/releases/15/) | B | B |
| PDF as image input | **UNVERIFIED** (search summary said no; I believe newer Prince supports `<img src=x.pdf>` — unconfirmed) | B (no) | B |
| SVG | SVG 1.1 with exceptions (P: https://www.princexml.com/doc/graphics/) | B | B |
| MathML | P — basic; `table-baseline` for MathML (7.1); STIX integration on roadmap (P: https://www.princexml.com/roadmap/) | B (Chromium MathML Core) | B (UA sheet `VS:assets.ts:1348`) |
| Fonts: TTF/OTF/CFF, TTC, WOFF, WOFF2 (13+), variable fonts + CFF2 (16) | Y (P: https://www.princexml.com/releases/13/ , https://www.princexml.com/releases/16/) | B | B |
| Colour fonts | SVG-in-OT, CBDT/CBLC, sbix (limits); **COLR UNVERIFIED** (P: https://www.princexml.com/doc/styling/ , https://www.princexml.com/roadmap/) | B | B |
| JavaScript | Opt-in: `--javascript`; ES6-ish engine; `Prince.registerPostLayoutFunc(f)` re-layouts when DOM changes; `--max-passes=N`; `prince-script()` CSS function (P: https://www.princexml.com/doc/javascript/) | Paged.js **is** JS; it strips document `<script>` by default (`PJ:modules/filters/scripts.js`) | Is JS |
| Form fields as AcroForm | Y (`--pdf-forms`, see §1.11) | N | N |

---

## 2. Architecture insight: how the JS engines fragment

### 2.1 Paged.js (DOM-walk + measure + break token)

Pipeline (`PJ:polyfill/previewer.js` → `PJ:polisher/*` → `PJc:chunker.js` → `PJc:page.js` → `PJc:layout.js`):

1. **Polisher / CSS rewrite.** css-tree parses author CSS; each handler's `onAtPage`, `onDeclaration`,
   `onPseudoSelector`, `onContent` hooks *rewrite paged-media CSS into ordinary screen CSS*: `@page` rules become
   rules on `.pagedjs_page.pagedjs_first_page …` (`PJm:atpage.js:2400-2455`), margin boxes become a CSS-grid of
   divs (`PJ:polisher/base.js:267-370`), page size/margins/bleed become CSS custom properties
   (`--pagedjs-width`, `--pagedjs-margin-top`, `--pagedjs-bleed-*`, `PJm:atpage.js:1177-1300`), `string()`
   becomes `var(--pagedjs-string-first-<name>)`, `target-counter()` becomes `counter(target-counter-<uuid>)`
   (`PJg:target-counters.js:85-117`). Declarations that the browser must not see are removed from the AST.
2. **Content parser.** Source DOM cloned into a fragment; every element tagged with `data-ref` (UUID) so split
   pieces can be correlated (`PJc:parser.js`); handlers stamp `data-break-before`, `data-page`,
   `data-counter-*-reset/increment`, `data-note` attributes (`PJm:breaks.js:106-131`, `PJm:counters.js:254-312`).
3. **Page loop** — `async *layout()` generator (`PJc:chunker.js:517-607`): for each page: `handleBreaks()`
   (insert blank pages for left/right/recto/verso parity, `:428-480`) → `addPage()` clones a page template →
   `beforePageLayout` hooks → `page.layout(content, breakToken)` → `afterPageLayout` hooks (strings, running
   elements, target-counters, footnote overflow) → `finalizePage` (margin-box width fix-up) → `yield breakToken`.
4. **Filling a page** — `Layout.renderTo()` (`PJc:layout.js:~95-240`): a tree walker over the source appends
   nodes into the page wrapper *shallowly* (element shell, then children) and periodically calls
   `findBreakToken()`; forced breaks queue in `forcedBreakQueue`. If the new token equals the previous one →
   "Unable to layout item" (infinite-loop guard, `:216-219`).
5. **Overflow detection** — the page content area is a **multicol container whose column width = page width
   and column gap ≈ margins+bleed+1000px** (`PJc:page.js:61-63`, `PJ:polisher/base.js:49,385-390`). Content
   that does not fit flows into the "next column", i.e. off to the right. `hasOverflow` / `findOverflow`
   (`PJc:layout.js:844,1414-1575`) compare `getBoundingClientRect()` of rendered nodes against the area's bounds
   (with careful sub-pixel rounding, comment at `:1420-1430`) to find the first overflowing node.
   This trick also gives **widows/orphans and `break-inside` inside lines for free from Chromium's column
   fragmentation** — Paged.js never implements them.
6. **Text splitting** — `textBreak()` (`PJc:layout.js:1618-1714`) walks words then letters with `Range`
   `getBoundingClientRect()` until one exceeds bounds → offset. A `Range` from that point to the end is
   `extractContents()`-ed (`createOverflow`, `removeOverflow`, `:514-630,1716`) and a `BreakToken(node, [Overflow])`
   (`PJc:breaktoken.js`, `PJc:overflow.js`) records where the next page resumes. Split elements get
   `data-split-from` / `data-split-to` so CSS can suppress margins/text-indent on continuations
   (`PJm:splits.js`).
7. **Avoid rules** — `break-inside: avoid` is enforced by moving the whole ancestor (`avoidBreakInside`,
   `:496-510`); `break-before/after: avoid` by walking back to an earlier break opportunity (`:1265-1290`).
8. **Re-layout** — each page installs a `ResizeObserver` / `overflow`/`underflow` listeners
   (`PJc:page.js:246-370`). If a page overflows *after* rendering (late fonts/images), the chunker removes all
   following pages and re-renders from that page's break token (`PJc:chunker.js:674-704`). Underflow is ignored
   (commented-out). `counter(pages)` is resolved only once at the end via a CSS variable (`:298`), so
   "Page X of Y" never triggers re-layout.

Implications for recto: (a) the break-token/resume-point model (node + offset + forced-break queue) is the right
abstraction and maps directly to a Rust fragmentainer API; (b) Paged.js's correctness rests on Chromium's line
layout and column fragmentation, so recto must implement widows/orphans, avoid-break ladders and line-level
splitting itself; (c) its per-word `getBoundingClientRect` search is O(words) per page and is why Paged.js is
slow on 1000-page documents — recto should break at line boxes produced by its own line breaker, not by
re-measuring; (d) post-hoc page totals via a variable is a cheap, acceptable approach for `counter(pages)` if
margin boxes are laid out after body pagination (only margin boxes depend on it).

### 2.2 Vivliostyle (own layout over browser-measured view tree, penalties + retry)

- Page masters / partitions (`VS:page-master.ts`, `VS:css-page.ts`) model `@page` and margin boxes as
  partitions with spec sizing (`distributeAutoMarginBoxSizes` `:1434-1630`).
- Content flows into `Column` containers (`VS:layout.ts:448`) — `layoutBreakableBlock` (`:2651`) lays out
  view nodes, collects **break positions with penalties** (`VS:break-position.ts`, `EdgeBreakPosition :74`) and
  picks the best via `findAcceptableBreakPosition()` (`VS:layout.ts:3454-3463`) — i.e. a
  "breakpoint appeal" ladder like Chromium LayoutNG: forced > natural > avoid-violating.
- Line-level breaks: `findAcceptableBreakInside` with check-points per line (`VS:layout.ts:2535,2839`) →
  real widows/orphans.
- `LayoutRetryer`s (`VS:layout-retryers.ts:26`) redo a column layout with modified constraints (e.g. after
  a page float or footnote changes the available block size; `footnote-policy: line` constraint
  `VS:footnotes.ts:264`). Footnotes are implemented *as page floats* (`VS:footnotes.ts:34`).
- `counter(pages)`, `target-counter` to later pages, and running strings are resolved via a counters store with
  deferred expressions (`VS:counters.ts:953-1120`) and re-layout of affected pages.

Implication: a penalty-based breakpoint chooser + "retry this fragmentainer with new exclusions" loop is the
proven structure for footnotes and page floats; recto should design its fragmentainer so a page can be
re-laid-out with a different reserved footnote/float area without re-laying out previous pages.

---

## 3. Ranked feature list for recto

### 3.1 Tier 1 — table stakes for invoices / reports / contracts / statements (v1 must-have)

Ranked by how often real business templates use them (from the wkhtmltopdf/Chrome/WeasyPrint replacement
target):

1. `@page { size; margin }` with keywords `A3 A4 A5 B4 B5 JIS-B4 JIS-B5 letter legal ledger` + `portrait|landscape` (accept case-insensitively; also accept the Vivliostyle superset a0–a10/b0–b10/c0–c10 — cheap table).
2. `@page :first`, `:left`, `:right`, `:blank`, named pages (`page:` property) with group-`:first` semantics.
3. All 16 margin boxes with the **spec sizing algorithm** (Vivliostyle-correct, not Paged.js's heuristic) + `@top`/`@bottom`/`@left`/`@right` synonyms.
4. `counter(page)`, `counter(pages)`, page counter styles (decimal, lower/upper-roman, lower/upper-alpha), `counter-reset: page N` on elements.
5. `break-before/after/inside` incl. `page`, `left`, `right`, `recto`, `verso`, `avoid`, `avoid-page`; legacy `page-break-*` aliases.
6. `orphans`/`widows` (default 2), table `thead`/`tfoot` repetition, table row splitting, `break-inside: avoid` on rows.
7. Running headers/footers: `string-set` + `string(name, first|start|last|first-except)` with full `content()`/`attr()`/literal concatenation.
8. Running elements: `position: running(name)` + `content: element(name, first|start|last|first-except)` (invoices put logo/address blocks in headers).
9. `target-counter(attr(href url), page [, style])` + `leader(dotted|solid|space|"…")` — TOC "Section ....... 7".
10. Internal/external links → PDF link annotations; named destinations for `id`s.
11. Bookmarks: `bookmark-level`, `bookmark-label`, `bookmark-state` with UA default h1–h6 → 1–6.
12. PDF metadata from `<title>`, `<meta name=author|subject|keywords>`; page labels optional.
13. Tagged PDF (recto default ON — Prince defaults OFF) and PDF/A-3b (+ attachments with AFRelationship, for ZUGFeRD/Factur-X e-invoices) and PDF/UA-1 opt-in.
14. `position: fixed` → repeated on every page (Paged.js behaviour; cheap and commonly used in Chrome-era templates for headers/watermarks).
15. Images JPEG/PNG(+alpha)/GIF(first frame)/WebP; SVG (static subset); fonts TTF/OTF/WOFF/WOFF2, subsetting.
16. Flex and tables (non-fragmenting flex is acceptable — Prince itself ships flex without fragmentation).

### 3.2 Tier 2 — strong v1.x (cheap given Tier 1 machinery)

- `:nth(An+B [of name])` page selector (use a real An+B parser; doc-relative per css-gcpm-3, group-relative with `of`) and Prince 16 aliases `:first-of-group`, `:nth-of-group()`.
- `target-counters()`, `target-text(…, content|before|after|first-letter)`.
- Footnotes: `float: footnote`, `@footnote`, `::footnote-call`, `::footnote-marker`, `footnote-display: block|inline`, `footnote-policy: auto|line` (contracts and legal reports use footnotes).
- `bleed`, `marks: crop cross` (certificates, tickets, labels sent to print shops).
- Multicol with `column-span: all`, `column-fill` (newsletters/reports, "multicol where cheap").
- `hyphens: auto` + `hyphenate-limit-chars`, `hyphenate-limit-lines`, `hyphenate-character`.
- PDF viewer prefs (`@prince-pdf`-style page layout/mode), page labels (`prince-pdf-page-label`), XMP injection.
- AVIF/TIFF images.

### 3.3 Tier 3 — differentiating for high-end publishing (later)

- Page floats: `float: top|bottom|snap-block` + `float-reference: column|page` + `float-defer` (Prince is the only engine with `float-defer`).
- `footnote-display: compact`, `footnote-policy: block`, `footnote-style-position`, sidenotes.
- Page groups with explicit `page-group: start` control.
- Grid (Prince itself is single-page only — fragmentation can come much later).
- PDF/X-4, CMYK colour, output intents, spot colours.
- Baseline grid, line numbering, change bars (no engine has native support — genuine differentiator).
- `text-justify: inter-character`, CJK text-spacing, ruby, vertical writing (Vivliostyle is the leader here).
- AcroForm fields, signature fields.
- Colour fonts (COLRv0/v1, SVG-in-OT, CBDT, sbix), variable fonts.
- MathML Core.
- `page-orientation: rotate-left|rotate-right`, `page-margin-safety`.
- Never: document JavaScript (`registerPostLayoutFunc`, `prince-script()`) — out of scope by ADR.

### 3.4 Syntax recto should accept (standard first, vendor aliases mapped)

| Standard (canonical) | Aliases to accept (map to the same property) | Notes |
|---|---|---|
| `bookmark-level/label/state` | `-prince-bookmark-*`, `prince-bookmark-*` | Prince accepts both `-prince-` and `prince-` prefixes (P: https://www.princexml.com/doc/css-props/) |
| `bleed` | `-prince-bleed`, `prince-bleed` | Prince semantics: bleed outside trim; `auto` = 6pt if crop marks |
| `marks` | — | add `prince-trim`, `prince-mark-length/offset/width`, Vivliostyle `crop-offset`, `crop-marks-line-color` as optional extensions |
| `string-set`, `string()` | — | |
| `position: running(x)`, `element(x)` | Prince legacy `prince-flow: static(x)` / `content: flow(x)` (U) | |
| `float: footnote` | `-prince-footnote` (U) | |
| `footnote-display`, `footnote-policy` | `prince-footnote-policy` (U) | |
| `float-reference`, `float-defer` | `-prince-float-reference`, `-prince-float-placement`, `float-defer-page`, `float-defer-column` | Prince 14+ `float: top` defaults to column reference — recto should follow the spec (default `float-reference: inline` → page float only when `float-reference: page`), and document the difference |
| `hyphenate-limit-lines` | `-prince-hyphenate-lines`, `hyphenate-lines`, `prince-hyphenate-limit-lines` | |
| `hyphenate-limit-chars: <total> <before> <after>` | map `-prince-hyphenate-before/after` into it | |
| `text-justify` | `-prince-text-justify` (`prince-cjk` ≈ `inter-character`) | |
| `page-break-before/after/inside` | → `break-*` (`always` → `page`) | CSS2 legacy, mandatory |
| `@page :nth(An+B of name)` | `:first-of-group`, `:nth-of-group(An+B)` (Prince 16) | |
| `page-group` (non-standard) | `prince-page-group`, `-prince-page-group` | |
| PDF settings | `@prince-pdf { prince-pdf-page-layout; prince-pdf-page-mode; prince-pdf-open-action; prince-pdf-xmp }`, `@page { prince-pdf-page-label }`, `prince-pdf-tagged`, `-prince-pdf-tag-type`, `prince-alt-text`, `-prince-pdf-form` | Accept as an opt-in "Prince compatibility" layer; recto-native names can be `-recto-pdf-*` with the Prince names as aliases. Unknown `-prince-*` → warn, not error. |
| `repeat-on-break` | `-viv-repeat-on-break` | Vivliostyle extension, useful for tables/sections |
| `@page :recto/:verso` | — | Vivliostyle extension; trivially = `:right/:left` in LTR |
| Paged.js-only quirks | `bleed` with 2–4 values, quoted size `"A4"` | accept leniently (warn) |

---

## Findings that affect recto's design

1. **Only Prince is a true peer.** Paged.js and Vivliostyle delegate text layout, fonts, images, hyphenation,
   flex/grid/tables and the entire PDF writer to Chromium. Any "they support X" for those categories means
   "Chromium supports X"; recto must implement those itself. The JS engines are useful as *GCPM semantics*
   references, not layout references.
2. **Margin-box sizing:** implement the css-page-3 variable-dimension algorithm as Vivliostyle does
   (`VS:css-page.ts:1434-1630`); Paged.js's grid heuristic (`PJm:atpage.js:2090-2200`) gives wrong widths for
   asymmetric content and should not be copied.
3. **Break token = (node path, text offset, forced-break queue)** (`PJc:breaktoken.js`) is the right resume
   abstraction; for streaming page emission recto should make each page's layout a pure function of
   (previous break token, page context), so pages can be emitted as soon as their margin boxes are resolvable.
4. **Two late-binding values break streaming:** `counter(pages)` and forward `target-counter()`. Paged.js
   resolves `pages` post-hoc via a variable and never re-flows (`PJc:chunker.js:298`); recto can do the same —
   lay out body content streaming, but emit margin boxes / TOC entries that reference forward data only after
   resolution. Practical design: two-phase (paginate body → resolve counters → paint margin boxes) with an
   optional bounded second pass when a resolved string changes a line break in body text (e.g. TOC page
   numbers). Prince's no-`:last` decision shows the loop risk is real; cap passes (Prince: `--max-passes`).
5. **Use a penalty-based breakpoint chooser** (Vivliostyle `findAcceptableBreakPosition`) to implement
   avoid/orphans/widows correctly; Paged.js gets these only from Chromium's multicol trick.
6. **Footnotes as a special page float** (Vivliostyle `Footnote extends PageFloat`) gives one mechanism for
   footnotes now and page floats later; the page fragmentainer needs "re-layout this page with a reserved
   block-end area of height H" without disturbing earlier pages.
7. **Fragmenting flex and grid is not table stakes** — Prince ships flex (12+) and grid (16+) without
   fragmentation. recto v1 can treat flex/grid containers as monolithic or break only between flex lines /
   grid rows, and document it.
8. **Tagged PDF by default is a differentiator**: Prince defaults OFF; only PDF/A-*a and PDF/UA-1 force it.
9. **PDF/A-3b + AFRelationship attachments** (Prince `--attach-data` etc.) is the e-invoice (ZUGFeRD/Factur-X)
   enabler — high value for the invoice use-case; plan for it in the PDF writer early (embedded files,
   XMP extension schema).
10. **Vendor-prefix compatibility layer is cheap and valuable**: a property-alias table (`-prince-X`/`prince-X`
    → `X`) and `page-break-*` → `break-*` mapping at parse time lets Prince-authored templates run
    unchanged. Unknown `-prince-*` should warn, not fail.
11. **Page-size keyword table**: use the spec list plus Vivliostyle's superset (A/B/C 0–10, JIS-B 0–10) —
    Paged.js's list is incomplete (no JIS, no C-series).
12. **`:nth()` must be a real An+B parser** with `of <name>` and doc-relative default (css-gcpm-3, Prince 16
    semantics); Paged.js's string-splitting parser (`PJm:atpage.js:1950-1975`) is a cautionary example.
13. **`position: fixed` → repeat on every page** is a cheap compat win for Chrome-era templates (Paged.js
    `position-fixed.js`); Chrome print does the same.
14. **No engine has native change bars, line numbering, or true baseline grid** — these are optional
    differentiators, not parity items.
15. Watch spec additions not yet implemented anywhere inspected: `page-orientation`, `page-margin-safety`,
    `float-offset` — low priority.

## Recommendation

Target Prince-level GCPM semantics with Vivliostyle-level spec fidelity for the Tier-1 list in §3.1, using the
standard property names as canonical and a parse-time alias table for `-prince-*`/`prince-*`, `page-break-*`,
and a few Vivliostyle/Paged.js extensions (§3.4). Architect fragmentation around (a) break tokens à la Paged.js,
(b) a penalty-ranked breakpoint chooser and per-page retry à la Vivliostyle, and (c) a deferred
margin-box/generated-content resolution phase so body pages can stream while `counter(pages)` and forward
`target-counter()` are resolved later with a bounded re-layout pass. Defer page floats, `float-defer`, grid
fragmentation, PDF/X, forms and baseline grid to post-v1; ship PDF/A-3b + attachments and PDF/UA-1 + tagged-by-
default in v1 since they are the strongest differentiators against wkhtmltopdf/Chrome for invoices.

## Open questions / UNVERIFIED items

- Prince 17 (Sep 2026) release notes were not retrievable; any changes in 17 (grid fragmentation? COLR fonts?
  `:last`?) are UNVERIFIED.
- Prince: exact current list of `--pdf-profile` values (PDF/A-4? PDF/UA-2?) — UNVERIFIED.
- Prince: whether unprefixed `bleed` / `float-reference` / `float-defer` are accepted (vs only `prince-bleed`,
  `-prince-float-reference`, `float-defer-page/column`) — UNVERIFIED.
- Prince: `footnote-policy` / `prince-footnote-policy` value set (forum mentions `keep-with-line`) — UNVERIFIED.
- Prince: `:recto`/`:verso` page pseudo-classes, `hyphenate-limit-chars`, `hyphenate-character`, `counter-set`,
  `prince-flow`/`flow()` legacy running syntax, sidenote float values — UNVERIFIED.
- Prince: syntax of `prince-pdf-destination`, `prince-pdf-link-type`, `prince-pdf-paper-tray`; encryption
  options; CMYK/output-intent options — UNVERIFIED.
- Prince: PDF files as `<img>` sources — UNVERIFIED (search summary said "no"; not confirmed against docs).
- Prince: COLR/COLRv1 colour fonts — UNVERIFIED (docs list SVG, CBDT/CBLC, sbix).
- Prince: `--max-passes` default (forum says 2, older cookbook says unlimited) — conflicting, UNVERIFIED.
- pagedjs-cli and vivliostyle-cli (PDF outline/bookmark generation, page labels, CMYK post-processing) were not
  cloned; their bookmark support is UNVERIFIED.
- Paged.js `counter-set`, `break-inside: avoid-page/avoid-column` handling — not found in source; treated as
  browser-delegated, UNVERIFIED.
- Vivliostyle `box-decoration-break` handling and `position: fixed` repetition — UNVERIFIED.
