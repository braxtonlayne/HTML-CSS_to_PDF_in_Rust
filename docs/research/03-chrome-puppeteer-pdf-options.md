# 03 — Chrome print-to-PDF, Puppeteer/Playwright `page.pdf()`, Gotenberg and the options people actually use

Date: 2026-10-14
Topic slug: `chrome`
Purpose: catalog every knob of Chrome's print-to-PDF path and its popular wrappers, with exact defaults and conversions, so that recto's Puppeteer-compat layer (`CMP`), CLI (`CLI`) and HTTP server (`SRV`) can accept existing callers' options with predictable results.

## Sources inspected

| Name | Version / tag | Commit SHA | License | Last commit | Maintenance |
|---|---|---|---|---|---|
| ChromeDevTools/devtools-protocol | npm `0.0.1718299` (HEAD of `master`) | `dfad77069330a9188771bb64a32d18853a10b012` | BSD-3-Clause (Chromium) | 2026-10-14 | Auto-published daily from Chromium; authoritative CDP schema |
| chromium/chromium (GitHub mirror, sparse: `components/printing`, `components/headless/command_handler`, `headless/`, `printing/`) | `main` | `a15fdfc9004de642510fa28ae1c3aebee0d52c71` | BSD-3-Clause | 2026-10-14 | Upstream |
| google/skia (sparse `src/pdf`, `include/docs`) | `main` | `2a2bbea668449ba5b98b501420e9a4685ad79b7d` | BSD-3-Clause | 2026-10-14 | Upstream; Chrome's PDF backend |
| puppeteer/puppeteer | `puppeteer-v25.13.0` (puppeteer-core 25.13.0) | `6e95cc563dc57ad5535efb0067425065294c2ba6` | Apache-2.0 | 2026-10-08 | Very active, Google-maintained |
| microsoft/playwright (sparse) | `v1.64.1` | `cfe490d941f992655948eee8fd4fd94e1c4234bf` | Apache-2.0 | 2026-10-13 | Very active, Microsoft-maintained |
| gotenberg/gotenberg | `v8.37.0` | `430ed38cc545e301603aa6fdb1efbacba587eff4` | MIT | 2026-09-11 | Active, single main maintainer; uses chromedp v0.14.2 (pinned, `go.mod:8`) |
| spatie/browsershot | `5.4.0` | `dcf7a65fd1d0fc8fd113739b84982377728d0b2f` | MIT | 2026-05-26 | Active (Spatie) |
| chuongtrh/html_to_pdf (Node invoice example, 120★) | `master` | `9c442dfc2d380174f3e38829a64649776ea492d1` | no LICENSE file | 2026-03-30 | Example repo, low activity |
| Web (WebSearch) | — | — | — | — | used only for the headless CLI flag rename history and header/footer folklore; cited inline |

All clones live under `/tmp/claude-0/src/chrome/`. Paths below are relative to each clone.

---

## 1. CDP `Page.printToPDF` (the ground truth)

Source: `devtools-protocol/pdl/domains/Page.pdl:954-1012` (JSON form: `json/browser_protocol.json`, command `"printToPDF"` at line 24256). Behaviour/validation: `chromium/components/printing/browser/print_to_pdf/pdf_print_utils.cc`.

| Param | Type | Default (protocol doc) | Actual validation / behaviour (pdf_print_utils.cc unless noted) |
|---|---|---|---|
| `landscape` | bool | `false` | `print_settings.SetOrientation(landscape.value_or(false))`. Swaps paper width/height. |
| `displayHeaderFooter` | bool | `false` | When true, the page URL (username/password stripped via `url_sanitizer`) is stored for the `url` class. |
| `printBackground` | bool | `false` | `set_should_print_backgrounds(...)`; renderer sets `WebSettings::SetShouldPrintBackgrounds` (`print_render_frame_helper.cc:902`). |
| `scale` | number | `1` | Error `"scale is outside of [0.1 - 2] range"` if `<0.1` or `>2` (`kScaleMinVal=10`, `kScaleMaxVal=200`, /100). |
| `paperWidth` | number (inches) | `8.5` | `<= 0` → `"paper width is zero or negative"`. Paper size is converted to points with **`gfx::ToCeiledSize`** (rounded **up** to whole points). Default `printing::kLetterWidthInch`. |
| `paperHeight` | number (inches) | `11` | Same, `kLetterHeightInch`. |
| `marginTop/Bottom/Left/Right` | number (inches) | **1 cm ≈ 0.3937 in** each (`kDefaultMarginInMM = 10.0`, divided by `kMicronsPerMil` = 25.4) | Negative → error (`"top margin is negative"` …). Each margin is converted with **`base::ClampFloor(in * 72)`** → margins are **floored to whole points** before conversion to microns. Margins ≥ page → `"invalid print parameters: content area is empty"`. |
| `pageRanges` | string | `""` = all pages | Parser `TextPageRangesToPageRanges` (see §1.1). |
| `headerTemplate` | string (HTML) | `""` | Classes `date`, `title`, `url`, `pageNumber`, `totalPages` get their `textContent` replaced. **Empty string ⇒ Chrome's built-in default header** (see §5.2). |
| `footerTemplate` | string (HTML) | `""` | Same classes; empty ⇒ built-in default footer. |
| `preferCSSPageSize` | bool | `false` ("content will be scaled to fit the paper size") | Selects `PrintScalingOption::kSourceSize` (true) vs `kCenterShrinkToFitPaper` (false) (`print_render_frame_helper.cc:1455-1458`). |
| `transferMode` | enum `ReturnAsBase64` \| `ReturnAsStream` (experimental) | `ReturnAsBase64` | Stream mode returns an `IO.StreamHandle` (`stream`), `data` is empty. Puppeteer, Playwright and Gotenberg all use `ReturnAsStream`. |
| `generateTaggedPDF` | bool (experimental) | "embedder choice" | Passed through as `std::optional`; in headless_shell the fallback is `!--disable-pdf-tagging` (`headless/lib/renderer/headless_print_render_frame_helper_delegate.cc`, `ShouldGenerateTaggedPDF`) — i.e. **tagged by default** in headless when unset. |
| `generateDocumentOutline` | bool (experimental) | `false` | Maps to `GenerateDocumentOutline::kFromAccessibilityTreeHeaders`. Outline is only emitted if a structure tree was built (`printing/common/metafile_utils.cc:432-440`: `fOutline` set only inside `if (RecursiveBuildStructureTree(...))`) ⇒ **outline requires tagging**. |

Returns: `data` (base64 binary; empty when streaming), `stream` (experimental `IO.StreamHandle`).

Fixed internal settings: `print_settings.set_dpi(printing::kPointsPerInch)` (72), `print_to_pdf = true`; PDF document `fRasterDPI = 300` for rasterized content (`metafile_utils.cc`).

### 1.1 `pageRanges` grammar (exact, from `TextPageRangesToPageRanges`)

