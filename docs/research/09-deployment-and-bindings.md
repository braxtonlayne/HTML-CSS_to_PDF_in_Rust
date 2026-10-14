# 09 — Deployment and language bindings: how ecosystems call HTML→PDF today, and how recto should plug in

- Date: 2026-10-14
- Topic slug: `bindings`
- Scope: (1) the most-used HTML→PDF wrapper libraries in Node, Python, Go, Ruby, PHP, .NET and Java, plus server-style services: their public API and how they invoke the engine; (2) the Rust binding toolchains (napi-rs, PyO3 + maturin, wasm-bindgen + wasm-pack, cbindgen C ABI) and the binary-distribution toolchain (cargo-dist, cargo-binstall, musl static builds, `FROM scratch`, signing, SBOM); (3) a design recommendation that makes switching to recto a **one-line** change in each language.
- Clones live under `/tmp/claude-0/src/bindings/<org>_<repo>`. All paths below are relative to that clone root unless they start with `docs/`.
- Version policy: for each repo, "Version" is the version in the manifest at the inspected HEAD, and "Latest tag" is the newest tag from `git ls-remote --tags`. Rust crate versions were checked against `index.crates.io` on 2026-10-14.

## Sources inspected

### Wrapper libraries and services

| Name | Version (manifest @ HEAD) / latest tag | Commit inspected | License | Last commit | Maintenance assessment |
|---|---|---|---|---|---|
| puppeteer/puppeteer | `puppeteer-core` 25.13.0 | `29521992a24f` | Apache-2.0 | 2026-10-14 | Very active (Google). |
| marcbachmann/node-html-pdf (`html-pdf`) | 3.0.1 / v3.0.1 | `7e8c02af9363` | MIT | 2021-05-07 | Dead. PhantomJS-based. |
| devongovett/node-wkhtmltopdf | 0.4.0 / (no tags) | `51745d803a65` | none declared in package.json | 2021-05-14 | Dead. |
| mrafiqk/html-pdf-node | 1.0.7 / (no tags) | `3d89248e7faa` | ISC | 2021-12-14 | Dead, buggy (see §1.4). |
| JazzCore/python-pdfkit | 1.0.0 / 1.0.0 | `fb86d338a370` | MIT | 2023-09-14 | Self-declared deprecated (`README.rst:15-18`). |
| Kozea/WeasyPrint | 70.0 / v70.0 | `3c5f1ceb0cf1` | BSD-3 | 2026-10-14 | Very active. |
| fdemmer/django-weasyprint | 2.6.0 / v2.6.0 | `c88c5ef1d479` | Apache-2.0 | 2026-10-01 | Active. |
| xhtml2pdf/xhtml2pdf | 0.2.23 / v0.2.23 | `f28aec3ac0db` | Apache-2.0 | 2026-10-07 | Active (pure Python + ReportLab). |
| microsoft/playwright-python | v1.64.0 (tag) | `27e324a9a1cc` | Apache-2.0 | 2026-10-13 | Very active. |
| pyppeteer/pyppeteer | 2.0.0 | `7dc91ee5173d` | MIT | 2024-02-21 | Self-declared unmaintained (README banner). |
| SebastiaanKlippert/go-wkhtmltopdf | v1.9.3 | `1eb8cee79c70` | MIT | 2025-10-30 | Maintenance only. |
| chromedp/chromedp | v0.21.0 (go.mod: `cdproto v0.157.8`, `go 1.25`) | `7862adfd3424` | MIT | 2026-10-11 | Active. |
| gotenberg/gotenberg | v8.37.0 | `db150b773322` | MIT | 2026-10-13 | Very active. |
| starwalkn/gotenberg-go-client (cloned via `dcaraxes/gotenberg-go-client` redirect; module `github.com/starwalkn/gotenberg-go-client/v8`) | v8.12.0 | `350c3b2f49d9` | MIT | 2025-11-18 | Active. |
| thecodingmachine/gotenberg-go-client | v7.2.0 | `968713b31a03` | MIT | 2021-08-22 | Dead (v7 API). |
| mileszs/wicked_pdf | `VERSION = '2.8.1'` (latest tag 2.7.0) | `bce498de547c` | MIT | 2025-07-24 | Maintenance only. |
| pdfkit/pdfkit (Ruby) | 0.8.7.3 | `762b366e9420` | MIT | 2023-05-30 | Dormant. |
| Studiosity/grover | 1.2.10 | `8778650db063` | MIT | 2026-04-03 | Active. |
| rubycdp/ferrum | 0.18.0 | `ee96bac9c5b6` | MIT | 2026-10-13 | Active. |
| KnpLabs/snappy | v1.7.3 | `f749a7d2e0f1` | MIT | 2026-07-29 | Maintenance only. |
| barryvdh/laravel-snappy | v1.0.5 | `f38fff4c764b` | MIT | 2026-08-21 | Maintenance only. |
| spatie/browsershot | 5.4.0 | `519bbcd812f4` | MIT | 2026-07-09 | Active. |
| spatie/laravel-pdf | 2.14.0 | `b01799f` | MIT | 2026-10-05 | Active. Driver-based (see §5.4). |
| dompdf/dompdf | v3.1.6 | `c41f2f4871f1` | LGPL-2.1 | 2026-10-02 | Active (pure PHP). |
| mpdf/mpdf | `VERSION = '8.3.2'` (tag v8.3.1) | `a981bb7b9e31` | GPL-2.0 | 2026-10-13 | Active (pure PHP). |
| rdvojmoc/DinkToPdf | v1.0.8 | `b0546d21641e` | MIT | 2018-04-19 | Dead, but still widely deployed. P/Invoke into libwkhtmltox. |
| webgio/Rotativa.AspNetCore | 1.5.0 | `541ea978e123` | MIT | 2026-10-08 | Maintenance only. |
| fpanaccia/Wkhtmltopdf.NetCore | 5.0.2-preview | `9186b7c3a321` | Unlicense | 2021-02-22 | Dead. |
| hardkoded/puppeteer-sharp | 25.13.1 | `be0f47db0c12` | MIT | 2026-10-11 | Very active. |
| QuestPDF/QuestPDF | 2026.9.1 | `12d78dd4beac` | Dual: Community (revenue < USD 1M) / commercial | 2026-09-30 | Very active. Not HTML. |
| danfickle/openhtmltopdf | 1.0.11-SNAPSHOT (last release 1.0.10, 2021-09-13) | `780ba564839f` | LGPL-2.1+ | 2022-04-01 | Abandoned upstream. |
| openhtmltopdf/openhtmltopdf (community continuation) | `${revision}` = 1.1.5-SNAPSHOT; latest tag `openhtmltopdf-parent-1.1.4` | `7853e93` | LGPL-2.1+ | 2026-10-09 | Active. Maven namespace `io.github.openhtmltopdf`. |
| flyingsaucerproject/flyingsaucer | 10.7.0-SNAPSHOT / v10.6.0 (OpenPDF 3.0.5, Java 21) | `a5e280a0e06e` | LGPL-2.1+ | 2026-10-11 | Active. |
| jhonnymertz/java-wkhtmltopdf-wrapper | 1.3.1-RELEASE | `44f8d9e3db4b` | MIT | 2026-10-06 | Maintenance only. |
| browserless/browserless | 2.57.0 | `1e142fa8adce` | SSPL-1.0 or commercial | 2026-10-13 | Very active. |
| arachnys/athenapdf | v2.16.0 | `bfd04f16b01b` | MIT | 2023-03-06 | Self-declared deprecated (README line 1). |
| BurntSushi/ripgrep (allocator precedent only) | HEAD | `3fce3b5` | MIT/Unlicense | 2026-08-04 | Active. |

### Rust binding and distribution toolchains

| Name | Version (crates.io index, 2026-10-14) | Commit inspected | License | Last commit | Notes |
|---|---|---|---|---|---|
| napi-rs/napi-rs | `napi` 3.14.2, `napi-derive` 3.6.12, `napi-build` 2.6.0; `@napi-rs/cli` 3.10.8 (`cli/package.json`) | `2cceeb0ec5d6` | MIT | 2026-10-14 | Very active. |
| PyO3/pyo3 | index: 0.29.3. Git: tag `v0.30.0`, CHANGELOG `## [0.30.0] - 2026-10-13`, not yet visible in the index | `240dae51bf2b` | MIT/Apache-2.0 | 2026-10-14 | Very active. |
| PyO3/maturin | 1.15.0 | `6fe12cbc0cf6` | MIT/Apache-2.0 | 2026-10-08 | Very active. |
| wasm-bindgen (repo moved to `github.com/wasm-bindgen/wasm-bindgen` per `Cargo.toml:14`) | 0.2.129 | `f57e205b2bc0` | MIT/Apache-2.0 | 2026-10-12 | Active under the new org. |
| wasm-pack (moved to `wasm-bindgen/wasm-pack`) | 0.15.0 | `e33b17ae4168` | MIT/Apache-2.0 | 2026-08-12 | Active. |
| mozilla/cbindgen | 0.29.4 | `2b757a22bab7` | MPL-2.0 | 2026-08-22 | Active. |
| axodotdev/cargo-dist | index: 0.32.0. Git: `Cargo.toml` 0.33.0 (CHANGELOG "Version 0.33.0 (2026-09-10)"), tag `v1.0.0-rc.1` exists | `d1055f48071e` | MIT/Apache-2.0 | 2026-10-04 | Active. |
| cargo-bins/cargo-binstall | 1.25.3 | `44dada98ea7c` | GPL-3.0-only (a tool, not linked) | 2026-10-13 | Very active. |
| CycloneDX/cyclonedx-rust-cargo | `cargo-cyclonedx` 0.5.9 | `9037ba4cfd6f` | Apache-2.0 | 2026-10-12 | Active. |
| rust-secure-code/cargo-auditable | 0.7.7 | `cf81da8bf129` | MIT/Apache-2.0 | 2026-10-14 | Active. |
| Index-only lookups (not cloned) | `schemars` 1.2.3, `mimalloc` 0.1.52, `tikv-jemallocator` 0.7.0, `uniffi` 0.32.2, `diplomat` 0.16.1, `interoptopus` 0.16.6, `csbindgen` 1.9.8, `magnus` 0.9.2, `rb-sys` 0.9.130, `ext-php-rs` 0.16.2, `jni` 0.22.4, `rustler` 0.39.0 | — | — | — | Versions only. No API claims are made about these. |

