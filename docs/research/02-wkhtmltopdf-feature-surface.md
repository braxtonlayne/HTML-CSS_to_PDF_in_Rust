# 02 — wkhtmltopdf feature surface & `recto wkhtmltopdf` compatibility matrix

Date: 2026-10-14 · Topic slug: `wkhtmltopdf` · Author: research agent (Phase 0)

Purpose: catalog every wkhtmltopdf 0.12.6 CLI flag and the behaviours behind them (from source), so that `recto wkhtmltopdf …` can be a drop-in shim; define support levels for v1; document the smart-shrinking scale algorithm precisely enough to emulate.

## Sources inspected

| Name | Version / tag | Commit SHA | License | Last commit | Maintenance assessment |
|---|---|---|---|---|---|
| wkhtmltopdf/wkhtmltopdf | tag `0.12.6` (2020-06-11); also looked at `master` | tag `6a57c1449797d6cb915921fb747f3ac36199241f`; master HEAD `024b2b2bb459dd904d15b911d04c6df4ff2c9031` | LGPL-3.0-or-later (`LICENSE`, file headers) | master 2022-06-29 (`git log -1`) | **Abandoned.** 0.12.6 is the last release (`CHANGELOG.md`); master's `VERSION` = `0.12.7-dev`, only 31 commits after 0.12.6 (packaging/docs/Qt bumps). The GitHub repo was archived (read-only) on **2023-01-02** according to third-party sources (see below). I could not hit the GitHub API from this sandbox (`gh api` → 403), so the archive date itself is **UNVERIFIED from a primary source**. The last commit date is verified from the clone. |
| wkhtmltopdf/qt (patched Qt 4.8 + QtWebKit ~534) | branch `wk_4.8.7` (git submodule `qt` of the repo, `.gitmodules`) | `aa2e3129f8ef05dfa72c4b183feb8b7e1927ac8a` (2022-06-22) | LGPL-2.1 (Qt 4.8) | 2022-06-22 | Frozen fork of Qt 4.8.7 and an old WebKit; same status as the main repo. I sparse-checked out `WebCore/page/*`, `WebKit/qt/Api/*`, `src/gui/painting/{qprinter,qpdf,qprintengine_pdf}.cpp`. |
| KnpLabs/snappy (PHP) | `v1.7.3` | `f749a7d2e0f1260f4a0f96925323e34ede898f1f` | MIT | 2026-07-29 | Active |
| barryvdh/laravel-snappy (PHP, wraps snappy `^1.4.4`) | HEAD (no tag in the shallow clone) | `f38fff4c764b75aa99b652a3eb6ea6b7bc0a4acc` | MIT | 2026-08-21 | Active |
| JazzCore/python-pdfkit | HEAD (`pdfkit/__init__.py` `__version__ = '2.0.0'`) | `fb86d338a3706e6e0ede09170b9fa58fb740ec1e` | MIT | 2023-09-14 | Dormant |
| mileszs/wicked_pdf (Ruby) | HEAD (`lib/wicked_pdf/version.rb` `2.8.1`) | `bce498de547cdf00d037fdbec29fae844d69ee8e` | MIT | 2025-07-24 | Low activity |
| devongovett/node-wkhtmltopdf | HEAD (`package.json` `0.4.0`) | `51745d803a65134dd87c30fd3276ca48630e467d` | MIT (per package; no LICENSE file in the clone) | 2021-05-14 | Dormant |
| rdvojmoc/DinkToPdf (.NET, uses libwkhtmltox C API) | HEAD | `b0546d21641eaef71f6fe0ddfd3998e8502baab7` | MIT | 2018-04-19 | Abandoned |
| SebastiaanKlippert/go-wkhtmltopdf | HEAD | `1eb8cee79c70601d92fbf8449614b840d35a91ed` | MIT | 2025-10-30 | Low activity |

Clones: `/tmp/claude-0/src/wkhtmltopdf/{wk,qt,snappy,laravel-snappy,python-pdfkit,wicked_pdf,node-wkhtmltopdf,DinkToPdf,go-wkhtmltopdf}`. Unless stated otherwise, every `src/...` path below refers to the wkhtmltopdf repo at tag `0.12.6`, and every `src/3rdparty/...` or `src/gui/...` path refers to the `wkhtmltopdf/qt` clone.

Web sources (used only for the archive status): <https://www.itechguides.com/wkhtmltopdf-alternatives-how-to-migrate-safely/> and <https://awesome.ecosyste.ms/projects/67736>. Both say "archived 2023-01-02, last push 2022-11-22". These are secondary sources.

---

## 1. Architecture facts that drive compatibility

1. **Patched vs unpatched Qt.** Many features only exist in builds against the patched Qt. In the source they sit behind `__EXTENSIVE_WKHTMLTOPDF_QT_HACK__`, and the CLI marks each such flag with `qthack(true)`. The unpatched-only list (`src/pdf/pdfdocparts.cc`, `outputNotPatched`) is: more than one input document, running without X11, outline, headers/footers, TOC, links, printing with the *screen* media type, and disabling smart shrinking. An unpatched build prints `"The switch %s, is not support using unpatched qt, and will be ignored."` (`src/shared/commandlineparserbase.cc:136-139`). The official 0.12.6 binaries are patched builds, so **the shim must emulate the patched behaviour.** `--version` prints `wkhtmltopdf 0.12.6 (with patched qt)` (`commandlineparserbase.cc:80,90-91`).
2. **Pipeline** (`src/lib/pdfconverter.cc`):
   1. Load every page object. Header/footer HTML is also loaded at this stage, to measure its height when no margin was given (`beginConvert`, l.141-236).
   2. Count pages, build the outline from h1–h9 (`preprocessPage`, l.288-321).
   3. Generate the TOC XML, run it through XSLT, and load the TOC HTML. This repeats until the TOC page count and outline stop changing (`loadTocs`/`tocLoaded`, l.476-539 and 731-778).
   4. Resolve links (`findLinks`).
   5. Load header/footer HTML **once per output page**, with the variables in the query string (`loadHeaders`, l.440-473).
   6. Print each page via `QWebPrinter::spoolPage` and draw the text headers/footers (`endPage`, l.599-714).
   7. Write the outline (bookmarks) and optionally `--dump-outline`.
3. **Rendering is WebKit "print" pagination.** Layout is done once at a fixed width and then sliced into page-height strips (`PrintContext::computePageRects`, `src/3rdparty/webkit/Source/WebCore/page/PrintContext.cpp:66-111`). Page size, orientation and margins come **only from CLI/QPrinter settings**. `QWebPrinterPrivate` builds the page rect from `printer->width()/height()` (`src/3rdparty/webkit/Source/WebKit/qt/Api/qwebframe.cpp:220-232`) and never consults CSS `@page`, so **CSS `@page { size; margin }` is ignored** by wkhtmltopdf (derived from that code path). The shim should give CLI options priority over the document's `@page` rules for size and margins. See finding 3.
4. **Default media type is `screen`.** `Web::printMediaType = false` (`src/lib/websettings.cc`), and `updateWebSettings` calls `setPrintingMediaType(s.printMediaType?"print":"screen")` (`src/lib/converter.cc:46`). **Backgrounds are printed by default.** `Web::background = true` maps to `QWebSettings::PrintElementBackgrounds` (`converter.cc:54`).
5. **Command-line grammar** (`src/pdf/pdfcommandlineparser.cc`, `parseArguments`):
   ```
   wkhtmltopdf [GLOBAL OPTION]... [OBJECT]... <output file>
   OBJECT := (page)? <url|file|-> [PAGE OPTION]...
           | cover <url|file> [PAGE OPTION]...
           | toc [PAGE OPTION | TOC OPTION]...
   ```
   - Options before the first object may be global *or* page options. Page options given there become the defaults for **every** object (a `PdfObject def` is copied for each object).
   - Options after an object apply only to that object. A global option placed after an object is a hard error: `"%s specified in incorrect location"` (`commandlineparserbase.cc:120-124`).
   - TOC options are only legal after `toc`.
   - The last argv entry is always the output file. `-` means stdin (input) or stdout (output).
   - Long options are `--name value` with a **separate** argv entry. `--name=value` is **not** supported: `longToHandler.find(argv+2)` looks up the whole string.
   - Short switches can be combined (`-qg`). Each short switch with an argument takes the next argv entry in order.
   - There is a bug in the `--` "default mode" check. The code tests `argv[arg][2]=='0'` (the character `'0'`), not `'\0'` (`commandlineparserbase.cc:109`). A bare `--` therefore fails with "Unknown long argument --".
   - Unknown options are a hard error (exit 1 after printing usage).
6. **Cover object** = a page object with header/footer cleared, `includeInOutline=false`. It **still counts in page numbering** (`pagesCount` stays true) (`pdfcommandlineparser.cc`, the `cover` branch).
7. **Exit codes** (`src/lib/utilities.cc:140-180`):
   - 0: success.
   - 1: generic failure, or any HTTP/network error code not listed below.
   - 2: HTTP 404.
   - 3: HTTP 401.
   - Network errors are reported as code+1000 internally.

   **Stderr format** (`src/shared/progressfeedback.cc`):
   - `Warning: …` at `--log-level warn` and above.
   - `Error: …` at error and above.
   - At `info` (the default) it also prints phase names and progress bars, ending with `Done`.
   - `--quiet` is the same as `--log-level none`.

   Wrappers depend on this:
   - python-pdfkit tolerates a non-zero exit when the second-to-last stderr line is `Done`, and raises if `Error` appears in stderr (`python-pdfkit/pdfkit/pdfkit.py:129-150`).
   - Snappy throws only when the status is non-zero **and** stderr is non-empty (`snappy/src/Knp/Snappy/AbstractGenerator.php:477-482`).
   - wicked_pdf parses `--version` with `/wkhtmltopdf\s*(\d*\.\d*\.\d*\w*)/` (`wicked_pdf/lib/wicked_pdf/binary.rb:23`).