- Split on `,`, whitespace trimmed, empty pieces dropped (`SPLIT_WANT_NONEMPTY`).
- `N` → single page N.
- `-` → 1..end.
- `-B` → 1..B.
- `A-` → A..end.
- `A-B` (tokens split on `-`, whitespace-trimmed, exactly 2) → A..B.
- Non-integer → `kPageRangeSyntaxError` ("Page range syntax error"). `from < 1` or `from > to` → `kPageRangeInvalidRange`.
- Per the PDL: pages are emitted in document order, never twice; numbers past the end are capped; ranges entirely past the end are ignored; if no page remains → error ("Page range exceeds page count", mapped to HTTP 400 by Gotenberg, `gotenberg/pkg/modules/chromium/browser.go:621-633`).

### 1.2 Error strings callers match on

Gotenberg (`browser.go:621-633`) string-matches: `"Printing failed (-32000)"`, `"Show invalid printer settings error (-32000)"`, `"content area is empty (-32602)"`, `"Page range syntax error"`, page-range-exceeds-count. recto's server should produce analogous 400s with stable error codes.

---

## 2. Puppeteer `page.pdf(options)` (puppeteer-core 25.13.0)

Sources: `packages/puppeteer-core/src/common/PDFOptions.ts` (interface + paper table), `packages/puppeteer-core/src/common/util.ts:317-417` (`parsePDFOptions`, `unitToPixels`, `convertPrintParameterToInches`), `packages/puppeteer-core/src/cdp/Page.ts:1220-1295` (`createPDFStream`, `pdf`), `packages/puppeteer-core/src/bidi/Page.ts:490-545`, `common/TimeoutSettings.ts:7` (`DEFAULT_TIMEOUT = 30000`).

### 2.1 Options and exact defaults

| Option | Type | Puppeteer default (`parsePDFOptions` defaults object) | Sent to CDP as |
|---|---|---|---|
| `scale` | number | `1` (doc: "between 0.1 and 2"; range enforced by Chrome, not Puppeteer) | `scale` |
| `displayHeaderFooter` | bool | `false` | `displayHeaderFooter` |
| `headerTemplate` | string | `''` | `headerTemplate` (always sent) |
| `footerTemplate` | string | `''` | `footerTemplate` (always sent) |
| `printBackground` | bool | `false` | `printBackground` |
| `landscape` | bool | `false` | `landscape` |
| `pageRanges` | string | `''` | `pageRanges` |
| `format` | `PaperFormat` (case-insensitive) | none; effective size **Letter 8.5×11 in** (`let width = 8.5; let height = 11`) | `paperWidth/paperHeight` (inches). **`format` wins over `width`/`height`.** |
| `width`, `height` | string \| number | unset → 8.5 / 11 in | inches via `convertPrintParameterToInches` |
| `preferCSSPageSize` | bool | `false` | `preferCSSPageSize` |
| `margin.{top,right,bottom,left}` | string \| number | `undefined` → **`0`** (`|| 0`) | `marginTop…` — **always sent**, so Puppeteer's effective default margin is **0, not Chrome's 1 cm**. |
| `path` | string | `undefined` | not sent; output written by Puppeteer (`getReadableAsTypedArray(readable, path)`) relative to CWD |
| `omitBackground` | bool | `false` | not a printToPDF param: calls `Emulation.setDefaultBackgroundColorOverride` (transparent) before printing and resets afterwards (`emulationManager.setTransparentBackgroundColor()` / `resetDefaultBackgroundColor()`) |
| `tagged` | bool | **`true`** (experimental) | `generateTaggedPDF` |
| `outline` | bool | `false` (experimental) | `generateDocumentOutline`; **if `outline` is true, `tagged` is forced to true** (`util.ts`: "Quirk crbug 840455#c44") |
| `timeout` | number ms | `30_000` (`TimeoutSettings.DEFAULT_TIMEOUT`); `0` disables | races both the fonts wait and the printToPDF call |
| `waitForFonts` | bool | `true` | evaluates `document.fonts.ready` in an isolated realm before printing |
| `transferMode` | — | — | always `'ReturnAsStream'` (hard-coded) |

`createPDFStream(options)` returns a `ReadableStream<Uint8Array>` (same options). The page's media type during printing is `print` unless `page.emulateMediaType('screen')` was called (docs `docs/api/puppeteer.page.pdf.md` Remarks).

### 2.2 Paper formats (`paperFormats` in `PDFOptions.ts`) — exact values

"All A series paper format sizes in inches are calculated from centimeters rounded mathematically to four decimal places."

| Format | inches (CDP path) | cm (BiDi path) |
|---|---|---|
| letter | 8.5 × 11 | 21.59 × 27.94 |
| legal | 8.5 × 14 | 21.59 × 35.56 |
| tabloid | 11 × 17 | 27.94 × 43.18 |
| ledger | 17 × 11 | 43.18 × 27.94 |
| a0 | 33.1102 × 46.811 | 84.1 × 118.9 |
| a1 | 23.3858 × 33.1102 | 59.4 × 84.1 |
| a2 | 16.5354 × 23.3858 | 42 × 59.4 |
| a3 | 11.6929 × 16.5354 | 29.7 × 42 |
| a4 | 8.2677 × 11.6929 | 21 × 29.7 |
| a5 | 5.8268 × 8.2677 | 14.8 × 21 |
| a6 | 4.1339 × 5.8268 | 10.5 × 14.8 |

Accepted spellings: lowercase, `Uppercase<…>`, `Capitalize<…>` (TS type); runtime does `format.toLowerCase()`. An unknown format string makes `paperFormats[x]` `undefined`, so `[lengthUnit]` throws a `TypeError` *before* the `assert(format, 'Unknown paper format: …')` can fire (observation from `util.ts:337-341`). No B-series, no `Executive`, no `Letter`-landscape aliases.

### 2.3 Length conversion (`convertPrintParameterToInches`)

```ts
export const unitToPixels = { px: 1, in: 96, cm: 37.8, mm: 3.78 };
```

- **number** → CSS pixels ("aligned with phantom's paperSize"); inches = px / 96.
- **string**: unit = last 2 chars lowercased; if in table, value = rest; else the **whole string is parsed as px**. `Number(valueText)` must not be NaN, else `assert` throws `'Failed to parse parameter value: ' + text`.
- Consequences: `"10pt"`, `"1pc"`, `"1em"` → whole string parsed as px → `NaN` → error (no pt/pc/em support). `"10 mm"` works (`Number("10 ")` = 10, JS trims). `"5"` → 5 px. `"0"` → 0. `"10MM"` works (unit lowercased).
- Imprecise constants: `cm = 37.8` (true 37.7953…), `mm = 3.78` (true 3.77953…). Relative error +0.0125 %. Example: `width: '210mm'` → 210·3.78/96 = 8.26875 in (true 8.26772 in) — 0.074 pt wider than true A4. `format: 'A4'` → 8.2677 in.
- Chrome then **ceils** paper to whole points: A4 via `format` → 595.27 pt → **596 pt** × 841.89 → **842 pt** (derived from `ToCeiledSize` in `pdf_print_utils.cc`; not empirically checked here — see Open questions). Margins are **floored** to whole points: `'1cm'` → 0.39375 in → 28.35 pt → **28 pt**.

