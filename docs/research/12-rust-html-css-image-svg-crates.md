# 12 — Rust crates for HTML, CSS, images, SVG, encodings and templates

- **Date:** 2026-10-14
- **Topic slug:** `parsing`
- **Scope:** Which third-party crates recto should depend on for HTML parsing, CSS tokenizing/selector matching, raster image decoding, SVG, and the supporting pieces (text encodings, URLs, compression, WOFF fonts, JSON, templates), and which parts we must build ourselves.
- **Method:** Latest published versions come from the crates.io sparse index (`index.crates.io`), queried 2026-10-14. Sources were shallow-cloned from GitHub into `/tmp/claude-0/src/parsing/<repo>`. Each API claim below cites the file it comes from. Line numbers refer to the commit listed in the table. A claim that could not be checked against source is marked **UNVERIFIED**.
- **Unsafe counts** are the number of `unsafe {` / `unsafe fn` / `unsafe impl` occurrences in non-test sources (`grep -rE "unsafe *(\{|fn|impl)"`), so they show the order of magnitude only.

## Sources inspected

| Crate (latest on index) | Repo @ tag / ref inspected | Commit SHA | License | Last commit | MSRV | Maintenance assessment |
|---|---|---|---|---|---|---|
| html5ever 0.40.1, markup5ever 0.40.0, xml5ever 0.40.0, tendril 0.5.1, web_atoms 0.3.0 | servo/html5ever @ `html5ever-v0.40.1` | d7232d746d3112f08926d169591576bd12fe2fdf | MIT OR Apache-2.0 | 2026-09-14 | 1.85 | Active (Servo); releases in lock-step with stylo |
| markup5ever_rcdom (official: **unpublished**; index shows `0.39.0+unofficial`) | same repo, `rcdom/` | same | MIT OR Apache-2.0 | — | — | `publish = false`; test-only (see §1.2) |
| scraper 0.27.0 | rust-scraper/scraper @ `v0.27.0` | 9c1eff304e45a8bccb463968268ce6758703e821 | ISC | 2026-05-11 | none set | Active, but lags one version behind (html5ever 0.39, selectors 0.38, cssparser 0.37) |
| html5gum 0.8.4 | untitaker/html5gum @ `0.8.4` | d182efa7a6e315a4f38518697ba9addf3e8fc266 | MIT | 2026-06-22 | none | Active; tokenizer only |
| tl 0.7.8 | y21/tl @ HEAD | 604f644ada25d8aac78f423b4117932d766d6b79 | MIT | 2024-01-30 | none | **Stale**, not spec-compliant |
| lol_html 3.0.1 | cloudflare/lol-html @ `v3.0.1` | 608cc4a66b7ab4fcbe1bbdeb25df8f265572b11c | BSD-3-Clause | 2026-07-29 | 1.85 | Active (Cloudflare); streaming rewriter |
| blitz-dom 0.2.4 / 0.3.0-beta.3 | DioxusLabs/blitz @ main | e72650a6e67941852fddf025295cfee30c39ea32 | MIT OR Apache-2.0 | 2026-10-13 | 1.86 | Active, pre-1.0 |
| cssparser 0.38.0 | servo/rust-cssparser @ `v0.38.0` | d128a90e1203fc4afb959420d6dc5e24f77a3191 | MPL-2.0 | 2026-09-07 | 1.85 | Active (Servo/Mozilla) |
| selectors 0.41.0, stylo 0.22.0 (+ stylo_traits/_dom/_atoms/_static_prefs, servo_arc 0.5.0) | servo/stylo @ `v0.22.0` | 34d25f741765a0bdb894f8271852e633299352d8 | MPL-2.0 | 2026-09-30 | none set | Active (synced from mozilla-central) |
| lightningcss 1.0.0-alpha.72 (all published versions are alpha) | parcel-bundler/lightningcss @ master (Cargo.toml = alpha.72) | ab14f90df45b1a94c6c10a3d9ca16b39d09f67e0 | MPL-2.0 | 2026-10-07 | none | Active; minifier/transpiler |
| image 0.25.10 | image-rs/image @ `v0.25.10` | 76e57184f22772dad1138e96954e57945406b15e | MIT OR Apache-2.0 | 2026-03-10 | 1.88 | Active |
| zune-jpeg 0.5.15 (HEAD = 0.5.16-rc2) | etemesi254/zune-image @ HEAD | c727560dc176aab75125a654d5edac010c8288f3 | MIT OR Apache-2.0 OR Zlib | 2026-10-12 | 1.75 (index) | Active, single maintainer |
| png 0.18.1 | image-rs/image-png @ HEAD (Cargo.toml = 0.18.1) | b2f10c6a7e3127d4aaf231f3eae731a33e6eb0bc | MIT OR Apache-2.0 | 2026-09-23 | 1.73 | Active |
| image-webp 0.2.4 | image-rs/image-webp @ `v0.2.4` | 08b57d473c90148dd4b37a075df365afc3dfcc2b | MIT OR Apache-2.0 | 2025-08-26 | 1.80.1 | Maintained |
| gif 0.14.2 | image-rs/image-gif @ HEAD | a5f89ddc2b29424334244c97456b4a26e208aa7d | MIT OR Apache-2.0 | 2026-05-31 | 1.88 (HEAD), 1.62 (index) | Maintained |
| jpeg-decoder 0.3.2 | image-rs/jpeg-decoder @ HEAD | eb2d7c0f6a2d0298aba7a7f8b9ca1440353e8f8c | MIT OR Apache-2.0 | 2025-06-21 | 1.61 | **Maintenance mode** (README banner) |
| moxcms 0.9.1 (image pulls 0.8) | awxkee/moxcms @ HEAD | a61db8babddcb47f8cb46314f2c6577756d7496f | BSD-3-Clause OR Apache-2.0 | 2026-10-11 | 1.89 | Active |
| resvg / usvg 0.48.1 | linebender/resvg @ `v0.48.1` | 68b14c4c3bccdb60344c777406486b54c36ec1a4 | Apache-2.0 OR MIT | 2026-08-02 | 1.85 | Active (Linebender) |
| tiny-skia 0.12.0 | linebender/tiny-skia @ HEAD | 5d4754777746eef0828be166896eaf482c49f8f2 | BSD-3-Clause | 2026-08-20 | — | Active |
| roxmltree 0.21.1 | RazrFalcon/roxmltree @ `v0.21.1` | 67644e16f43c34cadc9e163163dd1aaf7ebe205e | MIT OR Apache-2.0 | 2025-10-12 | 1.60 | Stable/low churn |
| krilla 0.8.2, krilla-svg 0.8.1 | LaurenzV/krilla @ `krilla-v0.8.2` | 3ffdf0588cf98050aad6edba51ca70162e1fb5b5 | MIT OR Apache-2.0 | 2026-06-04 | **1.92** | Active (Typst) |
| svg2pdf 0.13.0 | typst/svg2pdf @ `v0.13.0` | ccab6d7a3081f512d412dfef456caed2caf3a698 | MIT OR Apache-2.0 | 2025-03-04 | — | **Stale**: still on usvg 0.45 and was replaced by krilla-svg in Typst |
| encoding_rs 0.8.42 | hsivonen/encoding_rs @ `v0.8.42` | a155adc7271c9e507556d053c95b459186671d2a | (Apache-2.0 OR MIT) AND BSD-3-Clause | 2026-09-24 | 1.88 | Active |
| url 2.5.8, data-url 0.3.2, percent-encoding 2.3.2 | servo/rust-url @ `v2.5.8` | d6ea13c5f8e7e6e627f6390161b3e185bda5e5ce | MIT OR Apache-2.0 | 2026-01-05 | 1.63 / 1.51 | Active |
| flate2 1.1.10 | rust-lang/flate2-rs @ `1.1.10` | ed93d4fc60eaf876c6aded741bf992d524551930 | MIT OR Apache-2.0 | 2026-08-26 | 1.67 | Active |
| miniz_oxide 0.9.1 | Frommi/miniz_oxide @ HEAD | cdd7ddd56cf57a6255203bb9f5c6a92bf1144bbf | MIT OR Zlib OR Apache-2.0 | 2026-10-14 | — | Active; `#![forbid(unsafe_code)]` |
| zlib-rs 0.6.8 | trifectatechfoundation/zlib-rs @ HEAD | 7909c0fc48f5d29f6610770e31d6f0c924f9ec3b | Zlib (**UNVERIFIED**) | 2026-09-17 | 1.75 | Active; ~469 unsafe sites (SIMD) |
| brotli-decompressor 6.1.0 | dropbox/rust-brotli-decompressor @ HEAD | 910099df8c358e58367593047f6b758920076ed6 | BSD-3-Clause/MIT | 2026-10-11 | — | Active |
| wuff 0.2.9 | nicoburns/wuff @ HEAD (post-0.2.9) | 02a1f4933cbc88c293bf5eddc4ca731ea906106f | MIT | 2026-09-08 | 1.85 | Active (Blitz author) |
| serde_json 1.0.154 | serde-rs/json @ HEAD | 20572a6d066958542d79cdd6cf1a7cd9f0c8e1f8 | MIT OR Apache-2.0 | 2026-10-11 | 1.71 | Active |
| minijinja 3.0.0 | mitsuhiko/minijinja @ HEAD (just after tag `3.0.0` c1e7e23) | 31d761dad763305baf1c02971a4168ea68de7338 | Apache-2.0 | 2026-10-13 | 1.70 | Very active |
| tera 2.4.0 | Keats/tera @ `v2.4.0` | 6ead3c0ffa1e731f58694f94130253a559da68f4 | MIT | 2026-09-11 | edition 2024 | Active (v2 is a rewrite) |
| upon 0.11.0 | rossmacarthur/upon @ `0.11.0` | 9361a3da0341a69c7e700cd50e61cd17f8612246 | MIT OR Apache-2.0 | 2026-07-25 | 1.66 | Active, small |
| handlebars 6.4.4 | sunng87/handlebars-rust @ `v6.4.4` | ddcc3324c43b5d9eef91ab57c5a13364390ee206 | MIT | 2026-08-12 | 1.85 | Active |
| mustache 0.9.0 | (index only) | — | — | published 2018-02-12 | — | **Abandoned** (still on `log ^0.3`) |
| hypher 0.1.8 / hyphenation 0.8.4 | typst/hypher @ HEAD d81cc506 / index only | d81cc506416bffef2a75ee2dc969d4b41bc36613 | MIT OR Apache-2.0 / — | 2026-09-17 / published 2021-08-19 | 1.64 / — | hypher active; hyphenation stale |
| string_cache 0.11.0 | servo/string-cache @ HEAD | 5f845e2cdf504e76a53d6827a6f6d4bfcced1c93 | — | 2026-09-14 | 1.85 | Active (dependency of markup5ever) |