8. **Input URL guessing** (`MultiPageLoader::guessUrlFromString`, `src/lib/multipageloader.cc:690-747`):
   - A string with a scheme is parsed as a URL.
   - An existing file path becomes a `file://` URL to its absolute path.
   - `host.tld…` becomes `http://…`.
   - Stdin (`-`) and C-API in-memory HTML are written to a **temp `.html` file**. Relative URLs in stdin HTML therefore resolve against the temp dir, and they are blocked anyway by the default local-file policy.

---

## 2. Complete CLI flag catalog (0.12.6)

Sources: `src/shared/commonarguments.cc` (doc/web/load args), `src/pdf/pdfarguments.cc` (PDF args), defaults from `src/lib/pdfsettings.cc:351-408`, `src/lib/loadsettings.cc:128-149`, `src/lib/websettings.cc`.

Column legend: **Scope** G = global-only; P = page option (also allowed in the global area, where it sets the default for all objects); T = only after `toc`. **QT** ✓ = the flag is `qthack(true)` (patched Qt required). **Ext** ✓ = hidden from plain `--help` (`extended(true)`).

### 2.1 Documentation / meta (G)

| Long | Short | Arg | Behaviour |
|---|---|---|---|
| `--help` | `-h` | – | Usage to stdout, exit 0 |
| `--version` | `-V` | – | `wkhtmltopdf 0.12.6 (with patched qt)`, exit 0 |
| `--license` | – | – | Prints the license |
| `--extended-help` | `-H` | – | Full usage. (The manual's examples misuse `-H` as if it were "default header": `pdfdocparts.cc` `outputExamples`.) |
| `--manpage`, `--htmldoc`, `--readme` | – | – | Ext; print docs |

### 2.2 Global options (`section("Global Options")`, `mode(global)`)

| Long | Short | Arg type | Default | Ext | QT | Semantics (source) |
|---|---|---|---|---|---|---|
| `--quiet` | `-q` | – | – | | | `logLevel=None` |
| `--log-level` | – | `none\|error\|warn\|info` (case-insensitive; `src/lib/logging.cc:40`) | `info` | | | Stderr verbosity |
| `--no-collate` / `--collate` | – | – | collate=true | | | Copy ordering |
| `--copies` | – | int | 1 | | | Repeats the page sequence N times (`printDocument`, `spoolTo`) |
| `--orientation` | `-O` | `Landscape\|Portrait` (case-insensitive) | Portrait | | | `QPrinter::setOrientation` |
| `--page-size` | `-s` | name (case-insensitive, list §5) | `A4` | | | Unknown name → "Invalid argument(s)" error |
| `--grayscale` | `-g` | – | Color | | | `QPrinter::GrayScale` (§6.6) |
| `--lowquality` | `-l` | – | HighResolution | | | Printer mode ScreenResolution (§6.6: effectively no-op) |
| `--title` | – | text | first object's `<title>` | | | PDF `/Title` (`pdfconverter.cc:409-416`) |
| `--read-args-from-stdin` | – | – | false | | | Each stdin line is a separate invocation, appended to argv (`src/pdf/wkhtmltopdf.cc` main) |
| `--margin-bottom` | `-B` | unitreal | unset(-1) → 10mm or header-measured | ✓ | | §6.3 |
| `--margin-left` | `-L` | unitreal | 10mm | ✓ | | |
| `--margin-right` | `-R` | unitreal | 10mm | ✓ | | |
| `--margin-top` | `-T` | unitreal | unset(-1) → 10mm or header-measured | ✓ | | |
| `--dpi` | `-d` | int | 96 | ✓ | | §6.2: geometry-neutral |
| `--page-height` / `--page-width` | – | unitreal | unset | ✓ | | Used only if **both** are set. The **height's unit is used for both** values (`pdfconverter.cc:380-381` `QSizeF(w.first,h.first), h.second`) — a bug |
| `--cookie-jar` | – | path | – | ✓ | | Netscape-ish raw cookie file, read and written (`multipageloader.cc:521-545`) |
| `--image-quality` | – | int | 94 | ✓ | ✓ | JPEG quality for re-encoded images |
| `--image-dpi` | – | int | 600 | ✓ | ✓ | Downsample images above this effective DPI |
| `--no-pdf-compression` | – | – | compression on | ✓ | ✓ | Disables Flate on streams |
| `--use-xserver` | – | – | false | ✓ | ✓ | Unix only |

### 2.3 Outline options (G; `section("Outline Options")`, still `mode(global)`)

| Long | Arg | Default | Semantics |
|---|---|---|---|
| `--outline` / `--no-outline` | – | **outline=true** | PDF bookmarks from h1–h9 (§7) |
| `--outline-depth` | int | 4 | Max bookmark tree depth (`src/lib/outline.cc:114`) |
| `--dump-outline` | file | – | Writes the outline XML (§7.2) |
| `--dump-default-toc-xsl` | – | – | Prints the default XSL to stdout and exits |

### 2.4 Page options (P; `section("Page Options")`, `mode(page)`)

| Long | Short | Arg | Default | QT | Semantics |
|---|---|---|---|---|---|
| `--default-header` | – | – | – | | Sets header-left=`[webpage]`, header-right=`[page]/[topage]`, header-line, **global** margin-top=2cm (`pdfarguments.cc:138-146`). Its help text says `--top 2cm` and `[toPage]`, but the code does the above |
| `--viewport-size` | – | `WxH` string | "" | | Global setting, page-placed; `QWebPage::setViewportSize`, scrollbars off (`pdfconverter.cc:127-133,304-308`) |
| `--enable-plugins` / `--disable-plugins` | – | – | disabled | | NPAPI/Java |
| `--minimum-font-size` | – | int | -1 (none) | | `QWebSettings::MinimumFontSize` |
| `--user-style-sheet` | – | path/url | – | | User stylesheet URL (`converter.cc:57-58`) |
| `--no-images` / `--images` | – | – | images on | | `AutoLoadImages` |
| `--disable-javascript` / `--enable-javascript` | `-n` (disable) | – | **JS enabled** | | |
| `--encoding` | – | encoding name | "" | | `setDefaultTextEncoding` (fallback charset). 0.12.6 changelog #4612: now works unpatched too |
| `--no-background` / `--background` | – | – | **background=true** | | `PrintElementBackgrounds` |
| `--include-in-outline` / `--exclude-from-outline` | – | – | include | ✓ | Outline and TOC participation |
| `--disable-smart-shrinking` / `--enable-smart-shrinking` | – | – | **enabled** | ✓ | §6.1 |
| `--print-media-type` / `--no-print-media-type` | – | – | **screen** | ✓ | |
| `--enable-forms` / `--disable-forms` | – | – | disabled | ✓ | AcroForm text/password/textarea/checkbox (`pdfconverter.cc:829-850`). Input text is painted white so the field shows instead (l.909-914) |
| `--disable-internal-links` / `--enable-internal-links` | – | – | enabled | ✓ | `__WKANCHOR_*` and cross-object links |
| `--disable-external-links` / `--enable-external-links` | – | – | enabled | ✓ | URI link annotations |
| `--resolve-relative-links` / `--keep-relative-links` | – | – | resolve | ✓ | Global setting (`s.resolveRelativeLinks`) |
| `--enable-toc-back-links` / `--disable-toc-back-links` | – | – | disabled | ✓ | Heading links back to the TOC entry |
| `--proxy` | `-p` | proxy string | env `proxy`/`all_proxy`/`http_proxy` (`commondocparts.cc` outputProxyDoc) | | Grammar `(http://\|socks5://)?(user(:pw)?@)?host(:port)?` or `none`; default port 1080 (`loadsettings.cc:64-110`) |
| `--proxy-hostname-lookup` | – | – | false | | DNS via proxy |
| `--bypass-proxy-for` | – | host (repeatable) | – | | |
| `--username` / `--password` | – | str | – | | HTTP auth |
| `--ssl-key-path` / `--ssl-key-password` / `--ssl-crt-path` | – | path/str | – | | Client cert; all 3 are required to take effect (`multipageloader.cc:114-135`) |
| `--load-error-handling` | – | `abort\|ignore\|skip` | abort | | Main-page load failure (§6.8) |
| `--load-media-error-handling` | – | `abort\|ignore\|skip` | **ignore** | | Failures of `css js png jpg jpeg gif` resources (`loadsettings.cc:32-38`) |
| `--custom-header` | – | name value (repeatable, 2 argv) | – | | Raw header on the main request |
| `--custom-header-propagation` / `--no-custom-header-propagation` | – | – | false | | Repeat custom headers on every sub-request. **Bug:** both flags set `true` (`commonarguments.cc:216-217`) |
| `--javascript-delay` | – | msec | **200** | | Wait after load (`multipageloader.cc:321-323`) |
| `--window-status` | – | str | "" | | Poll `window.status` every 50ms until it equals the value, then wait the jsdelay (l.326-333). Main page only |
| `--zoom` | – | float | 1.0 | | Page zoom (§6.1) |
| `--cookie` | – | name value (repeatable) | – | | Value "should be url encoded" |
| `--post` | – | name value (repeatable) | – | | Form-urlencoded POST body |
| `--post-file` | – | name path (repeatable) | – | | Switches the body to multipart |
| `--disable-local-file-access` / `--enable-local-file-access` | – | – | **blocked (0.12.6)** | | §6.7 |
| `--allow` | – | path (repeatable) | – | | Allow-list for local files |
| `--cache-dir` | – | path | – | | QNetworkDiskCache |
| `--debug-javascript` / `--no-debug-javascript` | – | – | false | | console → warnings |
| `--stop-slow-scripts` / `--no-stop-slow-scripts` | – | – | true | | |
| `--run-script` | – | js (repeatable) | – | | Evaluated after load, main loader only (`multipageloader.cc:315-317`) |
| `--checkbox-svg`, `--checkbox-checked-svg`, `--radiobutton-svg`, `--radiobutton-checked-svg` | – | path | "" | | Form-control rendering |
| `--page-offset` | – | int | **0** (arg default 1) | | Global setting, page-placed. Added to every printed page number (§4) |

### 2.5 Headers and footers (P; `section("Headers And Footer Options")`, all QT ✓, Ext ✓)

Header defaults come from `HeaderFooter::HeaderFooter` (`pdfsettings.cc:356-364`): fontSize 12, fontName "Arial", empty texts, line false, htmlUrl "", spacing 0.0 (mm).

| Long | Arg | Semantics |
|---|---|---|
| `--header-left` / `--header-center` / `--header-right` | text with `[var]` | Text drawn with QPainter (§4.2) |
| `--footer-left` / `--footer-center` / `--footer-right` | text | |
| `--header-font-name` / `--footer-font-name` | name | Default Arial |
| `--header-font-size` / `--footer-font-size` | int | Default 12 (QFont point size) |
| `--header-line` / `--no-header-line` | – | Rule below the header |
| `--footer-line` / `--no-footer-line` | – | Rule above the footer |
| `--header-spacing` / `--footer-spacing` | real (mm) | Gap between header/footer and content |
| `--header-html` / `--footer-html` | url/path | HTML header (§4.3). Error if the value "looks like HTML" (contains `<` before any `?`) or starts with `data:` (`pdfconverter.cc:73-76,162-186`) |
| `--replace` | name value (repeatable) | Extra `[name]` variables |

### 2.6 TOC options (T; all QT ✓, Ext ✓) — the `toc` object also accepts every page option

| Long | Arg | Default | Semantics |
|---|---|---|---|
| `--xsl-style-sheet` | file | built-in | XSLT 2.0 (QXmlQuery) over the outline XML (`pdfconverter.cc:488-521`) |
| `--toc-header-text` | text | "Table of Contents" | Caption (and `<title>`) |
| `--disable-toc-links` | – | links on | No TOC→heading links |
| `--disable-dotted-lines` | – | dotted on | The rule is actually `border-bottom: 1px dashed rgb(200,200,200)` |
| `--toc-text-size-shrink` | real | 0.8 | Nested `ul ul {font-size: N*100%}` |
| `--toc-level-indentation` | CSS length string | `1em` | `ul ul {padding-left: …}` |

### 2.7 Not flags in 0.12.6 (wrappers still emit them)

These are rejected by 0.12.6 as `Unknown long argument`:
- `--book` (a `BookFunc` exists but is never registered: `pdfarguments.cc:151-161`).
- `--redirect-delay`, `--ignore-load-errors`.
- `--toc-depth`, `--toc-font-name`, `--toc-l1-font-size`, `--toc-header-font-*`, `--toc-no-dots`, `--toc-disable-links`, `--toc-disable-back-links`, `--toc-lN-*`.
- `--output-format` (wkhtmltoimage only).

Snappy lists them as `// old v0.9` (`snappy/src/Knp/Snappy/Pdf.php:113,189,232-237`). wicked_pdf still emits `--book`, `--redirect-delay` and `--toc-*` from its option parser (`wicked_pdf/lib/wicked_pdf/option_parser.rb:101-125,176-183`).

---

## 3. libwkhtmltox C API (`src/lib/pdf.h`, `docs/libwkhtmltox/pagesettings.html`, reflection in `src/lib/pdfsettings.cc:106-167`, `src/lib/reflect.cc:54-95`)

Functions:
- Lifecycle: `wkhtmltopdf_init(use_graphics)`, `_deinit`, `_extended_qt`, `_version`.
- Settings objects: `_create/_destroy_global_settings`, `_create/_destroy_object_settings`.
- Settings access: `_set/_get_global_setting(name,value)`, `_set/_get_object_setting`.
- Converter: `_create/_destroy_converter`.
- Callbacks: `_set_{warning,error,phase_changed,progress_changed,finished}_callback`.
- Conversion: `_convert`, `_add_object(converter, object_settings, const char* data)` (data = in-memory HTML).
- Progress: `_current_phase`, `_phase_count`, `_phase_description`, `_progress_string`.
- Results: `_http_error_code`, `_get_output(converter, const unsigned char**)` when `out` is empty.

Every setting is a UTF-8 string, parsed by reflection. These names are also the natural keys for a recto "wk-compat settings JSON":

- **Global** (`PdfGlobal`): `size.pageSize`, `size.width`, `size.height`, `quiet` (compat alias), `logLevel`, `useGraphics`, `resolveRelativeLinks`, `orientation`, `colorMode` (`color|grayscale`), `resolution` (`screen|printer|high`), `dpi`, `pageOffset`, `copies`, `collate`, `outline`, `outlineDepth`, `dumpOutline`, `out` (""=memory buffer, "-"=stdout), `documentTitle`, `useCompression`, `margin.{top,right,bottom,left}`, `imageDPI`, `imageQuality`, `load.cookieJar`, `viewportSize`.
- **Object** (`PdfObject`):
  - `toc.{useDottedLines,captionText,forwardLinks,backLinks,indentation,fontScale}`, `page`.
  - `header.*` / `footer.*` = `{fontSize,fontName,left,right,center,line,htmlUrl,spacing}`.
  - `useExternalLinks`, `useLocalLinks`, `replacements`, `produceForms`, `includeInOutline`.
  - `pagesCount` — **API-only**: exclude an object from page numbering.
  - `isTableOfContent`, `tocXsl`.
  - `web.{background,loadImages,enableJavascript,enableIntelligentShrinking,minimumFontSize,printMediaType,defaultEncoding,userStyleSheet,enablePlugins}`.
  - `load.{username,password,clientSslKeyPath,clientSslKeyPassword,clientSslCrtPath,jsdelay,windowStatus,zoomFactor,customHeaders,repeatCustomHeaders,cookies,post,blockLocalFileAccess,allowed,stopSlowScripts,debugJavascript,loadErrorHandling,proxy,runScript,checkboxSvg,checkboxCheckedSvg,radiobuttonSvg,radiobuttonCheckedSvg,cacheDir,bypassProxyForHosts,proxyHostNameLookup}`.
  - `mediaLoadErrorHandling` is **not** reflected, so it cannot be set via the API.

Gaps and quirks:
- The docs list `load.stopSlowScript` (singular) and `load.repertCustomHeaders` (typo). The reflected names are `stopSlowScripts` and `repeatCustomHeaders`.
- DinkToPdf uses the wrong name `load.stopSlowScript` (`grep WkHtml(` in `DinkToPdf/src`), so that setting silently fails.
- DinkToPdf never uses `size.pageSize`. It always sends `size.width`/`size.height` with units, and margins as `"<n>mm|in|cm"` (`DinkToPdf/src/DinkToPdf/Settings/MarginSettings.cs:44-58`).
- Phases:
  - Patched build: "Loading pages", "Counting pages", "Loading TOC", "Resolving links", "Loading headers and footers", "Printing pages", "Done" (`pdfconverter.cc:88-98`).
  - Unpatched build: "Loading page", "Printing pages", "Done".

Recto's C ABI/bindings could offer a `wkhtmltox`-compatible façade (same function names, string settings). That is out of scope for v1, but the settings table above is the full contract.

---

## 4. Header/footer variables and injection

### 4.1 Variable values (`PdfConverterPrivate::fillParms`, `pdfconverter.cc:588-596`; `Outline::fillHeaderFooterParms`, `src/lib/outline.cc:294-321`; `loadHeaders`/`endPage`)

`off = --page-offset` (default 0). `pageNumber` is the 1-based running number over all objects whose `pagesCount` is true; covers and TOCs count.

| Var | Value |
|---|---|
| `[page]` | `pageNumber + off` |
| `[frompage]` | `off + 1` |
| `[topage]` | `off + totalPageCount` (outline's page count) |
| `[webpage]` | `ps.page`, the input string **as given** on the CLI (e.g. `-`, `/tmp/x.html`, `http://…`) |
| `[section]` | Level-0 outline item for this page (see below) |
| `[subsection]` | Level-1 item |
| `[subsubsection]` | Level-2 item (**undocumented**) |
| `[date]` | `QDate::toString(Qt::SystemLocaleShortDate)` — system locale |
| `[isodate]` | `YYYY-MM-DD` (`Qt::ISODate`) |
| `[time]` | `QTime::toString(Qt::SystemLocaleShortDate)` |
| `[title]` | This object's `<title>` |
| `[doctitle]` | `--title`, else the first non-TOC object's `<title>` |
| `[sitepage]` | 1-based page index within the current object |
| `[sitepages]` | Page count of the current object |
| `--replace k v` | Inserted **first**, so the built-ins override a same-named replacement (`outline.cc:311-312`) |

Notes on these values:
- `[topage]` is the total for the whole document. There is no per-object total except `[sitepages]`.
- `[date]` and `[time]` are evaluated at print time, which makes output non-deterministic.

**Section semantics** (`OutlinePrivate::buildHFCache`, `outline.cc` ~l.270-292). `hfCache[level][page]` is set to the **first** outline item at that level that *starts* on that page. A page with no new item inherits `hfCache[level].back()`, the value of the previous page. Consequences:
1. A page with no new heading shows the carried value.
2. If a page holds several level-0 headings, the following pages carry the **first** one on that page, not the last. This is a quirk.

"Level" means **outline-tree depth**, not the h-tag number (§7.1). An approximate CSS equivalent is `string-set` on the top-level heading tag plus `string(section, first)`.

### 4.2 Text headers (`--header-left/center/right`)

- Substitution is `hfreplace`: for each param, case-insensitive `replace("["+key+"]", value)` in `QHash` iteration order (`pdfconverter.cc:1077-1082`). `[toPage]`, `[Page]` etc. therefore work; DinkToPdf's README uses `[toPage]` (`DinkToPdf/README.md:48`). Values are not escaped. If a substituted value contains `[page]`, it may be substituted again depending on hash order (undefined).
- A page "has header/footer text" if any left/center/right text is non-empty or a line is enabled (`beginPrintObject`, l.903-906).
- Geometry (`endPage`, l.599-645). Device coords are reset so that (0,0) is the top-left of the **content area** (inside the margins) and `w`,`h` are the content-area size.
  - `spacingPx = spacing_mm * printer.height/printer.heightMM`.
  - Header line: `drawLine(0,-spacingPx, w,-spacingPx)`.
  - Header text: `font = QFont(fontName, fontSize)`; `dy` = bounding-rect height of `"M"`. Text is drawn in rect `(0, -dy-spacingPx, w, h)` with AlignTop + Left/HCenter/Right. The text box therefore sits immediately above the content box, `spacing` mm above it. It does **not** fill or centre in the margin.
  - Footer: line at `y = h+spacingPx`; text in rect `(0,0,w,h+dy+spacingPx)` with AlignBottom, so it sits immediately below the content box.
  - The text spans only the content width (left/right margins are not used).
  - If the top margin is smaller than `dy+spacing`, the text is clipped off the page. The C-API docs warn about this.

### 4.3 HTML headers (`--header-html`/`--footer-html`)

1. **One load per output page.** For every page of every object with header/footer HTML, the converter builds `QUrl u = guessUrlFromString(url)`, appends every param as `u.addQueryItem(key, value)` (all §4.1 vars + `sitepage`/`sitepages` + replacements), and loads it as a new `QWebPage` with the object's `load` settings (`loadHeaderFooter`, `pdfconverter.cc:1065-1071`; `loadHeaders`, l.440-473). **Values reach the HTML only through the query string.** The page's own JS must read `location.search` and fill the DOM. The canonical `subst()` snippet in the manual (`pdfdocparts.cc` `outputHeaderFooterDoc`) splits `location.search` on `&` and `=`, `decodeURI`s each value, and for each name in `['page','frompage','topage','webpage','section','subsection','date','isodate','time','title','doctitle','sitepage','sitepages']` sets `textContent` of every element with that **class**. The JS runs on `onload`, and the default `--javascript-delay` of 200ms also applies to header pages.
2. **Rendering** (`endPage`, l.649-712):
   - The header page is printed with its own `QWebPrinter` at **content width** (left/right margins kept; top/bottom margins temporarily zeroed), with page settings re-applied via `updateWebSettings` (smart shrinking, media type…).
   - Header: translated up by `spacing` and then by the header body height (`elementLocation(body).height`). Its **bottom edge sits `spacing` above the content top**.
   - Footer: translated to `printer.height + spacing`, so its **top edge sits `spacing` below the content bottom**.
   - Only page 1 of the header document is spooled (`wp.spoolPage(1)`).
   - The background is forced transparent (`QPalette::Base` transparent; changelog 0.12.4 #2416).
   - Links inside headers become annotations.
3. **Automatic margin from header height** (`beginConvert` l.161-231, `measuringHeadersLoaded` l.781-806, `calculateHeaderHeight` l.241-262):
   - If `--header-html` is given and `--margin-top` is **not**, the header is loaded once (no query params) and measured. `margin-top = bodyHeight/2.83464567 + header-spacing` (mm).
   - `elementLocation` returns **printer device px (1/dpi in, i.e. 1/96 in by default)**, but the code divides by the mm→**pt** factor 2.83464567. The reserved margin is therefore **4/3 ≈ 1.333× the header's real printed height** (at dpi 96, one device px is 0.2646 mm, but the code reserves 0.3528 mm per px). This is a source-verified source of the famous "×1.33" effect. Derived from code reading; not run.
   - The measuring loader's pages never get `updateWebSettings`, so they are measured with **default smart shrinking (0.8) and screen media**, even if `--disable-smart-shrinking`/`--print-media-type` is set. Derived; **UNVERIFIED** at runtime.
   - If `--margin-top` **is** given together with `--header-html`, the reserved top margin is `margin-top + header-spacing`. The spacing number (mm) is added to the margin number in the *margin's* unit (unit-mixing bug).
   - Bottom/footer is symmetric.
   - Without any HTML header/footer, unset top/bottom margins become 10 (mm).
   - With multiple objects, the page margin is the **max** reserve over all objects (one global margin).
4. **Restrictions:** the value must be a URL or path, not HTML (§2.5). It is loaded under the object's local-file policy; a `file://` header URL is itself auto-allowed (`multipageloader.cc:202-205`). Data URIs are disallowed (changelog 0.12.3 #2280).

---

## 5. Page sizes, units, margins

**Names accepted by `--page-size`** (case-insensitive; `pdfsettings.cc:175-208`), with dimensions from Qt's table (`src/gui/painting/qprinter.cpp:89-120`, mm, portrait W×H):

| Name | mm | Name | mm |
|---|---|---|---|
| A0 | 841×1189 | B0 | 1000×1414 |
| A1 | 594×841 | B1 | 707×1000 |
| A2 | 420×594 | B2 | 500×707 |
| A3 | 297×420 | B3 | 353×500 |
| A4 | 210×297 | B4 | 250×353 |
| A5 | 148×210 | B5 | 176×250 |
| A6 | 105×148 | B6 | 125×176 |
| A7 | 74×105 | B7 | 88×125 |
| A8 | 52×74 | B8 | 62×88 |
| A9 | 37×52 (mislabelled "A8" in the Qt comment) | B9 | 33×62 |
| B10 | 31×44 | C5E | 163×229 |
| Comm10E | 105×241 | DLE | 110×220 |
| Executive | 190.5×254 | Folio | 210×330 |
| Letter | 215.9×279.4 | Legal | 215.9×355.6 |
| **Ledger** | **431.8×279.4 (landscape-shaped)** | Tabloid | 279.4×431.8 |

- B-series are ISO B, not JIS.
- For named sizes the PDF engine rounds the media box to **integer points**: `Q_MM(n) = int((n*720+127)/254)` (`src/gui/painting/qpdf.cpp:894-909`), e.g. A4 = 595×842 pt and Letter = 612×792 pt.
- Custom `--page-width/--page-height` go through `PPK_CustomPaperSize`; whether they are rounded is **UNVERIFIED**.
- Orientation swap with custom sizes is **UNVERIFIED** (Qt 4.8 `QPrinter::setOrientation` behaviour was not read).

**Units** (`strToUnitReal`, `pdfsettings.cc:259-294`):
- Grammar: `[0-9]*(\.[0-9]*)?` immediately followed by a unit.
- Units: (none)|`mm`|`millimeter` → mm; `cm`|`centimeter` (×10 mm); `m`|`meter` (×1000 mm); `in`|`inch`; `pc`|`pica`; `pt`|`point`; `px`|`pixel` (= QPrinter DevicePixel = 1/dpi in); `didot`; `cicero`. Units are case-insensitive.
- **No sign and no whitespace**: `-5mm`, `5 mm` and `1,5cm` are rejected with "Invalid argument(s)". Negative margins are therefore impossible.
- Unitless numbers are mm. wicked_pdf and go-wkhtmltopdf send bare integers, e.g. go `MarginBottom.Set(40)` → `--margin-bottom 40` (`go-wkhtmltopdf/README.md:31`).

**Margin unit rule:** after the cm/m→mm normalisation, all four margins must share a unit, otherwise `"Currently all margin units must be the same!"` and failure (`pdfconverter.cc:353-360`). Because the left/right defaults are 10mm, `--margin-top 1in` *alone* fails. python-pdfkit's README sets all four margins to `0.75in` (`python-pdfkit/README.rst:86-90`), which works.

---

## 6. Rendering-control semantics

### 6.1 Smart shrinking, zoom and the scale model (precise, from source)

Inputs:
- `W_dev, H_dev` = printable area (paper minus margins) in **printer device px**, i.e. `inches × dpi` (`printer->width()/height()`; `QPrinter::setResolution(dpi)`, `pdfconverter.cc:349-351`).
- `Z = (dpi/96) × zoom` — QWebFrame zoom, applied per loaded page (`multipageloader.cc:253-255`: `devicePixelRatio = dpi/96`; `setZoomFactor(devicePixelRatio*zoomFactor)`).
- Shrink factors `(min,max)`:
  - **Smart shrinking ON (default):** global QWebSettings defaults `min=1.25, max=2.0` (`src/3rdparty/webkit/Source/WebKit/qt/Api/qwebsettings.cpp:534-535`; WebCore fallbacks `PrintContext.cpp:39,45`).
  - **OFF** (`--disable-smart-shrinking`): `updateWebSettings` sets `min=max=1.0` (`src/lib/converter.cc:42-45`).

Algorithm:
1. `PrintContext::begin(W_dev, H_dev)` (`PrintContext.cpp:188-208`) calls `Frame::setPrinting(true, (W_dev·min, H_dev·min), max/min)`. That leads to `FrameView::forceLayoutForPagination(pageSize, shrinkRatio)` (`FrameView.cpp:2521-2565`):
   1. `L0 = floor(W_dev·min)`. Set the RenderView logical width to `L0` and the page logical height to `H_dev·min`, then lay out.
   2. If `docWidth > L0` (content overflows): `L1 = min(docWidth, L0 × (max/min))`, so at most `W_dev·max`. Page height becomes `L1/(W_dev·min) × H_dev·min`, i.e. the page aspect ratio is preserved. Re-layout at `L1`, then clip overflow beyond `L1` (`addLayoutOverflow(IntRect(...,L1,...))`). RTL documents clip from the right.
2. `computePageRects` (`PrintContext.cpp:66-111`): `pageWidth = docWidth` (now = L), `pageHeight = view->pageLogicalHeight()`. The document is sliced into pages of that height (WebKit's own break-avoidance in `computePageRectsWithPageSizeInternal`).
3. `spoolPage` (`PrintContext.cpp:228-240`): `scale = W_dev / pageRect.width`. Paint the page rect scaled by `scale` into device px.

These layout widths are in **zoomed** px. With full-page zoom `Z`, the layout viewport in **CSS px** is `L/Z`. This step is derived; I believe QtWebKit-534 page zoom scales the RenderView style zoom, but I did not trace it end-to-end.

Resulting mapping (dpi cancels):
```
CSS layout width (no overflow) = W_in × 96 × min / zoom          [W_in = printable width in inches]
physical size of 1 CSS px     = zoom / (96 × min) inch            (no overflow)
                              = zoom / (96 × min × k) inch, k = L1/L0 ∈ (1, max/min]   (overflow case)
```
- **Default** (smart shrinking, zoom 1): 1 CSS px = 1/120 in, i.e. **content printed at 80 %**. A4 with 10mm side margins (190 mm = 7.48 in) gives a CSS viewport ≈ **897.6 → floor 897 px** wide (at dpi 96: W_dev=718.1→718; L0=floor(718×1.25)=897).
- Wide content (fixed 1200px tables etc.) relays out up to `2×` the printable width and shrinks down to **50 %**; anything wider is **clipped**.
- **`--disable-smart-shrinking`**: 1 CSS px = 1/96 in (CSS-correct). Viewport = printable width × 96 / zoom (A4/10mm ≈ 718 px). Overflow is clipped, never shrunk.
- **`--zoom z`** multiplies the physical size by `z` and divides the layout viewport by `z`. It is a true "scale" like Chrome's `page.pdf({scale})`. Common idioms:
  - `--zoom 1.25` with smart shrinking ≈ CSS-correct sizing, as long as nothing overflows.
  - wicked_pdf documents `:zoom => 0.78125` (75/96) to match old Linux vs Windows DPI rendering (`wicked_pdf/README.md:470`, issue #2184). That is pre-0.12.4 behaviour; 0.12.4 changelog #2463 "standardize rendering DPI to 96".
- **"1.33"** folklore — two distinct sources:
  - (a) 96/72 px-vs-pt confusions on old builds (pre-0.12.4 DPI was platform dependent: **UNVERIFIED** detail);
  - (b) the source-verified 4/3 over-reservation of auto-measured header/footer margins (§4.3).

  Neither is a parameter in 0.12.6. The shim should not invent one.
- `--dpi` does **not** change geometry: zoom and device px both scale by dpi/96. It changes rasterisation resolution and `devicePixelRatio`, i.e. CSS resolution media queries (`multipageloader.cc:255`).
- `elementLocation` (used for links, forms, anchors and outline page numbers) applies the same scale (`qwebframe.cpp:294`).

Emulation recipe for recto (`--wk-scale-model`, on by default in the shim):
- `s_min = 1.25` (or 1.0 if disabled), `s_max = 2.0` (or 1.0); `vw0 = floor(Wdev·s_min)/Z` with `Wdev` computed at dpi 96, so `Z = zoom`.
- Lay out at viewport width `vw0` and measure the max inline overflow `D`.
- If `D > vw0` and `s_max > s_min`: relayout at `vw1 = min(D, vw0·s_max/s_min)`.
- Page content height in CSS px = `vw · H/W`.
- Paint scale = `W_css96 / vw`, where `W_css96 = printable width in 1/96-in units`.
- Clip beyond `vw`.

This is "fit-to-width with floor and cap", which recto can implement as a pre-pass over the root inline size. It does not require WebKit's pagination quirks.

### 6.2 Media type, background, fonts
- `--print-media-type` → `@media print` applies. The default is `screen`. **The shim must default to `screen` media**, otherwise most legacy templates render differently.
- Backgrounds print by default; the shim should force `print-color-adjust: exact` semantics unless `--no-background` is given.
- `--minimum-font-size` sets a floor on computed font size in CSS px.
- Header text fonts: `QFont(name,size)`, a point size in device context. Exact rendered size is **UNVERIFIED**.

### 6.3 Margins defaults (summary)
- Left/right default to 10 mm.
- Top/bottom default to 10 mm, **unless** header/footer HTML exists and the margin is unset. Then the margin is the measured height ×4/3 plus spacing (§4.3).
- `--default-header` forces top = 2 cm.

### 6.4 Encoding
`--encoding X` sets only the *default* decoding when the document declares none (`setDefaultTextEncoding`). Stdin and C-API HTML are written to the temp file as UTF-8 (`multipageloader.cc:662`), so piped HTML without `<meta charset>` is decoded with the WebKit default (Latin-1?, **UNVERIFIED**) unless `--encoding utf-8` is passed. This is why pdfkit's README passes `encoding: UTF-8`.

### 6.5 Cookies, headers, POST, auth, proxy (`ResourceObject::load`, `multipageloader.cc:441-512`)
- `--cookie n v` adds extra cookies (`MyCookieJar::useCookie`) to every request URL. They are not URL-decoded by wkhtmltopdf.
- `--custom-header` applies to the main request. With propagation (`repeatCustomHeaders`) it applies to all sub-requests (`createRequest`, l.107-112).
- `--post` sends `application/x-www-form-urlencoded`. Any `--post-file` switches the body to `multipart/form-data` with a random boundary. The Content-Type header is written as `multipart/form-data, boundary=…` (comma, a bug).
- SSL errors are **always ignored** (`sslErrors` → `ignoreSslErrors`, l.433-438). This is a security note.
- HTTP auth: `--username/--password` on `authenticationRequired`.

### 6.6 Grayscale, lowquality, image-dpi/quality, compression (Qt PDF engine)
- **Grayscale:**
  - Pen and brush colours become `qGray(rgb)/255` written as an RGB triple (`qpdf.cpp:1293-1295`; `qprintengine_pdf.cpp:429-431`).
  - Images are written as 8-bit gray and never as JPEG (`qprintengine_pdf.cpp:739-743,897-899`).
  - `qGray` = `(r*11+g*16+b*5)/32` (Qt's definition; **UNVERIFIED** in this tree).
- **lowquality:** sets `QPrinter::ScreenResolution`. The PDF engine picks `resolution = qt_defaultDpi()` from that mode (`qpdf.cpp:1605-1609`), but wkhtmltopdf then calls `setResolution(dpi)`, which overrides it. **Likely a no-op in 0.12.6** (derived, **UNVERIFIED** at runtime).
- **image-dpi** (default 600): an image is downscaled to at most `placed_size_in_inches × imageDPI` px (`qprintengine_pdf.cpp:330-336`).
- **image-quality** (default 94): the engine encodes JPEG(q) and two zlib variants and keeps the smallest. An unscaled original JPEG is passed through as DCT (`qprintengine_pdf.cpp:890-960`).
- PDF `/Creator` is `wkhtmltopdf 0.12.6`, `/Producer` is `Qt 4.8.7`, plus a `/CreationDate` of now. Output is therefore not deterministic.

### 6.7 Local file access (0.12.6 breaking change)
- Default `blockLocalFileAccess = true`. Commit `2a5f25077895fb075812c0f599326f079a59d6cf` "BREAKING CHANGE: block local filesystem access by default" (#4536) flipped `false→true` in `src/lib/loadsettings.cc:143`; it is in the 0.12.6 `CHANGELOG.md`.
- Mechanism (`MyNetworkAccessManager::createRequest`, `multipageloader.cc:87-105`):
  - A request is "local" if the scheme length is ≤1 (Windows drive) or `file`.
  - If blocked, the canonical path and each ancestor are checked against the allow-set. On a miss the URL is rewritten to `about:blank`, with `Warning: Blocked access to file …`.
  - The allow-set = `--allow` paths (canonicalised) + **the input file itself only** (`l.202-205`), **not its directory**. Sibling CSS/images of a local input HTML are therefore blocked by default.
- Hence nearly every 0.12.6 user passes `--enable-local-file-access`. wicked_pdf's README says "must be true when using wkhtmltopdf > 0.12.6" (`wicked_pdf/README.md:47,193`).

### 6.8 Load errors
- `--load-error-handling` covers failure of the main page or object:
  - `abort` (default): error + fail.
  - `skip`: the object is omitted.
  - `ignore`: the object is rendered as loaded.
- Non-media sub-resource failures (network error, or HTTP ≥400 on extensions other than css/js/png/jpg/jpeg/gif) **always** produce an `Error:` and set the HTTP error code, which yields exit code 1/2/3 (`amfinished`, `multipageloader.cc:394-430`). Note that `svg`, `woff` etc. count as "non-media" in 0.12.6; master's f55b76b fixes svg.
- Media failures follow `--load-media-error-handling` (default `ignore` → `Warning:`).

### 6.9 JavaScript timing
- After `loadFinished`, the `--run-script`s run first (main loader).
- If loading failed, or the page called `window.print()` (`printRequested`), or `jsdelay==0`, conversion proceeds immediately.
- Else if `--window-status` is set, `window.status` is polled every 50ms until it equals the value, then the converter waits `jsdelay` more.
- Else it waits `jsdelay` (200ms).
- There is **no timeout** on `--window-status`; it can hang forever.

---

## 7. Outline, TOC, cover

### 7.1 Outline construction (`Outline::replaceWebPage`, `outline.cc` ~l.205-262)
- All `h1,h2,…,h9` elements (h7–h9 too) are collected and sorted by `(page, y, x)` of their printed location.
- Headings with empty `toPlainText()` (newlines → spaces, trimmed) or off-page are skipped.
- **Tree build with a level stack:** pop while `stack.top ≥ level`, then attach as a child. So h1→h3→h2 makes h2 a sibling of h3 under h1, and the depth is tree depth, not tag number.
- Each document gets a root item whose title is the page `<title>` (or the TOC caption).
- PDF bookmarks: children of each root, recursively, stopping when `level+1 > outlineDepth` (`outline.cc:114`; `printOutline` l.344-348). There are no document-level bookmarks.
- Anchors: `__WKANCHOR_<base36>`. TOC back-links are added only if `--enable-toc-back-links`.

### 7.2 Outline XML (`Outline::dump`, `outline.cc` ~l.150-175)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<outline xmlns="http://wkhtmltopdf.org/outline">
  <item title="DocTitle" page="N" link="__WKANCHOR_x" backLink="__WKANCHOR_y"> <item …/> </item>
</outline>
```
`page` = item page + pages of preceding objects + `pageOffset`. Note: this is offset+0-based-first-page style. Exact off-by-one relative to `[page]` is **UNVERIFIED**; it needs a runtime check. Attribute values are XML-escaped.

### 7.3 Default TOC XSL (`src/lib/tocstylesheet.cc`)

The output is XHTML with this CSS:
```
h1 {text-align:center; font-size:20px; font-family:arial}
div {border-bottom: 1px dashed rgb(200,200,200)}      (only if dotted lines)
span {float:right}  li {list-style:none}
ul {font-size:20px; font-family:arial}  ul ul {font-size: <shrink*100>%}
ul {padding-left:0em}  ul ul {padding-left:<indentation>}
a {text-decoration:none; color:black}
```
The body is `<h1>caption</h1><ul>` with templates for `outline:item/outline:item`; document roots are skipped and their children listed. Each item is rendered as `<li><div><a href=@link name=@backLink>title</a><span>page</span></div><ul>…</ul></li>`.

How the TOC is processed:
- The TOC is regenerated until stable (page counts/outline unchanged).
- The TOC page itself is rendered like any page object, with headers/footers and smart shrinking.
- A custom XSL receives the same XML. TOC options (`--toc-*`, `--disable-*`) only affect the default XSL (manual text, `pdfdocparts.cc` `outputTableOfContentDoc`).

### 7.4 Cover
A normal page object that has no header/footer and is excluded from the outline, but **counted** in page numbers (§1.6). Wrappers place `cover` and `toc` in different orders:
- python-pdfkit emits `toc` then `cover` unless `cover_first=True` (`pdfkit.py:93-105`).
- go-wkhtmltopdf always emits `cover` then `toc` then `page …` (`wkhtmltopdf.go:168-193`).

---

## 8. Wrapper evidence: which options are actually used

Option names each wrapper exposes or uses:

- **KnpLabs/snappy v1.7.3** (`src/Knp/Snappy/Pdf.php` `configure()`). It exposes *every* 0.12.x flag as a key, plus legacy keys (`ignore-load-errors`, `redirect-delay`, `toc-depth`, `toc-font-name`, `toc-l1-font-size`, `toc-header-font-name`, `toc-header-font-size`, `output-format`).
  - It serialises `--key 'value'` with separate tokens. `true` becomes a bare `--key`, except `toc`. Arrays repeat the flag. Associative arrays emit `--key 'k' 'v'`. `cover`/`toc` are emitted **in the option stream, without `--`** (`AbstractGenerator.php:531-576`). A global option ordered after `cover`/`toc` in the options array therefore lands in the wrong section — a wrapper bug that real wkhtmltopdf rejects.
  - `header-html`, `footer-html` and `cover` values that are neither a file nor an http(s) URL are written to temp `.html` files. An http(s) `xsl-style-sheet` is downloaded to a temp file (`Pdf.php:58-79,250-256`).
  - README examples: `disable-javascript`, `no-background`, `allow`, `cookie`, `post`, `cover`, `toc`, `cache-dir`, `copies`, `xsl-style-sheet` (`snappy/README.md:95-104,112,159-160`).
- **barryvdh/laravel-snappy.**
  - Dedicated methods: `setPaper` → `page-size` (+`orientation`), `setOrientation` (`src/PdfWrapper.php:73-90`).
  - Generic `setOption(s)`. Config default `options => []` (`config/snappy.php:36-41`).
  - README example: `setPaper('a4')->setOrientation('landscape')->setOption('margin-bottom', 0)` (`readme.md:160`).
- **JazzCore/python-pdfkit.**
  - Always appends `--quiet` unless `verbose=True` (`pdfkit.py:86-87`).
  - String/file-object input → `-` (stdin). No output path → `-` (stdout).
  - Options accepted as dict, with or without `--`; 2-tuples become two argv entries.
  - Separate `toc` dict and `cover` arg. Reads `<meta name="pdfkit-*">` options from HTML (`pdfkit.py:277-300`). The `css` param is prepended into the HTML.
  - README options: `page-size`, `margin-top/right/bottom/left` (`0.75in`), `encoding: UTF-8`, `custom-header`, `cookie`, `no-outline`, toc `xsl-style-sheet`, meta `page-size`/`orientation`; README recommends `--user-style-sheet` (`README.rst:86-100,116,120-150`).
- **mileszs/wicked_pdf 2.8.1** (`lib/wicked_pdf/option_parser.rb`).
  - Global: `orientation dpi page_size page_width page_height title log_level lowquality grayscale no_pdf_compression quiet image_dpi image_quality margin{top,bottom,left,right}`.
  - Others: `proxy username password encoding user_style_sheet viewport_size window_status allow cookie post redirect_delay zoom page_offset javascript_delay book default_header disable_javascript enable_plugins disable_internal_links disable_external_links keep_relative_links print_media_type disable_local_file_access enable_local_file_access disable_smart_shrinking use_xserver no_background images no_images no_stop_slow_scripts`.
  - `outline{outline,outline_depth}`; header/footer `{center,font_name,left,right,font_size,spacing,line,html.url|content}`. Content is written to a temp file and passed as a `file:///` URL.
  - `cover` (HTML content → temp file); `toc{…legacy…, header_text, xsl_style_sheet, text_size_shrink, level_indentation, disable_dotted_lines, disable_toc_links}`; `basic_auth`; `extra` (raw argv).
  - Input is always `file:///<tmp>` (`wicked_pdf.rb:55-81`), so `[webpage]` is a temp path for wicked users.
  - README sample: `print_media_type: true` (l.189,279), `enable_local_file_access` (l.47,193), `disable_smart_shrinking: true` (l.196), `zoom` platform note (l.470).
- **devongovett/node-wkhtmltopdf 0.4.0.**
  - camelCase → `--dasherized`; a 1-char key → `-k` short switch (`index.js:64-66`).
  - Always `--quiet` unless `debug` (l.54-56).
  - Moves TOC-specific keys (`disableDottedLines tocHeaderText tocLevelIndentation disableTocLinks tocTextSizeShrink xslStyleSheet`) after `toc` (l.38-52).
  - HTML string → stdin `-`; no output → stdout `-` (l.104,109).
  - README example: `pageSize`, `allow`, `customHeader`.
- **rdvojmoc/DinkToPdf** (C API).
  - Settings used: `collate colorMode copies documentTitle dpi dumpOutline footer.* header.* imageDPI imageQuality includeInOutline load.{blockLocalFileAccess,cookieJar,cookies,customHeaders,debugJavascript,jsdelay,loadErrorHandling,password,proxy,repeatCustomHeaders,stopSlowScript(sic),username,zoomFactor} margin.* orientation out outline outlineDepth page pageOffset pagesCount produceForms size.{width,height} useCompression useExternalLinks useLocalLinks viewportSize web.*`.
  - README: `ColorMode, Orientation, PaperSize, Margins{Top=10}, PagesCount, HtmlContent, WebSettings.DefaultEncoding="utf-8", HeaderSettings{FontSize=9, Right="Page [page] of [toPage]", Line=true, Spacing=2.812}` (`README.md:38-75`).
- **SebastiaanKlippert/go-wkhtmltopdf.**
  - Typed options covering every 0.12.6 flag (`options.go`); all names were extracted with `grep 'option: "…"'`. The extracted list matches §2 exactly.
  - Margins are uint (mm), `*Unit` variants are strings, floats use `%.3f` (`options.go:267-275`).
  - Emits explicit `page` keywords; `-` for stdin and stdout.
  - README: `PageSize`, `MarginBottom(40)`, `Orientation`, `Dpi`, `NoCollate`, `Grayscale`, page `FooterRight("[page]")`, `FooterFontSize`, `Zoom` (README l.25-90, **partially UNVERIFIED**: only l.30-31 and l.84 were grepped).

**"Commonly used"** (★ in the matrix) is defined as appearing in README examples, dedicated API methods or sample configs of ≥2 wrappers, or the docs flagging it as required. This is a heuristic from the wrappers above, not usage telemetry.

The ★ list: `page-size, orientation, margin-*, encoding, quiet (implicit via pdfkit/node), header-html, footer-html, header-/footer-left/center/right, header-/footer-font-size, header-/footer-spacing, header-/footer-line, cover, toc, xsl-style-sheet, print-media-type, enable-local-file-access, allow, disable-smart-shrinking, zoom, javascript-delay, window-status, no-outline/outline, title, dpi, grayscale, lowquality, image-quality, custom-header, cookie, user-style-sheet, disable-javascript, no-background, page-offset, copies`. Also `-` stdin/stdout (pdfkit, node, go) and `--version` (wicked).

---

## 9. COMPATIBILITY MATRIX — `recto wkhtmltopdf …` v1

Support levels:
- **F** = Full (same observable semantics; may be a documented no-op where wkhtmltopdf's effect is nil or geometry-neutral).
- **A** = Approximate (same intent, layout differs in details).
- **W** = Accepted, ignored, warning on stderr (`Warning: …`, exit 0).
- **E** = Rejected with error (exit 1, `Error: …`).

Global policy proposals:
- `--strict` turns every **W** into **E**.
- `--lenient` keeps warnings but also accepts 0.9-era legacy flags.
- Warnings are suppressed by `-q`/`--log-level none|error`.
- Warning text must never contain the substring `Error` (python-pdfkit heuristic).

| Flag(s) | ★ | Category | wk semantics (short) | recto mapping | v1 | Why |
|---|---|---|---|---|---|---|
| `-h/--help`, `-H/--extended-help`, `--manpage`, `--htmldoc`, `--readme`, `--license` | | meta | docs | Print shim usage listing support levels | F | trivial |
| `-V/--version` | ★ | meta | `wkhtmltopdf 0.12.6 (with patched qt)` | Print `wkhtmltopdf 0.12.6 (recto <ver> compat shim)` | F | wicked_pdf regex needs `wkhtmltopdf X.Y.Z`; snappy/pdfkit don't parse |
| `-q/--quiet`, `--log-level` | ★ | output | stderr verbosity | Same levels. At `info`, end with a `Done` line | F | pdfkit `Done` heuristic |
| `-O/--orientation` | ★ | page | Portrait/Landscape | Swap page box; overrides `@page size` | F | |
| `-s/--page-size` | ★ | page | Named sizes §5 | Same table incl. Ledger landscape quirk; round media box to integer pt like Qt | F | Byte-level page sizes matter for pixel diff tests |
| `--page-width/--page-height` | | page | Both required; height's unit used for both | Correct per-value units. Warn if only one is given or units differ | F | Faithfully copying the bug is not useful |
| `-T/-B/-L/-R --margin-*` | ★ | page | Defaults 10mm; unit grammar §5; same-unit rule | Page margins overriding `@page margin`; same unit grammar; **accept mixed units** (superset) | F | Wrappers never rely on the error |
| `--copies`, `--collate/--no-collate` | ★(copies: snappy README) | output | Repeat page sequence | Repeat pages in output | F | Cheap |
| `-g/--grayscale` | ★ | color | qGray on vectors; gray images | Post-paint colour conversion to DeviceGray with the same luma formula | A | Rasterised/SVG/gradient conversions differ |
| `-l/--lowquality` | ★ | quality | Effectively no-op (§6.6) | No-op | F | Matches wk |
| `--title` | ★ | metadata | PDF Title; default first `<title>` | `/Title` + XMP dc:title | F | |
| `--read-args-from-stdin` | | batch | One invocation per stdin line, shell-like quoting (`wkhtmltopdf.cc` `parseString`) | Same tokenizer, run in-process (recto batch) | F | Fits recto's batch mode |
| `-d/--dpi` | ★ | quality | Geometry-neutral; raster res + DPR | Set `resolution` media-feature value; no geometry change | F | Source shows dpi cancels |
| `--image-dpi` | | quality | Downsample >N dpi | Optional downsampling | A | Recto may pass originals through; output smaller or larger |
| `--image-quality` | ★ | quality | JPEG q for re-encoded images | Use only when recto re-encodes; JPEG passthrough otherwise | A | Recto shouldn't re-encode needlessly |
| `--no-pdf-compression` | | output | No Flate | Disable stream compression | F | |
| `--use-xserver` | | env | X11 | ignore | W | Meaningless |
| `--cookie-jar` | | network | Read/write cookie file | Accept; used only when network is enabled; else warn | W | Network off by default |
| `--outline/--no-outline` | ★ | outline | Default **on** | Bookmarks on by default in shim | F | |
| `--outline-depth` | | outline | Default 4; tree depth | Same | F | |
| `--dump-outline` | | outline | XML §7.2 | Write the same XML schema | F | Small |
| `--dump-default-toc-xsl` | | toc | Print XSL | Print the verbatim default XSL | F | Static text (LGPL-licensed text: quote or regenerate) |
| `--default-header` | | header | Macro (§2.4) | Expand the macro | F | |
| `--viewport-size` | | layout | QWebPage viewport | Ignore; printing width is forced anyway (§6.1) | W | Effect limited to vh/media queries |
| `--enable/--disable-plugins` | | web | NPAPI | ignore silently | F (no-op) | Plugins never work headless |
| `--minimum-font-size` | | text | Font floor | Clamp computed font-size | F | |
| `--user-style-sheet` | ★ | css | User stylesheet | User-origin sheet (cascade origin "user") | F | |
| `--images/--no-images` | | web | AutoLoadImages | Skip image decode, keep layout box | F | |
| `-n/--disable-javascript`, `--enable-javascript` | ★ | js | JS toggle | No-op (recto never runs JS). With JS "enabled" (default) and `<script>` present, emit one W: "scripts not executed" | F / W | No JS by design |
| `--javascript-delay` | ★ | js | Wait ms | Ignore (no async loading) | F (no-op) | Nothing to wait for |
| `--window-status` | ★ | js | Wait for window.status | Ignore, warn: content set by JS will be missing | W | Signals that JS fills the page |
| `--run-script` | | js | Eval JS | warn (strict: E) | W | Can't run |
| `--debug-javascript`, `--(no-)stop-slow-scripts` | | js | – | ignore silently | F (no-op) | |
| `--encoding` | ★ | input | Fallback charset | Same: fallback only, per WHATWG sniffing order | F | |
| `--background/--no-background` | ★ | paint | Default print backgrounds | Shim default `print-color-adjust: exact`; `--no-background` suppresses backgrounds | F | |
| `--include/--exclude-from-outline` | | outline | Per-object | Per-document flag | F | |
| `--disable/--enable-smart-shrinking` | ★ | scale | §6.1 | **Shim default: emulate the 1.25/2.0 shrink model**; disable → scale 1, clip overflow | A (target F for the no-overflow case) | Default 0.8 scale must match or every page reflows |
| `--zoom` | ★ | scale | Page zoom | `scale` factor (viewport ÷ z, paint × z) | F | Same as Chrome scale |
| `--print-media-type/--no-print-media-type` | ★ | css | Default **screen** | Shim default media=screen; flag → print | F | Critical default |
| `--enable-forms/--disable-forms` | | forms | AcroForm fields | v1: render static controls; warn on enable | W | AcroForm not in v1 scope |
| `--checkbox-svg` & 3 siblings | | forms | Custom control SVG | Render those SVGs for `input[type=checkbox/radio]` | A | Rare; easy if SVG support exists |
| `--disable/--enable-internal-links` | | links | Internal links | Toggle GoTo annotations | F | |
| `--disable/--enable-external-links` | | links | URI links | Toggle URI annotations | F | |
| `--resolve-relative-links/--keep-relative-links` | | links | Absolutise | Same | F | |
| `--enable/--disable-toc-back-links` | | toc | Heading → TOC link | Link annotation on headings | F | |
| `-p/--proxy`, `--proxy-hostname-lookup`, `--bypass-proxy-for` | | network | Proxy | Network disabled by default → W; with network opt-in honour http(s) proxy; socks5 → W | W (A with network) | Secure by default |
| `--username/--password` | | network | HTTP auth | As above | W | |
| `--ssl-key-path/--ssl-key-password/--ssl-crt-path` | | network | Client cert | Reject when network is enabled (not v1) | W→E with network | Keep TLS surface minimal |
| `--custom-header`, `--custom-header-propagation`, `--no-custom-header-propagation` | ★ | network | Request headers | Honour only with network enabled, else W. Note wk bug: both propagation flags enable propagation | W (A with network) | pdfkit README uses these out of habit |
| `--cookie` | ★ | network | Extra cookies | As above | W | |
| `--post`, `--post-file` | | network | POST body | E when network is enabled (not supported); W otherwise | W | Rare |
| `--load-error-handling` | | errors | abort/skip/ignore for objects | Same for unreadable input documents | F | |
| `--load-media-error-handling` | | errors | Default ignore for css/js/img | Recto missing-resource policy; default ignore + `Warning:` | F | Extend the classification to fonts/svg (wk counts them as non-media → hard error) — documented deviation |
| `--enable-local-file-access` | ★ | security | Allow any file | Allow reads under `/` (or the effective FS root) with an info log | F | Most common 0.12.6 flag; refusing it breaks users |
| `--disable-local-file-access` | | security | Block (default) | Default recto policy: input dir + `--allow` | A | Recto allows the input's directory (wk allows only the file). More permissive, deliberately |
| `--allow` | ★ | security | Allow path & descendants | Add to the read allow-list (canonicalised) | F | |
| `--cache-dir` | ★(snappy README) | network | Disk cache | ignore | W | |
| `--page-offset` | | numbering | `[page]=n+off` | `counter-reset: page off` semantics applied to all page-number outputs and the TOC | F | |
| `--header-left/center/right`, `--footer-…` | ★ | header | Text + `[vars]`, Arial 12, drawn just outside the content box | Generate margin boxes `@top-left/center/right` (bottom: `@bottom-*`) with `vertical-align:bottom` (top) / `top` (bottom), `padding` = spacing, content built from `counter(page)`, `counter(pages)`, `string(section)`, literals | A | Positioning differs (wk uses font-ascent math, not CSS boxes); text identical |
| `--header-font-name/size`, `--footer-…` | ★ | header | QFont | `font-family`/`font-size: Npt` in margin boxes | A | Font availability (Arial → metric-compatible fallback) |
| `--header-line/--no-header-line`, `--footer-…` | ★ | header | Full-content-width rule at spacing | A rule across the full content width at the boundary | A | CSS margin boxes don't tile exactly; needs a recto-internal "page decoration" primitive |
| `--header-spacing/--footer-spacing` | ★ | header | mm gap | padding between margin box and content | F | |
| `--header-html/--footer-html` | ★ | header | Per-page HTML + JS `subst()` via query string; auto margin = 4/3 × height | Load as a recto running-element template; emulate the JS contract (§10); auto margin when unset (replicate the 4/3 factor under `--wk-quirks`, default on) | A | No JS; covers the canonical pattern; custom JS logic can't work |
| `--replace` | | header | Custom vars | Same substitution (text headers + HTML class/query emulation) | F | |
| `cover <url>` | ★ | structure | Doc without header/footer, no outline, counted | Separate document in a multi-doc job with `@page { @top-*{content:none} … }` | F | |
| `page <url>` / multiple inputs | ★ | structure | Concatenated docs, continuous numbering, per-object options | Multi-document job; per-doc settings | F | Needed for Snappy/go arrays |
| `toc` | ★ | toc | XSLT-generated TOC from h1–h9 outline, iterated to fixpoint | Built-in TOC generator producing the same HTML structure as the default XSL, with `target-counter()` page numbers | F | Recto has target-counter |
| `--xsl-style-sheet` | ★ | toc | Custom XSLT 2.0 | No XSLT engine in v1 → **E** with a clear message (lenient: W + default TOC) | E | Silent fallback would produce a wrong TOC |
| `--toc-header-text`, `--disable-toc-links`, `--disable-dotted-lines`, `--toc-text-size-shrink`, `--toc-level-indentation` | | toc | Default-XSL params | Same CSS knobs in the built-in TOC | F | |
| `-` (stdin input), `-` (stdout output) | ★ | io | temp file / stdout | Stream directly; base URL for stdin = CWD (deviation; wk used a temp dir) | F | pdfkit/node/go rely on it |
| Legacy flags (§2.7: `--book`, `--redirect-delay`, `--toc-depth`, `--toc-l*`, `--toc-*-font-*`, `--ignore-load-errors`, `--output-format`) | | legacy | Unknown → error in 0.12.6 | E by default (parity); `--lenient` → W | E | wicked_pdf users on 0.12.6 already get errors |
| `--opt=value` syntax | | grammar | Unsupported in wk | Accept as an extension | F (superset) | Harmless |

Grammar parity: the shim must reproduce section/placement rules, apart from the leniencies noted:
- Global options after the first object → E "specified in incorrect location".
- TOC options outside `toc` → E.
- The last positional argument is the output.
- Combined short switches.

---

## 10. Emulating `--header-html` without JavaScript (design sketch)

wkhtmltopdf contract: the header document receives `?page=…&frompage=…&topage=…&webpage=…&section=…&subsection=…&subsubsection=…&date=…&isodate=…&time=…&title=…&doctitle=…&sitepage=…&sitepages=…[&replace-keys]`, and **its own JS** puts the values into the DOM.

Recto (no JS) approach. Status: **Approximate**.
1. Parse the header HTML once and treat `<body>` as a running element placed in the top margin area. Width = content width. Bottom edge at `content-top − spacing`, i.e. not a CSS margin box: a recto "page decoration" region.
2. **Variable binding without JS:** for each known variable name `v`, every element with `class~="v"` **or** `id="v"` gets generated content:
   - `page` → `counter(page)`
   - `topage` → `counter(pages)`
   - `frompage` → literal
   - `section`/`subsection`/`subsubsection` → `string(wk-section-N, first)`
   - `sitepage`/`sitepages` → per-document counters
   - `webpage`/`title`/`doctitle`/`date`/`isodate`/`time` → literals

   The class rule covers the manual's canonical `subst()`, which most templates copy (wicked_pdf's and Snappy's docs point to it). The id rule is a cheap common variant.

   Also substitute literal `[page]`-style tokens in text nodes. wkhtmltopdf does **not** do that for HTML headers, but it makes templates that were designed for the text options work. Make it a quirk flag; default off for parity? Decide in implementation; low risk either way.
3. Emit `Warning: header HTML contains <script>; only the standard class-based substitution is emulated` when scripts other than the canonical pattern are present.
4. Auto margin when `--margin-top` is unset: `measured_height_mm × 4/3 + spacing` (§4.3 quirk, measured at the shim scale 0.8). Recompute the height per document (wk measures once per object).
5. Make `[date]/[time]` deterministic: honour `SOURCE_DATE_EPOCH` and use ISO-like formats rather than system locale (deviation, documented).

---

## Findings that affect recto's design

1. **The shim's defaults must be wkhtmltopdf's, not recto's:**
   - media = **screen**;
   - backgrounds **on**;
   - **smart-shrink scale model on** (content at 80 %; wide content shrunk to ≥50 % then clipped);
   - outline **on** (depth 4);
   - margins 10 mm;
   - A4 portrait;
   - page numbers from 1 + offset 0;
   - local file reads allowed for the input (recto's input-dir policy).

   Without these, every legacy document re-paginates.
2. Recto needs a **page "scale/fit-width" layout primitive**: layout viewport = printable width × 96 × s / zoom, plus an optional second pass that widens to the overflow width (cap ×1.6 of the first width) and scales down, clipping beyond. This doubles as Puppeteer's `scale` option (finding shared with the Puppeteer shim).
3. **CLI page geometry must override author `@page size/margin`** in shim mode, since wkhtmltopdf ignores CSS `@page` entirely (the QWebPrinter path never reads it). Recto's cascade needs a "UA-override page context" layer above the author origin.
4. Recto needs **multi-document jobs** with continuous page numbering, per-document settings (header/footer, outline inclusion, numbering inclusion `pagesCount`), and covers. TOC generation from headings must cover h1–h9, follow the level-stack tree semantics, and iterate to a fixpoint or use target-counter.
5. Recto needs a **"page decoration" region API** (header/footer anchored to the content box with spacing, spanning content width, with a full-width rule). This is distinct from the 16 CSS margin boxes; wkhtmltopdf geometry cannot be expressed exactly with margin boxes.
6. Recto needs **running-element templates with variable binding** (class/id-based) to emulate JS `subst()`. It also needs page-scoped strings for section/subsection/subsubsection with "first on page, else carried" semantics (`string(x, first)` ≈ wk, apart from the carry-first quirk).
7. Variables `[date]`/`[time]`/`/CreationDate` are time-dependent. To keep recto deterministic, honour `SOURCE_DATE_EPOCH`, or a fixed epoch unless `--wk-quirks=live-date`.
8. **Unit parser parity**: unitless = mm; `cm m mm in inch pt point px pixel pc pica didot cicero`; no sign/whitespace. `px` = 1/96 in (dpi default). Named page sizes need Qt's exact table (Ledger is landscape-shaped; ISO B series) and integer-pt rounding.
9. **Error/exit-code/stderr parity** is load-bearing for wrappers:
   - exit 0/1/2(404)/3(401);
   - `Warning:` / `Error:` prefixes;
   - a final `Done` at info level;
   - stdin/stdout via `-`;
   - `--version` containing `wkhtmltopdf 0.12.6`.
10. **Security posture**: wkhtmltopdf ignores all TLS errors, allows network by default, and runs JS. Recto shim keeps network **off** by default. Network flags (cookie, custom-header, proxy, auth, post) are warn-ignored unless network is explicitly enabled. `--enable-local-file-access` must be honoured, because it is the most-used 0.12.6 flag (wicked README: "must be true").
11. `--xsl-style-sheet` can't be supported without an XSLT 2.0 engine. Reject it with a clear error in v1. A tiny XSLT-1-subset interpreter is not worth it unless telemetry shows demand.
12. A wkhtmltox-compatible C ABI (string settings `size.pageSize`, `margin.top`, `web.printMediaType`, …) would let DinkToPdf/NReco-style .NET users switch. The settings table in §3 is the complete contract. Candidate for post-v1.
13. Grayscale should be a post-paint colour-space conversion (luma `qGray`) applied to vectors and images. `--lowquality` and `--dpi` are no-ops for geometry.
14. Forms (`--enable-forms`) → AcroForm is a post-v1 feature. Static rendering of the controls is fine for v1.

## Recommendation

- Ship `recto wkhtmltopdf` in v1 with the matrix in §9: Full for the page geometry, structure, links, outline, TOC (default XSL look), cover, CLI/IO/exit-code surface; Approximate for text and HTML headers/footers and grayscale; warn-ignore for JS/network/plugins/forms; error for XSLT and legacy 0.9 flags (lenient mode available).
- Make the **scale model** (finding 2) and the **UA-override page context** (finding 3) first-class engine features, not shim hacks, since the Puppeteer shim needs the same mechanisms.
- Build a golden-test corpus from the wrapper READMEs' flag sets (pdfkit, Snappy, wicked_pdf, go) and compare page count, page boxes and text positions against real wkhtmltopdf 0.12.6 output, generated once and stored, since the binary is abandoned.

## Open questions / UNVERIFIED items

1. Repo archive date 2023-01-02. From secondary web sources only; the GitHub API was not reachable here. The last commit (2022-06-29) is verified.
2. Whether QtWebKit-534 page zoom scales the RenderView layout width such that the CSS viewport is `L/zoom`. Derived from the code structure, not traced or run. Verify with a runtime test (render a 100%-width ruler at `--zoom 2`).
3. The exact 0.8 scale and ~897px A4 viewport. Derived arithmetic; confirm with a measurement page in real 0.12.6 (`document.documentElement.clientWidth` printed into the page).
4. 4/3 over-reservation of auto-measured header margins, and measurement with default (not user-specified) shrink and media settings. Derived from `calculateHeaderHeight`; needs runtime confirmation.
5. Custom `--page-width/height` rounding to integer points, and orientation swap behaviour with custom sizes (Qt 4.8 `QPrinter` internals not read).
6. `--lowquality` being a no-op. The resolution override is derived; other effects of PrinterMode in Qt 4.8 were not checked.
7. Default text decoding for stdin HTML without a charset (WebKit default `ISO-8859-1`?).
8. Outline XML `page` numbering vs `[page]` off-by-one.
9. `qGray` formula in this Qt tree (Qt 4.8 documents `(r*11+g*16+b*5)/32`; not re-read here).
10. Table header (`thead`) repetition across pages in patched WebKit. Implied by changelog 0.12.5 #1524/#1914, but the WebKit render code was not inspected. Recto should repeat `thead`/`tfoot` by default in shim mode if confirmed.
11. Header text font size units (QFont point size on a 96-dpi printer device) and exact baseline position. Needs a runtime measurement.
12. go-wkhtmltopdf README lines beyond those grepped (only l.30-31 and l.84 were checked).