### 2.4 BiDi (Firefox / WebDriver BiDi) path differences (`bidi/Page.ts:490-545`)

Uses `parsePDFOptions(options, 'cm')` and `browsingContext.print({background, margin, orientation, page:{width,height}, pageRanges, scale, shrinkToFit: !preferCSSPageSize})`. **Ignored on BiDi:** `displayHeaderFooter`, `headerTemplate`, `footerTemplate`, `omitBackground`, `tagged`, `outline`, `waitForFonts` (fonts are always awaited). `pageRanges` split on literal `', '` only. Relevance: recto callers coming from Firefox-Puppeteer already live without header templates.

---

## 3. Playwright `page.pdf(options)` (v1.64.1, Chromium only)

Sources: `packages/playwright-core/src/server/chromium/crPdf.ts`, `packages/playwright-core/src/client/page.ts:907-926`, `packages/playwright-core/types/types.d.ts:4135-4245`, `packages/playwright-core/src/server/channels.d.ts:4460-4480`, `docs/src/api/class-page.md:3006-3096`.

| Aspect | Playwright | Puppeteer | Note |
|---|---|---|---|
| Option set | `scale, displayHeaderFooter, headerTemplate, footerTemplate, printBackground, landscape, pageRanges, format, width, height, preferCSSPageSize, margin, tagged, outline, path` | + `omitBackground, timeout, waitForFonts` | Playwright has no `omitBackground`, no per-call `timeout` (client sends `kNoTimeout`), no fonts wait. |
| `tagged` default | **`false`** | **`true`** | Same Chrome, different default ⇒ different output. |
| `outline` | does **not** force `tagged` | forces `tagged = true` | `outline:true, tagged:false` in Playwright yields **no outline** (Chrome builds the outline from the structure tree, §1). |
| Paper table (inches) | `a0 33.1×46.8, a1 23.4×33.1, a2 16.54×23.4, a3 11.7×16.54, a4 8.27×11.7, a5 5.83×8.27, a6 4.13×5.83`, letter/legal/tabloid/ledger same | 4-decimal values | Playwright A4 = 8.27×11.7 in = 210.06×297.18 mm → Chrome ceils to **596×843 pt** (vs Puppeteer 596×842). |
| Units | `px:1, in:96, cm:37.8, mm:3.78`; numbers converted to `"<n>px"` on the client | identical constants | Same parsing (last 2 chars; else whole string as px). |
| Zero width | `convert(...) || paperWidth` → `width: 0` silently falls back to 8.5 in | `?? width` → 0 is passed, Chrome errors | edge case only |
| `path` | `mkdir -p` dirname then write | writes, no mkdir | |
| Unknown `format` | `assert` → "Unknown paper format: X" | `TypeError` | |
| Media | docs: PDF uses `print` media; `page.emulateMedia({media:'screen'})` to switch | `page.emulateMediaType('screen')` | |
| Doc notes | "Script tags inside templates are not evaluated", "Page styles are not visible inside templates", "By default, page.pdf() generates a pdf with modified colors for printing. Use `-webkit-print-color-adjust`" (`class-page.md:3015-3083`) | same color remark in `puppeteer.page.pdf.md` | |

---

## 4. Chrome headless CLI (`--print-to-pdf`)

Sources: `chromium/components/headless/command_handler/headless_command_switches.cc`, `headless_command_handler.cc:136-170`, `headless_command.js:231-246`; WebSearch for rename history.