---

## 1. HTML parsing

### 1.1 html5ever 0.40.1 / markup5ever 0.40.0: the parser to use

**Dependencies** (index): html5ever needs `log`, `markup5ever ^0.40` and `memchr`. markup5ever needs `log`, `tendril ^0.5` and `web_atoms ^0.3`. web_atoms needs `phf 0.14` and `string_cache 0.11`, which uses `parking_lot` for its global dynamic-atom set (`string-cache/src/dynamic_set.rs:10,45`; entries are refcounted, `:29`). The tree is small and contains no C.

**Unsafe:** 4 sites in `html5ever/src`, 1 in `markup5ever` and 120 in `tendril`. Tendril is the old, unsafe-heavy string buffer type, and it is the main audit concern.

**Fuzzing:** `html5ever/fuzz/fuzz_targets/fuzz_document_parse.rs` exists.

#### TreeSink: current signature (verified)

`markup5ever/interface/tree_builder.rs:133-298`. All mutating methods now take `&self`, so the sink must use interior mutability (`RefCell`/`Cell`).

```rust
pub trait TreeSink {
    type Handle: Clone;
    type Output;
    type ElemName<'a>: ElemName where Self: 'a;          // GAT; e.g. Ref<'a, QualName>
    fn finish(self) -> Self::Output;
    fn parse_error(&self, msg: Cow<'static, str>);
    fn get_document(&self) -> Self::Handle;
    fn elem_name<'a>(&'a self, target: &'a Self::Handle) -> Self::ElemName<'a>;
    fn create_element(&self, name: QualName, attrs: Vec<Attribute>, flags: ElementFlags) -> Self::Handle;
    fn create_comment(&self, text: StrTendril) -> Self::Handle;
    fn create_pi(&self, target: StrTendril, data: StrTendril) -> Self::Handle;
    fn append(&self, parent: &Self::Handle, child: NodeOrText<Self::Handle>);
    fn append_based_on_parent_node(&self, element: &Self::Handle, prev_element: &Self::Handle, child: NodeOrText<Self::Handle>);
    fn append_doctype_to_document(&self, name: StrTendril, public_id: StrTendril, system_id: StrTendril);
    fn mark_script_already_started(&self, _node: &Self::Handle) {}          // default no-op
    fn pop(&self, _node: &Self::Handle) {}                                   // default no-op; "element closed" hook
    fn get_template_contents(&self, target: &Self::Handle) -> Self::Handle;
    fn same_node(&self, x: &Self::Handle, y: &Self::Handle) -> bool;
    fn set_quirks_mode(&self, mode: QuirksMode);
    fn append_before_sibling(&self, sibling: &Self::Handle, new_node: NodeOrText<Self::Handle>);
    fn add_attrs_if_missing(&self, target: &Self::Handle, attrs: Vec<Attribute>);
    fn associate_with_form(&self, ..) {}                                     // default no-op
    fn remove_from_parent(&self, target: &Self::Handle);
    fn reparent_children(&self, node: &Self::Handle, new_parent: &Self::Handle);
    fn is_mathml_annotation_xml_integration_point(&self, _: &Self::Handle) -> bool { false }
    fn set_current_line(&self, _line_number: u64) {}
    fn allow_declarative_shadow_roots(&self, _: &Self::Handle) -> bool { true }
    fn attach_declarative_shadow(&self, ..) -> bool { false }                // default: no shadow DOM
    fn maybe_clone_an_option_into_selectedcontent(&self, option: &Self::Handle) { _ = option; }
}
```

**Arena DOM pattern.** scraper (`scraper/src/html/tree_sink.rs:14-27`) and Blitz (`blitz-html/src/html_sink.rs:170-190`) both do the same thing:

- `struct Sink(RefCell<Arena>)` with `type Handle = NodeId` (a `u32`/`usize` index).
- `type ElemName<'a> = Ref<'a, QualName>`.
- `parse_error` pushes onto a `RefCell<Vec<_>>`.

recto should do the same: one `Vec<Node>` arena with first-child/next-sibling/parent indices, which is cache-friendly and deterministic. Implementation notes:

- **Text merging:** `append` and `append_before_sibling` must merge adjacent text (trait docs, `:193-196, :233-241`).
- **`<template>`:** when `ElementFlags.template` is set (`:46-55`), allocate a separate DocumentFragment node and return it from `get_template_contents`. Template contents are inert, so layout never walks them. The fragment only needs to exist so the tree builder can append into it.
- **Shadow DOM:** the default `attach_declarative_shadow -> false` means `<template shadowrootmode>` stays a plain template, which is fine for v1.
- **Quirks mode:** the tree builder calls `set_quirks_mode(Quirks | LimitedQuirks | NoQuirks)` from the DOCTYPE (`QuirksMode` enum `:36-44`). Store it on the document. The selector matcher needs it for case-insensitive class/id matching in quirks mode (`MatchingContext::new(.., quirks_mode, ..)`, `selectors/context.rs:200-207`).

**Options** (`html5ever/src/tree_builder/mod.rs:47-75`, `tokenizer/mod.rs:73-107`):

- `TreeBuilderOpts { exact_errors, scripting_enabled, iframe_srcdoc, drop_doctype, quirks_mode }`. **`scripting_enabled` defaults to `true`**, which makes `<noscript>` content a single text node. recto executes no JS, so it **must set `scripting_enabled: false`** so that `<noscript>` content is parsed and rendered. Blitz does this (`blitz-html/src/html_sink.rs:109,149`).
- `TokenizerOpts { exact_errors, discard_bom (default true), profile, initial_state, last_start_tag_name }`.

**Error reporting and line numbers:**

- Line only, no column. The tokenizer tracks `current_line` (`tokenizer/mod.rs:183,279`) and passes it with every token. The tree builder calls `sink.set_current_line(n)` when the line changes (`tree_builder/mod.rs:477-479`).
- To build diagnostics, record the last line in a `Cell<u64>` and attach it in `parse_error`.
- With `exact_errors: false` the messages are coarse. With `true` they are more detailed but the tokenizer is slower: it takes the char-by-char path (`tokenizer/mod.rs:282-317,405`).
- No column or byte offset is exposed. If we want them, we need a small wrapper that counts or a patch (**UNVERIFIED** whether a fork would be accepted upstream).

**Encoding:** html5ever **does not decode bytes**.

- `Parser::from_utf8()` wraps the parser in a lossy UTF-8 decoder (`driver.rs:144-149`).
- `<meta charset>` and `http-equiv=content-type` are recognised by the tree builder (`tree_builder/rules.rs:192-216`) and surface as `TokenizerResult::EncodingIndicator(label)` (`markup5ever/interface/mod.rs:65-73`). However, the stock driver loop ignores everything except `Done` (`driver.rs:150-160`, `// FIXME: Properly support </script> and encoding indicators somehow.`).
- recto must therefore do its own WHATWG encoding sniff before parsing:
  1. Check for a BOM with `encoding_rs::Encoding::for_bom` (`encoding_rs/src/lib.rs:2921`).
  2. Otherwise use the transport/CLI override.
  3. Otherwise run our own *prescan* of the first 1024 bytes for `<meta charset>` (≈150 lines, per the HTML spec "prescan a byte stream").
  4. Otherwise default to UTF-8. This deliberately differs from browsers' windows-1252 default; document it.