Web sources (WebSearch summaries, for things not on GitHub): DocRaptor API docs (https://docraptor.com/documentation/api, https://docraptor.com/documentation/api/making_documents), PDFShift v3 docs (https://api.pdfshift.io, https://docs.pdfshift.io/docs/varying-responses), spatie laravel-pdf v2 docs (https://spatie.be/docs/laravel-pdf/v2/introduction), PHP FFI configuration (https://php.net/manual/ffi.configuration.php, https://php.watch/codex/ffi.enable), JEP 454 (https://openjdk.org/jeps/454), GitHub artifact attestations (https://docs.github.com/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds), PyPI attestations / PEP 740 (https://docs.pypi.org/attestations/, https://peps.python.org/pep-0740).

---

## 0. Executive summary of how ecosystems invoke engines today

Almost every wrapper uses one of five integration shapes. recto has to cover all five for "switching is one line" to hold.

| Shape | Examples | Data path | Cost | recto drop-in strategy |
|---|---|---|---|---|
| **A. wkhtmltopdf subprocess** | python-pdfkit, node-wkhtmltopdf, wicked_pdf, Ruby pdfkit, KnpLabs/snappy + laravel-snappy, Rotativa, Wkhtmltopdf.NetCore, go-wkhtmltopdf, java-wkhtmltopdf-wrapper | argv flags. HTML goes in on stdin (`-`) or a temp file. The PDF comes back on stdout (`-`) or in a temp file. | ~0.2–1 s per process (Qt startup), shell quoting bugs | **wkhtmltopdf-compatible CLI shim.** Point the wrapper's "binary path" setting at `recto` (argv0 = `wkhtmltopdf`), or install a `wkhtmltopdf` symlink. Zero code change, or one config line. |
| **B. libwkhtmltox in-process (C ABI)** | DinkToPdf (.NET P/Invoke, 27 C functions) | settings as string key/value pairs, output buffer | not thread-safe, so a single-thread queue | **Optional `libwkhtmltox`-ABI shim** (cdylib exporting the same 27 symbols). |
| **C. Headless browser via CDP** | puppeteer, playwright, pyppeteer, chromedp, PuppeteerSharp, ferrum, grover (Node child), browsershot (Node child), html-pdf-node | `Page.printToPDF` with a Puppeteer-style options object. HTML set via `setContent` or a URL. | 100s of MB RSS, ~1 s, sandbox flags | **Native binding exposing a Puppeteer-shaped `pdf(html, options)`.** The options object is a superset of Puppeteer `PDFOptions`. |
| **D. HTTP service** | Gotenberg (multipart form), browserless (`POST /pdf` JSON), DocRaptor (`POST /docs` JSON), PDFShift (`POST /v3/convert/pdf` JSON), athenapdf (deprecated) | HTTP | network + container | **`recto serve` with Gotenberg-compatible and browserless-compatible routes** plus a native `/v1/render` route. Existing clients switch by changing the base URL. |
| **E. Pure in-language engine** | WeasyPrint (Python), xhtml2pdf (Python), dompdf/mpdf (PHP), openhtmltopdf/flying-saucer (Java), QuestPDF (.NET, code-first) | in-process objects | slow but no external dependencies | Native binding for Python. For PHP and Java, a thin client (subprocess/HTTP) with an API shaped like the incumbent. |

---

## 1. Node.js

### 1.1 Puppeteer `page.pdf()` (the de-facto standard options shape)

- The options type is `PDFOptions` in `puppeteer_puppeteer/packages/puppeteer-core/src/common/PDFOptions.ts`. Fields at lines 78–188: `scale`, `displayHeaderFooter`, `headerTemplate`, `footerTemplate`, `printBackground`, `landscape`, `pageRanges`, `format`, `width`, `height`, `preferCSSPageSize`, `margin {top,bottom,left,right}`, `path`, `omitBackground`, `tagged` (default **true**, experimental), `outline` (default false, experimental), `timeout` (default 30 000 ms), `waitForFonts` (default true).
- Paper formats are in `paperFormats` (same file, from line 226): `letter`, `legal`, `tabloid`, `ledger`, `a0`–`a6`. Lookup is case-insensitive (`options.format.toLowerCase()` in `common/util.ts:340`).
- Length parsing is in `common/util.ts:378-416`. `unitToPixels = {px:1, in:96, cm:37.8, mm:3.78}`. A bare number, or a string with an unknown unit, is treated as **px** ("consistent with phantom's paperSize behavior"). recto's compat parser must reproduce this exactly. Note that `cm: 37.8` is a rounded value, not 96/2.54 = 37.795…. For byte-identical *page sizes* versus Chrome, recto should use the same constants in compat mode only.
- Defaults are in `parsePDFOptions` (`common/util.ts:317-360`): Letter 8.5×11 in, margins 0, `preferCSSPageSize:false`. With that default, Chrome **scales content to fit the paper** instead of honoring `@page size`. recto's native default should honor `@page`. The compat mode must document the difference.
- Invocation is in `cdp/Page.ts:1261-1296`. It sends `Page.printToPDF` with `transferMode: 'ReturnAsStream'`, `generateTaggedPDF`, `generateDocumentOutline`, and so on, then reads the protocol stream. `pdf()` returns `Promise<Uint8Array>` (`cdp/Page.ts:1298`). `createPDFStream()` returns a `ReadableStream`. **Both shapes (buffer and stream) should exist in the recto Node API.**
- `headerTemplate`/`footerTemplate` are HTML strings with magic classes `date`, `title`, `url`, `pageNumber`, `totalPages` (`PDFOptions.ts:86-103`). The compat layer should translate them into `@page` margin boxes with `counter(page)`/`counter(pages)` (CMP doc).

### 1.2 `html-pdf` (marcbachmann/node-html-pdf 3.0.1): PhantomJS subprocess

- `lib/pdf.js:7` requires `phantomjs-prebuilt`. `PdfExec` (`lib/pdf.js:88-161`) runs `childprocess.spawn(phantomPath, [...phantomArgs, script])` and writes a JSON config (HTML + options) to the child's **stdin** (`child.stdin.write(config + '\n')`, line 156). The PDF path or bytes come back on stdout. Its `localUrlAccess` flag defaults to `--local-url-access=false` (line 39).
- API: `pdf.create(html, options).toBuffer(cb) | toFile(path, cb) | toStream(cb)`. A recto replacement needs callback-style compatibility only if we ship a `html-pdf` shim package. Not worth it in v1. A README migration snippet is enough.

### 1.3 `node-wkhtmltopdf` 0.4.0: wkhtmltopdf via `sh -c`

- `index.js:14-223`. camelCase option keys are dasherized to `--kebab-case` (`slang.dasherize`, line 65). One-letter keys become `-x`. Array values repeat the flag. `toc`/`cover`/`page` are moved last (lines 28-51).
- HTML input goes to **stdin** (`-`) unless it matches `^(https?|file)://` (line 104). Output goes to **stdout** (`-`) unless `output` is given (line 109).
- On Linux/macOS it spawns `/bin/sh -c 'set -o pipefail ; <args joined> | cat'` (lines 117-124). Values are quoted by `quote()` (lines 5-12), but **option keys and non-string values are interpolated unquoted into a shell command line**. That is a shell-injection hazard if keys are user-influenced. The override point is the module-level `wkhtmltopdf.command = 'wkhtmltopdf'` (line 221), so **`wkhtmltopdf.command = 'recto wkhtmltopdf'` is the one-line switch**, which works because the command is run through `sh -c`.

### 1.4 `html-pdf-node` 1.0.7: Puppeteer wrapper

- `index.js`: `generatePdf(file, options, cb)` calls `puppeteer.launch()` **per call**, then `newPage`, `setContent(html, {waitUntil:'networkidle0'})`, then `page.pdf(options)`, then `browser.close()`. The `options` object is passed straight through to `page.pdf`, so it uses the Puppeteer PDFOptions shape. It also runs `inline-css` and then `handlebars.compile(data)` and calls `template(data)` with the HTML string itself as context, which is a bug: the template is compiled from the inlined HTML and then given itself as data. Default launch args are `--no-sandbox --disable-setuid-sandbox`.
- Lesson: users who adopt such wrappers want `generatePdf({content}, options) → Buffer`. Per-call browser launch is the main performance problem recto removes.

### 1.5 Node summary

The canonical Node shape is `await page.pdf(PDFOptions) → Uint8Array/Buffer`. recto's Node binding should accept exactly `PDFOptions` (camelCase), plus recto-only keys, and return `Buffer`.

---

## 2. Python

### 2.1 python-pdfkit 1.0.0: wkhtmltopdf subprocess (deprecated)

- `README.rst:15-18`: "This library has been deprecated to match the wkhtmltopdf project status".
- API (`pdfkit/api.py:7,30,54,78`): `from_url(url, output_path=None, options=None, toc=None, cover=None, configuration=None, cover_first=False, verbose=False)`, `from_file(...)`, `from_string(input, output_path=None, options=None, ..., css=None, ...)`, `configuration(**kwargs)`. With `output_path=False` the call returns bytes.
- Invocation (`pdfkit/pdfkit.py:153-190`): `subprocess.Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)` then `communicate(input=...)`. HTML goes on stdin. `css=` is prepended into the HTML string (line 181). Options are a dict of wkhtmltopdf flags (`{'page-size': 'A4', 'margin-top': '0.75in', 'encoding': 'UTF-8'}`). `--quiet` is added unless verbose (`_command`, lines 77-92).
- Binary path: `pdfkit.configuration(wkhtmltopdf='/path')` (`configuration.py:12`). It also supports **`<meta name="pdfkit-…">` options inside the HTML** (`meta_tag_prefix='pdfkit-'`, `configuration.py:12`).
- One-line switch: `config = pdfkit.configuration(wkhtmltopdf=shutil.which('recto-wkhtmltopdf'))`.

### 2.2 WeasyPrint 70.0: pure Python (pydyf + Pango via cffi)

- `weasyprint/__init__.py:158`: `HTML(guess=None, filename=None, url=None, file_obj=None, string=None, encoding=None, base_url=None, url_fetcher=None, media_type='print')`.
- `write_pdf(target=None, zoom=1, finisher=None, font_config=None, counter_style=None, color_profiles=None, **options)` (`__init__.py:224`). With `target=None` it returns bytes.
- `DEFAULT_OPTIONS` (`__init__.py:66-86`): `stylesheets, attachments, attachment_relationships, pdf_identifier, pdf_variant, pdf_version, pdf_forms, pdf_tags (False), uncompressed_pdf, xmp_metadata, custom_metadata, presentational_hints, output_intent, optimize_images, jpeg_quality, dpi, full_fonts, hinting, cache`. This snake_case options vocabulary is what Python users already know. recto's Python binding should accept these names where they map (`pdf_variant='pdf/a-3b'`, `pdf_tags`, `attachments`, `stylesheets`, `presentational_hints`, `uncompressed_pdf`).
- `URLFetcher` class (`urls.py:236-260`): `URLFetcher(timeout=10, ssl_context=None, http_headers=None, allowed_protocols=None, allow_redirects=True, fail_on_errors=False)`. A subclass with a `fetch` method can be passed as `url_fetcher`. **In-process resource-resolver callbacks are a core integration point.** django-weasyprint builds on it (`DjangoURLFetcher`, `src/django_weasyprint/utils.py:31`), resolving `static`/`media` URLs from storage without HTTP.
- The CLI (`__main__.py`) takes positional `input output` (`-` for stdin/stdout), plus `-s/--stylesheet`, `-a/--attachment`, `--pdf-variant`, `--pdf-tags`, `-m/--media-type`, `-u/--base-url`, `-t/--timeout`, `--allowed-protocols`, `--fail-on-http-errors`, `--http-header`, `-p/--presentational-hints`, `-D/--dpi`, `-j/--jpeg-quality`, and others. spatie/laravel-pdf's `WeasyPrintDriver` shells out to this CLI (`src/Drivers/WeasyPrintDriver.php:35`, binary `weasyprint`).

### 2.3 django-weasyprint 2.6.0

- `src/django_weasyprint/views.py`: `WeasyTemplateResponse` (line 11) with overridable hooks `get_base_url` (70), `get_url_fetcher` (81), `get_font_config` (87), `get_css(base_url, url_fetcher, font_config)` (93), `get_document` (108), and `rendered_content` (138). `WeasyTemplateResponseMixin` (146) has `get_pdf_filename` (157). `WeasyTemplateView` is at line 201.
- Implication: a `django-recto` package (or a `recto.contrib.django` module) should copy this class hierarchy so the switch is a one-word import change: `from recto.contrib.django import RectoTemplateView as WeasyTemplateView`.

### 2.4 xhtml2pdf 0.2.23: pure Python, ReportLab

- `xhtml2pdf/document.py:231`: `pisaDocument(src, dest=None, dest_bytes=False, path="", link_callback=None, debug=0, default_css=None, xhtml=False, encoding=None, xml_output=None, raise_exception=True, capacity=100*1024, context_meta=None, encrypt=None, signature=None, show_error_as_pdf=False, resource_policy=None, **kwargs)`. `CreatePDF = pisaDocument` (`pisa.py:35`). It also uses a `link_callback` resolver hook, which is the same pattern as WeasyPrint's `url_fetcher`.

### 2.5 Playwright-Python 1.64.0 and pyppeteer

- `playwright/async_api/_generated.py:19483-19501`: `async def pdf(self, *, display_header_footer, footer_template, format, header_template, height, landscape, margin, outline, page_ranges, path, prefer_css_page_size, print_background, scale, tagged, width) -> bytes`. These are **snake_case** versions of the Puppeteer names. recto's Python binding must accept snake_case keys (and should accept camelCase too, for JSON pasted from Node docs).
- pyppeteer is unmaintained ("Please consider playwright-python", README).

---

## 3. Go

### 3.1 SebastiaanKlippert/go-wkhtmltopdf v1.9.3

- `wkhtmltopdf.go`: `NewPDFGenerator() (*PDFGenerator, error)` (line 382) looks for the binary. `NewPDFPreparer()` (line 390) skips the lookup. `AddPage(NewPageReader(io.Reader))` or `NewPage(url)`. `Create()` / `CreateContext(ctx)` (lines 315-320) run `exec.CommandContext(ctx, binPath, Args()...)` (line 332). Stdout goes to an internal buffer or `SetOutput(w)` (lines 347-350). A `PageReader` page is piped to **stdin** (line 356). Results come from `Bytes()`, `Buffer()`, or `WriteFile()`.
- Binary lookup: `SetPath(path)` (line 38), the `WKHTMLTOPDF_PATH` env dir (line 282), then `exec.LookPath`. **One-line switch: `wkhtmltopdf.SetPath("/usr/local/bin/recto-wkhtmltopdf")`, or set the env var.**
- Notable: `ToJSON()` / `NewPDFGeneratorFromJSON()` (`json.go:27,58`) serialize the full job, with stdin pages base64-encoded, "to prepare a PDF file and generate the actual PDF elsewhere, for example on AWS Lambda" (README:122-132). **This is direct evidence that users want a serializable job description, which supports a canonical JSON options/job schema shared by the CLI, server and bindings.**

### 3.2 chromedp v0.21.0

- `pdf.go:61`: `func PrintToPDF(opts ...PDFOption) Action[[]byte]`, with `type PDFOption = func(*page.PrintToPDFParams)` (line 34). Helpers include `PDFPaper(PaperA4)`, `PDFLandscape()`, `PDFMargin(0.5)`, `PDFPrintBackground()`, `PDFHeaderTemplate`, `PDFFooterTemplate` (doc comment lines 44-51). Lengths are in **inches**. Usage: `buf, err := chromedp.Run(ctx, chromedp.PrintToPDF(...))` (`example_test.go:477-495`). This is the v0.21 generic `Action[T]` API.

### 3.3 Gotenberg v8.37.0: the de-facto self-hosted PDF HTTP API

- Routes are in `pkg/modules/chromium/routes.go`: `POST /forms/chromium/convert/url` (467), `/forms/chromium/convert/html` (563), `/forms/chromium/convert/markdown` (653), and screenshot variants. Plus `/forms/libreoffice/convert` and `/forms/pdfengines/{merge,split,flatten,optimize,convert,metadata/read,metadata/write,bookmarks/read,bookmarks/write,encrypt,embed,watermark,stamp,rotate,…}` (`pkg/modules/pdfengines/routes.go:1012-1930`). `/health` and `/version` are at `pkg/modules/api/api.go:503-504`.
- Request shape: `multipart/form-data`. The HTML route **requires a file part named `index.html`** (`MandatoryPath("index.html", …)`, routes.go:590). Optional `header.html`/`footer.html` file parts (routes.go:331-332) are Chrome header/footer templates. All other files in the form (CSS, images, fonts) are written to the same working directory and referenced relatively.
- Form fields, extracted from routes.go: `paperWidth`, `paperHeight`, `marginTop`, `marginBottom`, `marginLeft`, `marginRight` (inches by default; units accepted), `preferCssPageSize`, `generateDocumentOutline`, `generateTaggedPdf`, `printBackground`, `omitBackground`, `landscape`, `scale`, `nativePageRanges`, `singlePage`, `waitDelay`, `waitForExpression`, `waitForSelector`, `waitWindowStatus`, `emulatedMediaType`, `emulatedMediaFeatures`, `cookies`, `extraHttpHeaders`, `userAgent`, `failOnHttpStatusCodes`, `failOnResourceHttpStatusCodes`, `failOnResourceLoadingFailed`, `failOnConsoleExceptions`, `skipNetworkIdleEvent`, `skipNetworkAlmostIdleEvent`, `url`, `downloadFrom`. From pdfengines helpers: `pdfa`, `pdfua` (`FormDataPdfFormats`, pdfengines/routes.go:90), `metadata` (JSON), `splitMode`/…, `encrypt`, `embeds`, watermarks/stamps, and Factur-X (lines 107-853).
- Headers: `Gotenberg-Output-Filename`, `Gotenberg-Trace` (correlation ID), `Gotenberg-Webhook-Url`, `Gotenberg-Webhook-Error-Url`, `Gotenberg-Webhook-Method`, `Gotenberg-Webhook-Error-Method`, `Gotenberg-Webhook-Extra-Http-Headers`, `Gotenberg-Webhook-Events-Url`.
- Server flags (`pkg/modules/api/api.go:201-210`): `--api-port` (3000), `--api-timeout` (30s), `--api-body-limit`, `--api-root-path`, `--api-tls-cert-file`/`--api-tls-key-file`, `--api-correlation-id-header` (`Gotenberg-Trace`). There is a Prometheus module (`/prometheus/metrics`).
- **Ecosystem leverage:** Go (starwalkn client), PHP (`gotenberg/gotenberg-php`, UNVERIFIED as not cloned), spatie/laravel-pdf's `GotenbergDriver` (`Http::attach('files', $html, 'index.html')`, `src/Drivers/GotenbergDriver.php:66`), and numerous others already speak this protocol. **A recto server that implements `POST /forms/chromium/convert/html` (and `/url` when network is enabled), `/health` and `/version` with the same field names gives every Gotenberg client a one-line (base-URL) switch.**

### 3.4 starwalkn/gotenberg-go-client v8.12.0

- `gotenberg.NewClient("localhost:3000", http.DefaultClient)`, `document.FromPath/FromString/FromBytes/FromReader("index.html", …)`, `gotenberg.NewHTMLRequest(index)` (README lines 29-86). The switch is the base URL.

---

## 4. Ruby

### 4.1 wicked_pdf (VERSION 2.8.1): temp-file in, temp-file out

- `lib/wicked_pdf.rb:59-100`: `pdf_from_string(string, options)` writes a `WickedPdf::Tempfile('wicked_pdf.html')` and then calls `pdf_from_html_file` → `pdf_from_url("file:///#{filepath}")`. That builds `command = [binary, *option_parser.parse(options), url, generated_pdf_file.path]` and runs `Open3.capture3(*command)` (line 88), using argv with no shell, then reads the output temp file. Header/footer/cover HTML are also temp files (`option_parser.rb:89`, `pdf_helper.rb:112`). There is an optional `use_xvfb` mode.
- Binary resolution (`lib/wicked_pdf/binary.rb:50-64`): `WickedPdf.config[:exe_path]`, then `which`, then well-known dirs. **One-line switch: `WickedPdf.configure { |c| c.exe_path = '/usr/local/bin/recto-wkhtmltopdf' }`**.
- Important for recto's security model: the input is a **temp file in /tmp**, while assets are typically absolute `file:///app/public/...` paths or `wicked_pdf_asset_base64` data URIs. recto's "no file access outside input dir" default would **break** existing wicked_pdf apps that use `file://` asset paths. The wkhtmltopdf shim must map wkhtmltopdf's `--enable-local-file-access` and `--allow <path>` flags onto recto's read allowlist. The shim's default should match wkhtmltopdf 0.12.6, which blocks local file access unless enabled.

### 4.2 pdfkit (Ruby) 0.8.7.3

- `lib/pdfkit/pdfkit.rb:65-80`: `to_pdf(path=nil)` runs `IO.popen(invoke, "wb+")`. HTML is written to stdin and the PDF is read from stdout when `path` is nil. `PDFKit.configure { |c| c.wkhtmltopdf = path }` (`configuration.rb:38`). The meta-tag prefix is configurable (`configuration.rb:5`). There is also Rack middleware.

### 4.3 Grover 1.2.10: Puppeteer via a persistent Node child, JSON over stdio

- `lib/grover/processor.rb:35-90`: `Open3.popen3(node_env_vars, 'node', processor.cjs)`. Each request is written as **one JSON line** `[method, url_or_html, options]` on stdin (line 84). The response is a JSON array `[status, message, error_class, errors]` on stdout (line 90).
- Options are snake_case Ruby keys converted to Puppeteer camelCase (`options_fixer.rb`, `utils.rb`). Meta-tag options: `<meta name="grover-margin-top" content="10px">` (README:41-42). API: `Grover.new(url_or_html, format: 'A4').to_pdf` (README:27-31). There is also Rack middleware.
- **Pattern worth copying:** a long-lived child speaking line-delimited JSON. A `recto --stdio` worker mode lets any language without a native binding amortize font loading across requests.

### 4.4 Ferrum 0.18.0 (CDP from Ruby)

- `lib/ferrum/page/screenshot.rb:147-151`: `pdf(timeout:, **opts)` merges `transferMode: "ReturnAsStream"` and sends `Page.printToPDF`. `pdf_options` (lines 232-247) maps `format:` to `paper_width`/`paper_height` and converts snake_case keys to camelCase. It uses the CDP field names directly (`paper_width` in inches).

---

## 5. PHP

### 5.1 KnpLabs/snappy v1.7.3 + barryvdh/laravel-snappy v1.0.5

- `src/Knp/Snappy/AbstractGenerator.php`: `generate($input, $output, $options, $overwrite)` (178), `generateFromHtml` (223), `getOutput($input, $options)` (240), `getOutputFromHtml($html, $options)` (252). **HTML is always written to a temp file** (`createTemporaryFile`, 493), and so is the output for `getOutput` (242). The command runs via `Process::fromShellCommandline($command)` (602), from symfony/process ^5–^8.
- README:30-42 warns about `--enable-local-file-access` and recommends AppArmor/SELinux sandboxing, which is the security problem recto solves by default.
- laravel-snappy: `PdfWrapper` has `loadView`, `loadHTML`, `loadFile`, `setOption(s)`, `output`, `save`, `download`, `inline` (`src/PdfWrapper.php:112-249`). Facade `SnappyPdf`. Binary config is `'binary' => env('WKHTML_PDF_BINARY', '/usr/local/bin/wkhtmltopdf')` (`config/snappy.php:38`). **One-line switch: `WKHTML_PDF_BINARY=/usr/local/bin/recto-wkhtmltopdf` in `.env`.**

### 5.2 spatie/browsershot 5.4.0: PHP → Node → Puppeteer

- `src/Browsershot.php`: `Browsershot::html($html)` (90) / `::url()` (85), fluent `format()`, `margins(t,r,b,l,unit='mm')`, `paperSize(w,h,unit='mm')`, `showBackground()`, then `pdf(): string` (742), `savePdf($path)` (753), `base64pdf()` (766).
- Invocation: HTML is written to a temp dir as `index.html` (`createTemporaryHtmlFile`, 1088-1094). The JSON command is written to a temp `command.js` (1104-1110). The child is `PATH=… NODE_PATH=… "node" bin/browser.cjs <options>` via `Process::fromShellCommandline` (1124, 1175-1205). That is two temp dirs plus a Node process plus Chrome for every PDF.

### 5.3 dompdf v3.1.6 and mPDF 8.3.2 (pure PHP)

- dompdf: `new Dompdf($options)` (`src/Dompdf.php:251`), `loadHtml($str, $encoding)` (436), `setPaper($size, $orientation)` (1024), `render()` (719), `output()` (938), `stream($filename)` (917). Security-relevant options (`src/Options.php`): `$chroot` (68), `$allowedProtocols` (80), `$isPhpEnabled=false` (192), `$isRemoteEnabled=false` (214), `$isPdfAEnabled=false` (242), `$isJavascriptEnabled=true` (256). Its "chroot + remote disabled by default" model matches recto's.
- mPDF: `new \Mpdf\Mpdf(array $config)` (`src/Mpdf.php:1049`), `WriteHTML($html, $mode, $init, $close)` (13182), `Output($name, $dest)` (9507), plus `OutputBinaryData/OutputHttpInline/OutputHttpDownload/OutputFile` (9658-9679). It is GPL-2.0, which is a reason commercial PHP users look for alternatives.

### 5.4 spatie/laravel-pdf 2.14.0: driver architecture (best hook for recto in PHP)

- `src/Drivers/PdfDriver.php`: `interface PdfDriver { generatePdf(string $html, ?string $headerHtml, ?string $footerHtml, PdfOptions $options): string; savePdf(..., string $path): void; }`. Shipped drivers are `Browsershot`, `Chrome`, `Cloudflare`, `DomPdf`, `Gotenberg` and `WeasyPrint` (`src/Drivers/`). The default comes from `config/laravel-pdf.php:12`: `'driver' => env('LARAVEL_PDF_DRIVER', 'browsershot')`.
- `PdfOptions` (`src/PdfOptions.php`): `format`, `paperSize`, `margins`, `orientation`, `scale`, `pageRanges`, `tagged`, `encryption`, `waitForReady`, `waitForReadyTimeout`, `documentOutline`.
- **One-line switch path for Laravel: contribute a `RectoDriver` upstream (or ship it in `recto/laravel`) so the switch is `LARAVEL_PDF_DRIVER=recto`. Zero lines today: `LARAVEL_PDF_DRIVER=gotenberg` + `GOTENBERG_URL=http://recto:3000` already works once recto implements the Gotenberg route.** Header/footer in the WeasyPrint driver are injected as `<div class="pdf-header">` into `<body>` (WeasyPrintDriver.php, `mergeHeaderFooter`). recto can do better with running elements.

### 5.5 PHP FFI constraint

- `ffi.enable` defaults to `"preload"`: FFI works only in CLI and preloaded files, it is INI_SYSTEM (not settable by `ini_set`), and that is also the recommended production value (php.net ffi.configuration; php.watch). Under PHP-FPM a pure-FFI binding needs the user to edit `php.ini` and set up opcache preload. **That is not a one-line switch, so PHP's primary transport must be subprocess (bundled static binary) or HTTP.**

---

## 6. .NET

### 6.1 DinkToPdf v1.0.8: P/Invoke into libwkhtmltox

- `src/DinkToPdf/WkHtmlToXBindings.cs`: `const string DLLNAME = "libwkhtmltox"` (line 11), 28 `[DllImport(..., CallingConvention.Cdecl)]` declarations over **27 distinct C functions**: `wkhtmltopdf_init, _deinit, _version, _extended_qt, _create_global_settings, _set_global_setting, _destroy_global_settings, _create_object_settings, _set_object_setting, _destroy_object_settings, _create_converter, _add_object (×2 overloads), _convert, _destroy_converter, _get_output, _set_{phase_changed,progress_changed,finished,warning,error}_callback, _phase_count, _current_phase, _phase_description, _progress_string, _http_error_code`.
- Thread model: `SynchronizedConverter` (`SynchronizedConverter.cs:12-58`) funnels all conversions through **one dedicated thread** with a `BlockingCollection<Task>`, because libwkhtmltox is not thread-safe. README:85-91 says it "must be registered as singleton".
- Distribution pain: "Copy native library to root folder of your project" (README:12). The repo ships `v0.12.4/{32 bit,64 bit}` binaries by hand. Users paste these into Docker images with apt-installed X/fontconfig dependencies.
- **recto opportunity:** a `librecto_wkhtmltox` cdylib exporting these 27 symbols (settings are string key/value pairs such as `"size.paperSize"`, `"margin.top"`, `"web.printMediaType"`; the exact key list is for CMP/BND specs) lets DinkToPdf, and the many forks that keep its `IConverter` API, switch by **replacing the `.so`/`.dll` file**. recto is thread-safe, so `SynchronizedConverter` still works, only slower than needed.

### 6.2 Rotativa.AspNetCore 1.5.0 and Wkhtmltopdf.NetCore 5.0.2-preview: wkhtmltopdf subprocess

- Rotativa: `return new ViewAsPdf("View", model) { PageSize = Size.A4, PageOrientation = …, PageMargins = …, CustomSwitches = "…" }` (README:31-66). Properties carry `[OptionFlag("-s")]`, `[OptionFlag("-O")]`, `[OptionFlag("--page-width")]` attributes (`AsPdfResultBase.cs:18-44`). `WkhtmlDriver.Convert` (`WkhtmlDriver.cs:18-60`) prefixes `-q`, appends ` -` (stdin) and ` -` (stdout), starts `Process` with `RedirectStandardInput/Output/Error`, and writes the rendered Razor HTML to stdin. The binary is found in a folder: `app.UseRotativa()` / `RotativaConfiguration.Setup(env, "path")` (README:17-25), with a fixed file name `wkhtmltopdf[.exe]`.
- Wkhtmltopdf.NetCore: `services.AddWkhtmltopdf(string wkhtmltopdfRelativePath = "Rotativa")` (`WkhtmltopdfConfiguration.cs:22`). `IGeneratePdf.GetPDF(string html)`, `GetByteArray<T>(View, model)`, `GetPdf<T>(View, model) → IActionResult` (`IGeneratePdf.cs`). Uses `Process` (`GeneratePdf.cs:55`).
- **One-line (zero-code) switch for both:** put recto's `wkhtmltopdf` shim (a hard link or copy of `recto` named `wkhtmltopdf`, with argv0 dispatch) in the `Rotativa/` folder.

### 6.3 PuppeteerSharp 25.13.1

- `IPage.PdfDataAsync(PdfOptions) → Task<byte[]>` (`IPage.cs:927-937`), `PdfStreamAsync` (946-956), `PdfAsync(file, options)` (907-918). `PdfOptions` has `HeaderTemplate`, `PrintBackground`, `Format`, `MarginOptions`, `PreferCSSPageSize`, `Tagged = true`, `Outline = false` (`PdfOptions.cs:37-109`). These are the Puppeteer names in PascalCase.

### 6.4 QuestPDF 2026.9.1 (not HTML, but the .NET packaging reference)

- It P/Invokes a Skia-based native library (`src/dotnet/library/QuestPDF/Skia/*.cs`). The **NuGet package ships natives under `runtimes/<rid>/native`** (`QuestPDF.csproj:82-94`, `PackagePath="runtimes\..."`, plus `build`/`buildTransitive` targets). RIDs shipped (`src/dotnet/library/QuestPDF/Runtimes/`): `linux-arm64, linux-musl-x64, linux-x64, osx-arm64, osx-x64, win-arm64, win-x64, win-x86`. **recto's NuGet package should copy this layout exactly.**
- Licensing (LICENSE.md, effective 2026-07-06, v3.0): Community license for organisations under USD 1,000,000 annual gross revenue (line 90). Public sector and publicly traded companies are excluded (line 98). It states that "Code generated by an AI coding tool or agent on behalf of an organisation is treated as written by a Developer". A permissively licensed recto has a clear positioning advantage in .NET.

---

## 7. Java

### 7.1 openhtmltopdf: pure-Java HTML→PDF with paged media (most important JVM incumbent)

- Upstream `danfickle/openhtmltopdf` stopped at 1.0.10 (2021-09-13, `CHANGELOG.md`). The last commit was 2022-04-01. The community continuation `openhtmltopdf/openhtmltopdf` (Maven namespace `io.github.openhtmltopdf`, README "GETTING STARTED") is active, with latest tag `openhtmltopdf-parent-1.1.4`.
- Feature set (README "DIFFERENCES WITH FLYING SAUCER", plus source verification): PDFBox backend instead of iText; **PDF/UA** (`PdfRendererBuilder.usePdfUaAccessibility(boolean)`, `openhtmltopdf-pdfbox/.../PdfRendererBuilder.java:211`) and **PDF/A** (`usePdfAConformance(PdfAConformance)`, line 188, `useColorProfile(byte[])`, line 224); SVG via Batik (`openhtmltopdf-svg-support`) and MathML, LaTeX and RTL modules; font fallback; footnotes (1.0.10, #711); `target-counter` (`css/parser/property/ContentPropertyBuilder.java`, `context/ContentFunctionFactory.java`); `leader()`; page margin boxes (`"top-left-corner"`, `"bottom-center"` in `render/PageBox.java` and the CSS code); running elements (`"running"`/`"element"`); `-fs-page-sequence`; bookmarks via a `<bookmarks>` element in `<head>` (`PdfBoxBookmarkManager.java`); initial page number (#727).
- Explicitly unsupported (continuation README "DISCLAIMER"): **flexbox and grid**, and **transparency / alpha colours**. It needs XHTML-ish input ("We recommend users to utilize the Jsoup library to pre-emptively parse the HTML", README) and has no OpenType font support (upstream README).
- Builder API (`openhtmltopdf-core/.../BaseRendererBuilder.java` method names): `withHtmlContent(html, baseUri)`, `withW3cDocument`, `withUri`, `withFile`, `useFastMode`, `useFont(...)`, `useUriResolver`, `useHttpStreamImplementation`, `useProtocolsStreamImplementation`, `useExternalResourceAccessControl`, `useDefaultPageSize`, `useInitialPageNumber`, `useSVGDrawer`, `useMathMLDrawer`, `addDOMMutator`, `withDiagnosticConsumer`, `testMode`. Plus `PdfRendererBuilder.toStream(OutputStream)` (line 167) and `run()`. Typical usage: `new PdfRendererBuilder().useFastMode().withHtmlContent(html, base).toStream(os).run()`.
- Positioning: openhtmltopdf is recto's closest *conceptual* competitor (no JS, paged media, PDF/UA). recto beats it on flexbox, modern HTML5 parsing, OpenType shaping, speed, and a permissive license (LGPL is a friction point for some).

### 7.2 Flying Saucer v10.6.0 (10.7.0-SNAPSHOT)

- `ITextRenderer` (`flying-saucer-pdf/.../ITextRenderer.java:79`): `setDocumentFromString`/`setDocument(Document)` (219), `layout()` (325), `createPDF(OutputStream[, finish[, initialPageNo]])` (367-413). Uses OpenPDF 3.0.5 and Java 21 (`pom.xml:330,339`).
- New `flying-saucer-chrome-pdf` module (CHANGELOG: "#633 add flying-saucer-chrome-pdf module (#666)"; "add `warmup` method … to pre-download and verify Chrome browser (#714)"). Classes: `ChromiumPdfRenderer`, `ChromeBinaryDownloader`, `DevToolsSession`, `ChromiumPdfOptions`. **Even the pure-Java incumbent now ships a Chrome fallback for modern CSS**, which is evidence that the JVM market lacks a fast modern-CSS engine.

### 7.3 jhonnymertz/java-wkhtmltopdf-wrapper 1.3.1-RELEASE

- `Pdf.getPDF()` (`Pdf.java:314-321`) runs `Runtime.getRuntime().exec(getCommandAsArray())` with STDINOUT `"-"` (line 46). Pages from strings are written to temp files (`objects/Page.java:57`). It has a `WrapperConfig(String wkhtmltopdfCommand)` constructor and `WrapperConfig.findExecutable()` (`WrapperConfig.java:38-43`). **One-line switch: `new Pdf(new WrapperConfig("/usr/local/bin/recto-wkhtmltopdf"))`.**

### 7.4 iText pdfHTML (commercial/AGPL)

- Not cloned. pdfHTML is an iText 7/8/9 add-on, dual AGPL/commercial (**UNVERIFIED**, not inspected). Its main API is `HtmlConverter.convertToPdf(html, outputStream, converterProperties)` (**UNVERIFIED**).

### 7.5 Java FFI

- JEP 454 (Foreign Function & Memory API) was finalized in **JDK 22** (openjdk.org/jeps/454). Previews ran from JDK 19 to 21, and the API incubated from JDK 17. JDK 17/21 LTS users therefore cannot use FFM without preview flags, and enterprise Java on 17/21 is common. jextract availability per JDK is spotty (heise, WebSearch). **Conclusion: the Java client should default to subprocess/HTTP, with an optional FFM backend for JDK ≥ 22 (hand-written bindings over ~6 C functions, no jextract dependency).**

---

## 8. Server-style services (API shapes)

| Service | Endpoint | Request | Options naming | Response | Notes |
|---|---|---|---|---|---|
| Gotenberg 8 | `POST /forms/chromium/convert/html` | multipart: `index.html` (required), `header.html`, `footer.html`, assets, form fields | camelCase CDP-ish (`paperWidth`, `marginTop`, `preferCssPageSize`, `printBackground`, `generateTaggedPdf`, `pdfa`, `pdfua`, `metadata`…) | `application/pdf`. Webhook mode via `Gotenberg-Webhook-Url`. | §3.3. MIT. |
| browserless 2.57 | `POST /pdf` and `/chromium/pdf` (`src/shared/pdf.http.ts:86`) | JSON (`accepts = [contentTypes.json]`, line 74) `{ html?, url?, options?: Puppeteer PDFOptions & {fullPage?}, addStyleTag?, addScriptTag?, cookies?, emulateMediaType?, gotoOptions?, waitForSelector?, waitForTimeout?, setJavaScriptEnabled?, viewport?, … }` (`pdf.http.ts:38-64`) | **Puppeteer PDFOptions verbatim** under `options` | `application/pdf` | SSPL-1.0 or commercial license. |
| DocRaptor | `POST /docs` | JSON `{ document_content | document_url, type|document_type: "pdf", test: bool, prince_options: { media, encrypt, disallow_print, … } }` | snake_case; Prince options nested | PDF bytes (sync) or async status | From WebSearch: docraptor.com/documentation/api. Field `type` vs `document_type` is inconsistent across their pages (**UNVERIFIED** which is current). |
| PDFShift v3 | `POST https://api.pdfshift.io/v3/convert/pdf` | JSON `{ source: <url or html>, sandbox?: bool, filename?: … }`, HTTP Basic auth (`api:<key>`) | snake_case | raw binary, or JSON + S3 URL when `filename` is given | From WebSearch: api.pdfshift.io. |
| athenapdf | — | — | — | — | Deprecated (README). Electron + Go "weaver". |

Takeaways: (1) the two open, self-hosted protocols that clients already exist for are **Gotenberg multipart** and **browserless JSON-with-Puppeteer-options**; (2) every service accepts either inline HTML or a URL; (3) every service offers a "test/sandbox" or "trace" flag; (4) async/webhook delivery is standard in Gotenberg and DocRaptor.

---

## 9. Rust binding toolchains

### 9.1 napi-rs (napi 3.14.2, @napi-rs/cli 3.10.8)

- **Async work on the libuv pool:** `trait Task: Send { type Output; type JsValue; fn compute(&mut self) -> Result<Output>; fn resolve(&mut self, env, output) -> Result<JsValue>; fn reject(…); fn finally(…) }` (`crates/napi/src/task.rs:6-27`). `compute` runs "in libuv thread". `AsyncTask::with_signal(task, AbortSignal)` (`bindgen_runtime/js_values/task.rs:18-59`) gives cancellation from a JS `AbortSignal`. libuv's default pool has 4 threads (`UV_THREADPOOL_SIZE`; **UNVERIFIED**, from general Node knowledge). Long renders occupy pool slots shared with `fs`/`crypto`/`zlib`. Alternative: the `tokio_rt` feature with `execute_tokio_future` / `spawn_blocking` (`tokio_runtime.rs:1706,1780`) to run on recto's own pool.
- **Buffers:** `Buffer` is a "zero copy u8 vector shared between rust and napi … designed to be used in `async` context" (`bindgen_runtime/js_values/buffer.rs:400-416`). There is `impl From<Vec<u8>> for Buffer` (line 505). Externally-backed buffers fall back to `napi_create_buffer_copy` when the runtime reports `napi_no_external_buffers_allowed`: "the same path Electron uses" (lines 48-52, 146-152). `BufferSlice<'env>` covers sync calls (line 29), and there is a `Uint8Array` typed array (`arraybuffer.rs:1554`). For recto, returning `Buffer` from `Vec<u8>` is zero-copy on Node and copies once on Electron.
- **Streaming:** `ThreadsafeFunction` (`threadsafe_function.rs:188`, builder at `bindgen_runtime/js_values/function.rs:310`) lets a Rust worker thread push page chunks to JS, which can back a `Readable`.
- **N-API levels:** features `napi1`…`napi10` (`crates/napi/Cargo.toml:45-54`). Pick the lowest level that has the needed APIs (`napi4` for threadsafe functions) to cover old Node LTS lines.
- **Prebuilt binary distribution:** `napi prepublish` rewrites the root package's `optionalDependencies` to `{ "<pkg>-<platformArchABI>": version }` for every target (`cli/src/api/pre-publish.ts:260-290`). `create-npm-dirs` writes per-platform `package.json` with `os`, `cpu` and `libc: ['glibc'|'musl']` (`cli/src/api/create-npm-dirs.ts:477,583-585`). The generated loader (`cli/src/api/templates/js-binding.ts`) detects musl at runtime (`isMusl`, line 254). Supported targets (`cli/src/utils/target.ts:14-39`) include `{x86_64,aarch64}-unknown-linux-{gnu,musl}`, `{x86_64,aarch64}-apple-darwin`, `universal-apple-darwin`, `{x86_64,aarch64,i686}-pc-windows-msvc`, `armv7-unknown-linux-{gnueabihf,musleabihf}`, FreeBSD, Android, OHOS, `riscv64gc`, `loongarch64`, `s390x`, `powerpc64le`, and **`wasm32-wasip1`/`wasm32-wasip1-threads`**. The WASI package is only declared as an optionalDependency when it is the only target, because "npm evaluates every entry independently, so every consumer downloads a `.wasm` binary" (pre-publish.ts:245-258; rolldown issue 10556). The default target set is `x86_64-apple-darwin, aarch64-apple-darwin, x86_64-pc-windows-msvc, x86_64-unknown-linux-gnu` (target.ts:45-48).
- Package config: `"napi": { "binaryName", "packageName", "targets", "npmClient", "constEnum", "dtsHeader", "wasm" }` (`cli/src/utils/config.ts:39-97`). It generates `.d.ts`.
- Bun/Deno load Node-API addons (**UNVERIFIED**, not checked in source). The `wasm32-wasip1-threads` fallback is the path for edge runtimes and StackBlitz.
- Contrast with cargo-dist's npm installer, which downloads the binary in a postinstall step using shrinkwrapped fetch dependencies (`book/src/installers/npm.md:87`). That breaks offline/air-gapped `npm ci` and `--ignore-scripts`. **Use the napi-rs optionalDependencies model for npm, including for the CLI.**

### 9.2 PyO3 (0.29.3 published; 0.30.0 tagged 2026-10-13) + maturin 1.15.0

- **GIL release:** `Python::allow_threads` was renamed to **`Python::detach`** in 0.26.0 (CHANGELOG line 573, "[0.26.0] - 2025-08-29", PR #5221). The definition is `pub fn detach<T, F>(self, f: F) -> T` (`src/marker.rs:562`). recto's `render()` must run inside `py.detach(|| …)` so other Python threads keep running. Inputs (`&str`/`&[u8]`) must first be copied into owned Rust data, or the borrow kept under rules that are valid while detached. The output is `PyBytes`.
- **Stable ABI:** features `abi3`, `abi3-py39` … `abi3-py315` (`Cargo.toml:121-130`). New **`abi3t`/`abi3t-py315`** (lines 132-135) is the free-threaded stable ABI for CPython 3.15+ (CHANGELOG 0.29.x/0.30.0 entries mention `abi3t`). Recommendation: one `abi3-py310` wheel per platform (3.9 is EOL), plus later an `abi3t-py315` wheel for free-threaded builds. The guide `guide/src/free-threading.md` covers free-threaded support since PyO3 0.23. Because recto releases the GIL anyway, free-threading mainly removes a contention point.
- **maturin:** manylinux/musllinux policies come from `src/auditwheel/manylinux-policy.json` (`manylinux_2_17`, `_2_28`, `_2_31`, …) and `musllinux-policy.json`. `--zig` cross-links against old glibc without docker (`src/build_options.rs:75`). `--compatibility pypi` rejects targets PyPI does not accept (`guide/src/distribution.md:14,78`). Built-in **SBOM**: CycloneDX SBOMs go into the wheel under `.dist-info/sboms/` per PEP 770, generated via cargo-cyclonedx (`guide/src/sbom.md`). **`bin` bindings** package a Rust binary as a wheel script (`guide/src/bindings.md:103-112`), which lets `pip install recto-cli` deliver the static CLI (the ruff/uv model). It also supports PGO (`distribution.md:56`).
- Because recto is pure Rust with zero system dependencies, `manylinux_2_17` + `musllinux_1_2` wheels via `--zig` need no auditwheel grafting.

### 9.3 wasm-bindgen 0.2.129 + wasm-pack 0.15.0

- Both repos moved to the `wasm-bindgen` GitHub org (`Cargo.toml:14` / wasm-pack `Cargo.toml:6`).
- wasm-pack targets: `bundler`, `web`, `nodejs`, `no-modules`, `deno` (`src/command/build.rs:56-98`).
- **Threads:** require `RUSTFLAGS='-C target-feature=+atomics'`, **nightly** Rust and `-Z build-std=panic_abort,std` (`guide/src/examples/raytrace.md:20-45`). In browsers, `SharedArrayBuffer` needs cross-origin-isolation headers (same file, line 124). recto-wasm v1 should therefore be **single-threaded**, with parallelism (if any) at the JS level via multiple workers.
- **No filesystem, no system fonts** on `wasm32-unknown-unknown`. All resources (fonts, images, CSS) must be passed in as bytes, or resolved through a JS callback (`resolve(url) → Uint8Array | Promise`). The default font set has to be bundled (size cost) or supplied by the caller. This shapes the core API: the engine must take a `ResourceProvider` trait, not paths.
- Size budget and the `wasm32-wasip1` alternative (via napi-rs or wasmtime) are open questions (see the end of this document).

### 9.4 C ABI via cbindgen 0.29.4

- cbindgen emits C, C++ or Cython headers (`src/bindgen/config.rs:22-25`). Plan: one `recto-capi` crate (`crate-type = ["cdylib", "staticlib"]`) with an opaque-handle API (sketch in §11.4), and a generated `recto.h`.
- Consumers:
  - **Go:** cgo. It breaks `CGO_ENABLED=0` static cross-compilation, which Go users value, so cgo must stay opt-in (a separate module with build tag `recto_cgo`, linking `librecto.a`).
  - **Ruby:** the `ffi` gem against platform gems that bundle `librecto.so`/`.dylib`/`.dll`. Alternatively magnus 0.9.2 / rb-sys 0.9.130 for a native extension (versions from the index; API not inspected).
  - **PHP:** FFI is gated by `ffi.enable=preload` (§5.5). ext-php-rs 0.16.2 exists (index), but distributing PHP extensions per PHP minor version and ZTS/NTS combination is heavy. Not for v1.
  - **.NET:** `[LibraryImport]`/`[DllImport]` plus NuGet `runtimes/<rid>/native` (QuestPDF layout, §6.4). csbindgen 1.9.8 (index) can generate the C# P/Invoke declarations from Rust.
  - **Java:** FFM on JDK ≥ 22 (§7.5).
- ABI rules: (1) every exported fn is `extern "C"` and panic-safe (`catch_unwind` → error code); (2) output buffers are allocated by Rust and freed with `recto_buffer_free`, never `free()`; (3) the options are passed as a **UTF-8 JSON string** (the canonical schema), which keeps the C ABI tiny and stable across versions; (4) handles are thread-safe (`Send + Sync` engine), unlike libwkhtmltox (§6.1).

---

## 10. Binary distribution

### 10.1 cargo-dist (0.32.0 published; 0.33.0 in git, 2026-09-10)

- `InstallerStyle` (`cargo-dist/src/config/mod.rs:177-189`): `Shell`, `Powershell`, `Npm`, `Homebrew`, `Msi`, `Pkg`. Config keys (`cargo-dist/src/config/v0.rs`): `installers` (102), `tap` (113, the Homebrew tap repo), `npm_scope` (178), `ssldotcom_windows_sign` (398), `macos_sign` (406), **`github_attestations`** (410, with filters/phase), `install_updater` (453), **`cargo_auditable`** (499), **`cargo_cyclonedx`** (504), `omnibor` (509). The latest CHANGELOG adds Azure Artifact Signing for Windows.
- Targets include static musl: "x64 Linux (static musl): x86_64-unknown-linux-musl", "arm64 Linux (static musl): aarch64-unknown-linux-musl" (book config reference, around line 244).
- Use cargo-dist for **CLI tarballs, shell/powershell installers, Homebrew tap, MSI, attestations, SBOM**. Do **not** use its npm installer (§9.1). Publish the CLI to npm through napi-rs-style platform packages and to PyPI through maturin `bin` wheels.

### 10.2 cargo-binstall 1.25.3

- `[package.metadata.binstall]` with templated `pkg-url = "{ repo }/releases/download/v{ version }/{ name }-{ target }-v{ version }{ archive-suffix }"`, `bin-dir`, `pkg-fmt` (tgz/zip/…), and per-target overrides (`SUPPORT.md:13-74`). Signing is documented in `SIGNING.md`. cargo-dist's artifact naming is auto-detected by binstall (**UNVERIFIED**, from `book/src/installers/other.md` mention only). Setting explicit metadata is cheap and removes the doubt.

### 10.3 Static musl builds and the allocator

- Pure-Rust dependency set: no OpenSSL. If remote fetching is ever enabled (opt-in), use `rustls` with **embedded `webpki-roots`**, so `FROM scratch` needs no `/etc/ssl/certs`. Default builds can omit the HTTP client entirely (feature-gated).
- **musl malloc is slow.** ripgrep's precedent: `[target.'cfg(all(target_env = "musl", target_pointer_width = "64"))'.dependencies.tikv-jemallocator] version = "0.7.0"` (`ripgrep/Cargo.toml:69-70`), with the rationale in `crates/core/main.rs:20-36`: "musl's allocator … appears to slow down ripgrep quite a bit. Therefore, when building with musl, we use jemalloc." recto is allocation-heavy (DOM, style, fragments), so this matters more for recto than for ripgrep.
- Choice: **mimalloc 0.1.52** (MIT, builds cleanly for musl and Windows, small) vs **tikv-jemallocator 0.7.0** (no Windows support, larger, better long-running fragmentation behaviour in the server). Recommendation: a `global-allocator` cargo feature selecting mimalloc for all release binaries (CLI and server). Bindings (napi/pyo3/C ABI cdylib) should **not** install a global allocator. They use the host's malloc, which avoids conflicts inside Node/Python/JVM processes. Benchmark both in PERF (open question).
- Determinism: allocator choice must not affect output bytes. The DET doc must ensure no address-dependent iteration order (e.g. HashMap with pointer keys).

### 10.4 Docker `FROM scratch`

- Image: `FROM scratch`, `COPY recto /recto`, `COPY fonts/ /usr/share/recto/fonts/` (optional layer), `USER 65534:65534`, `ENTRYPOINT ["/recto","serve"]`, `EXPOSE 3000`. Ship two tags: `recto:<v>` (binary + bundled default fonts) and `recto:<v>-slim` (binary only; fonts mounted or embedded via feature).
- Port 3000 matches Gotenberg's default (`api.go:201`), so `docker run -p 3000:3000` replaces Gotenberg in compose files with only the image name changed. Health route: `/health`.
- Multi-arch manifest: `linux/amd64` + `linux/arm64` from the musl static binaries.

### 10.5 Signing, provenance, SBOM

- **GitHub artifact attestations** (Sigstore-backed; public repos use the Sigstore public-good instance and Rekor transparency log; verify with `gh attestation verify <file> -R <org>/<repo>`; WebSearch: docs.github.com artifact attestations). Enable via cargo-dist `github_attestations = true` for release archives, and `actions/attest-build-provenance` for container images. Container images can additionally be signed with `cosign sign --yes <image>@<digest>` (keyless OIDC) (**UNVERIFIED** CLI syntax, not inspected).
- **npm:** publish with provenance from GitHub Actions (`npm publish --provenance`; **UNVERIFIED** in this session, as the search returned nothing on npm).
- **PyPI:** Trusted Publishing produces PEP 740 attestations by default with the canonical GitHub action (docs.pypi.org/attestations; peps.python.org/pep-0740).
- **SBOM:** `cargo auditable build` embeds the dependency list in a linker section, which `cargo audit bin` can scan (`cargo-auditable/README.md`). `cargo cyclonedx --format json --spec-version …` (`cargo-cyclonedx/src/cli.rs`: `--format`, `--spec-version`, `--all-features`, `--target`, `--override-filename`, `--top-level`, `--no-build-deps`) produces CycloneDX files attached to releases. maturin embeds CycloneDX into wheels (PEP 770). Enable all three (cargo-dist `cargo_auditable` + `cargo_cyclonedx`).

---

## 11. Design recommendation

### 11.1 Principles

1. **One engine, one options schema, many transports.** The Rust `RenderOptions` struct is the single source of truth. A JSON Schema (draft 2020-12) is generated from it with `schemars` 1.2.3 and published at a stable URL plus inside every package. The CLI (`--options file.json` and individual flags), the server (`/v1/render` JSON body or multipart `options` field), the C ABI (JSON string), and every binding (object/dict/hash/map) accept *the same document*.
2. **Canonical keys are camelCase** (they match Puppeteer `PDFOptions`, Gotenberg form fields and browserless). Every binding also accepts the snake_case spelling (Python, Ruby, PHP idiom; Playwright-Python precedent). Normalization happens in Rust, in one place, so all languages get identical semantics. Unknown keys are an **error** by default (not silently ignored). `strict: false` downgrades them to warnings returned in the result.
3. **Compat is a mode, not a fork.** `compat: "puppeteer" | "wkhtmltopdf" | "gotenberg" | "weasyprint" | null` selects default values and unit rules (e.g. Puppeteer's bare-number-is-px, Letter default, `preferCSSPageSize:false` scaling; Gotenberg's inches). Native recto defaults: honor `@page`, A4 vs Letter by `locale` (open question), tagged PDF on.
4. **Secure by default in every transport.** No network, and file reads only under `baseDir` (or the input file's directory). Resources come from an in-memory map or a resolver callback. The wkhtmltopdf shim is the only place that defaults to wkhtmltopdf's semantics, and it maps `--enable-local-file-access`/`--allow` onto the allowlist.
5. **In-process where the ecosystem expects it (Node, Python, Rust, WASM, .NET). Subprocess/HTTP where native extension distribution is hostile (PHP, Go-default, Java-default, Ruby-default).** Every thin client can be pointed at either a bundled binary (`--stdio` worker) or a server URL by a single constructor argument.

### 11.2 Canonical options object (sketch; normative schema belongs to API/BND specs)

```jsonc
{
  "$schema": "https://recto.dev/schema/render-options/v1.json",   // placeholder URL
  // ---- input (exactly one of html | url | file) ----
  "html": "<!doctype html>…",
  "baseUrl": "file:///srv/app/templates/",          // resolution base; also the read-allowlist root
  "resources": { "logo.png": "<bytes|base64>", "style.css": "…" },  // in-memory files (Gotenberg-like)
  "stylesheets": ["…css…"],                          // extra user stylesheets (WeasyPrint `stylesheets`)
  "data": { },  "template": "…",                      // TPL mode (doc 22)
  // ---- page (Puppeteer-compatible names) ----
  "format": "A4", "width": "210mm", "height": "297mm", "landscape": false,
  "margin": { "top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm" },
  "preferCSSPageSize": true, "scale": 1, "pageRanges": "1-3,5",
  "printBackground": true, "omitBackground": false,
  "displayHeaderFooter": false, "headerTemplate": "", "footerTemplate": "",   // compat → margin boxes
  "mediaType": "print",
  // ---- PDF output ----
  "tagged": true, "outline": true,
  "pdfVariant": null,            // "pdf/a-2b" | "pdf/a-3b" | "pdf/ua-1" | "pdf/ua-2" … (WeasyPrint pdf_variant vocabulary)
  "pdfVersion": "1.7",
  "metadata": { "title": "", "author": "", "subject": "", "keywords": [], "creator": "", "lang": "en" },
  "attachments": [ { "name": "factur-x.xml", "data": "…", "relationship": "Data", "mime": "text/xml" } ],
  "deterministic": true,         // fixed IDs/dates (doc 25)
  // ---- security & limits ----
  "allowNetwork": false, "allowedHosts": [], "allowFileAccess": "baseDir",   // "none" | "baseDir" | ["/abs/allow", …]
  "timeoutMs": 30000, "maxMemoryMb": 512, "maxPages": 10000,
  // ---- behaviour ----
  "compat": null, "strict": true, "fonts": { "dirs": [], "default": "bundled" }
}
```

Mapping evidence: Puppeteer `PDFOptions.ts:78-188`; Gotenberg `routes.go` field list (§3.3); WeasyPrint `DEFAULT_OPTIONS` (`__init__.py:66-86`); spatie `PdfOptions` (§5.4).

The result object is the same everywhere: `{ pdf: bytes, pageCount, warnings: [{code, message, url?}], timings? }`. Errors carry a stable `code` string (e.g. `RESOURCE_BLOCKED`, `TIMEOUT`, `LIMIT_PAGES`, `INVALID_OPTION`) shared with CLI exit codes and HTTP status mapping (SRV doc).

### 11.3 Transport matrix

| Language | Primary (default) | Package name (proposal, availability **UNVERIFIED**) | Mechanism | Secondary | Async / threading |
|---|---|---|---|---|---|
| Rust | in-process | crate `recto` | direct | — | `render()` sync; `render_stream(writer)` |
| Node / Bun / Deno | **in-process** | npm `@recto/pdf` + `@recto/pdf-<platformArchABI>` optionalDependencies; CLI `@recto/cli` (same model) | napi-rs `AsyncTask` + `AbortSignal`; `Buffer` result; `Readable` via ThreadsafeFunction | `@recto/pdf-wasm32-wasi` fallback (not auto-installed); HTTP client in same package (`new Recto({url})`) | Promise; `renderSync` for scripts |
| Browser / edge | in-process WASM | npm `@recto/wasm` | wasm-bindgen, single-thread, fonts/resources as bytes or JS resolver | — | Promise |
| Python | **in-process** | PyPI `recto` (abi3-py310 wheels: manylinux_2_17 x86_64/aarch64, musllinux_1_2, macOS x86_64/arm64, win amd64/arm64); `recto-cli` (maturin `bin` wheel) | PyO3 + `py.detach` | `recto.Client(url=…)` HTTP | sync API releasing the GIL; `async def arender` = `asyncio.to_thread` wrapper |
| .NET | **in-process** | NuGet `Recto` with `runtimes/{linux-x64,linux-arm64,linux-musl-x64,linux-musl-arm64,osx-x64,osx-arm64,win-x64,win-arm64}/native` (QuestPDF layout) | P/Invoke over C ABI (JSON options) | `Recto.Http` client; `Recto.Compat.DinkToPdf` (libwkhtmltox-ABI shim) | `Task<byte[]> RenderAsync` = `Task.Run` over thread-safe native call |
| Java / Kotlin | **subprocess (`--stdio` worker) bundling the static binary in per-platform classifier jars** | Maven `dev.recto:recto` + `dev.recto:recto-native-<os>-<arch>` | JSON-lines over stdio (Grover pattern) | FFM backend on JDK ≥ 22 (`dev.recto:recto-ffm`); HTTP client | `CompletableFuture<byte[]>` |
| Go | **subprocess (`--stdio` worker) or HTTP; pure Go, `CGO_ENABLED=0`-friendly** | module `github.com/<org>/recto-go` | binary located via `RECTO_PATH`/`$PATH`, or `recto.NewHTTP(url)` | `recto-go/cgo` with static `librecto.a` (build tag) | `ctx`-aware `Render(ctx, Options) ([]byte, error)` |
| Ruby | **subprocess (`--stdio` worker)**; binary shipped in platform gems | gem `recto` (+ `x86_64-linux`, `aarch64-linux`, `x86_64-linux-musl`, `arm64-darwin`, `x64-mingw-ucrt` platform gems) | JSON-lines worker (Grover pattern) | `ffi` gem over C ABI (opt-in); HTTP | thread-safe client; worker pool size option |
| PHP | **subprocess** (Symfony Process, like snappy) **or HTTP** | Composer `recto/recto`; binary via `recto/recto-bin-<platform>` packages or a post-install download; `recto/laravel` (laravel-pdf driver) | argv + stdin/stdout, no temp files, no shell (`new Process([...])`, not `fromShellCommandline`) | FFI only if `ffi.enable=true` | sync |

Why Java, Go, Ruby and PHP default to subprocess: (a) recto's cold start target (<100 ms) makes per-call process cost small, and the `--stdio` worker amortizes it to ~0; (b) native-extension distribution in those ecosystems is the main source of install failures (cgo, ffi.enable, JDK version gating, Ruby ABI per minor version); (c) process isolation gives a hard memory/time kill switch (LIM doc) for free.

### 11.4 C ABI surface (for .NET, Java FFM, Go cgo, Ruby ffi)

```c
typedef struct recto_engine recto_engine;      /* thread-safe; holds font DB + caches */
typedef struct { uint8_t* ptr; size_t len; } recto_buf;
int  recto_engine_new(const char* engine_opts_json, recto_engine** out);
int  recto_render(recto_engine*, const char* options_json,
                  const uint8_t* html, size_t html_len,
                  recto_resolve_fn resolver, void* resolver_ctx,   /* may be NULL */
                  recto_buf* out_pdf, recto_buf* out_report_json);
void recto_buf_free(recto_buf);
void recto_engine_free(recto_engine*);
const char* recto_version(void);
```
Six functions. Panic → error code `RECTO_E_PANIC`. Every string is UTF-8. The `report_json` carries warnings/errors in the canonical shape.

### 11.5 Server-mode compatibility surface (`recto serve`)

| Route | Compat target | Notes |
|---|---|---|
| `POST /v1/render` | native | JSON (`application/json`, the canonical options with inline `html`/`resources`) or multipart (`index.html` + assets + `options` JSON field). Returns `application/pdf`. `Accept: application/json` returns `{pdf: base64, warnings}`. |
| `POST /forms/chromium/convert/html` | **Gotenberg 8** | Same multipart contract (`index.html` required, `header.html`/`footer.html`, assets). Same field names (§3.3). `pdfa`/`pdfua` mapped to `pdfVariant`. Unsupported fields (`waitForExpression`, `emulatedMediaFeatures`, `cookies` without network…) return Gotenberg-style 400s, or are ignored with a `Recto-Warning` header in non-strict mode. |
| `POST /forms/chromium/convert/url` | Gotenberg | Only when `--allow-network`. Otherwise 403. |
| `GET /health`, `GET /version` | Gotenberg | `/health` JSON. |
| `POST /pdf`, `POST /chromium/pdf` | **browserless** | JSON `{html, url?, options: PDFOptions}`. `addStyleTag[].content` is supported. Script-related keys are rejected (no JS). |
| Headers | Gotenberg | Honor `Gotenberg-Output-Filename`, `Gotenberg-Trace` (echoed); webhook headers optional (later milestone). |
| Default port | 3000 | Same as Gotenberg. |

### 11.6 One-line "before → after" per ecosystem

Each row gives the most common incumbent call or config and the recto replacement. "Zero-code" rows only change configuration.

| Ecosystem / incumbent | Before | After |
|---|---|---|
| Node / Puppeteer | `const pdf = await page.pdf({ format: 'A4', printBackground: true });` (after `browser.newPage(); page.setContent(html)`) | `const pdf = await require('@recto/pdf').render(html, { format: 'A4', printBackground: true });` |
| Node / node-wkhtmltopdf | `wkhtmltopdf(html, { pageSize: 'A4' }).pipe(res)` | add `wkhtmltopdf.command = 'recto wkhtmltopdf';` (zero other changes; the module runs the command through `sh -c`) |
| Node / html-pdf-node | `htmlPdf.generatePdf({ content: html }, { format: 'A4' })` | `require('@recto/pdf').render(html, { format: 'A4' })` |
| Python / WeasyPrint | `HTML(string=html, base_url=base).write_pdf()` | `recto.HTML(string=html, base_url=base).write_pdf()`, i.e. `from recto.compat.weasyprint import HTML` (same kwargs subset: `stylesheets`, `pdf_variant`, `pdf_tags`, `attachments`, `url_fetcher`) |
| Python / django-weasyprint | `from django_weasyprint import WeasyTemplateView` | `from recto.contrib.django import WeasyTemplateView` |
| Python / pdfkit | `pdfkit.from_string(html, False, options=opts)` | `pdfkit.from_string(html, False, options=opts, configuration=pdfkit.configuration(wkhtmltopdf='recto-wkhtmltopdf'))` (or `recto.render(html, **opts)`) |
| Python / Playwright | `await page.pdf(format="A4", print_background=True)` | `await recto.arender(html, format="A4", print_background=True)` |
| Go / go-wkhtmltopdf | `pdfg, _ := wkhtmltopdf.NewPDFGenerator()` | `wkhtmltopdf.SetPath("recto-wkhtmltopdf")` before it (or env `WKHTMLTOPDF_PATH`) |
| Go / chromedp | `chromedp.Run(ctx, chromedp.PrintToPDF(chromedp.PDFPaper(chromedp.PaperA4)))` | `recto.Render(ctx, recto.Options{HTML: html, Format: "A4"})` |
| Go / Gotenberg client | `gotenberg.NewClient("gotenberg:3000", http.DefaultClient)` | `gotenberg.NewClient("recto:3000", http.DefaultClient)` (zero-code if DNS/env-driven) |
| Ruby / wicked_pdf | `WickedPdf.new.pdf_from_string(html)` | `WickedPdf.configure { \|c\| c.exe_path = 'recto-wkhtmltopdf' }` (one initializer line) |
| Ruby / Grover | `Grover.new(html, format: 'A4').to_pdf` | `Recto.new(html, format: 'A4').to_pdf` (same snake_case keys; `Recto::Grover = Recto` alias) |
| Ruby / pdfkit | `PDFKit.new(html).to_pdf` | `PDFKit.configure { \|c\| c.wkhtmltopdf = 'recto-wkhtmltopdf' }` |
| PHP / laravel-snappy | `SnappyPdf::loadView('invoice', $d)->download('i.pdf')` | `.env`: `WKHTML_PDF_BINARY=/usr/local/bin/recto-wkhtmltopdf` |
| PHP / spatie laravel-pdf | `Pdf::view('invoice', $d)->save('i.pdf')` | `.env`: `LARAVEL_PDF_DRIVER=recto` (driver package), or today `LARAVEL_PDF_DRIVER=gotenberg` + recto server URL |
| PHP / Browsershot | `Browsershot::html($html)->format('A4')->pdf()` | `Recto\Recto::html($html)->format('A4')->pdf()` (same fluent subset) |
| PHP / dompdf | `$d=new Dompdf(); $d->loadHtml($h); $d->render(); $d->output();` | `Recto\Recto::html($h)->pdf();` (or a `Recto\Compat\Dompdf` class with the same four methods) |
| .NET / DinkToPdf | `services.AddSingleton(typeof(IConverter), new SynchronizedConverter(new PdfTools()));` | unchanged code; replace `libwkhtmltox.so/.dll` with `Recto.Compat.DinkToPdf` package's native shim. Or `services.AddRecto();` and inject `IRecto` |
| .NET / Rotativa | `return new ViewAsPdf("Invoice", model);` | unchanged; drop recto's `wkhtmltopdf` shim into the `Rotativa/` folder |
| .NET / PuppeteerSharp | `await page.PdfDataAsync(new PdfOptions { Format = PaperFormat.A4 })` | `await Recto.RenderAsync(html, new RenderOptions { Format = "A4" })` |
| Java / openhtmltopdf | `new PdfRendererBuilder().useFastMode().withHtmlContent(h, base).toStream(os).run();` | `Recto.builder().withHtmlContent(h, base).toStream(os).run();` (builder name-compatible subset) |
| Java / wkhtmltopdf wrapper | `new Pdf()` | `new Pdf(new WrapperConfig("recto-wkhtmltopdf"))` |
| Any / Gotenberg HTTP | `POST http://gotenberg:3000/forms/chromium/convert/html` | `POST http://recto:3000/forms/chromium/convert/html` (image swap in compose) |
| Any / browserless | `POST https://chrome.browserless.io/pdf?token=…` `{html, options}` | `POST http://recto:3000/pdf` same body |

### 11.7 The `recto-wkhtmltopdf` shim (enables ~9 wrappers with zero code)

- Dispatch on argv0 basename `wkhtmltopdf` (hard link or symlink), or the explicit `recto wkhtmltopdf …` subcommand. Ship `recto-wkhtmltopdf` as a tiny launcher/symlink in every package that bundles the binary. Windows needs a real copy or a `.exe` launcher, since symlinks are unreliable there.
- Must support the I/O conventions the wrappers actually use: `-` for stdin input and stdout output (node-wkhtmltopdf, pdfkit, Rotativa, java wrapper), file paths and `file:///` URLs for input and output (wicked_pdf, snappy), `-q/--quiet`, `-V/--version` (wicked_pdf probes `-V`: `binary.rb:41`), repeated `--allow`, `--enable-local-file-access`, `toc`/`cover`/`page` positional keywords (node-wkhtmltopdf moves them last), and `--header-html`/`--footer-html` *file paths* (wicked_pdf passes temp files).
- Exit codes: 0 on success. wkhtmltopdf's "1 = error, 2 = page load errors" semantics need verification in the CMP doc (**UNVERIFIED**). Wrappers check `status.success?` (wicked_pdf), an empty result (pdfkit), or the exit code (go-wkhtmltopdf).

---

## Findings that affect recto's design

1. **The integration surface is five shapes** (wkhtmltopdf CLI, libwkhtmltox C ABI, Puppeteer-style `pdf(options)`, Gotenberg/browserless HTTP, in-language engine API). Covering them gives near-zero-code migration for nine wkhtmltopdf wrappers, every Gotenberg client and the laravel-pdf Gotenberg driver.
2. **Puppeteer `PDFOptions` is the lingua franca.** Field names recur in Playwright (snake_case), PuppeteerSharp (PascalCase), chromedp, Ferrum, Grover, Gotenberg and browserless. recto's canonical options must be a superset with identical names and Puppeteer's unit rules in compat mode (bare number = px; `cm = 37.8 px`; Letter default; `preferCSSPageSize:false` scales to fit).
3. **Snake_case aliases are mandatory** (Playwright-Python, Grover, Ferrum, WeasyPrint `DEFAULT_OPTIONS`). Normalize in Rust once.
4. **Resource resolver callbacks are a first-class need** (WeasyPrint `url_fetcher`, django `DjangoURLFetcher`, xhtml2pdf `link_callback`, openhtmltopdf `useUriResolver`/`useHttpStreamImplementation`). The core API must take a resolver trait. The C ABI must expose a callback. HTTP transport uses in-request files (Gotenberg multipart).
5. **Temp files plus `file://` asset paths are pervasive** (wicked_pdf, snappy, browsershot, java wrapper). recto's default "only the input dir" policy breaks them unless the wkhtmltopdf shim maps `--enable-local-file-access`/`--allow` to an allowlist. Document that `--allow /app/public` is the usual migration line.
6. **Engine thread-safety is a selling point.** DinkToPdf must serialize all work onto one thread because libwkhtmltox is not thread-safe. recto's engine handle must be `Send + Sync`, with shared immutable font DB and caches and per-render state.
7. **Per-call browser launch is the main incumbent performance cost** (html-pdf-node per call; browsershot = temp dirs + node + Chrome; Grover keeps a persistent Node child to amortize it). A `--stdio` JSON-lines worker mode (Grover pattern) gives subprocess-based clients warm caches.
8. **Serializable jobs are wanted** (go-wkhtmltopdf `ToJSON`/`NewPDFGeneratorFromJSON` for Lambda). Make the canonical options plus inline resources a self-contained JSON job document usable by CLI `recto render job.json`, the server, and queues.
9. **Gotenberg's protocol is the de-facto self-hosted API.** Implementing `/forms/chromium/convert/html` + `/health` + `/version` on port 3000 is cheap and unlocks existing clients. browserless's JSON `/pdf` is the second target.
10. **npm distribution must use napi-rs optionalDependencies per platform/libc**, not postinstall downloads (cargo-dist npm installer). That covers offline installs and `--ignore-scripts`. Do not auto-install the WASI fallback (napi-rs pre-publish.ts rationale).
11. **PyO3 `detach` (ex-`allow_threads`) around every render. Ship one abi3-py310 wheel per platform.** Plan `abi3t` free-threaded wheels for CPython 3.15. maturin `bin` wheels also ship the CLI on PyPI. maturin embeds a PEP 770 SBOM.
12. **WASM v1 is single-threaded and filesystem-less.** Threads need nightly + build-std + COOP/COEP. Fonts must be bundled or supplied. This forces the core API to be path-free (bytes + resolver).
13. **The C ABI should be ~6 functions taking JSON options**, not a mirrored struct API. That keeps .NET/Java/Go/Ruby bindings thin and ABI-stable across versions. Rust-allocated buffers are freed by `recto_buf_free`, and the panic boundary is enforced.
14. **PHP cannot rely on FFI** (`ffi.enable=preload` default, INI_SYSTEM). The primary PHP transport is a bundled static binary via `Symfony\Process` with array argv (no shell, unlike snappy and browsershot), or HTTP.
15. **Java on JDK 17/21 cannot use FFM** (final in JDK 22). The Java default is a subprocess worker with per-platform classifier jars. FFM is opt-in.
16. **Go users expect `CGO_ENABLED=0`.** The default Go client is pure Go (subprocess/HTTP). cgo is behind a build tag.
17. **NuGet natives go in `runtimes/<rid>/native`** for at least the eight RIDs QuestPDF ships, plus `linux-musl-arm64`.
18. **Static musl release binaries need a non-musl allocator** (ripgrep uses jemalloc on 64-bit musl for this reason). Use mimalloc behind a `global-allocator` feature in binaries only, never in cdylib bindings.
19. **No OpenSSL anywhere.** If network fetching exists it is opt-in, with rustls + embedded webpki-roots, so `FROM scratch` works. Default port 3000 and `/health` make recto a drop-in for Gotenberg in compose files.
20. **Release supply chain via cargo-dist:** `github_attestations`, `cargo_auditable`, `cargo_cyclonedx`, Homebrew `tap`, shell/powershell/MSI installers, and cargo-binstall metadata. Publish to npm with provenance and to PyPI via Trusted Publishing (PEP 740 attestations).
21. **The JVM incumbent (openhtmltopdf) lacks flexbox, grid, alpha transparency and OpenType**, and is LGPL. Flying Saucer now ships a Chrome fallback module. Both point to an unserved JVM demand that recto can meet with an openhtmltopdf-shaped builder API.
22. **Licensing friction in incumbents** (QuestPDF revenue-gated with an "AI-written code counts as Developer" clause; browserless SSPL; mPDF GPL; dompdf/openhtmltopdf/flying-saucer LGPL) makes a permissive license (MIT/Apache-2.0) part of the migration story.
23. **Meta-tag options are an established convention** (`<meta name="pdfkit-…">`, `<meta name="grover-…">`). Consider supporting `<meta name="recto-…">` (or reading those prefixes in compat mode) so templates carry their own page options.

## Recommendation

Adopt the transport matrix in §11.3 and the canonical options object in §11.2 as the BND/SRV/CMP spec baseline:

- **Native in-process bindings in v1:** Rust crate, Node (napi-rs, `@recto/pdf` + platform packages), Python (PyO3 abi3 + maturin, `recto`). Then .NET (P/Invoke over the 6-function C ABI, NuGet `runtimes/`) as the first C-ABI consumer.
- **Thin clients in v1:** Go (pure Go, subprocess `--stdio` worker or HTTP), PHP (Symfony Process with array argv, or HTTP, plus a laravel-pdf driver), Ruby (worker in platform gems, Grover-compatible API), Java (worker in classifier jars; openhtmltopdf-shaped builder; FFM later).
- **Compat drop-ins in v1:** the `recto-wkhtmltopdf` argv0 shim (highest leverage: nine wrappers, zero code) and Gotenberg-compatible server routes on port 3000. Fast follow: browserless `/pdf` JSON route, `libwkhtmltox` ABI shim for DinkToPdf, WeasyPrint-API compat module in the Python package.
- **Distribution:** cargo-dist for archives, installers, Homebrew and attestations; napi-rs model for npm (CLI included); maturin (`pyo3` and `bin`) for PyPI; `FROM scratch` multi-arch images (`recto`, `recto-slim`); musl static with mimalloc; cargo-auditable + CycloneDX SBOMs everywhere.

## Open questions / UNVERIFIED items

1. Package-name availability (`recto` on npm, PyPI, crates.io, RubyGems, NuGet, Packagist; the `@recto` npm scope; a Maven groupId) is **UNVERIFIED**. "recto" is a working name (ADR-0001).
2. libwkhtmltox settings key list (`size.paperSize`, `margin.top`, `web.printMediaType`, `load.*`, …) and wkhtmltopdf exit-code semantics: verify against the wkhtmltopdf source in the CMP research (**UNVERIFIED** here).
3. iText pdfHTML API and license were not inspected (**UNVERIFIED**).
4. DocRaptor: is the current field `type` or `document_type`? (Sources disagree; **UNVERIFIED**.) PDFShift: is raw HTML also accepted in `source`? (**UNVERIFIED**.)
5. `gotenberg/gotenberg-php` and other non-Go Gotenberg clients were not inspected. The claim that they only depend on the routes and field names in §3.3 is **UNVERIFIED** per client.
6. Bun/Deno loading napi-rs addons, and the libuv default pool size of 4, are **UNVERIFIED** in this session.
7. `npm publish --provenance` and `cosign sign` syntax are **UNVERIFIED** (the search returned nothing for npm).
8. pyo3 0.30.0 is tagged in git (CHANGELOG 2026-10-13) but the sparse index still shows 0.29.3 as newest. Pin to the published version at implementation time. Similarly cargo-dist: 0.33.0 in git vs 0.32.0 in the index.
9. Whether cargo-binstall auto-detects cargo-dist artifact names without metadata (**UNVERIFIED**). Set explicit `[package.metadata.binstall]` anyway.
10. Allocator choice (mimalloc vs jemalloc vs system) for the musl server binary needs PERF benchmarks on a 1000-page document and on a sustained server workload (fragmentation).
11. WASM build size with bundled default fonts, and whether `wasm32-wasip1` (napi-rs / wasmtime) is a better edge target than `wasm32-unknown-unknown` + wasm-bindgen.
12. Default paper size when neither `@page size` nor `format` is given (A4 vs Letter, locale-driven?). Puppeteer and Gotenberg default to Letter.
13. Should the Gotenberg-compat route translate `header.html`/`footer.html` (Chrome templates with `pageNumber`/`totalPages` classes) into margin boxes with running elements? Fidelity rules belong in the CMP doc.
14. Ruby native path: `ffi` gem vs magnus/rb-sys native extension. Neither was inspected beyond index versions.
