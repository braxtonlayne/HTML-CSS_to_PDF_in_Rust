# 08 — Rust PDF writers: krilla vs pdf-writer vs printpdf (+ lopdf, svg2pdf, krilla-svg)

Date: 2026-10-14 · Topic slug: `pdf` · Author: Phase-0 research agent

Every API claim below cites a file in a source tree cloned at the tag listed here. Paths are
relative to each repo root, for example `krilla/crates/krilla/src/page.rs`. Anything I could not
check against source is marked **UNVERIFIED**.

## Sources inspected

| Crate / repo | Latest published (sparse index) | Tag / commit inspected | License | Last commit (tag / default branch) | MSRV | Maintenance assessment |
|---|---|---|---|---|---|---|
| `krilla` (LaurenzV/krilla) | 0.8.2 | `krilla-v0.8.2` @ `3ffdf0588cf98050aad6edba51ca70162e1fb5b5` | MIT OR Apache-2.0 | 2026-06-04 / `main` 2026-10-13 (`21e2578`) | 1.92 (`Cargo.toml` `rust-version`) | **Very active.** Since 0.8.2, unreleased on `main`: forms parts 1+2 (#423, #430), PNG passthrough (`from_png_native`, #435), indexed PNG (#415), custom Info fields (#419), version ID (#424), streaming image compression (#443). Typst depends on it, so there is a funded downstream. |
| `krilla-svg` | 0.8.1 | same repo/tag, `crates/krilla-svg` | MIT OR Apache-2.0 | same | 1.92 | Same as krilla. |
| `pdf-writer` (typst/pdf-writer) | 0.15.0 | `v0.15.0` @ `639214e1745f2b1ff29ad0621da151807118d7bc` | MIT OR Apache-2.0 | 2026-05-27 / `main` 2026-08-17 (`fdf0901`) | none declared (edition 2021) | Mature and slow-moving. Typst/krilla own it. |
| `printpdf` (fschutt/printpdf) | 0.12.8 | `v0.12.8` @ `6ff6bb5f808f85f39dfe1809e73277ccb2be0a0e` | MIT | 2026-09-05 / `master` 2026-10-02 | 1.88 | Active, single maintainer. Builds on lopdf and azul. |
| `lopdf` (J-F-Liu/lopdf) | 0.45.0 | `v0.45.0` @ `e6a0cfbf837de321e77b9c4ac5aed5b9f08ed143` | MIT | 2026-09-08 / `master` 2026-10-14 | 1.88 | Active. It is a reader/editor, not a typesetting writer. |
| `svg2pdf` (typst/svg2pdf) | 0.13.0 | `v0.13.0` @ `ccab6d7a3081f512d412dfef456caed2caf3a698` | MIT OR Apache-2.0 | 2025-03-04 / `main` 2026-07-10 | — | **Unmaintained.** The `main` HEAD `55723cb` commit is "This project is not maintained anymore", and the README says: "Use krilla with krilla-svg instead." |
| `subsetter` (typst/subsetter) | 0.2.6 | `v0.2.6` @ `c3f23c67bc0190587f639bda84dc0005ca3f54d5` | MIT OR Apache-2.0 | 2026-06-04 | 1.85 | Active (krilla's subsetter). |
| `xmp-writer` (typst/xmp-writer) | 0.3.3 (krilla dep) | `main` @ `61b88dd697c21ab66eb4eb4c25e2c6d16ea3c872` | MIT OR Apache-2.0 | 2026-08-07 | — | Low churn. |
| `typst-pdf` (typst/typst `crates/typst-pdf`) | 0.15.1 | `v0.15.1` @ `9dfd3a08500b7896045f907433cf7b4b02434fad` | Apache-2.0 | 2026-07-17 | 1.92 | Reference consumer of krilla. |

Sparse-index dependency lists (non-dev) at the latest versions:

- **krilla 0.8.2**:
  - Always on: base64, bumpalo, flate2, float-cmp, indexmap, pdf-writer ^0.15, rustc-hash, siphasher, skrifa ^0.42, smallvec, subsetter ^0.2.6, tiny-skia-path, xmp-writer ^0.3.3, yoke.
  - Optional: `raster-images` (png, zune-jpeg, gif, image-webp, imagesize), `simple-text` (rustybuzz), `rayon`, `comemo`, `pdf` (hayro-write).
  - Default features are `raster-images` and `simple-text`.
- **krilla-svg 0.8.1**: krilla, usvg ^0.47, resvg ^0.47, tiny-skia, fontdb ^0.23 (default features, which turns on `fs`, `memmap` and `fontconfig`), skrifa, flate2, smallvec.
- **pdf-writer 0.15.0**: bitflags, itoa, memchr, ryu. Nothing else.
- **printpdf 0.12.8**: lopdf ^0.44, allsorts(-azul) ^0.17.1, time, serde, serde_json, base64, flate2, weezl, smallvec, wasm-bindgen(-futures) (non-optional), getrandom 0.4. Optional: azul-core/css/layout 0.0.16, rust-fontconfig, image, svg2pdf ^0.13, js-sys, web-sys, xmlparser.
- **lopdf 0.45.0**: aes, cbc, ecb, md-5, sha2, rand ^0.10, getrandom, nom, flate2, brotli-decompressor, encoding_rs, indexmap, rangemap, stringprep, thiserror, weezl, log. Optional: chrono, jiff, time, image, rayon, serde, skrifa, tokio.
- **typst-pdf 0.15.1** depends on `krilla ^0.8.2` and `krilla-svg ^0.8.1`, and **not** on pdf-writer directly. The workspace `typst/Cargo.toml:79` sets `krilla = { version = "0.8.2", default-features = false, features = ["raster-images", "comemo", "rayon", "pdf"] }`.

---

## 1. API style at a glance

| | krilla 0.8.2 | pdf-writer 0.15.0 | printpdf 0.12.8 | lopdf 0.45.0 |
|---|---|---|---|---|
| Level | High-level drawing surface (fills, strokes, glyph runs, images, masks, groups) | Low-level, strongly typed object and operator writer. You allocate the `Ref`s and write each dict | Mid-level: a serde-able op list (`Op` enum) per page, plus an HTML mode through azul | Generic object model (`BTreeMap<ObjectId, Object>`) with read/modify/write |
| Entry | `Document::new_with(SerializeSettings)` → `start_page_with(PageSettings)` → `page.surface()` (`krilla/src/document.rs`, `page.rs`) | `Pdf::new()`, `Chunk`, `Content` (`pdf-writer/src/lib.rs`, `chunk.rs`, `content.rs`) | `PdfDocument { pages: Vec<PdfPage>, … }` → `serialize_pdf` (`printpdf/src/lib.rs:292`, `serialize.rs:90`) | `Document` (`lopdf/src/document.rs:19-34`) |
| Coordinate system | y-down, top-left origin. Krilla applies the flip `Transform::from_row(1,0,0,-1,0,h)` (`page.rs` `page_root_transform`) | Raw PDF user space (y-up) | PDF user space (mm/pt units helpers) | n/a |
| Resource management | Automatic: resource dicts, dedup by SipHash128 (`serialize.rs` `register_cached`, `cached_mappings`) | Manual | Semi-automatic (ids in `PdfResources`) | Manual |
| Output | `Document::finish() -> KrillaResult<Vec<u8>>` | `Pdf::finish() -> Vec<u8>`, or `finish_with_xref_stream[_and_filter]` | `serialize_pdf(&doc, &opts, &mut impl Write, &mut warnings)` through `lopdf::Document::save_to` | `save`, `save_to`, `save_with_options`, `save_modern` |

**Typst's exporter uses krilla, confirmed.** `typst/crates/typst-pdf/src/convert.rs:47-94`:

1. Builds `SerializeSettings { compress_content_streams: !pretty, no_device_cs: true, xmp_metadata: true, configuration: options.standards.config, enable_tagging: options.tagged, render_svg_glyph_fn: krilla_svg::render_svg_glyph, … }`.
2. Calls `Document::new_with`, then `convert_pages`, which loops `document.start_page_with(settings)` → `page.surface()` → `handle_frame` → `surface.finish()`, then adds link annotations.
3. Calls `attach_files` → `set_outline` → `set_metadata` → `set_tag_tree` → `document.finish()`.

Other Typst usage:

- Text goes through `surface.draw_glyphs(…)` with a custom `krilla::text::Glyph` impl (`text.rs:50,110`). Fonts come from `krilla::text::Font::new_variable` (`text.rs:90`).
- Images go through `Image::from_jpeg_with_icc` or `Image::from_custom(PdfRasterImage)` (`image.rs:203-209`). SVG goes through `krilla_svg::SurfaceExt` (`image.rs:9`).
- Creation date comes from the document or `options.timestamp`. It is never read from the clock in the exporter (`metadata.rs:59-62`).
- The document ID comes from `options.ident` and is passed to `Metadata::document_id` (`metadata.rs:42-43`).

Typst's own PDF code is about 8k LOC, of which about 4k is tagging logic (`tags/**`). That gives a realistic size for **our** adapter layer.

---

## 2. Feature matrix with file-level evidence

Legend: ✅ supported · ⚠️ partial or with caveats · ❌ absent · (n/a) not applicable.

### 2.1 Content stream / graphics

| Feature | krilla | pdf-writer | printpdf |
|---|---|---|---|
| Path fill/stroke, dash, caps, joins, even-odd | ✅ `Surface::draw_path`, `set_fill/set_stroke` (`surface.rs:113-135`). `Stroke`, `StrokeDash`, `LineCap`, `LineJoin`, `FillRule` (`graphics/paint.rs:269-417`) | ✅ every operator (`content.rs:169-490`) | ✅ `Op` enum (`ops.rs:406+`, 59 variants) |
| Clipping | ✅ `push_clip_path(&Path, &FillRule)` (`surface.rs:426`) | ✅ `clip_nonzero/clip_even_odd` (`content.rs:482-490`) | ✅ |
| Transforms | ✅ `push_transform` (`surface.rs:412`) | ✅ `transform([f32;6])` | ✅ |
| Opacity / transparency groups | ✅ `push_opacity`, `push_isolated` (`surface.rs:476,488`). Opacity is emitted through ExtGState or an opacified XObject stream | ✅ `ExtGraphicsState::{stroking_alpha, non_stroking_alpha, soft_mask, blend_mode}` (`content.rs:1538-1584`), `Group` (`xobject.rs`) | ⚠️ ExtGState exists. No group abstraction found |
| Blend modes | ✅ all 16 separable and non-separable (`graphics/blend.rs:6-23`), `push_blend_mode` | ✅ `BlendMode` type | ⚠️ **UNVERIFIED** |
| Soft masks (luminosity/alpha) | ✅ `Mask::new(stream, MaskType)` (`graphics/mask.rs:21-87`), `push_mask` | ✅ `SoftMask` writer (`content.rs:1678+`) | ❌ not found |
| Gradients | ✅ `LinearGradient`, `RadialGradient`, `SweepGradient` with `SpreadMethod` (`graphics/paint.rs:16-245`). Repeat/Reflect and sweep use PostScript functions, which raises `ValidationError::ContainsPostScript` under PDF/A (`configure/validate.rs:78`) | ✅ `FunctionShading`, `StreamShading`, `ShadingPattern`, sampled/exponential/stitching/PostScript functions (`color.rs`, `functions.rs`) | ⚠️ `shading.rs` (224 LOC) |
| Tiling patterns | ✅ `Pattern` (`graphics/paint.rs:144`, `graphics/tiling_pattern.rs`) | ✅ `TilingPattern` | **UNVERIFIED** |
| Reusable XObjects | ✅ `Graphic::new(Stream, isolated)` + `draw_graphic`, deduplicated by hash (`graphics/graphic.rs`, `surface.rs:539`). Built with `surface.stream_builder()` (`surface.rs:104`) | ✅ `FormXObject` | ✅ `xobject.rs` |
| Embed pages of an existing PDF (letterhead/stationery) | ✅ feature `pdf` (hayro-write): `Document::embed_pdf_pages`, `Surface::draw_pdf_page` (`document.rs`, `surface.rs:442`). Forbidden under PDF/A-2+ and UA (`ValidationError::EmbeddedPDF`) | manual | ✅ parse + merge via lopdf |
| Optional content (OCG) | ❌ krilla's own `configure/PDF_A1.md:60` says "krilla does not support optional content" | ⚠️ no typed OCG writer. Use raw `Dict` | ❌ "layering" flag only (`conformance.rs:289`) |
| Overprint | ❌ (`configure/PDF_A2.md:70`) | ✅ `ExtGraphicsState::overprint*` (`content.rs:1427-1443`) | **UNVERIFIED** |

### 2.2 Text and fonts

| Feature | krilla | pdf-writer | printpdf |
|---|---|---|---|
| Glyph-run API | ✅ `draw_glyphs(start, &[impl Glyph], Font, text: &str, size, outlined)` (`surface.rs:275`). The `Glyph` trait carries `glyph_id`, `text_range` (cluster → source text), x/y advance and offset, and `location` (`text/glyph/mod.rs:89-106`). The shaping is ours | operators only: `show`, `show_positioned` (TJ) (`content.rs:645-726`) | text ops + azul text layout |
| TrueType (`glyf`) | ✅ CIDFontType2, `/CIDToGIDMap /Identity`, FontFile2 (`text/cid.rs:270-284`, `font_file2`) | writer types only (`Type0Font`, `CidFont`, `FontDescriptor`) | ✅ |
| CFF (OpenType) | ✅ CIDFontType0 with a bare CFF program as FontFile3 `/Subtype /CIDFontType0C` (`text/cid.rs:244-256,370-406`) | types only | ✅ (`font.rs:378-380`) |
| CFF2 / variable fonts | ✅ `Font::new_variable(data, index, &[(Tag, f32)])` (`text/font.rs:41`). Subsetting goes through `subsetter::subset_with_variations`, which **instances** the font and converts CFF2 to TrueType (`subsetter/src/lib.rs:117-160`, `cff2.rs:"CFF2 fonts will currently be converted into TTF fonts"`) | n/a | ❌ **UNVERIFIED** |
| COLR/CPAL v0/v1 color fonts | ✅ rendered into Type3 glyphs with real vector paths and gradients (`text/glyph/colr.rs`, 581 LOC; `text/type3.rs`). `draw_color_glyph` prefers COLR, then SVG, then bitmap (`text/glyph/mod.rs:35-60`) | n/a (Type3 writer `start_color_glyph/start_shape_glyph`, `content.rs:743-754`) | ❌ |
| SVG-in-OpenType | ✅ when `render_svg_glyph_fn = krilla_svg::render_svg_glyph` (`serialize.rs` `RenderSvgGlyphFn`; `krilla-svg/src/lib.rs:120`). The default is a no-op | n/a | ❌ |
| sbix / CBDT / EBDT bitmap emoji | ⚠️ **PNG data only** (`text/mod.rs:5-6` doc, `text/glyph/bitmap.rs:32-34` `BitmapData::Png`). Other bitmap formats silently draw nothing | n/a | ❌ |
| Type3 fallback | ✅ Type3 fonts of at most 256 glyphs each, split automatically (`text/mod.rs:40-45`, `Type3FontMapper`) | ✅ writer | ❌ |
| Subsetting | ✅ always on, through `subsetter` 0.2.6. CID-keyed, `.notdef` always kept (`text/cid.rs:121-125,437-470`). Subset tag = hash of the glyph set (`subset_tag`) → deterministic | ❌ | ✅ allsorts `SubsetProfile::Pdf` (`font.rs:888-926`) |
| ToUnicode CMap | ✅ always written from the cluster text (`text/cid.rs:394-401`, `write_cmap_entry`) | ✅ `UnicodeCmap` builder + `Cmap` writer | ✅ |
| `/ActualText` | ✅ automatic when a cluster cannot be expressed in ToUnicode, for example inconsistent glyph↔text mapping (`text/group.rs:29-46,129-134`; `content.rs:772-776`) | ✅ `MarkContent::properties().actual_text()` (`content.rs:1058`) | ⚠️ marked-content ops only (`ops.rs:498-514`) |
| Outlined text (glyph → path) | ✅ `outlined: true` (`surface.rs:283`) | n/a | n/a |
| fsType restricted-license check | ✅ raises `ValidationError::RestrictedLicense` only for PDF/A and UA (`text/cid.rs:214-233`) | n/a | n/a |
| CIDSet (PDF/A-1) | ✅ written unless the version deprecates it (`text/cid.rs:303-322`) | n/a | n/a |

### 2.3 Images

| Feature | krilla 0.8.2 | pdf-writer | printpdf |
|---|---|---|---|
| JPEG passthrough (DCTDecode) | ✅ `Image::from_jpeg`, `from_jpeg_with_icc` (`graphics/image.rs:214-243`). Bytes are embedded as is (`FilterStreamBuilder::new_from_jpeg_data`, `image.rs:470`). CMYK/YCCK Adobe JPEGs get a `/Decode` invert (`image.rs:488-497`) | manual | ✅ (`image.rs:1295,1449-1481`) |
| PNG with alpha → SMask | ✅ alpha split into a DeviceGray `/SMask` image (`image.rs:444-466`). The PNG is **decoded and re-deflated**: `png` crate with `Transformations::EXPAND`, so palette PNGs become RGB(A) (`image.rs:506,558-568`). On `main`, unreleased, `from_png_native` adds passthrough (#435) and native indexed (#415) | manual | ✅ (`image.rs:1417`, `image_types.rs:399`) |
| 16-bit | ✅ `BitsPerComponent::Sixteen` (`image.rs:35-46`). Rejected with `KrillaError::SixteenBitImage` when the target version or PDF/A-1 does not allow it (`image.rs:425-434`) | manual | ✅ (`image.rs:336`) |
| ICC profiles | ✅ embedded PNG/JPEG ICC used when its color space matches (`image.rs:71-76,371-395`) | ✅ `IccProfile` writer | ⚠️ **UNVERIFIED** |
| CMYK images | ✅ `ImageColorspace::Cmyk`. Under `no_device_cs` without a CMYK profile → `ValidationError::MissingCMYKProfile` (`image.rs:412-415`) | manual | **UNVERIFIED** |
| GIF / WebP | ✅ `from_gif`, `from_webp` (first frame) (`image.rs:247-271`) | ❌ | ✅ through `image` crate features |
| Custom/raw images | ✅ `CustomImage` trait + `from_custom`, `from_rgba8` (`image.rs:129-345`) | manual | ✅ |
| Interpolate flag | ✅ (forbidden under PDF/A, `ValidationError::ImageInterpolation`) | ✅ | ? |
| Image dedup | ✅ SipHash of the full `Data` bytes (`data.rs:15-19`, `register_image`) | n/a | by id |

### 2.4 Color

| Feature | krilla | pdf-writer | printpdf |
|---|---|---|---|
| DeviceRGB / Gray / CMYK | ✅ `rgb::Color`, `luma::Color`, `cmyk::Color`, all **u8 per channel** (`graphics/color.rs:175-308`) | ✅ | ✅ |
| ICCBased | ✅ `no_device_cs = true` swaps device spaces for embedded sRGB/sGrey ICC (`serialize.rs` `register_colorspace`). CMYK needs a `cmyk_profile: Option<ICCProfile<4>>` | ✅ | ⚠️ |
| Separation / spot colors | ✅ `SeparationSpace`, `SeparationColorant` (`graphics/color.rs:428-460`, `graphics/separation.rs`) | ✅ `Separation`, `DeviceN` | **UNVERIFIED** |
| DeviceN | ❌ (`configure/PDF_A2.md:82`) | ✅ | ? |
| Output intent | ✅ automatic sRGB OutputIntent (subtype chosen per PDF/A part by `Archival::output_intent`, `validate.rs:894`) when a PDF/A validator is set (`serialize.rs` `serialize_destination_profiles`) | ✅ `OutputIntent` writer | ✅ (`serialize.rs:118-147`) |

### 2.5 Navigation, interactivity, metadata

| Feature | krilla 0.8.2 | pdf-writer | printpdf |
|---|---|---|---|
| URI links | ✅ `LinkAnnotation::new(rect, Target::Action(Action::Link(LinkAction)))`, with quad points and borders (`interactive/annotation.rs:116-200`, `action.rs:17-45`) | ✅ `Annotation`, `Action` writers | ✅ (`annotation.rs:113-148`) |
| Internal GoTo | ✅ `Destination::Xyz(XyzDestination{page_index, point})`. Resolved at `finish`, so **forward references to later pages work** (`serialize.rs` `xyz_destinations` comment) | ✅ `Destination` | ✅ |
| Named destinations | ✅ `Destination::Named`, `Document::register_named_destination`. The Dests name tree is sorted bytewise (`chunk_container.rs:259-283`) | ✅ `NameTree` | ? |
| Outlines/bookmarks | ✅ `Outline`, `OutlineNode::new(text, XyzDestination).with_open()` (`interchange/outline.rs:32-175`) | ✅ `Outline`, `OutlineItem` | ✅ `bookmarks` |
| Page labels | ✅ `PageLabel{style, prefix, offset}` via `PageSettings::with_page_label`. Number tree with consecutive runs collapsed (`page.rs:497-612`) | ✅ `PageLabel` | **UNVERIFIED** |
| Page boxes | ✅ media/crop/bleed/trim/art (`page.rs:26-170`) | ✅ | ✅ |
| Info dict | ✅ title, subject (description), keywords, author, creator, producer, Creation/ModDate (`interchange/metadata.rs:247-298`). Omitted under PDF 2.0 and when `prohibits_info_dict` | ✅ `DocumentInfo` | ✅ (`serialize.rs:2130`) |
| XMP | ✅ always written by default (`SerializeSettings.xmp_metadata = true`), uncompressed stream (`chunk_container.rs:190-200`). **No public hook for custom XMP or extension schemas**; issue LaurenzV/krilla#209 "Support custom XMP metadata in PDFs" is open | ✅ `Metadata` stream writer (bring your own XMP; `xmp-writer` supports `Namespace::Custom` and PDF/A extension schemas, `xmp-writer/src/types.rs:45`, `lib.rs:712`, `pdfa.rs`) | ⚠️ templated XMP string with a random instance id (`lib.rs:857-879`) |
| Document `/ID` control | ✅ deterministic. `document_id = siphash128(pdf_version, Metadata::document_id)`, else `hash(version,title,authors)`, else the instance id. `instance_id = siphash128(all PDF bytes)` (`chunk_container.rs:153-170`). The hasher is stable across 32/64-bit (`util.rs:153-170`) | ✅ `Pdf::set_file_id` (`lib.rs`) | ❌ **non-deterministic**: `random_character_string_32()` from a process-global `AtomicUsize` xorshift (`utils.rs:10-45`, `serialize.rs:412-421`) |
| CreationDate control | ✅ written only if `Metadata::creation_date(DateTime)` is set. No clock reads anywhere in krilla (grep for `SystemTime`/`Instant::now`/`rand` finds nothing). PDF/A-2/3/4 then raises `MissingDocumentDate` (`validate.rs`) | ✅ (you write it) | ⚠️ `PdfDocumentInfo.creation_date: OffsetDateTime`, defaulting from `OffsetDateTime::now_utc()` (`date.rs:113`) |
| Embedded files / associated files | ✅ `Document::embed_file(EmbeddedFile{path, mime_type, description, association_kind, data, modification_date, compress})` (`interchange/embed.rs`). Writes `/EmbeddedFile` with `/Subtype` MIME, `/Params{Size, ModDate}`, Filespec with `/UF`, `/AFRelationship`, and catalog `/AF` + `/Names/EmbeddedFiles` (sorted `BTreeMap`) (`chunk_container.rs:286-305`) | ✅ `FileSpec::association_kind`, `associated_files()` on catalog, page, struct elem and xobject (`files.rs:83,166`; `structure.rs:155,414,578`) | ❌ not found |
| Annotations / AcroForm | ⚠️ 0.8.2 has **link annotations only** (`annotation.rs:116-118`) and its docs say "does not support interactive forms" (`PDF_A2.md:157`). `main` adds forms (push buttons, checkboxes, radios, text and choice fields; #423, #430), unreleased | ✅ `Form`, `Field`, widget annotations (`forms.rs`, `annotations.rs`) | ⚠️ annotations, no forms |
| Digital signatures | ❌ (`PDF_A2.md:161`) | ❌ (raw dicts only) | ❌ |
| Encryption | ❌ "krilla does not support encryption" (`configure/PDF_A1.md:20`, `PDF_A4.md:18`) | ❌ (no Encrypt dictionary or crypt writer; `files.rs:175` only names `EncryptedPayload`) | ❌ (lopdf could) |
| Viewer prefs / page layout | ✅ DisplayDocTitle (auto for UA), Direction, PageLayout (`chunk_container.rs:232-254`) | ✅ | ? |

### 2.6 Tagged PDF / accessibility

krilla, from `interchange/tagging/mod.rs`, `tag.rs` and `generated.rs`:

- **Model.** You build a `TagTree` (with `.with_lang()`) of `TagGroup`s and `Node`s. Leaves are `Identifier`s returned by `Surface::start_tagged(ContentTag)` / `end_tagged` (MCIDs are assigned automatically per page, `page.rs` `num_mcids`) or by `Page::add_tagged_annotation` (`page.rs:226-240`). You hand the tree over with `Document::set_tag_tree` before `finish` (`mod.rs:62-90`). Tagged content calls cannot be nested; `ContentTag` is `Artifact(ArtifactType)` or `Span(SpanTag)`.
- **Content-level properties.** `SpanTag::with_lang/with_alt_text/with_expanded/with_actual_text` (`mod.rs:388-433`).
- **Artifacts.** `Artifact{kind: ArtifactType, bbox}` with page header/footer subtypes (version-gated: `VersionedFeature::HeaderFooterArtifactSubtypes`).
- **Tag kinds** (`generated.rs:11-134`): Part, Article, Section, Div, BlockQuote, Caption, TOC, TOCI, Index, P, Hn (arbitrary level, mapped through RoleMap below PDF 2.0), L, LI, Lbl, LBody, Table, TR, TH, TD, THead, TBody, TFoot, Span, InlineQuote, Note, Reference, BibEntry, Code, Link, Annot, Figure, Formula, Form, NonStruct, Datetime, Terms, Title, Strong, Em.
- **Attributes** (`generated.rs:4121-4409`): Id, Lang, Alt, Expanded, ActualText, Title, HeadingLevel, ListNumbering, Table `Summary`, `HeaderScope` (TH `/Scope`), `CellHeaders` (TD `/Headers` → TH ids), RowSpan/ColSpan, Layout attributes (BBox, Placement, WritingMode, colors, borders, padding, spacing, …).
- **Serialization** (`serialize.rs` `serialize_tag_tree`): StructTreeRoot, ParentTree number tree, ParentTreeNextKey, IDTree, `/MarkInfo <</Marked true /Suspects false>>`. Below PDF 2.0 a RoleMap maps custom kinds (Datetime→Span, Terms→Part, Title→P, Strong/Em→Span, Hn→P). For PDF 2.0 it writes the namespaces (PDF 2.0 SSN + a krilla namespace). `/Tabs /S` is written on pages with annotations or under UA/A-a (`page.rs:440-470`).

pdf-writer has every typed writer but no logic: `StructTreeRoot`, `StructElement` (`lang`, `alt`, `expanded`, `actual_text`, `title`, `namespace`, `associated_files`), `RoleMap`, `ClassMap`, `Namespace`/`NamespaceRoleMap`, `MarkedRef`/`ObjectRef`, `TableAttributes::{headers, scope, summary, row_span, col_span}` (`structure.rs:91-584,1548`; `attributes.rs:1008-1035`), and `MarkContent::identify(mcid)` + `artifact()` (`content.rs:1050-1116`).

printpdf has **no tagging**. A grep for `StructTreeRoot`/`MarkInfo` in non-parser sources finds nothing; only raw BMC/BDC ops exist.

### 2.7 Conformance profiles and validation

| | krilla 0.8.2 | pdf-writer | printpdf |
|---|---|---|---|
| PDF versions | 1.4, 1.5, 1.6, 1.7, 2.0 (`configure/version.rs:15-24`) | any (`Pdf::set_version`) | header set by lopdf |
| PDF/A | `Validator::A(Archival)`: A1_A, A1_B, A2_A, A2_B, A2_U, A3_A, A3_B, A3_U, A4, A4F, A4E (`configure/validate.rs:463-528`) | ❌ (DIY) | enum of identifiers (A1B…A3, UA, X1A…X5PG; `conformance.rs`). It **does not validate**: only predicates like `must_have_xmp_metadata`, `is_jpeg_content_allowed` (`conformance.rs:213-289`) |
| PDF/UA | `Validator::Ua(Accessibility::UA1)` only (`validate.rs:1090`). **No UA-2.** Issue LaurenzV/krilla#449 "PDF/UA-2: what veraPDF finds on krilla's output, and a branch that passes" is open | ❌ | flag only |
| PDF/X | ❌ (`PDF_A4.md:62`: "since PDF/X and PDF/E are not supported") | ❌ | flag only |

How krilla's "validator" works:

- It is a **write-time conformance enforcer**, not a parser-validator. Writers call `sc.register_validation_error(e)`. `Validators::prohibits` decides per standard (`validate.rs:179+`, rule tables at about `:540-660`). `finish()` returns `Err(KrillaError::Validation(Vec<ValidationError>))`, de-duplicated and order-preserving (`serialize.rs:470-490`).
- Errors carry an optional user `Location` (a u64 we choose) to map back to source spans. Typst does exactly this (`convert.rs:841` `to_span`).
- Standards also flip settings: `no_device_cs`, `enable_tagging` and `xmp_metadata` are forced by the validator (`serialize.rs` `SerializeContext::new`).
- Per-standard compliance notes live in `configure/PDF_A1.md … PDF_UA1.md`.
- **Krilla's CI validates its outputs with veraPDF 1.31.x, the Arlington model checker (`-e ISO_19005_3`), pdfcpu `validate -m strict`, and Ghostscript** (`.github/workflows/ci.yml:38-90`). That is good evidence for correctness. We still need veraPDF in our own CI, because semantic rules (reading order, alt text quality) are ours.

### 2.8 Compression, file structure, determinism, memory

| | krilla 0.8.2 | pdf-writer | printpdf / lopdf |
|---|---|---|---|
| Deflate | flate2 zlib at **fixed level 6** (`stream.rs:348-349`). Only an on/off switch (`compress_content_streams`). `ascii_compatible` adds ASCIIHex | none built in (you filter) | lopdf `SaveOptions.compression_level` |
| Object streams / xref streams | ❌ `Document::finish` calls `Pdf::finish()`, which writes a **classic xref table** (`document.rs` `finish`; `pdf-writer/src/lib.rs` `finish`). The doc comment says renumbering "might make implementing features like object streams easier down the road" (`chunk_container.rs:108-113`) | ⚠️ xref **streams** yes (`finish_with_xref_stream[_and_filter]`). **No ObjStm writer**: `write_offsets` only emits type-1 entries | lopdf ✅ `SaveOptions{use_object_streams, use_xref_streams, max_objects_per_stream, compression_level}`, `save_modern` (`lopdf/src/save_options.rs`, `writer.rs:30-62`) |
| Object order | refs allocated sequentially. At finish everything is **renumbered** 1..N in a fixed visiting order: non-stream chunks → mixed → streams (fonts, shadings, patterns, pages, embedded files, ICC, xobjects, images) (`chunk_container.rs:100-140,420-470`) | yours | lopdf `BTreeMap` order |
| HashMap use | maps are used for lookup only. Every map that is iterated into output is sorted or a BTreeMap/IndexMap: named destinations sorted (`chunk_container.rs:271`), embedded files `BTreeMap`, font map `IndexMap`, Type3 gids sorted (`text/type3.rs:240-245`), id tree `BTreeMap`. A reproducibility test exists (`tests/src/text.rs:401-404` `text_two_fonts_reproducibility`) | n/a | printpdf: random `/ID` (above) |
| Parallelism | feature `rayon`: page streams and images compress on rayon through `Deferred` (`util.rs:211-250`). Output order is still fixed because chunks are awaited in visit order | n/a | lopdf `rayon` feature |
| **Streaming / memory model** | ❌ **No streaming.** See §3 | ⚠️ `Pdf` is one in-memory `Vec<u8>`, but `Chunk`s can be written to any `io::Write` by us (§3.3) | ❌ the whole `PdfDocument` op-list is converted to a `lopdf::Document` and then serialized (`serialize.rs:74-101`) |
| Encryption | ❌ | ❌ | lopdf ✅ RC4 (V1/V2), AES-128 (V4), AES-256 (V5/R6), deprecated R5 (`lopdf/src/encryption.rs:139-200`, `document.rs:392-420`). Uses `rand::rng()` for IVs and seeds (`encryption/algorithms.rs:774,926,990,1043`), so output is non-deterministic |

### 2.9 Footprint, MSRV, wasm

- **krilla**: MSRV 1.92 (`krilla/Cargo.toml` `rust-version`). That is the floor for us too, matching Typst (`typst/Cargo.toml:8`).
  - With `default-features = false, features = ["raster-images"]` (dropping `simple-text`/rustybuzz, since we shape ourselves), the pure-Rust tree is: skrifa/read-fonts/font-types, subsetter (+write-fonts, kurbo via its default `variable-fonts` feature, which krilla enables: `krilla/Cargo.toml` `subsetter = { …, features = ["variable-fonts"] }`), pdf-writer, xmp-writer, flate2 (miniz_oxide backend by default), png, zune-jpeg, gif, image-webp, imagesize, tiny-skia-path, yoke, bumpalo, indexmap, siphasher, base64, smallvec, float-cmp, rustc-hash.
  - No C, no system libraries, no network, no clock. Fits `scratch` Docker.
- **krilla-svg** pulls usvg/resvg/tiny-skia and **fontdb with default features**, which enables `fs`, `memmap` (memmap2, `unsafe` mmap) and `fontconfig` parsing. These come from the sparse index (fontdb 0.23.0 defaults `["std","fs","memmap","fontconfig"]`) and the krilla workspace `fontdb = "0.23.0"`.
  - krilla-svg never scans system fonts itself; it only clones `tree.fontdb()` (`krilla-svg/src/lib.rs:107-111`). The fs code still links, though.
  - For the "no file access outside input dir" policy we must build `usvg::Options` ourselves: an empty or our own fontdb, and a custom `ImageHrefResolver`.
  - **Perf note:** `render_tree` does `Arc::make_mut(&mut tree.fontdb().clone())`, which deep-clones the fontdb `Database` on every SVG draw while the tree still holds a reference (`lib.rs:107-111`). Keep the SVG fontdb small, or patch this.
- **pdf-writer**: 4 tiny deps, `#![forbid(unsafe_code)]` (`lib.rs`), no MSRV declared.
- **printpdf**: `crate-type = ["cdylib","rlib"]`. The default feature `html` pulls azul-layout/azul-css/azul-core, rust-fontconfig, hyphenation and xmlparser. `wasm-bindgen` is a non-optional dependency. That is heavy and unrelated to our needs.
- **wasm**: krilla has **no wasm target in CI** (no `wasm` in `.github/workflows/ci.yml`). Typst's web app runs typst-pdf in wasm, so krilla (without `rayon`) compiling for `wasm32-unknown-unknown` is very likely, but this is **UNVERIFIED** from source here. pdf-writer is trivially wasm-safe. printpdf ships an explicit wasm API (`src/wasm`).

---

## 3. Memory model and streaming page emission (measured from code)

### 3.1 What krilla retains per page (0.8.2)

1. `Document::start_page_with` returns `Page<'_>`, which **mutably borrows** the `Document`'s `SerializeContext` + `ChunkContainer` (`document.rs:1-14`, `page.rs:197-205`). So only one page can be open at a time, and page **serialization** is sequential. Our layout can still run in parallel.
2. `Surface` builds the content stream into an in-memory `Stream { content: Vec<u8>, resource_dictionary, bbox, validation_errors }`.
3. When `Page` drops (`page.rs:280-300`), `InternalPage::new` (`page.rs:340-380`):
   - moves the raw content into a `Deferred` closure that deflates it into a `Chunk`. Without `rayon` it runs **immediately** (`util.rs:195-208`, `Deferred::new` calls `f()`), so the uncompressed bytes are freed at page end. With `rayon` they live until the background task runs;
   - keeps `stream_resources` (resource-name maps), `annotations`, `PageSettings` and bbox in `InternalPage`. That goes into `GlobalObjects.pages: Vec<(Ref, InternalPage)>` (`serialize.rs` `register_page`). The page **dictionary is not written until `finish`**, because "pages might contain annotations which in turn depend on future pages" (`serialize.rs` `GlobalObjects.pages` doc);
   - pushes the compressed stream chunk into `chunk_container.streams.pages: Vec<Deferred<Chunk>>` at `finish` (`page.rs` `InternalPage::serialize`).
4. Images: `Image` holds an `Arc` to its decoded `Repr`. Its serialized (deflated) chunk is kept in `chunk_container.streams.images` (`image.rs:430-505`). Fonts keep the original font `Data` (Arc) plus glyph sets and cmap entries, and are **subset only at `finish`** (`serialize.rs` `serialize_fonts`).

### 3.2 Peak at `finish`

`ChunkContainer::finish` (`chunk_container.rs:100-140`):

1. Visits every chunk to build `remapper: HashMap<Ref, Ref>` and sum `chunks_byte_len`.
2. Allocates `Pdf::with_settings_and_capacity(1.1 × chunks_byte_len + 200)`.
3. Copies **every chunk** into it with `renumber_into`.
4. Appends Info, XMP and catalog. `Pdf::finish` then appends the xref into the same buffer and returns `Vec<u8>`.

The chunks are not freed until `finish` returns, so:

> **Peak resident ≈ Σ(compressed chunks) + 1.1 × Σ(compressed chunks) ≈ 2.1 × final file size**, plus original font files, plus any decoded images the caller still holds, plus the tag tree. Nothing is written to the sink before the very end, so time-to-first-byte equals total time.

Worked example. A 1000-page text invoice run at about 5–15 KB compressed per page gives a 5–15 MB file, so the peak is roughly 12–35 MB. That is acceptable for typical batch jobs, but it is not "bounded memory" for arbitrarily large documents. For example, a 10,000-page statement with images at 200 MB leads to a peak of about 450 MB.

### 3.3 Options for bounded memory

**Option A: patch krilla with a streaming sink (preferred long-term; upstream first).** Code facts that make this tractable:

- The global renumbering is cosmetic. Refs are already allocated monotonically by `sc.new_ref()`, and the renumbering only "makes it a lot cleaner" (`chunk_container.rs:108-113`). A streaming mode can skip renumbering.
- Page **content streams** and **image XObjects** have no forward dependencies, so they can be written to an `io::Write` sink the moment they are ready. Their `(Ref, offset)` pairs go into a growing xref vector of about 16 B per object.
- Page dicts, annotations, fonts (subset at end), the struct tree, outline, name trees, XMP and catalog are small, or bounded by distinct fonts, and are written at the end as today.
- `instance_id = siphash(all bytes)` (`chunk_container.rs:153`) becomes an incremental SipHasher over the bytes as they are written. That stays deterministic.
- Retained per page becomes: page ref, resource dict, annotations, label, MCID count. That is O(pages × small).
- Estimate: about 300–600 LOC touching `chunk_container.rs`, `page.rs`, `serialize.rs` and `document.rs`, plus a `finish_to<W: Write>` API. pdf-writer would need either a public `Chunk` offset accessor (today `offsets` is `pub(crate)`, `chunk.rs:36`; only `refs()` is public, `chunk.rs:97`) or "one indirect object per chunk", where the offset is the chunk start.

**Option B: our own streaming backend on pdf-writer.** This means reimplementing what krilla gives us:

- CID/Type3 font pipeline and COLR/SVG/bitmap glyphs (`text/**`, about 2.5k LOC)
- ToUnicode/ActualText grouping
- image decode/SMask/ICC (`image.rs`, 835 LOC)
- shadings/gradients (`shading_function.rs`, 865 LOC)
- masks/groups/opacity
- the tag-tree serializer and validators (`tagging/**`, `validate.rs`, about 3k LOC excluding generated code)
- XMP

That is about 15k LOC of solved and veraPDF-tested code. It is not justified for v1.

**Option C: chunked documents plus merge.** Rejected. Fonts would be subset and duplicated per chunk, the tag tree is document-global, and links cross chunks.

**Pragmatic plan.** For v1, use krilla in-memory with a configurable **output-size cap** (memory cap ÷ 2.2) and a page-count/time cap. In parallel, open an upstream issue or PR for a streaming sink (Option A). If upstream declines, keep a thin fork, since the patch is local to the 4 files above. Streaming has little user-visible latency benefit anyway: viewers need the trailer, and we do not linearize. The motivation is bounded RSS.

---

## 4. Factur-X / ZUGFeRD (PDF/A-3 + embedded XML)

Requirements, with secondary sources: [loslab Factur-X XMP article](https://blog.loslab.com/el/delphi-pdf-library/pdflibpas-pdfa3-xmp-extension-schema-facturx.html), [Aspose forum thread](https://forum.aspose.com/t/support-for-factur-x-standard/254958), [loslab AddFacturXAssociatedFile](https://www.loslab.com/hotpdf-component-doc/en-gb/topics/THotPDFAddFacturXAssociatedFileMethod.html). The official FNFE/FeRD spec could not be fetched here, so re-check it.

- PDF/A-3 (b, or a/u).
- An embedded `factur-x.xml` (ZUGFeRD 2.x also uses `factur-x.xml`; XRechnung uses `xrechnung.xml`) with `/Subtype /text#2Fxml`, `/Params /ModDate`, `/AFRelationship` (`Alternative` for BASIC/EN16931/EXTENDED, `Data` for MINIMUM/BASIC WL), referenced from catalog `/AF`.
- XMP with the `fx` namespace `urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#` and properties `fx:DocumentType=INVOICE`, `fx:DocumentFileName`, `fx:Version`, `fx:ConformanceLevel`. These **must also be described in a `pdfaExtension:schemas` block**, or veraPDF fails ISO 19005-3 6.6.2.3.1.

What krilla 0.8.2 already does: `Validator::A(A3_B)` + `Document::embed_file(EmbeddedFile{ path: "factur-x.xml", mime_type: MimeType::new("text/xml"), description: Some(..), association_kind: AssociationKind::Alternative, modification_date: Some(..), .. })`. That writes:

- the `/Type /EmbeddedFile` stream (`pdf-writer/src/files.rs:101`)
- `/Subtype /text#2Fxml` (pdf-writer escapes `/` as `#2F`, `object.rs:347-351`)
- `/Params`
- Filespec `/F` + `/UF` + `/AFRelationship` + `/Desc`
- catalog `/AF` and `/Names/EmbeddedFiles`

(`krilla/src/interchange/embed.rs`, `chunk_container.rs:286-305`). PDF/A-3 enforces date, description and MIME (`validate.rs:614-626`).

**Gap: custom XMP.** krilla builds the `XmpWriter` internally in `ChunkContainer::finish` (`chunk_container.rs:172-200`) and only adds its own PDF/A/UA extension-schema descriptions (`validate.rs:242-296,961-974,1172-1178`). Issue #209 is open. Options:

- (a) **Preferred:** contribute a krilla API such as `Metadata::custom_xmp(fn(&mut XmpWriter))` plus a hook into `extension_schemas()`. xmp-writer already supports `Namespace::Custom` and `PdfAExtSchemasWriter` (`xmp-writer/src/types.rs:45`, `lib.rs:712`, `pdfa.rs:23-165`).
- (b) Fork patch, a few dozen LOC.
- (c) Post-process. The XMP stream is written **uncompressed** right before the catalog (`chunk_container.rs:190-197`). We could rewrite the tail: metadata object + catalog + xref. This is possible but brittle. Not recommended.

Also add a recto-side Factur-X validation step: schema-validate the XML (CII D16B) and check the profile ↔ AFRelationship pairing.

---

## 5. SVG embedding: svg2pdf vs krilla-svg

- **svg2pdf 0.13.0** is pinned to pdf-writer 0.12, usvg 0.45 and resvg 0.45. Those are two major lines behind krilla's pdf-writer 0.15 and usvg 0.47, so mixing it in would duplicate crates. It is **unmaintained** (`main` @ `55723cb`, 2026-07-10). printpdf still depends on it (`svg2pdf ^0.13`).
- **krilla-svg 0.8.1**:
  - API: `SurfaceExt::draw_svg(&usvg::Tree, Size, SvgSettings{embed_text, filter_scale})` (`krilla-svg/src/lib.rs:37-90`).
  - The README claim "passes nearly the whole resvg test suite" is in `lib.rs:4-5`.
  - Text in SVG is embedded as real, selectable text through krilla fonts (`embed_text: true`), with variable-font support (#402 in 0.8.1). Fonts are deduplicated against ours because krilla hashes `Font` by `FontInfo` (checksum + metrics + name), not by pointer (`text/font.rs:241-249`).
  - Filters are **rasterized** with resvg at `filter_scale` (default 4.0) (`filter.rs:9-80`).
  - Clip paths, masks and gradients map to krilla primitives (`clip_path.rs`, `mask.rs`).
  - Also provides `render_svg_glyph` for SVG-in-OpenType (`lib.rs:120`).
- **Decision: krilla-svg.** We parse SVG with `usvg` ourselves, which lets us control `Options`, the fontdb and the href resolver for the sandbox, and then call `draw_svg`.

---

## 6. printpdf and lopdf, briefly

- **printpdf** has these structural problems for recto:
  - an op-list document model held fully in memory and converted to a lopdf `Document` at save (`serialize.rs:74-101`)
  - **no tagged PDF**
  - conformance enums that do not validate (`conformance.rs`)
  - a non-deterministic `/ID` from a process-global counter (`utils.rs:10-45`) and a clock-based default date (`date.rs:113`)
  - no COLR/SVG/bitmap glyph support
  - heavy default features (azul HTML layout)

  Interesting as a competitor: it ships an HTML→PDF mode through azul-layout (feature `html`). As a writer: **reject**.
- **lopdf** is useful only as a **post-processor**: encryption (RC4/AES-128/AES-256 R6), object streams and xref streams, incremental updates (`incremental_document.rs`), and reading or merging PDFs. Costs: a full reparse into a `BTreeMap<ObjectId, Object>`, so all objects are resident, and random IVs (non-deterministic). Reasonable for an opt-in `--encrypt` path; not for the main pipeline.

---

## 7. Integration boundary: recto display list → krilla

Proposed crate split: `recto-paint` (display list, writer-agnostic) and `recto-pdf` (krilla adapter, about 3–5k LOC, by analogy with `typst-pdf`'s 8k including about 4k of tagging).

| recto display-list item | krilla call(s) | Notes |
|---|---|---|
| `Page{size_pt, bleed, label, named_page}` | `start_page_with(PageSettings::from_wh(w,h).with_trim_box(..).with_page_label(PageLabel::new(style,prefix,offset)))` | krilla is y-down and top-left like CSS, so there is no flip in our code (`page.rs` `page_root_transform`) |
| `PushTransform/Pop` | `surface.push_transform(&Transform)` / `pop()` | push and pop must balance, or `Surface::finish` panics (`surface.rs:555-558`) |
| `PushClip(path, rule)` (overflow, border-radius) | `push_clip_path` | q-nesting is capped at 28 under PDF/A (`ValidationError::TooHighQNestingLevel`). Flatten nested clips where possible |
| `PushOpacity(a)` / `PushBlend(mode)` / `PushIsolated` | `push_opacity`, `push_blend_mode`, `push_isolated` | CSS `opacity` → isolated group. PDF/A-1 forbids transparency (`ValidationError::Transparency`) |
| `FillPath{path, paint}` / `StrokePath{path, stroke}` (backgrounds, borders) | `set_fill(Some(Fill{paint, opacity, rule}))` + `draw_path` | colors are u8/channel. CSS gradients → `LinearGradient`/`RadialGradient` (avoid `Repeat`/`Reflect` under PDF/A because of PostScript) |
| `GlyphRun{font_id, size, glyphs[{gid, cluster_range, adv, off}], text, fill, stroke}` | `draw_glyphs(origin, &glyphs, font, &text, size, false)` with our `impl Glyph` | this is where ToUnicode/ActualText correctness comes from: **cluster ranges must index the run's `text`**. Soft hyphens should be U+00AD (`tagging/mod.rs:118-121`) |
| `Image{id, rect}` | cached `krilla::image::Image` per resource id. `from_jpeg_with_icc` for JPEG passthrough, `from_png`/`from_custom` otherwise. `draw_image(img, size)` under a transform | keep one `Image` per source, since krilla dedups by hashing the full bytes |
| `Svg{tree, rect}` | `krilla_svg::SurfaceExt::draw_svg` | |
| `Repeated{key, content}` (running headers, logos) | build once with `stream_builder()` → `Graphic::new(stream, isolated)` → `draw_graphic` on each page | deduplicated as one XObject |
| `Link{rect | quads, Uri | Anchor(id)}` | `page.add_tagged_annotation(Annotation::new_link(LinkAnnotation::new_with_quad_points(..), alt))` with `Target::Destination(Destination::Named(..))` for `#id` | named destinations resolve at finish, so forward links (TOC → page 900) cost nothing |
| `Bookmark{level, title, anchor}` | `Outline` / `OutlineNode` at the end | |
| `TagStart(kind, attrs)/TagEnd` + content | `surface.start_tagged(ContentTag::Span(SpanTag{lang, alt, actual_text}))` / `end_tagged()` → `Identifier` pushed into our `TagGroup` tree. Margin boxes → `ContentTag::Artifact(Artifact::new(ArtifactType::Header/Footer…))` | tagged content cannot nest. Our tree builder owns the hierarchy and calls `document.set_tag_tree(tree)` at end. Table `<th scope>`/`headers` → `HeaderScope`/`CellHeaders` |
| `Location(u64)` | `surface.set_location` / `Glyph::location` | maps `ValidationError`s back to HTML nodes, the way Typst does |

Document-level settings:

- `SerializeSettings { compress_content_streams: true, no_device_cs: <pdfa>, xmp_metadata: true, enable_tagging: true (default on), configuration: Configuration::new_with_validator(..), render_svg_glyph_fn: krilla_svg::render_svg_glyph, .. }`. Exact constructor names in `configure/mod.rs` should be confirmed when coding.
- `Metadata::new().title().language().creation_date(<from input or SOURCE_DATE_EPOCH or omitted>).document_id(<stable hash of template+data or user-supplied>)`. This gives byte-identical output.
- The `rayon` feature affects only the parallelism of compression and image encoding, not the output bytes.

---

## Findings that affect recto's design

1. **Use krilla 0.8.x (MIT/Apache, MSRV 1.92) as the PDF backend.** It is the only Rust option with full tagging (struct tree, MCIDs, artifacts, Lang/Alt/ActualText, TH scope/headers), PDF/A-1…4 and UA-1 enforcement, COLR/SVG/bitmap color glyphs, CFF/CFF2/variable-font subsetting, automatic ToUnicode/ActualText, and deterministic output. Its CI also checks outputs with veraPDF, Arlington, pdfcpu and Ghostscript. Typst ships it in production (`typst-pdf` 0.15.1 → `krilla ^0.8.2`).
2. **Set our MSRV to ≥ 1.92** to match krilla 0.8.2 and Typst.
3. **No streaming in krilla.** Every page's compressed content is retained, and `finish()` copies everything into a fresh buffer, so peak ≈ **2.1 × output size** (`chunk_container.rs:100-140`). v1 needs an **output-size/memory cap** and must document this. Plan the krilla streaming-sink patch (§3.3 A, about 300–600 LOC, upstream first).
4. **Determinism is achievable with krilla:**
   - No clock or RNG reads.
   - `/ID` is derived from `Metadata::document_id` or a content hash.
   - Ordered maps or sorted iteration everywhere output depends on them.
   - Stable 32/64-bit hashing.
   - recto must: never call `creation_date(now)` by default (use `SOURCE_DATE_EPOCH` or input metadata), always pass `document_id`, and pin krilla/flate2 versions. Deflate output depends on the flate2/miniz_oxide version, so the lockfile matters for byte-identity across releases.
5. **Display-list text runs must carry cluster→text ranges.** krilla derives ToUnicode and ActualText from `Glyph::text_range`, which makes copy/paste and PDF/UA quality our shaper's responsibility.
6. **Tag tree ownership is ours.** krilla only serializes. We keep a document-global tree builder (HTML semantics → `TagKind`) and call `set_tag_tree` at the end. Margin boxes and running headers become `Artifact` with Header/Footer subtype. Use `typst-pdf/src/tags/**` (about 4k LOC) as the reference design.
7. **Gaps we must build or patch:**
   - (a) **Custom XMP / Factur-X `fx` extension schema.** krilla patch; issue #209 open.
   - (b) **Streaming sink.**
   - (c) **Encryption.** krilla and pdf-writer have none. Defer, or offer an opt-in lopdf post-processor (non-deterministic IVs, full reparse). Encryption is incompatible with PDF/A anyway.
   - (d) **PDF/UA-2.** krilla has only UA-1; issue #449 is open with a passing branch. Track it.
   - (e) **PDF/X.** Unsupported.
   - (f) **Object streams / xref streams** for smaller files. pdf-writer has xref streams but no ObjStm writer.
   - (g) **Forms.** On krilla `main` only, unreleased; needed only if we ever support `<input>` → AcroForm.
   - (h) **Deflate level** is fixed at 6. Patch if we want a `--compress-level`.
8. **Images:**
   - JPEG passthrough is free.
   - PNG is re-encoded in 0.8.2, which costs CPU; 0.9 will likely have `from_png_native` (#435).
   - 16-bit is OK except on PDF 1.4 / PDF/A-1.
   - CMYK images under PDF/A need a CMYK ICC profile (`cmyk_profile`).
   - Cache one `krilla::Image` per source resource.
9. **SVG:**
   - Use krilla-svg with our own `usvg::Options`: sandboxed href resolver, our fontdb.
   - Drop svg2pdf (unmaintained, old dependency versions).
   - Expect filters to rasterize (`filter_scale`).
   - Watch the fontdb clone on every `draw_svg`.
10. **Pages are written sequentially** (the `Page` borrow is `&mut Document`). Parallelize layout and display-list building, not PDF emission. Enable krilla's `rayon` feature to compress in parallel. For wasm builds, drop `rayon`.
11. **Repeated content** (headers, footers, logos, watermarks) should use `Graphic` XObjects (dedup by hash) to keep 1000-page outputs small.
12. **Letterhead/background PDFs** (a common invoice feature) are available through krilla's `pdf` feature (hayro-write, `draw_pdf_page`). It is forbidden under PDF/A-2+/UA, so it is opt-in.
13. **Disable krilla's default `simple-text` feature** (rustybuzz); we shape upstream. Keep `raster-images`.

## Recommendation

1. **Primary writer: `krilla` 0.8.2 + `krilla-svg` 0.8.1**, `default-features = false, features = ["raster-images", "rayon", "pdf"]` (gate `pdf` and `rayon` behind recto features, with `rayon` off for wasm). Wrap it behind a `recto-pdf` adapter that consumes our writer-agnostic display list (§7). Do not expose krilla types publicly, so a fork or replacement stays possible.
2. **Do not** build on pdf-writer directly for v1. It would cost about 15k LOC of reimplementation (fonts, color glyphs, images, shadings, tagging, validators) for one benefit, streaming, that a small krilla patch delivers. pdf-writer stays a transitive dependency and our escape hatch for raw objects. The adapter may write raw `pdf_writer` objects only through a krilla patch, since krilla does not expose its chunks.
3. **Patches to upstream (or carry as a thin fork), in priority order:**
   - (1) custom XMP hook, for Factur-X/ZUGFeRD and custom metadata (#209)
   - (2) streaming output `Document::finish_to(W: Write)`: write page and image streams on page drop, skip renumbering, hash incrementally
   - (3) a configurable deflate level, and possibly object streams
   - Track: forms (#423/#430), PNG passthrough (#435), PDF/UA-2 (#449).
4. **Encryption:** out of scope for v1. If demanded, add an opt-in post-process with `lopdf` 0.45 (AES-256 R6) and document that it breaks determinism and PDF/A.
5. **Validation:** krilla's validators are a write-time guard. recto CI must additionally run veraPDF (PDF/A-1b/2b/2u/3b/3a/4 and UA-1) and a Factur-X XML/XMP check on golden documents, mirroring krilla's CI.
6. **Reject** printpdf (no tagging, non-deterministic IDs, in-memory op model, heavy deps) and svg2pdf (unmaintained).

## Open questions / UNVERIFIED items

- **UNVERIFIED:** krilla builds and runs on `wasm32-unknown-unknown`. It is not in krilla's CI, and the inference rests on Typst's web app. Test this in our CI.
- **UNVERIFIED:** printpdf support for blend modes, tiling patterns, overprint, ICC, CMYK images, page labels and named destinations. I did not read deeply because printpdf is rejected on other grounds.
- **UNVERIFIED:** exact `Configuration` constructor names (`configure/mod.rs`), not read line-by-line. Confirm when coding.
- The Factur-X requirements (fx namespace URI, property set, AFRelationship per profile) come from secondary vendor docs found by WebSearch. **Verify against the official Factur-X 1.0.07 / ZUGFeRD 2.3 spec** and veraPDF before implementing.
- Will krilla 0.9 (with forms, PNG passthrough, custom Info fields, and the PDF 2.0 namespace change #450) ship before our v1? Check the sparse index before pinning. A `main` dependency would violate "published crates only".
- Would upstream accept a streaming-sink and custom-XMP API? Contact the maintainer (LaurenzV) early.
- Memory figures in §3.2 are derived from code, not measured. Phase 1 should benchmark RSS on 1k- and 10k-page fixtures, with and without `rayon`.
- Byte-identity across platforms depends on flate2's backend (miniz_oxide by default). Confirm that no feature unification switches it to zlib-ng or zlib-rs in our dependency graph.