- Then decode with `Encoding::decode_with_bom_removal` (`:3086`) and feed `parse_document(sink, opts).one(StrTendril::from(text))`.
- Optional: drive the `Tokenizer` manually and restart on `EncodingIndicator` if the prescan missed it. Probably not worth it.

**Fragment parsing:** `parse_fragment` and `parse_fragment_for_element` (`driver.rs:59,81`) are useful for template partials or a header/footer HTML option (wkhtmltopdf `--header-html`).

**Limits:** html5ever has **no nesting-depth or node-count limit** (no depth/limit constants in `tree_builder/*.rs`). Deep `<div>` nesting must be capped by our sink, for example by refusing to nest deeper than N (Chromium's parser caps at 512 — **UNVERIFIED**) and appending to the deepest allowed ancestor instead. Every recursive layout and style walk must then be bounded by the same N.

**Determinism:** attributes arrive as `Vec<Attribute>` in source order and the builder emits no hash-ordered output, so the result is deterministic. Atoms come from a global interner, but their identity does not affect output.

**Performance:** no benchmark numbers verified here (**UNVERIFIED**). html5ever is used in Servo and Blitz production paths. Its `tendril` buffers avoid copying.

### 1.2 markup5ever_rcdom: do not use

- `rcdom/Cargo.toml` has `publish = false`, and the description is "Basic, unsupported DOM structure for use by tests".
- `rcdom/README.md`: "not intended to be a production-quality DOM implementation, and has not been fuzzed or tested against arbitrary, malicious, or nontrivial inputs. No maintenance or support…".
- On crates.io the last official release is 0.3.0 (html5ever 0.27). Later entries are `…+unofficial` re-uploads by a third party (index: `0.39.0+unofficial`).
- Verdict: test reference only. Its `Rc<RefCell>` graph is also the wrong shape for us.

### 1.3 scraper 0.27.0

- Built on ego-tree (`ego-tree ^0.11`). It is a good **reference implementation** of a `TreeSink` plus a `selectors::Element` impl (`scraper/src/element_ref/element.rs:13-150`).
- Features:
  - `errors` (default) collects `Vec<Cow<str>>` (`html/mod.rs:29-31`).
  - `deterministic` switches attributes from `Vec` to `IndexMap` (`node.rs:211-218`).
- It pins **html5ever ^0.39, selectors ^0.38, cssparser ^0.37** (index), one release behind the stylo-0.22 set. Adding it would duplicate the parser crates.
- Verdict: copy the pattern, do not depend on it.

### 1.4 Other HTML options

| Crate | What it is | Verdict |
|---|---|---|
| **html5gum 0.8.4** | WHATWG-compliant **tokenizer only** (README). The `tree-builder` feature delegates tree building to **html5ever ^0.29** (index), an old version. `#![forbid(unsafe_code)]`; AFL fuzz feature. | No. We need tree construction (adoption agency, foster parenting), which html5gum does not do itself. |
| **tl 0.7.8** | Fast, non-spec parser. README: "does *not* strictly follow the full specification… silently ignores tags that are invalid… large chunks of the document do not appear". 51 unsafe sites. Last commit 2024-01. | No. Wrong results on real-world HTML, and stale. |
| **lol_html 3.0.1** | Streaming rewriter with a CSS-selector API (Cloudflare Workers). Uses `encoding_rs` and `selectors ^0.37`/`cssparser ^0.36`. `#![forbid(unsafe_code)]` in `src/lib.rs`. Builds no DOM. | No for parsing. Possibly useful later for pre-render URL rewriting in server mode, but html5ever plus our DOM already covers that. |
| **Blitz** (`blitz-dom` 0.2.4 stable, 0.3.0-beta.3 at HEAD) | A whole browser engine: html5ever 0.40 sink, stylo 0.22, taffy, parley, `image =0.25.6` (exact pin), usvg. Workspace pins `html5ever = "0.40.1"`, "needs to match stylo web_atoms version" (`blitz/Cargo.toml:70-72`). | Do not depend on it, for size, scope, and because it has no paged media (see §2.4). It is a useful reference for wiring html5ever and stylo/selectors together (`blitz-dom/src/stylo.rs`, 1518 lines, implements `TNode`, `TElement`, `selectors::Element`). |

**xml5ever 0.40.0** (XHTML input) uses the same `TreeSink`, so one arena sink serves both. Call `xml5ever::driver::parse_document(sink, XmlParseOpts)` (`xml5ever/src/driver.rs:23-44`). It is an *error-tolerant* "XML5" parser, not a validating XML 1.0 parser, which suits `.xhtml` input. Named character references are handled (`tokenizer/char_ref/mod.rs:130`). Blitz uses it the same way (`html_sink.rs:132`).

---

## 2. CSS

### 2.1 cssparser 0.38.0: the tokenizer and rule framework to use

**Dependencies:** `dtoa-short`, `itoa`, `smallvec`, and optionally `cssparser-macros`/`phf` (the `fast_match_byte` feature), `serde`, `malloc_size_of`. 22 unsafe sites. Fuzz targets are in `fuzz/fuzz_targets`.

**Public API** (`src/lib.rs:70-87`):

- `Parser`, `ParserInput`, `Token`, `SourceLocation`, `SourcePosition`.
- `StyleSheetParser`, `RuleBodyParser`, and the traits `AtRuleParser`, `QualifiedRuleParser`, `DeclarationParser`, `RuleBodyItemParser` (`rules_and_declarations.rs:25,68,156,216`).
- `parse_important`, `parse_one_declaration`, `parse_nth`, `ToCss`, `serialize_*`, `UnicodeRange`, `color` module.

**What it gives us:**

- **Arbitrary at-rules and properties:** an `AtRuleParser` impl sees every at-rule name, so `@page :first { @top-left { … } }` is ours to define. We parse `@page` and the 16 margin at-rules with nested `RuleBodyParser`s.
- **Source locations:** `SourceLocation { line: u32 /*0-based*/, column: u32 /*1-based, UTF-16 units*/ }` (`tokenizer.rs:579-586`). `Parser::current_source_location()` (`parser.rs:430`) works per declaration, which beats lightningcss (§2.3). `current_source_map_url`/`current_source_url` exist (`:439,448`).
- **Stylesheet encoding:** `cssparser::stylesheet_encoding::<E: EncodingSupport>(css, protocol_label, env_encoding)` (`from_bytes.rs:32-40`) implements the css-syntax "determine fallback encoding" (BOM, `@charset`). We supply a ~15-line `EncodingSupport` impl over `encoding_rs`.

**Determinism:** pure function of the input.

### 2.2 selectors 0.41.0 (published from `servo/stylo/selectors`)

The crate is published from the stylo repo (`stylo/selectors/Cargo.toml`: `name = "selectors"`, `version = "0.41.0"`, MPL-2.0).

**Dependencies:** `bitflags`, `cssparser ^0.38`, `derive_more 2`, `log`, `new_debug_unreachable`, `precomputed-hash`, `rustc-hash`, `servo_arc 0.5`, `smallvec`; `to_shmem` is optional. 10 unsafe sites. No fuzz dir. Around 9k lines.

**`Element` trait** (`selectors/tree.rs:46-185`), required methods:

- Tree navigation: `opaque`, `parent_element`, `parent_node_is_shadow_root`, `containing_shadow_host`, `is_pseudo_element`, `prev_sibling_element`, `next_sibling_element`, `first_element_child`.
- Name and attribute tests: `is_html_element_in_html_document`, `has_local_name`, `has_namespace`, `is_same_type`, `attr_matches`, `has_attr_in_no_namespace` (signature at `:98`).
- Pseudo-classes and pseudo-elements: `match_non_ts_pseudo_class`, `match_pseudo_element`, `apply_selector_flags`.
- Misc: `is_link`, `is_html_slot_element`, `has_id`, `has_class`, `has_custom_state`, `imported_part`, `is_part`, `is_empty`, `is_root`, `add_element_unique_hashes(&self, &mut BloomFilter) -> bool`.
- Defaults exist for `pseudo_element_originating_element`, `assigned_slot` and `ignores_nth_child_selectors`.
- scraper's full impl (`element.rs`) is about 140 lines, so it is a small job.

**`SelectorImpl`** (`parser.rs:~230-255`) needs the associated types `ExtraMatchingData`, `AttrValue`, `Identifier`, `LocalName`, `NamespaceUrl`, `NamespacePrefix`, `BorrowedNamespaceUrl`, `BorrowedLocalName`, `NonTSPseudoClass` and `PseudoElement`. `PrecomputedHash` is required on atoms, so web_atoms' `LocalName`/`Namespace` fit directly.

**Parser hooks:** `selectors::parser::Parser<'i>` (`parser.rs:273-370`) has opt-in hooks that **all default to `false`**: `parse_nth_child_of`, `parse_is_and_where`, `parse_has`, `parse_slotted`, `parse_part`, `parse_host` and `parse_parent_selector`. recto must override them to return `true` for `:is/:where`, `:nth-child(… of S)` and `:has`. We also implement `parse_non_ts_pseudo_class` (`:link`, `:hover`→never, `:lang()`, `:dir()`, and so on) and `parse_pseudo_element` (`::before`, `::after`, `::marker`, `::first-line`, `::first-letter`, and later `::footnote-call`/`::footnote-marker`).

**Matching** (`matching.rs:123,260`):

```rust
pub fn matches_selector<E: Element>(
    selector: &Selector<E::Impl>,
    offset: usize,
    hashes: Option<&AncestorHashes>,
    element: &E,
    context: &mut MatchingContext<E::Impl>,
) -> bool
```

and `matches_selector_list`. The context is built with `MatchingContext::new(MatchingMode, Option<&BloomFilter>, &mut SelectorCaches, QuirksMode, NeedsSelectorFlags, MatchingForInvalidation)` (`context.rs:200-207`).

**Caches and specificity:**

- `SelectorCaches { nth_index: NthIndexCache, relative_selector: RelativeSelectorCache, relative_selector_filter_map }` (`context.rs:121-128`) caches `:nth-*` and `:has`.
- Bloom filter: `pub type BloomFilter = CountingBloomFilter<BloomStorageU8>` with 12-bit keys (`bloom.rs:12-19`). The caller maintains it during a DFS: push the ancestor's hashes on descent and pop on ascent. Stylo does exactly this.
- `Selector::specificity() -> u32` packs id/class/element counts into 10-bit fields (`builder.rs:243-281`, `parser.rs:882`).

**What selectors does *not* provide:**

- A rule map or index (bucketing selectors by rightmost id/class/tag). Stylo has `SelectorMap`; we write our own, roughly 200 lines.
- The cascade, origin and importance ordering, `@layer`, inheritance, computed values.

### 2.3 lightningcss 1.0.0-alpha.72: not suitable as our CSS model

1. **It is a parser, minifier and transpiler, not a style engine.** It has no cascade and no computed values. The only mentions of specificity are in minifier rule-merging (`src/rules/mod.rs:765-769`) and a TODO (`context.rs:94`).
2. **`@page` support is good**:
   - `PageRule { selectors, declarations: DeclarationBlock, rules: Vec<PageMarginRule>, loc: Location }` (`src/rules/page.rs:162-174`).
   - `PageMarginBox` enumerates all 16 margin boxes (`:82-…`).
   - `PageMarginRule { margin_box, declarations, loc }` (`:132-140`).
3. **Paged-media and document properties are mostly *not* typed:**
   - The property table in `src/properties/mod.rs` has ~349 entries but **no** `content`, `counter-reset`/`counter-increment`, `quotes`, `float`, `break-before/after/inside`, `orphans`, `widows`, `page`, `size`, `column-*`, `table-layout`, `border-collapse`, `string-set` or `bookmark-*`.
   - Under "css-break-3" there is only `box-decoration-break` (`:1520-1521`).
   - Unknown properties become `Property::Custom(CustomProperty)` with a raw `TokenList` (module docs `:81-89`, `:693-724`). We would still have to parse `content: element(x) target-counter(attr(href url), page)`, `running()`, `string-set` and similar ourselves.
4. **Source locations are per rule only.** `Location { source_index, line /*0-based*/, column /*1-based UTF-16*/ }` (`rules/mod.rs:120-128`). `DeclarationBlock` is just `{ important_declarations: Vec<Property>, declarations: Vec<Property> }` (`declaration.rs:61-68`), with no per-declaration location. That is weaker for diagnostics than raw cssparser.
5. **Footprint:**
   - About 95k lines of Rust in `src/` plus a vendored fork of selectors (`parcel_selectors 0.28.3`, `path = "./selectors"`) on **cssparser 0.37**, which would duplicate our cssparser 0.38 and selectors 0.41.
   - Default features are `bundler`, `nodejs` and `sourcemap` (`Cargo.toml [features]`). These pull `dashmap`, `rayon` and `parcel_sourcemap`, so `default-features = false` would be mandatory.
   - Non-optional deps include `ahash`, `indexmap`, `itertools 0.10`, `lazy_static`, `data-encoding`, `pathdiff`, `const-str`, `pastey`. `getrandom` is wasm32-only (`Cargo.toml:97-98`).
   - 18 unsafe sites (`values/string.rs` transmutes). No fuzz dir found.
6. Every published version is `1.0.0-alpha.N`, so semver gives no stability promise.

**Verdict:** do not use lightningcss as recto's CSS model. Its typed values cover browser-UI properties we don't need, and miss half of the ones we do. Its `@page` grammar is a useful *reference* for our own parser.

### 2.4 stylo 0.22.0: not feasible for recto

`servo/stylo` publishes `stylo` (dir `style/`), `stylo_traits`, `stylo_dom`, `stylo_atoms`, `stylo_static_prefs`, `stylo_derive`, `selectors`, `servo_arc`, `to_shmem` (README "Crates"). Blitz consumes them under renamed deps (`blitz/Cargo.toml:61-66`).

**Blockers verified in source:**

1. **`@page` is Gecko-only.**
   - `stylesheets/rule_parser.rs:290`: `"page" if cfg!(feature = "gecko") => Self::Page`.
   - Margin at-rules, `rule_parser.rs:303`: `if cfg!(feature = "gecko") && crate::pref!("layout.css.margin-rules.enabled")`.
   - In `servo` mode (the only mode usable outside Firefox), `@page` is dropped entirely.
2. **The paged properties are Gecko-engine-only.** In `style/properties/longhands.toml`, `break-after`, `break-inside`, `page` and `size` all have `engine = "gecko"`. `orphans` and `widows` are listed only in `counted_unknown_properties.py:10-11`, meaning they are not implemented at all. `string-set`, `bookmark-*` and `running()` are absent.
3. **The `gecko` feature requires Gecko bindings** (`mozbuild`, `nsstring`, `gecko_*` features in the index entry) and is not buildable standalone (**UNVERIFIED** in detail, but implied by the deps).
4. **Build-time Python:** `style/build.rs:19-64` runs `python3` (Mako templates in `properties/*.py`). A hermetic static build then needs Python in CI, which is acceptable, but every contributor needs it too.
5. **Size:** about 137k lines in `style/`, with 514 unsafe sites. It is coupled to `rayon`, `parking_lot`, `icu_segmenter`, `app_units`, `euclid` and `string_cache`, and needs the `SharedRwLock`/`Stylist`/`Device` setup (`blitz-dom/src/document.rs:444-447`). The integration has to implement `TDocument`, `TNode`, `TShadowRoot`, `TElement` and `selectors::Element` (`blitz-dom/src/stylo.rs:238-620`) and drive `style::driver::traverse_dom` (`stylo.rs:143-153`). That is about 1.5k lines of glue for Blitz alone, and every stylo release bumps it (Blitz pins html5ever to match stylo's web_atoms, `Cargo.toml:70-72`).
6. **Generated content and counters:** stylo computes `content` and `counter-*`, but leaves counter *resolution* and page-based counters to layout. We would still need our own `@page` cascade, margin-box cascade, `string-set`, `running()`, `target-counter()`, page counters and named pages.

**Verdict:** stylo would give us selector matching, cascade and computed values for the screen properties. It would give us *none* of the paged-media layer, which is recto's core differentiator, and it costs huge binary, compile-time and audit burden plus permanent version churn. **Build our own cascade on cssparser + selectors.** The recto-specific part (paged media) has to be written either way.

### 2.5 What recto builds on top of cssparser + selectors

The subset is "the CSS real documents use", about 120–150 properties. We build:

- **Stylesheet model:**
  - Parse with `StyleSheetParser` and `AtRuleParser`/`QualifiedRuleParser` impls.
  - Support `@media` (print/screen, width/height/orientation/resolution against the page size), `@page` with selectors (`:first`, `:left`, `:right`, `:blank`, `:nth()`, named pages), 16 margin rules, `@font-face`, `@import` (restricted to the input dir), `@supports`, `@layer` (cheap), `@counter-style` (later), and `@namespace`.
  - Each declaration keeps its `SourceLocation` for diagnostics.
- **Property parsing:** a table-driven `PropertyId` enum with a parse fn per property. Shorthand expansion. `var()` with an `UnparsedValue` token list substituted at computed-value time (like lightningcss's `UnparsedProperty`). `!important`.
- **Rule index:** buckets by rightmost id, class, tag or universal selector. Matching walks the DOM in document order with a `BloomFilter` push/pop and a shared `SelectorCaches`.
- **Cascade:** origin (UA < user < author), importance, `@layer`, specificity, source order. Inline `style=""` parsed with `parse_one_declaration`.
- **Computed values:** inheritance, `inherit`/`initial`/`unset`/`revert`, `em`/`rem`/`%` resolution (layout-dependent percentages deferred), colors via `cssparser::color`, and our own GCPM values: `string-set`, `content: element()/string()/counter(page)/target-counter()/target-text()/leader()`, `position: running()`, `bookmark-level/label/state`, `page`, `break-*`, `orphans`, `widows`, `footnote` (later).
- **UA stylesheet** for HTML, adapted from the HTML spec rendering section for print.

**Determinism:** use `Vec`/`IndexMap` everywhere and `rustc-hash`/`FxHashMap` only for lookups, never for iteration that affects output.

---

## 3. Images

### 3.1 image 0.25.10: the decoding façade (pinned features)

**Dependencies and features** (index):

- Mandatory deps are `bytemuck`, `byteorder-lite`, `num-traits` and, new and **non-optional**, `moxcms ^0.8` (pure-Rust color management; used for CICP conversion in `metadata/cicp.rs:94,174`). MSRV is **1.88**.
- `default = ["rayon", "default-formats"]`, and `default-formats` includes `avif` (→ `ravif`, an encoder), `exr`, `tiff`, `dds`, `hdr`, `qoi`, and others.
- Codec features:
  - `jpeg = ["dep:zune-core", "dep:zune-jpeg"]`
  - `png = ["dep:png"]`
  - `gif = ["dep:gif", "dep:color_quant"]`
  - `webp = ["dep:image-webp"]`
  - `bmp = []`, `ico = ["bmp", "png"]`
  - `avif-native = ["dep:mp4parse", "dep:dav1d"]`. AVIF *decoding* needs dav1d, which is C, so it is excluded.
- **Use** `default-features = false, features = ["png", "jpeg", "gif", "webp", "bmp"]`. Optionally add `"ico"` for favicons. Leave out `rayon` for deterministic, single-threaded, low-memory decoding; we parallelise at page level if at all.

**Limits** (`io/limits.rs:33-75`):

- `Limits { max_image_width: Option<u32>, max_image_height: Option<u32>, max_alloc: Option<u64> }`.
- `Default` sets **`max_alloc: Some(512 MiB)`** and no width/height cap. `Limits::no_limits()` exists.
- Apply with `ImageReader::limits(l)` (`io/image_reader_type.rs:137`) or `ImageDecoder::set_limits` (`io/decoder.rs:115`). Per-codec support exists (png `codecs/png.rs:264`, jpeg `codecs/jpeg/decoder.rs:168`, gif `:102`, tiff).
- recto should set something like `max_image_width = max_image_height = 16384` and `max_alloc` derived from the job's memory budget, for example 128 MiB per image.

**Metadata APIs** (`io/decoder.rs:22-60`):

- `ImageDecoder::icc_profile()`, `exif_metadata()`, `xmp_metadata()`, `iptc_metadata()`, and `orientation() -> Orientation`. The default `orientation()` parses the EXIF chunk via `Orientation::from_exif_chunk` (`metadata.rs:84`).
- Implemented for JPEG (`codecs/jpeg/decoder.rs:86-140`), PNG (icc + exif, `codecs/png.rs:181-185`), WebP (icc, exif, orientation, `codecs/webp/decoder.rs:68-95`) and GIF (icc, `codecs/gif.rs:219`).
- `DynamicImage::apply_orientation(Orientation)` (`images/dynimage.rs:1161`).
- So **EXIF orientation needs no extra crate** (`kamadak-exif` is not needed). CSS `image-orientation: from-image` is the default, so call `orientation()` and apply the rotation in the PDF transform rather than re-encoding the pixels. For JPEG passthrough this is mandatory, because we cannot rotate the DCT data.

### 3.2 JPEG passthrough (DCTDecode) and header parsing

**Use `zune-jpeg` directly** for headers. It is the same crate `image` uses:

- `JpegDecoder::new(bytes)` then `decode_headers()` (`zune-jpeg/src/decoder.rs:1523,3071`) give `info() -> ImageInfo { width, height, components, sof: SOFMarkers, x_density, y_density, exif_data, xmp_data, iptc_data, … }` (`:3181-3211`).
- Also `icc_profile()` (assembles APP2 chunks, `:2395`), `exif()` (`:2449`), `input_colorspace()` (`:1864`).

**Prior art:** krilla does exactly this. `krilla/src/graphics/image.rs:592-646` reads `decode_headers`, `dimensions` and the colorspace, then emits the raw bytes as a `DCTDecode` stream (`stream.rs:151`) with `invert_cmyk` for `ColorSpace::CMYK | YCCK` (`:640-646`). That is the usual Adobe-APP14 inverted-CMYK convention.

**Checks we need:**

- **Reject or transcode** SOF types that PDF readers handle poorly: arithmetic coding (SOF9–11) and lossless (SOF3). Progressive (SOF2) is fine for PDF 1.3 and later.
- Handle 12-bit JPEGs.

zune-jpeg facts:

- The crate has 83 unsafe sites, all SIMD IDCT/colour code.
- `src/lib.rs:280` reads `#![cfg_attr(not(any(feature = "x86", feature = "neon")), forbid(unsafe_code))]`, so with the SIMD features off it is unsafe-free.
- However, `image` depends on `zune-jpeg` **with default features** (index: no `default-features = false`), which include `x86` and `neon`. Cargo feature unification therefore turns SIMD on whenever `image/jpeg` is enabled.
- Fuzz targets: `fuzz/fuzz_targets/decode_buffer.rs`, `fuzz_idct.rs`, `decode_incremental`.

**jpeg-decoder 0.3.2:** README says "in maintenance mode as image-rs seeks to move over to the zune-jpeg crate". Do not use it.

### 3.3 PNG / GIF / WebP

**png 0.18.1:**

- Pure Rust and `#![forbid(unsafe_code)]` (`image-png/src/lib.rs`).
- Deps: `fdeflate`, `flate2`, `miniz_oxide`, `crc32fast`, `bitflags`. The `zlib-rs` feature exists.
- `Decoder::new_with_limits` and `set_limits` (`src/decoder/mod.rs:132,177`), `icc_profile()` and `exif_metadata()` (`:643-648`).
- For PDF we can sometimes pass IDAT through as `FlateDecode` with PNG predictors (non-interlaced, ≤8 bpc, no alpha). Otherwise decode, split alpha into an SMask and re-deflate. That is a PDF-writer decision (see the PDF report).

**gif 0.14.2:** decode the first frame only.

**image-webp 0.2.4:**

- Pure Rust, `#![forbid(unsafe_code)]`, lossy and lossless.
- Its last commit (2025-08-26) is older than the rest of the image stack, but it is the only pure-Rust WebP decoder and is maintained by image-rs.

**BMP** is built into `image` (no extra dependency). **AVIF, HEIC and JPEG XL** are not supported in v1, since dav1d is C. JPEG XL could later come from a pure-Rust decoder (`jxl-oxide`, **UNVERIFIED**, not inspected).

**ICC profiles:** extract them with the APIs above and embed as an `ICCBased` color space in PDF. For PDF/A an OutputIntent sRGB profile is needed, which belongs to the PDF report. `moxcms` arrives transitively via image if we ever need to convert CMYK or other color spaces to sRGB.

**Header-only sizing:** `imagesize 0.15.0` (zero deps) reads dimensions without decoding, which is useful for layout before decoding. usvg uses it, and krilla uses 0.14.

---

## 4. SVG: resvg / usvg 0.48.1, tiny-skia 0.12.0, roxmltree 0.21.1

### 4.1 usvg Options and security

**`usvg::Options`** (`crates/usvg/src/parser/options.rs:17-100`): `resources_dir`, `dpi`, `font_family`, `font_size`, `languages`, `shape_rendering`, `text_rendering`, `image_rendering`, `default_size`, `image_href_resolver`, `font_resolver` (feature `text`), `fontdb: Arc<fontdb::Database>` (feature `text`), and `style_sheet: Option<String>`. The last one injects CSS; we use it to pass the HTML context's `color` for `currentColor`.

**Security: the default resolver reads arbitrary files.**

- `ImageHrefResolver::default_string_resolver()` (`parser/image.rs:80-112`): "treats an input string as a file path and tries to open", via `std::fs::read(&path)`. `get_abs_path` keeps absolute paths absolute, and `..` is not checked.
- recto **must** replace `resolve_string` with a closure that goes through our sandboxed resource loader (input-dir confinement, no network unless allowed). It must also replace `resolve_data`: the default `ImageHrefDataResolverFn` decodes data URLs (`:15-21`), and we want our size limits applied.
- Nested SVG images are parsed via `Tree::from_data_nested`. That path already disables external `resolve_string` (`parser/mod.rs:125-151`) but forwards `resolve_data`. Recursion through nested `data:` SVGs is therefore bounded only by input size. Our `resolve_data` should count the nesting depth.

**Limits found:**

- More than 1,000,000 SVG nodes gives `ElementsLimitReached` (`parser/svgtree/parse.rs:417`, `parser/mod.rs:40-41`).
- Element nesting deeper than 1024 is an error (`svgtree/parse.rs:182-183`).
- Self-recursive `<use>`/patterns are detected (`svgtree/parse.rs:625-639, 748, 794`).
- **svgz:** `decompress_svgz` uses `GzDecoder::read_to_end` with **no output cap** (`parser/mod.rs:180-189`), so it is a gzip-bomb vector. Either disable the `svgz` feature or decompress ourselves with a cap and pass plain bytes.
- **XML:** `Tree::from_str` uses `roxmltree::ParsingOptions { allow_dtd: true, ..Default }` (`parser/mod.rs:160-163`), and `nodes_limit` defaults to `u32::MAX` (`roxmltree/src/parse.rs:341-346`). Entity expansion is guarded by `LoopDetector`: reference depth ≤ 10 and ≤ 255 references per root reference (`roxmltree/src/parse.rs:500-540`), so billion-laughs input fails with `EntityReferenceLoop`. For tighter control, parse with `roxmltree::Document::parse_with_options(text, ParsingOptions { allow_dtd: true, nodes_limit: N, .. })` ourselves and call `usvg::Tree::from_xmltree(&doc, &opt)` (`parser/mod.rs:172`).

**CSS inside SVG:** `<style>` is parsed with **simplecss 0.2** (`svgtree/parse.rs:7,93`). It is a small CSS subset (simple selectors). It is separate from our CSS engine, which is acceptable for v1. Inline SVG embedded in HTML (`<svg>` inside the HTML DOM) must be re-serialized to a string, or converted directly, before going to usvg. Styles from the HTML stylesheet do not apply to it unless we inject them via `Options::style_sheet`.

**Text:**

- With feature `text`, usvg shapes text using **harfrust** + **skrifa** + `fontdb` (deps: `harfrust ^0.12`, `skrifa ^0.44`, `fontdb ^0.24`).
- `Text::flattened() -> &Group` gives the text as paths (`tree/text.rs:704`), and `layouted()` gives positioned spans (`:714`).
- `fontdb` features `fs`, `memmap` and `fontconfig` come in through usvg's `system-fonts`/`memmap-fonts` features, which are in usvg's **defaults**. Use `default-features = false, features = ["text"]` and fill `fontdb::Database` from our own font registry (`Database::new()` is empty).
- Note the shaper divergence: usvg uses harfrust and skrifa. If recto's text stack uses something else, two shapers get compiled in. Coordinate with the text/fonts report.

**Tree API for the PDF conversion:**

- `Tree::root() -> &Group`, `size()`, `fontdb()`, `clip_paths()`, `linear_gradients()`, … (`tree/mod.rs:1543-1690`).
- `Node = Group | Path | Image | Text` (`tree/mod.rs:906-911`).
- `ImageKind = JPEG | PNG | GIF | WEBP (raw bytes) | SVG(Tree)` (`:1470-1481`). Raster images inside SVG come back undecoded, so we route them through §3.

**Determinism:** IDs are derived with `DefaultHasher::new()` (fixed SipHash keys, `parser/converter.rs:257-261`) and `SipHasher13::new_with_keys(0, key)` (`svgtree/names.rs:697`). Both are deterministic.

**Safety:** `#![forbid(unsafe_code)]` in usvg and resvg (`src/lib.rs`).

### 4.2 Converting usvg trees to PDF vectors

- **krilla-svg 0.8.1** (`krilla/crates/krilla-svg/src/lib.rs`):
  - API: `trait SurfaceExt { fn draw_svg(&mut self, tree: &usvg::Tree, size: Size, settings: SvgSettings) -> Option<()> }` with `SvgSettings { embed_text: bool /*default true*/, filter_scale: f32 /*4.0*/ }` (`:37-60`).
  - Filters are **rasterized via `resvg::render_node`** (`filter.rs:9,73`), which is why tiny-skia and resvg come along.
  - It pins **usvg/resvg 0.47** (`krilla/Cargo.toml:43,54`), not 0.48, and krilla's MSRV is **1.92**.
  - If recto adopts krilla as its PDF writer, it must use **usvg 0.47.x** to avoid two copies.
- **svg2pdf 0.13.0:** last release 2025-03, on usvg 0.45 and pdf-writer 0.12. Typst moved the logic into krilla-svg. **Do not use.**
- **Writing our own converter:** if recto writes PDF with its own writer or pdf-writer directly, the converter is roughly 1.5–2.5k lines. Size estimate from the `krilla-svg/src/*.rs` file list (clip_path, filter, group, image, mask, path, text, util), not counted.
- The choice depends on the PDF-writer decision (separate report). Either way, **usvg is the right SVG front end**.

---

## 5. Miscellaneous crates

### 5.1 encoding_rs 0.8.42

- MSRV **1.88**. License `(Apache-2.0 OR MIT) AND BSD-3-Clause` (the BSD part covers the WHATWG index data). 180 unsafe sites (SIMD/ASCII fast paths).
- APIs used: `Encoding::for_label` (`src/lib.rs:2774`), `for_bom` (`:2921`), `decode_with_bom_removal` (`:3086`), `new_decoder_with_bom_removal` (`:3406`).
- It is the de-facto standard (Firefox) and the only option.
- `chardetng 1.0.0` (statistical detection) is **not** needed: we default to UTF-8.

### 5.2 url 2.5.8, data-url 0.3.2, percent-encoding 2.3.2

- **url:** a WHATWG URL parser. Dependency: `idna 1.1` → `idna_adapter 1.2.2` → **`icu_normalizer` + `icu_properties` 2.2** (index). That is a sizeable ICU4X data footprint (**UNVERIFIED** size). It is probably shared with the text stack, since `harfrust` optionally uses the same ICU crates. Parse every resource reference with `Url::join` against the document base. Then the sandbox checks the scheme (`file`, `data`, and `http(s)` only if enabled) and resolves `file:` paths inside the allowed root after canonicalising (symlink escape).
- **data-url:** zero dependencies. `DataUrl::process(&str)` (`data-url/src/lib.rs:72`), `mime_type()` (`:89`), `decode_to_vec()` (`:111`). Spec-compliant forgiving-base64. usvg already depends on it.
- **percent-encoding:** zero dependencies, for PDF URI actions and URL serialization.

### 5.3 Compression: flate2 1.1.10

**Backends** (index features):

- `default = ["rust_backend", "runtime_detection"]`, where `rust_backend` means `miniz_oxide ^0.9`.
- `zlib-rs = ["any_zlib", "dep:zlib-rs"]`. zlib-rs 0.6.8 is pure Rust with 469 unsafe sites (SIMD).
- `zlib`, `zlib-ng` and `cloudflare_zlib` are C. Excluded.

**miniz_oxide 0.9.1:** `#![forbid(unsafe_code)]` (`miniz_oxide/src/lib.rs:25`).

**Determinism:**

- Both backends are deterministic for a given input, level and *crate version*.
- In zlib-rs, CPU dispatch affects only the `compare256` result-equivalent fast paths (`deflate/compare256.rs:19-25`). The hash variant is chosen from `max_chain_length` only (`deflate/hash_calc.rs:11-18`), not from CPU features. Cross-architecture byte equality is therefore *likely*, but **UNVERIFIED** without a test.
- Output differs between the two backends and can change across versions. **Pin exact versions** (`=`) and add a golden-hash test on x86_64 and aarch64.

**Recommendation:**

- Use `flate2 = { version = "1.1.10", default-features = false, features = ["rust_backend"] }` for determinism and safety.
- Offer `zlib-rs` as an opt-in feature for speed on 1000-page jobs, after benchmarking (**UNVERIFIED** speed delta).
- The png crate also has its own `fdeflate` fast path for decoding.

### 5.4 WOFF / WOFF2

**wuff 0.2.9:**

- Pure Rust, MIT. A hand-port of Google's woff2. README: "verified to produce byte-identical output to Google's woff2 library for every font in google/fonts".
- `wuff::decompress_woff2(&[u8])` and a WOFF1 decoder.
- Deps: `brotli-decompressor ^5` (no_std mode), `flate2`, `bytes`.
- Anti-bomb check: `K_MAX_PLAUSIBLE_COMPRESSION_RATIO = 100.0` (`wuff/src/decompress_woff2.rs:23,88,120`).
- 12 unsafe sites, all in `wuff-capi`. No fuzz dir. Blitz uses it (`blitz-dom` feature `woff-rust = ["dep:wuff"]`).
- **Recommended.**

| Alternative | Problem |
|---|---|
| `woff2 0.3.0` | Published 2022; old `brotli ^3` (and `woff2-patched 0.4.0` is a fork). |
| `woff 0.6.3` | C (`libz-sys`, C++ woff2). Excluded. |
| `allsorts 0.17` | Has WOFF/WOFF2 support (it is Prince's font library), but default features pull C zlib (`flate2_zlib`). Heavy, so only worth it if the fonts report picks allsorts. |

Fontations (`read-fonts 0.45`, `skrifa 0.48`): no WOFF2 decoder found in the index feature lists (**UNVERIFIED**, source not inspected).

**brotli-decompressor:** 6.1.0 is current (BSD-3-Clause/MIT), but wuff 0.2.9 depends on `^5.0.0`. Let wuff bring its own version, and do not add a direct dependency unless something else needs brotli.

### 5.5 Hyphenation (brief; the text report decides)

- **hypher 0.1.8** (Typst): zero dependencies, embedded tries per language behind features, MSRV 1.64, actively maintained (2026-09-17). Preferred.
- **hyphenation 0.8.4:** last release 2021, uses `bincode 1`, `fst`, `serde`, and `pocket-resources` for embedded dictionaries. Stale.

### 5.6 serde_json 1.0.154

- The `Map` is a `BTreeMap` by default, or `IndexMap` with `preserve_order` (`json/src/map.rs:3-39`).
- **Enable `preserve_order`** so that template iteration over JSON objects follows document order. Users expect that, and it stays deterministic.
- Recursion limit is 128 by default (`de.rs:34,63`). Keep it; do not enable `unbounded_depth`.
- Has a fuzz dir. Do not enable `arbitrary_precision`, which changes the `Value` representation. Note that `float_roundtrip` is off by default.

### 5.7 Template engines for "data mode"

| | **minijinja 3.0.0** | tera 2.4.0 | upon 0.11.0 | handlebars 6.4.4 | mustache 0.9.0 |
|---|---|---|---|---|---|
| Syntax | Jinja2 (familiar to Python/WeasyPrint users) | Jinja-like, deliberately deviates (README) | Own, minimal | Handlebars | Mustache |
| License | Apache-2.0 | MIT | MIT OR Apache-2.0 | MIT | — |
| Required deps | **none** (all optional: `serde`, `indexmap`, `percent-encoding`, `unicase`, `stacker`, `v_htmlescape`, …) | `serde` (+ optional `ahash`, `indexmap`, …) | none required (`serde`, `unicode-*` default) | `derive_builder`, `pest`, `pest_derive`, `serde_json`, `thiserror`, `num-order` | `log 0.3`, `serde` |
| Filesystem access | None unless the embedder calls `set_loader(path_loader(dir))` (`src/loader.rs:443-454`) | `glob_fs` feature (off by default) | none | `dir_source` feature (off) | — |
| Auto-escaping | By template-name extension (`.html/.htm/.xml` → HTML, `src/defaults.rs:31-45`). Override with `set_auto_escape_callback` (`environment.rs:487`) | `autoescape_on(...)` (`tera.rs:202`) | **No HTML escaping by default.** The default formatter writes values raw (`fmt.rs:214-229`); we would add our own | `register_escape_fn` (HTML escape by default, **UNVERIFIED**) | — |
| Resource limits | `set_fuel(Option<u64>)` instruction budget (feature `fuel`, `environment.rs:580-596`); `set_recursion_limit` capped at 500 (`:51,651-654`); `range()` capped at 100000 (`functions.rs:422`) | Parser recursion depth 40, expression complexity 256 (`parsing/parser.rs:21-27`); component recursion 20; range ≤100k (`functions.rs:65`). No fuel | `set_max_include_depth` (default 64, `lib.rs:365-377`) | `strict_mode`; no fuel (**UNVERIFIED**) | none |
| Determinism | Value maps are `BTreeMap`, or `IndexMap` with `preserve_order` (`value/mod.rs:330-333`) | **UNVERIFIED** (HashMap use not audited) | `BTreeMap` for templates and callables | depends on serde_json | — |
| Unsafe / fuzz | 36 unsafe sites; no fuzz dir in crate | 3 unsafe; `tera/fuzz` | `#![forbid(unsafe_code)]`; `fuzz/` | 0 unsafe | — |
| Size (lines in src) | ~27.5k | ~15.5k | ~11k | ~10.8k (+pest) | — |
| Maintenance | Very active (3.0.0 released 2026-10-08) | Active (v2 rewrite) | Active, single maintainer | Active | **Abandoned 2018** |

**Recommendation: minijinja 3.0.0.**

- Features: `default-features = false, features = ["builtins", "macros", "multi_template", "serde", "fuel", "preserve_order", "json"]`. Keep `debug` (better error messages with line info) if the binary-size cost is acceptable. `adjacent_loop_items` and `loop_controls` are optional extras.
- Always set:
  - `set_fuel(Some(N))`
  - `set_recursion_limit(≤ 100)`
  - `set_auto_escape_callback(|_| AutoEscape::Html)`, so escaping is forced regardless of the template name
  - `set_undefined_behavior(Strict)` as an option, via `environment.rs:499`
  - no loader, or a loader confined to the input dir.
- Output size is not capped by fuel alone. Wrap the output writer and abort past a byte cap (**UNVERIFIED** whether minijinja exposes a streaming `render_to_write`; check before relying on it).
- Optionally offer **Handlebars-syntax compatibility** later for users coming from wkhtmltopdf/Node pipelines. Not in v1.

---

## 6. Version-alignment matrix (avoid duplicate crates)

| Family | Aligned set (verified via index deps) | Out-of-family users that would duplicate |
|---|---|---|
| Servo HTML/CSS | html5ever 0.40.1, markup5ever 0.40.0, xml5ever 0.40.0, web_atoms 0.3.0, tendril 0.5.1, string_cache 0.11.0, cssparser 0.38.0, selectors 0.41.0, servo_arc 0.5.0, precomputed-hash 0.1.1 (the stylo 0.22.0 set) | scraper 0.27 (html5ever 0.39 / selectors 0.38 / cssparser 0.37), lightningcss (cssparser 0.37 + parcel_selectors), lol_html (selectors 0.37 / cssparser 0.36) |
| image-rs | image 0.25.10 → png 0.18, zune-jpeg 0.5, gif 0.14, image-webp 0.2, moxcms 0.8 | krilla 0.8.2 uses png 0.18.1, zune-jpeg 0.5.5, gif 0.14.2, image-webp 0.2.1 (compatible) |
| SVG | usvg/resvg 0.48.1 + tiny-skia 0.12 + fontdb 0.24 + skrifa 0.44 + harfrust 0.12 | krilla-svg 0.8.1 → usvg/resvg **0.47**, fontdb **0.23**, skrifa **0.42**. Pick one usvg line for the whole workspace |
| Compression | flate2 1.1.10 → miniz_oxide 0.9 | png 0.18.1 depends on `miniz_oxide ^0.8`, `fdeflate`; usvg on `flate2 ^1.1` (two miniz_oxide majors likely, **UNVERIFIED** via lockfile) |

Note: **`cargo build` could not be run** (crate downloads are blocked), so the actual `Cargo.lock` duplication was not checked. The first workspace PR should run `cargo tree -d`.

---

## Findings that affect recto's design

1. **Use our own arena DOM as the html5ever `TreeSink`.** The sink must be `&self` with `RefCell` internals, `Handle = NodeId`, and `ElemName<'a> = Ref<'a, QualName>`. scraper and Blitz both prove the pattern. `markup5ever_rcdom` is unpublished and test-only.
2. **Set `scripting_enabled: false`** in `TreeBuilderOpts` (the default is `true`). Otherwise `<noscript>` fallbacks become raw text.
3. **We must implement HTML encoding sniffing.** html5ever ignores `<meta charset>`: it returns `EncodingIndicator`, but the stock driver drops it. Do BOM → override → our 1024-byte prescan → UTF-8 default, decoding with encoding_rs. For CSS use `cssparser::stylesheet_encoding`.
4. **Diagnostics:** HTML errors have line numbers only, through `set_current_line` plus `parse_error`. CSS has line and column (UTF-16 columns) per token through `Parser::current_source_location()`. The diagnostics format should allow the column to be optional.
5. **Neither html5ever nor our sink limits depth by default.** Cap DOM depth in the sink and use the same cap for every recursive style or layout routine. Add a total-node cap tied to the memory budget.
6. **The CSS engine is ours, on cssparser 0.38 + selectors 0.41.** Stylo cannot parse `@page`, margin rules, `break-*`, `page` or `size` outside the `gecko` feature (`rule_parser.rs:290,303`; `longhands.toml` `engine = "gecko"`), so it is unusable for paged media. lightningcss lacks typed values for about half the properties we need and has no cascade.
7. **selectors opt-ins:** our `Parser` impl must return `true` from `parse_is_and_where`, `parse_nth_child_of` and `parse_has`. We supply the `SelectorMap`-style rule index, the bloom-filter push/pop during DOM traversal, and one `SelectorCaches` per document. Pass the document's quirks mode into `MatchingContext`.
8. **Paged-media values are ours entirely:** `@page` selectors and margin boxes, `string-set`, `running()`/`element()`, `target-counter()`/`target-text()`, `counter(page/pages)`, `bookmark-*`, `leader()`, named pages. lightningcss's `rules/page.rs` is a good grammar reference.
9. **Images:** depend on `image` with exactly `png`, `jpeg`, `gif`, `webp` and `bmp`, `default-features = false` (no rayon, no avif or dav1d). Always pass explicit `Limits` (width, height, `max_alloc`). The default `max_alloc` is 512 MiB with no width or height cap.
10. **JPEG passthrough:** read headers with zune-jpeg (`decode_headers`, `info`, `icc_profile`, `exif`) and emit `DCTDecode`. Invert Adobe CMYK/YCCK, reject or transcode arithmetic and lossless SOFs, and apply EXIF orientation as a PDF matrix (`image-orientation: from-image`). krilla's `graphics/image.rs:592-646` is prior art.
11. **SVG via usvg, sandboxed:**
    - Replace both `ImageHrefResolver` closures (the default reads arbitrary files).
    - Decompress svgz ourselves with a cap (usvg has no cap), or disable the `svgz` feature.
    - Pre-parse with roxmltree and a `nodes_limit`, then call `Tree::from_xmltree`.
    - Disable usvg's `system-fonts` and `memmap-fonts` features and feed `fontdb` from our font registry.
12. **The SVG→PDF converter depends on the PDF-writer decision.** krilla-svg is the maintained option (svg2pdf is stale). It pins usvg 0.47 and MSRV 1.92, so the workspace usvg version must follow krilla's if we adopt it.
13. **Workspace MSRV floor:** the chosen set needs **≥ 1.88** (image 0.25.10, encoding_rs 0.8.42). It needs **≥ 1.92** if krilla is used.
14. **Deterministic compression:** pin flate2 and miniz_oxide exactly. Golden-hash PDFs on x86_64 and aarch64 in CI. zlib-rs is an opt-in speed feature only after a cross-architecture equality test.
15. **Templates:** minijinja with `fuel`, a recursion limit, forced HTML auto-escape, no filesystem loader, `preserve_order` (also on serde_json) and an output byte cap.
16. **Licenses:** cssparser, selectors and lightningcss are MPL-2.0 (file-level copyleft). That is fine for static linking but must appear in the NOTICE/third-party list. encoding_rs carries BSD-3-Clause for data. No GPL or LGPL anywhere in the recommended set.

## Recommendation

### Workspace dependencies (`[workspace.dependencies]`)

```toml
# HTML
html5ever    = "=0.40.1"
markup5ever  = "=0.40.0"
xml5ever     = "=0.40.0"            # XHTML input
# (tendril / web_atoms come transitively; use markup5ever's re-exports)

# CSS
cssparser    = "=0.38.0"            # default features (fast_match_byte via cssparser-macros)
selectors    = "=0.41.0"            # no features (to_shmem off)
servo_arc    = "=0.5.0"             # selectors' public types use it
precomputed-hash = "0.1.1"

# Encoding / URLs
encoding_rs  = "=0.8.42"            # default ("alloc"); consider "simd-accel" only on nightly — skip
url          = "2.5.8"
data-url     = "0.3.2"
percent-encoding = "2.3.2"

# Images
image        = { version = "=0.25.10", default-features = false, features = ["png", "jpeg", "gif", "webp", "bmp"] }
zune-jpeg    = "0.5.15"             # header parse for DCT passthrough; SIMD (x86/neon) is on anyway via image's default-feature dep
png          = "0.18.1"             # direct use for IDAT passthrough decisions
imagesize    = { version = "0.15.0", default-features = false, features = ["png", "jpeg", "gif", "webp", "bmp"] }

# SVG (if NOT adopting krilla; otherwise use =0.47.x to match krilla-svg)
usvg         = { version = "=0.48.1", default-features = false, features = ["text"] }
roxmltree    = { version = "0.21.1", default-features = false, features = ["std", "positions"] }
# resvg/tiny-skia only if we rasterize SVG filters ourselves:
# resvg      = { version = "=0.48.1", default-features = false, features = ["text"] }

# Fonts (decoding only; font stack decided in the fonts report)
wuff         = { version = "0.2.9", default-features = false, features = ["brotli", "z"] }

# Compression
flate2       = { version = "=1.1.10", default-features = false, features = ["rust_backend"] }
miniz_oxide  = "=0.9.1"             # pin for deterministic output

# Data mode
serde        = { version = "1", features = ["derive"] }
serde_json   = { version = "1.0.154", features = ["preserve_order"] }
minijinja    = { version = "3.0.0", default-features = false, features = ["builtins", "macros", "multi_template", "serde", "fuel", "preserve_order", "json", "debug"] }

# Hyphenation (defer to text report)
hypher       = { version = "0.1.8", default-features = false, features = ["english" /*, … per-language */] }
```

Do **not** depend on: markup5ever_rcdom, scraper, tl, html5gum, lol_html, blitz-*, stylo, lightningcss, jpeg-decoder, svg2pdf, woff, woff2, mustache, hyphenation, kamadak-exif, chardetng, or the `avif-native`/`dav1d` image features.

### Build ourselves

| Component | Estimated size |
|---|---|
| Arena DOM + `TreeSink` (+ depth/node caps, line tracking, `<template>` fragments, quirks flag) | ~600 lines |
| HTML encoding prescan (WHATWG "prescan a byte stream") + BOM/override logic | ~200 lines |
| `selectors::Element` + `SelectorImpl` + `selectors::parser::Parser` impls; rule index; bloom-filter DFS | ~1.2k lines |
| Stylesheet parser (at-rules incl. `@page` + 16 margin boxes, `@media` print evaluation, `@font-face`, `@import` sandboxed, `@supports`, `@layer`) | — |
| Property table + value parsers for the v1 subset incl. GCPM values; shorthand expansion; `var()` substitution | — |
| Cascade, inheritance, computed values; UA stylesheet for print | — |
| Sandboxed resource loader (URL join, scheme allow-list, root confinement, size caps) used by HTML, CSS, images, usvg resolvers and fonts | — |
| JPEG SOF/APP14 inspection policy, PNG passthrough policy, EXIF→matrix (on top of zune-jpeg, png and image) | — |
| usvg Tree → PDF converter, unless krilla-svg is adopted with the PDF writer | — |

## Open questions / UNVERIFIED items

1. **Performance:** throughput and memory figures for html5ever versus alternatives were not measured (no build possible here). Benchmark in the first spike.
2. **zlib-rs determinism and speed:** whether zlib-rs produces byte-identical output across x86_64 and aarch64, and its speed advantage over miniz_oxide for PDF content streams. Needs a test.
3. **Lockfile duplication:** actual duplicate versions (`cargo tree -d`) for the recommended set, especially miniz_oxide 0.8 vs 0.9 (png 0.18.1 vs flate2 1.1.10) and fontdb/skrifa versions between usvg and our font stack.
4. **minijinja streaming:** whether minijinja 3.0 offers `render_to_write` (streaming), for an output byte cap without buffering. Also whether its `debug` feature's binary-size cost is significant.
5. **handlebars defaults:** whether handlebars-rust escapes HTML by default (believed yes) and has any execution-limit API. Only relevant if a Handlebars compatibility mode is added.
6. **zlib-rs license:** stated as Zlib from memory. Not read from its Cargo.toml.
7. **stylo with the `gecko` feature:** buildability outside mozilla-central was not attempted. The conclusion relies on the `mozbuild`/`nsstring` optional deps in the index entry.
8. **Fontations and WOFF2:** whether fontations (read-fonts/skrifa) gained a WOFF2 decoder. The source was not inspected.
9. **html5ever error positions:** column or byte-offset reporting for parse errors would need an upstream patch. Effort not assessed.
10. **zune-jpeg version:** HEAD inspected is `0.5.16-rc2`, while the latest stable on the index is `0.5.15`. The APIs cited (`decode_headers`, `info`, `icc_profile`, `exif`) are used by krilla against `^0.5.5`, so they are assumed stable across 0.5.x.
11. **JPEG XL:** a JPEG XL decoder (e.g. `jxl-oxide`) was not evaluated.
12. **Blitz print support:** whether Blitz plans paged media. No `@page`/print handling was found in `blitz-dom/src`, but that was a grep only.