| Flag | Semantics (source) |
|---|---|
| `--headless` | required (new headless is default `--headless` since Chrome 112; old one is the separate `chrome-headless-shell` binary) [developer.chrome.com/docs/chromium/new-headless](https://developer.chrome.com/docs/chromium/new-headless) |
| `--print-to-pdf[=path]` | "Save a PDF file of the loaded page." Default file name `output.pdf` in CWD (`kDefaultPDFFileName`). |
| `--no-pdf-header-footer` | "Do not display header and footer in the printed PDF file." → `noHeaderFooter` → `displayHeaderFooter: false`. |
| `--print-to-pdf-no-header` | **Old name** of the above; not present in current Chromium source (grep over `headless/` and `components/headless/` finds nothing). Docs say the functionality "was previously available as `--print-to-pdf-no-header`" ([new-headless docs](https://developer.chrome.com/docs/chromium/new-headless); [Simon Willison TIL](https://til.simonwillison.net/chrome/headless) reports it not working). recto CLI shim should accept both. |
| `--disable-pdf-tagging` | "Do not emit tags when printing PDFs." → `generateTaggedPDF: false`; also the renderer fallback when CDP callers omit `generateTaggedPDF`. |
| `--generate-pdf-document-outline` | "Embed the document outline into printed PDFs." |
| `--timeout=ms` | "Issues a stop after the specified number of milliseconds. This cancels all navigation and causes the DOMContentLoaded event to fire." |
| `--virtual-time-budget=ms` | virtual-time wait; timers fast-forwarded, no advance while fetches pending. |
| `--default-background-color=RRGGBBAA` | default page background (e.g. `00000000` transparent) — CLI analogue of `omitBackground`. |

**CLI print parameters are hard-coded** (`headless_command.js:236-242`):

```js
{ displayHeaderFooter: !params.noHeaderFooter,   // ON by default!
  generateTaggedPDF: !params.disablePDFTagging,  // ON by default
  generateDocumentOutline: params.generateDocumentOutline,
  printBackground: true,                         // ON (differs from CDP/Puppeteer)
  preferCSSPageSize: true }                      // ON (differs from CDP/Puppeteer)
```

Paper (Letter), margins (1 cm) and scale take CDP defaults; there is no CLI flag for paper size or margins — users control them via CSS `@page`. So **CLI users already write `@page { size; margin }`** and are recto's easiest migrants. The default header/footer (date + title / URL + "n/N") appears unless `--no-pdf-header-footer` is passed — the most common complaint about the CLI.

---

## 5. Chrome behaviours that set fidelity expectations

### 5.1 Page size and margin precedence

From `print_render_frame_helper.cc`:
- For `Page.printToPDF`, `EnterPrintMode(..., /*ignore_css_margins=*/false)` (line ~1488) and `ignore_page_size = ShouldIgnoreCssPageSize(ignore_css_margins, params)` = `false`. Hence **author `@page { margin }` overrides the `margin*` params**, and author `@page { size }` is honoured for layout.
- `print_scaling_option = (center_on_paper && !prefer_css_page_size) ? kCenterShrinkToFitPaper : kSourceSize` (lines 1455-1458).
  - `preferCSSPageSize: false` (default): the PDF page is the **param paper size**; a page laid out at a different CSS `@page` size is shrunk (never enlarged) and centered onto the paper. A4 CSS on Letter paper = slightly scaled-down content, white bands.
  - `preferCSSPageSize: true`: the PDF page size is the CSS `@page` size (per page, so mixed sizes/named pages work); pages without `size` use the param paper.
- `landscape` param interacts only with the param paper; CSS `size: A4 landscape` wins under `preferCSSPageSize: true`.
- Paper dimensions are ceiled to whole points; margins floored to whole points (§1).
- Default margins: CDP **1 cm (≈0.3937 in, floored to 28 pt)**; Puppeteer/Playwright **0** (always send explicit zeros); Gotenberg **0.39 in** (28.08 pt → 28 pt); headless CLI 1 cm.

### 5.2 Header/footer templates (`components/printing/resources/print_header_footer_template_page.html`, `print_render_frame_helper.cc:570-640`)

- Rendered **per page** into a **separate, freshly created WebView/frame** (`HeaderAndFooterContext::CreateWebView`) via `document.open(); document.write(<template page>)`; the user template is injected with `header.innerHTML = options.headerTemplate || <default>` ⇒ `<script>` in templates is not executed (innerHTML), page styles/fonts/`@font-face` of the main document are not visible, external resources are unreliable (folklore: use data: URIs; [browserless guide](https://cloud.browserless.io/blog/puppeteer-pdf-generator) — UNVERIFIED in source).
- The header box is the **top margin area** (`header.style.height = topMargin px`), footer is the bottom margin area. With margin 0 (Puppeteer default) the template has zero height ⇒ invisible. Users must set `margin.top/bottom`.
- Layout of header/footer is **non-paginated** (`use_paginated_layout = false`), overflow is clipped.
- Template-page CSS: `body{display:flex;flex-direction:column;margin:0}`, `#header{align-items:flex-start;padding-top:15pt}`, `#footer{align-items:flex-end;padding-bottom:15pt}`, `.left{padding-left:24pt;padding-right:6pt}`, `.center{flex:auto;padding:0 24pt;text-align:center}`, `.right{padding-left:6pt;padding-right:24pt}`, `.text{font-size:8pt;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}`, plus `chrome://resources/css/text_defaults.css`. The 15pt/24pt paddings apply to user templates too (they sit inside `#header`/`#footer`).
- **Empty template ⇒ default**: header = `<div class='date text left'>` + `<div class='title text center'>`; footer = `<div class='url text left grow'>` + `<div class='text right'><span class='pageNumber'></span>/<span class='totalPages'></span></div>`. Since Puppeteer sends `headerTemplate: ''` by default, `displayHeaderFooter: true` with only a `footerTemplate` still prints Chrome's date/title **header**. This is why real code sets `headerTemplate: '<p></p>'` or `'<span></span>'` (chuongtrh `example.js:32-33`; Browsershot `hideHeader()` = `headerHtml('<p></p>')`).
- Value injection: for each class in `date,title,url,pageNumber,totalPages`, **every** element with that class gets `textContent` set. `date` = `base::Time::Now()` formatted with `Intl.DateTimeFormat(navigator.languages[0], {dateStyle:'short', timeStyle:'short'})` (locale- and time-dependent). `title` = `document.title`, falling back to `params.title`. `url` = page URL sans credentials. `pageNumber` = page_index+1. `totalPages` = total_pages.
- Elements with class `text` that intersect the content area are hidden (`visibility:hidden`) — prevents the default header overlapping content when margins are small.
- `isRtl` → `.text` elements (except url/title) get `dir=rtl`.
- The template body is sized `width = page width`, `height = page height` in **CSS px numerically equal to the page size in points** (layout units are 72-dpi based because `set_dpi(kPointsPerInch)`). Folklore: text without explicit `font-size` renders very small, so callers always set `font-size: 10px` etc. (Gotenberg fixture `test/integration/testdata/header-footer-html/header.html` uses `body{font-size:12px;margin:auto 20px}`). Exact scale factor **UNVERIFIED**.
- When both templates are empty strings, `printing_internal_headers_and_footers = true` (line 626).

### 5.3 Backgrounds and colours

- `printBackground:false` ⇒ Blink does not paint backgrounds (colors/images) **unless** the element has `print-color-adjust: exact` (`-webkit-print-color-adjust`). Gotenberg comment: "The -webkit-print-color-adjust: exact CSS property forces the print of the background, whatever the printToPDF args" (`gotenberg/pkg/modules/chromium/tasks.go:593-597`).
- Gotenberg therefore **always injects** `html { -webkit-print-color-adjust: exact !important; }` and, when `printBackground=false`, `html, body { background: none !important; }` (`forceExactColorsActionFunc`). Net: Gotenberg users get exact colors everywhere and only the root/body background is controlled by `printBackground`.
- Docs of both Puppeteer and Playwright: "By default, page.pdf() generates a pdf with modified colors for printing." Whether Blink's economy mode changes *text* colours (not just drops backgrounds) is **UNVERIFIED**.
- `omitBackground`: the default white canvas is replaced with transparent (`Emulation.setDefaultBackgroundColorOverride` RGBA 0,0,0,0). Gotenberg requires `printBackground=true` with `omitBackground=true` (`ErrOmitBackgroundWithoutPrintBackground`, `tasks.go:567-570`).

### 5.4 Units, media, layout width

- CSS px = 1/96 in throughout (Puppeteer `in: 96`; Gotenberg `px: 1/96`; Gotenberg singlePage comment "There are 96 CSS pixels per inch", `tasks.go:73`).
- Print media type is `print` by default; `page.emulateMediaType('screen')` / Playwright `emulateMedia({media:'screen'})` / Gotenberg `emulatedMediaType=screen` / Browsershot `emulateMedia('screen')` switch media queries. Widely used for "print it like the web page" (Tailwind/Bootstrap pages hide things in `@media print`). recto must support a `media` override.
- `emulatedMediaFeatures` (Gotenberg JSON map, Browsershot `emulateMediaFeatures`) → `Emulation.setEmulatedMedia({features})`, e.g. `prefers-color-scheme: dark`.
- `scale` changes layout: content is laid out at (page content width / scale) CSS px and rendered scaled (Chrome scale_factor); text reflows. recto's implementation should be "layout viewport = content box / scale, then paint transform × scale".
- Viewport size (Browsershot default `windowSize(800, 600)`) does not determine print layout width; print layout uses the page content width (**UNVERIFIED** for `vw`-unit edge cases).

### 5.5 Tagging / outline

- Tagged PDF structure is derived from Chrome's accessibility tree (`RecursiveBuildStructureTree(tree.root(), &tag_root)` in `metafile_utils.cc`). Outline uses `SkPDF::Metadata::Outline::StructureElementHeaders` (h1–h6) and is only produced when tagging produced a tree.
- Gotenberg launches Chromium with `--disable-pdf-tagging` (`browser.go:149`, issue #831) and defaults `generateTaggedPdf=false`; turns tagging on when outline requested (`resolvePdfOptions`, `tasks.go:35-41`). Tagging cost/stability is a known Chrome pain point (#831/#1210 references; details **UNVERIFIED**).

### 5.6 Nondeterminism sources in Chrome PDFs (what recto beats)

| Source | Where | Effect |
|---|---|---|
| `/CreationDate`, `/ModDate` | `printing/common/metafile_utils.cc` `MakePdfDocument`: `metadata.fCreation = metadata.fModified = TimeToSkTime(base::Time::Now())`; emitted by `skia/src/pdf/SkPDFMetadata.cpp:77-82` | every run differs |
| Header/footer `date` class | `base::Time::Now()` + `Intl.DateTimeFormat(navigator.languages[0])` | content differs per run and per locale |
| `/Creator` | `GetAgent()` (set via `printing::SetAgent(user_agent)`; empty → `"Chromium"`) | varies by Chrome version/UA (commonly a full `HeadlessChrome/…` UA string — value **UNVERIFIED** here) |
| `/Producer` | `SkString("Skia/PDF m" SK_MILESTONE)` (`skia/include/docs/SkPDFDocument.h:121`) | changes every Chrome milestone |
| `/ID` and XMP | Skia emits `/ID` and XMP only when `fPDFA` is set (`SkPDFDocument.cpp:282-289`, `157`); Chrome never sets it | No `/ID` at all (deterministic but non-conformant for PDF/A; if enabled, `CreateUUID` hashes `SkTime::GetMSecs()` ⇒ random) |
| Font fallback/subsetting | system fontconfig in the container | glyphs and metrics vary across hosts/images |
| Network / JS timing | `networkidle`, `waitDelay`, lazy images, animations, `document.fonts.ready` | page content differs if resources race (Gotenberg exposes five different wait knobs) |
| Chrome version | layout/paint changes each release | Gotenberg pins chromedp because v0.15 "breaks the headless print-mode paint pipeline" (`go.mod:8`) |
| Tagging | AX-tree derived, version-dependent | structure tree changes across releases |

recto: fixed or `SOURCE_DATE_EPOCH`-derived dates, fixed Producer string per recto version, `/ID` = hash of content, header `date` from an explicit option, no network, no JS, bundled fonts ⇒ byte-identical output.

---

## 6. Gotenberg Chromium routes (v8.37.0) — the reference HTTP API

Routes (`pkg/modules/chromium/routes.go`): `POST /forms/chromium/convert/url` (field `url`, `file://` rejected), `POST /forms/chromium/convert/html` (file `index.html` mandatory + any asset files in the same multipart; resolved relative to index.html), `POST /forms/chromium/convert/markdown` (`index.html` with `{{ toHTML "x.md" }}` + `.md` files), and `/forms/chromium/screenshot/{url,html,markdown}`. All multipart/form-data. Booleans are `"true"/"false"` strings; JSON fields are JSON strings.

### 6.1 Page/print fields (`FormDataChromiumPdfOptions`, defaults from `DefaultPdfOptions()` in `chromium.go:321-341`)

| Field | Type | Default | Semantics |
|---|---|---|---|
| `singlePage` | bool | `false` | Uses `Page.getLayoutMetrics` `cssContentSize`; paperHeight = content height/96 + marginTop + marginBottom (landscape: both dimensions sized to content), `pageRanges="1"` (`tasks.go:65-90`). |
| `paperWidth` | length | `8.5` (in) | **Bare number = inches**; units `pt, px, in, mm, cm, pc` (`api/formdata.go:202-250`: pt/72, px/96, mm/25.4, cm/2.54, pc/6). |
| `paperHeight` | length | `11` | idem |
| `marginTop/Bottom/Left/Right` | length | `0.39` in each | idem |
| `preferCssPageSize` | bool | `false` | → `preferCSSPageSize` |
| `generateDocumentOutline` | bool | `false` | forces `generateTaggedPdf=true` |
| `generateTaggedPdf` | bool | `false` | → `generateTaggedPDF` |
| `printBackground` | bool | `false` | see §5.3 (Gotenberg always forces exact colors; false removes html/body background) |
| `omitBackground` | bool | `false` | transparent default background; requires `printBackground=true` else 400 |
| `landscape` | bool | `false` | |
| `scale` | float | `1.0` | Chrome validates 0.1–2 |
| `nativePageRanges` | string | `""` | → `pageRanges` (Chrome grammar §1.1) |
| `header.html` (file) | file | `<html><head></head><body></body></html>` | full HTML document; when either header or footer differs from the default, `displayHeaderFooter=true` and both templates are sent (`tasks.go:111-123`). Note: default is a non-empty empty-body doc, so supplying only `footer.html` gives an **empty** header (unlike raw Puppeteer). |
| `footer.html` (file) | file | same | same classes `date,title,url,pageNumber,totalPages` |

### 6.2 Browser/load fields (`FormDataChromiumOptions`, defaults `chromium.go:230-250`)

| Field | Default | Semantics |
|---|---|---|
| `waitDelay` | `0` (Go duration, e.g. `5s`) | sleep before print (skipped if JS disabled) |
| `waitWindowStatus` | `""` | wait until `window.status` equals value |
| `waitForExpression` | `""` | wait until JS expression is truthy |
| `waitForSelector` | `""` | wait until selector visible |
| `skipNetworkIdleEvent` | `true` | if false, wait for network idle |
| `skipNetworkAlmostIdleEvent` | `true` | if false, wait for network almost-idle |
| `emulatedMediaType` | `""` (= print) | `screen` \| `print` |
| `emulatedMediaFeatures` | none | JSON map name→value |
| `cookies` | none | JSON array `{name,value,domain,path?,secure?,httpOnly?,sameSite?}` (sameSite case-insensitive) |
| `userAgent` | `""` | UA override |
| `extraHttpHeaders` | none | JSON map; value may carry `;scope=<regex>` to limit to matching URLs (≤64 headers, scope ≤1024 chars) |
| `failOnHttpStatusCodes` | `[499,599]` | JSON array of codes; `X99` means range X00–X99; main document only |
| `failOnResourceHttpStatusCodes` | none | same for sub-resources |
| `ignoreResourceHttpStatusDomains` | none | JSON array of domains excluded from the resource check |
| `failOnResourceLoadingFailed` | `false` | fail on network errors of sub-resources |
| `failOnConsoleExceptions` | `false` | fail on JS exceptions |

### 6.3 Post-processing fields shared with PDF engines (`pkg/modules/pdfengines/routes.go`), applied in this order (`routes.go` `convertUrl`): split → watermark → stamp → rotate → optimize → PDF/A-UA convert → metadata → embeds → embedsMetadata → Factur-X → encrypt

| Field | Semantics |
|---|---|
| `splitMode` (`intervals`\|`pages`), `splitSpan` (int ≥1 for intervals, page-range string for pages), `splitUnify` (bool, pages mode only) | split output into several PDFs (zip response) |
| `watermarkSource`/`stampSource` (`text`\|`image`\|`pdf`), `…Expression`, `…Pages`, `…Options` (JSON map), files `watermark`/`stamp` | repeated fields, aligned by position; watermark = behind content, stamp = over content |
| `rotateAngle` (90/180/270), `rotatePages` | rotate pages |
| `optimizeImages` (bool), `imageQuality` (1–100, default 80) | recompress images |
| `pdfa` (string; constants `PDF/A-1a/1b/2a/2b/2u/3a/3b/3u` in `gotenberg/pdfengine.go:116-137`; which ones each engine accepts was not checked), `pdfua` (bool) | conformance conversion as a post-step by the configured PDF engine (engine choice not inspected) |
| `metadata` | JSON object written via exiftool (Author, Title, Subject, Keywords, Creator, Producer, CreationDate, ModDate, Trapped, …) |
| files in field `embeds`, `embedsMetadata` (JSON keyed by filename) | file attachments |
| `facturxXml` (file), `facturxConformanceLevel` (`MINIMUM`,`BASIC WL`,`BASIC`,`EN 16931`,`EXTENDED`,`XRECHNUNG`), `facturxDocumentType` (default invoice), `facturxVersion` | Factur-X/ZUGFeRD e-invoice (PDF/A-3 + embedded XML) |
| `userPassword`, `ownerPassword`, `allowPrinting/Copying/Modifying/Annotating/FillingForms/Assembling` (default true) | encryption; restrictions without a password → 400 |
| (pdfengines route only) `bookmarks` JSON | bookmarks list or map |

Request headers: `Gotenberg-Output-Filename`, `Gotenberg-Trace`, `Gotenberg-Webhook-Url`, `Gotenberg-Webhook-Method`, `Gotenberg-Webhook-Error-Url`, `Gotenberg-Webhook-Error-Method`, `Gotenberg-Webhook-Extra-Http-Headers`, `Gotenberg-Webhook-Events-Url`.

Server-level Chromium flags (`chromium.go:467-489`): `--chromium-allow-list`, `--chromium-deny-list` (default `^file:(?!//\/tmp/).*`), `--chromium-deny-private-ips`, `--chromium-deny-public-ips`, `--chromium-disable-javascript`, `--chromium-clear-cache/cookies/storage`, `--chromium-ignore-certificate-errors`, `--chromium-proxy-server`, `--chromium-host-resolver-rules`, … Launch flags include `--font-render-hinting=none` (Puppeteer issues #661/#2410: glyph-spacing differences) and `--disable-pdf-tagging`.

---

## 7. Real-world usage survey

### 7.1 Browsershot 5.4.0 (`src/Browsershot.php`, `bin/browser.cjs`)

PDF-relevant methods → Puppeteer options:

| Browsershot | Puppeteer option |
|---|---|
| `showBrowserHeaderAndFooter()` / `hideBrowserHeaderAndFooter()` | `displayHeaderFooter: true/false` |
| `headerHtml($html)` / `footerHtml($html)` | `headerTemplate` / `footerTemplate` |
| `hideHeader()` / `hideFooter()` | template `'<p></p>'` (works around the default-template behaviour) |
| `margins($t,$r,$b,$l,$unit='mm')` | `margin` with unit suffix (default **mm**) |
| `paperSize($w,$h,$unit='mm')` | `width`, `height` |
| `format($f)` | `format` |
| `landscape()` | `landscape` |
| `pages('1-3')` | `pageRanges` |
| `scale($s)` | `scale` |
| `showBackground()` / `hideBackground()` | `printBackground` |
| `transparentBackground()` | `omitBackground: true` |
| `taggedPdf()` | `tagged: true` |
| `emulateMedia('screen')`, `emulateMediaFeatures([...])` | `page.emulateMediaType`, `page.emulateMediaFeatures` |
| `initialPageNumber($n)` | prepends n−1 hidden `.empty-page` divs with `page-break-after: always` and sets `pageRanges "{n}-"` — a hack to start page numbering at n (`browser.cjs:418-434`) |
| `timeout`, `delay`, `waitUntilNetworkIdle`, `waitForFunction`, `waitForSelector`, `setOption($k,$v)` (passthrough, e.g. `outline`) | load/wait knobs |

`initialPageNumber` shows a real need for `counter-reset: page N` / a "first page number" option.

### 7.2 Node invoice example (chuongtrh/html_to_pdf `example.js:31-42`, `index.js`)

Handlebars template → `data:` URL → `page.goto(..., {waitUntil:'networkidle0'})` → `page.pdf({format:'A4', headerTemplate:'<p></p>', footerTemplate:'<p></p>', displayHeaderFooter:false, margin:{top:'40px', bottom:'100px'}, printBackground:true, path:'invoice.pdf'})`.

### 7.3 Option frequency (qualitative, from the above + Gotenberg defaults)

Ubiquitous: `format` (A4/Letter), `printBackground: true`, `margin` (px/mm strings), `path`. Common: `displayHeaderFooter` + `headerTemplate`/`footerTemplate` with `pageNumber`/`totalPages`, `landscape`, `preferCSSPageSize`, `emulateMediaType('screen')`. Occasional: `scale`, `pageRanges`, `width/height`, `omitBackground`. Rare/new: `tagged`, `outline`, `waitForFonts`, `timeout`.

---

## 8. Mapping: Puppeteer `PDFOptions` → recto (Node-binding compat layer)

Support levels: **Full** = same observable result; **Equivalent** = same intent via different mechanism, minor visual differences; **Partial**; **Ignored** (accepted, warning); **Rejected** (error).

Precedence model the compat layer should implement (mirrors §5.1): synthesise an `@page` rule from options and inject it as a **UA-origin** sheet (lowest precedence) so author `@page { margin }` wins (Chrome behaviour). For size: if `preferCSSPageSize=false`, inject `@page { size: W H }` as a **user `!important`** declaration (option wins); if true, inject at UA level (author wins). Do not emulate Chrome's shrink-to-fit of a mismatched CSS page (document as a deviation; recto lays out directly at the paper size, which is what users actually wanted).

| Puppeteer option | Default to replicate | recto equivalent | Support |
|---|---|---|---|
| `format` | Letter (8.5×11 in) | `@page { size: <name> }`; use **exact ISO sizes** (A4 = 210×297 mm), not Puppeteer's 4-decimal inches or Chrome's point ceiling; add B-series etc. natively | Full (≤1 pt difference vs Chrome, documented) |
| `width`, `height` | — | `@page { size: W H }`; parse exactly like Puppeteer (number = px; suffix px/in/cm/mm by last 2 chars; else whole string as px; NaN → error). Use exact 96/2.54 px per cm (deviation ≤0.0125 % vs Puppeteer's 37.8) — or offer `compat.exact_units=false` to match bit-for-bit. Also accept `pt`/`pc` (superset). | Full |
| `landscape` | false | swap W/H of the injected size (`size: A4 landscape`) | Full |
| `margin.*` | **0** (Puppeteer always sends 0) | `@page { margin: t r b l }` at UA origin | Full |
| `preferCSSPageSize` | false | controls precedence (above) | Equivalent (no shrink-to-fit) |
| `scale` | 1, range [0.1, 2] → error outside | engine option `scale`: layout width = content width / scale, paint ×scale | Full (Partial in v1 if only paint-scaling) |
| `printBackground` | false | engine option `print_backgrounds`; when false skip background painting except for elements with computed `print-color-adjust: exact`. recto native default should be **true** (document generation); compat sets false | Full |
| `omitBackground` | false | no-op: recto never paints a default white canvas (PDF page is transparent); when false, optionally paint white page for parity | Full |
| `displayHeaderFooter` | false | enables header/footer emulation | Equivalent |
| `headerTemplate`, `footerTemplate` | `''` (⇒ Chrome default date/title & url/n/N when displayHeaderFooter) | Translate to running elements: parse the template HTML into an out-of-flow running element and place it in a single margin box spanning the full page width (Chrome's header area is the whole top margin, edge to edge, not the CSS `@top-center` box), holding `element(rectoHeader)`; class substitutions: `pageNumber`→`counter(page)`, `totalPages`→`counter(pages)`, `title`→`<title>` text (string-set), `url`→input URL (or file name; empty in sandbox), `date`→explicit `date` option or `SOURCE_DATE_EPOCH`, formatted `short/short` in a configured locale. Apply Chrome template-page CSS (8pt `.text`, 15pt top/bottom padding, 24pt side padding for default template). Template styles isolated from document (separate stylesheet scope). Empty template + displayHeaderFooter ⇒ emit Chrome-like default header/footer (opt-out `compat.chrome_default_header=false`). `<script>` ignored (as in Chrome). Images only `data:` (as in Chrome folklore). | Equivalent |
| `pageRanges` | `''` | output filter after pagination (counters still count all pages); implement Chrome grammar §1.1 exactly incl. `-`, `-B`, `A-`, capping, "no pages" error, "start > end" error | Full |
| `tagged` | **true** | recto tags by default; `false` disables structure tree | Full (better: real PDF/UA path) |
| `outline` | false | bookmarks from h1–h6 (`bookmark-level` UA defaults); unlike Chrome, does not require tagging | Full |
| `path` | undefined | binding writes the buffer (resolve relative to CWD; create no dirs, like Puppeteer) | Full |
| `timeout` | 30000 ms, 0 = none | engine wall-clock cap → typed timeout error | Full |
| `waitForFonts` | true | no-op (fonts are loaded synchronously before layout) | Ignored (silently) |
| `createPDFStream()` | — | recto streaming page emission → Node `ReadableStream` | Full |
| `page.emulateMediaType('screen'\|'print'\|null)` | print | engine option `media` | Full |
| `page.emulateMediaFeatures([...])` | — | engine media-feature overrides (`prefers-color-scheme`, `prefers-reduced-motion`, …) | Full |
| `page.setContent(html)` / `goto(file://…)` / `goto(data:…)` | — | input HTML string / file in sandbox dir | Full |
| `goto(http…)`, `waitUntil`, `waitForSelector`, `evaluate`, `addScriptTag` | — | no network/JS: reject URL inputs unless network allowlist enabled; JS-dependent waits are no-ops | Ignored / Rejected |
| `addStyleTag({content})` | — | extra user stylesheet | Full |
| BiDi-only behaviour | — | n/a | — |

Playwright adapter: same table but `tagged` default **false**, `outline` does **not** imply tagging (recto can still emit bookmarks — document as improvement), Playwright's paper table (A4 = 8.27×11.7 in) — use exact ISO, note difference ≤1.3 pt in height.

## 9. Mapping: Gotenberg form field → recto (SRV compat route `/forms/chromium/convert/{html,markdown}`)

| Gotenberg field | recto equivalent | Support |
|---|---|---|
| `index.html` + asset files | input document + sandbox asset directory (multipart files become the allowed file root) | Full |
| `url` route | network fetch disabled by default; enable via allowlist config | Partial (opt-in) |
| markdown route `{{ toHTML "x.md" }}` | could map to template batch mode | Partial / later |
| `paperWidth`, `paperHeight` | `@page size` (bare number = **inches**; units pt/px/in/mm/cm/pc) | Full |
| `marginTop/Bottom/Left/Right` | `@page margin` at UA origin; default **0.39 in** each | Full |
| `preferCssPageSize` | size precedence switch | Equivalent |
| `landscape` | orientation | Full |
| `scale` | engine scale | Full |
| `singlePage` | engine option `single_page`: page block-size = content height + vertical margins (auto-height page) | Full (easy in recto: one fragmentainer of infinite height) |
| `nativePageRanges` | page filter (§1.1 grammar) | Full |
| `header.html`, `footer.html` | header/footer template translation (§8); Gotenberg semantics: providing either ⇒ displayHeaderFooter=true, missing one = empty | Equivalent |
| `printBackground` | `print_backgrounds`; to match Gotenberg exactly: treat everything as `print-color-adjust: exact` and only drop html/body backgrounds when false | Full |
| `omitBackground` | no-op (+ validation parity: 400 if `printBackground=false`) | Full |
| `generateDocumentOutline` | bookmarks | Full |
| `generateTaggedPdf` | tagging (default false in Gotenberg! compat should honour false only if explicitly sent? — recommend: recto tags by default; honour explicit `false`) | Full |
| `emulatedMediaType` | `media` | Full |
| `emulatedMediaFeatures` | media-feature overrides | Full |
| `waitDelay`, `waitWindowStatus`, `waitForExpression`, `waitForSelector`, `skipNetworkIdleEvent`, `skipNetworkAlmostIdleEvent` | no JS / no network timing: accept and ignore; `waitForExpression`/`waitWindowStatus` emit a warning header since they imply JS-built content | Ignored |
| `failOnConsoleExceptions` | n/a (no JS) | Ignored |
| `cookies`, `userAgent`, `extraHttpHeaders` | apply to the network fetcher only when network enabled | Partial |
| `failOnHttpStatusCodes`, `failOnResourceHttpStatusCodes`, `ignoreResourceHttpStatusDomains`, `failOnResourceLoadingFailed` | resource-load policy: `fail_on_missing_resource` (also for local missing files) | Equivalent |
| `pdfa` | native PDF/A output (`PDF/A-1b/2b/3b`, a/u variants) | Full (native, not post-conversion) |
| `pdfua` | native PDF/UA-1 (and UA-2) | Full |
| `metadata` (JSON) | document info + XMP (Title/Author/Subject/Keywords/Creator/Producer/CreationDate/ModDate/Trapped); CreationDate default deterministic | Full |
| `embeds`, `embedsMetadata` | file attachments (`/EmbeddedFiles`, `/AF` for PDF/A-3) | Full (needed for Factur-X) |
| `facturxXml`, `facturxConformanceLevel`, `facturxDocumentType`, `facturxVersion` | PDF/A-3b + embedded `factur-x.xml` + XMP extension schema | Partial (later milestone; high value for invoices) |
| `userPassword`, `ownerPassword`, `allow*` | PDF encryption (AES-256) | Partial / later |
| `splitMode`, `splitSpan`, `splitUnify` | post-pagination split into multiple outputs (zip) | Partial / later |
| `watermark*`, `stamp*` | prefer CSS (`@page` background / margin boxes) — accept text watermark natively; image/pdf sources later | Partial |
| `rotateAngle`, `rotatePages` | page `/Rotate` | Partial |
| `optimizeImages`, `imageQuality` | image recompression option | Partial |
| `Gotenberg-Output-Filename` | `Content-Disposition` filename | Full |
| `Gotenberg-Trace` | request id header | Full |
| `Gotenberg-Webhook-*` | async webhook delivery | Partial / later |
| Screenshot routes | out of scope | Rejected |

---

## Findings that affect recto's design

1. **Default margins differ by caller**: raw CDP 1 cm (floored to 28 pt), Puppeteer/Playwright 0, Gotenberg 0.39 in, headless CLI 1 cm. Each compat entry point must inject its own default. Recommendation for recto's native CLI: 1 cm when the document has no `@page` margin, because that is what `chrome --print-to-pdf` users get today (and printing with zero margin is rarely intended); the Node compat layer uses 0, the Gotenberg route 0.39 in.
2. **Author `@page` margins override option margins in Chrome**; author `@page size` overrides option size only under `preferCSSPageSize`. Implement options as UA-origin `@page` (margins) and user-`!important` vs UA-origin (size, depending on `preferCSSPageSize`).
3. **Empty header/footer template ⇒ Chrome default (date/title, url, n/N at 8pt)**. Puppeteer's default `headerTemplate: ''` triggers it; real code works around with `'<p></p>'`. Compat must reproduce the default when `displayHeaderFooter` is true and a template is `''`, and must render header/footer inside the margin area only (zero margin ⇒ invisible).
4. **Header templates are isolated documents**: no page styles, no scripts, values injected via class names (`date,title,url,pageNumber,totalPages`), every matching element replaced. Translate to recto running elements + `counter(page)`/`counter(pages)` with a separate style scope; this gives users a migration path to native `@page` margin boxes.
5. **`pageRanges` grammar** (§1.1) must be implemented exactly, including `-`, `-B`, `A-`, silent capping and the two error classes; Gotenberg exposes it as `nativePageRanges`.
6. **Unit parsing differs**: Puppeteer/Playwright bare number = px, suffix by last 2 chars (px/in/cm/mm only, cm=37.8 px); Gotenberg bare number = inches, units pt/px/in/mm/cm/pc. Two separate parsers in CMP/SRV; use exact constants internally but offer a bit-exact compat flag.
7. **Paper sizes**: Puppeteer A4 = 8.2677×11.6929 in, Playwright 8.27×11.7 in, Chrome ceils to whole points (A4 → 596×842 / 596×843 pt). recto should emit exact ISO sizes (595.276×841.890 pt) and document the ≤1.3 pt difference; never round to points.
8. **Tagging defaults conflict**: Puppeteer `tagged: true`, Playwright `false`, Gotenberg `false` (+ `--disable-pdf-tagging`), CLI true. Chrome's outline requires tagging. recto: tag by default, decouple outline from tagging, honour explicit `false`.
9. **`printBackground=false` is the Puppeteer default but nearly every real caller sets `true`**; Gotenberg forces `print-color-adjust: exact` on everything. recto needs `print-color-adjust` support plus a `print_backgrounds` engine flag; native default true.
10. **Media emulation is mainstream** (`screen`, plus media features): recto must expose `media` and media-feature overrides in CLI, server and bindings.
11. **`singlePage` (auto-height page) and `initialPageNumber` (Browsershot hack)** are real needs; recto can do both natively (infinite-height fragmentainer; `counter-reset: page N` / `first_page_number` option).
12. **Load/JS wait knobs** (`waitDelay`, `waitForExpression`, `waitForSelector`, `waitForFonts`, network idle) are the biggest category of Gotenberg/Browsershot options; recto should accept and ignore them with a warning, not reject, to keep migrations painless — except URL inputs, which are rejected unless network is explicitly enabled.
13. **Determinism**: Chrome output always varies via `/CreationDate`/`/ModDate` (= now), header `date` (= now, locale-formatted), `/Producer` (`Skia/PDF m<milestone>`), `/Creator` (agent), system fonts and network timing; Chrome emits no `/ID` and no XMP (so it is not PDF/A-valid without post-processing — which is why Gotenberg runs a separate PDF/A conversion step). recto's selling point: byte-identical output, `SOURCE_DATE_EPOCH`, content-hash `/ID`, native PDF/A + Factur-X instead of post-conversion.
14. **Gotenberg's post-processing pipeline** (split, watermark, stamp, rotate, optimize, PDF/A, metadata, embeds, Factur-X, encrypt) is part of the de-facto API that invoice users rely on; recto's server should at least support `pdfa`, `pdfua`, `metadata`, `embeds`, Factur-X natively, with others staged.
15. **`scale`** reflows layout (content width / scale) and is validated to [0.1, 2]; replicate the range check and error message shape.
16. Header/footer text without explicit `font-size` is reported tiny in Chrome; recto's translation should apply Chrome's template-page CSS but users should be told to migrate to `@page` margin boxes.

## Recommendation

- Build the Puppeteer compat layer (CMP) as a pure options→(UA stylesheet + engine options) translator following §8, with per-entry-point default tables (Puppeteer, Playwright, Gotenberg, Chrome CLI) encoded as data and covered by golden tests that assert the synthesised `@page` CSS and engine options for each of the defaults listed here.
- Expose a Gotenberg-compatible multipart route (`/forms/chromium/convert/html`) in the server (SRV) using §9, including `Gotenberg-Output-Filename` and HTTP 400 parity for invalid ranges/scale/omitBackground, so existing Gotenberg clients (there are SDKs in many languages) can switch by changing the base URL.
- Accept the headless CLI flags `--print-to-pdf[=path]`, `--no-pdf-header-footer`, `--print-to-pdf-no-header`, `--disable-pdf-tagging`, `--generate-pdf-document-outline` in a `chrome` CLI shim, with Chrome CLI defaults (`printBackground`/`preferCSSPageSize` true, default header/footer on).
- Do not emulate Chrome's point-rounding or shrink-to-fit; document these as intentional deviations with measured magnitudes.

## Open questions / UNVERIFIED items

1. Exact `MediaBox` Chrome emits for `format: 'A4'` (derived 596×842 pt from `ToCeiledSize`); not verified empirically (no Chrome binary run). Similarly whether CSS `@page { size: A4 }` under `preferCSSPageSize` yields exact 595.28×841.89 pt.
2. Scale factor applied to header/footer template content (body width set in "px" equal to point dimensions) and the effective default font size of user templates — UNVERIFIED; folklore says "tiny", set font-size explicitly.
3. Whether external images (`http:`/`file:`) load in header/footer templates — UNVERIFIED in source (folklore: only data: URIs work).
4. Value of `totalPages` in headers when `pageRanges` restricts output (document total vs printed total) — UNVERIFIED.
5. Whether `printBackground=false` in Blink also alters text/border colours ("modified colors for printing") beyond dropping backgrounds — UNVERIFIED.
6. `/Creator` string value in headless Chrome output (`printing::SetAgent` caller not found in the sparse checkout) — UNVERIFIED.
7. Gotenberg issues #831 (reason for `--disable-pdf-tagging`) and #1210 not read (GitHub issues not cloned) — UNVERIFIED.
8. When `--print-to-pdf-no-header` was removed from Chromium — not determined (only its absence in current source is verified).
9. Option-frequency ranking (§7.3) is qualitative from a small sample (Browsershot, Gotenberg, one invoice example), not a code-search census.
