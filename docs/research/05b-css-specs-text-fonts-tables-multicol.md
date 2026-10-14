# 05b — CSS specs: Multi-column 1, Fonts 4, Text 3, Tables 3, CSS 2.1 §8–§10 & §17 essentials

Date: 2026-10-14 · Topic slug: `cssspecs` · Companion file: `05a-css-specs-paged-fragmentation.md`

Purpose: concrete, testable requirements (numbered, with § ids from the Bikeshed sources) for the non-pagination
parts of recto's layout engine that document generation leans on: fonts & font matching, text processing and line
breaking, tables (incl. their fragmentation), multicol, and the CSS 2.1 visual formatting core (margin collapsing,
IFC/line height/strut, vertical-align, floats, positioning).

## Sources inspected

One sparse clone of `w3c/csswg-drafts` at HEAD `1c249b342ee7a0dfe0fcf7f7dc75272b1e794d52` (2026-10-14),
at `/tmp/claude-0/src/cssspecs/csswg-drafts`. License: W3C Software and Document License (repo `LICENSE.md`).
"Last commit" = `git log -1 -- <dir>/Overview.bs`.

| Spec | File | `Status` / `Work Status` (bs metadata) | Date field | Last commit touching file | Assessment |
|---|---|---|---|---|---|
| CSS Multi-column Layout 1 (`css-multicol-1`) | `css-multicol-1/Overview.bs` (2364 lines) | ED / **Testing** (TR: CR 2024-05-16, per changes appendix) | — | `b8c37b8` 2026-08-04 | Stable; well interop'd in browsers; balancing details are UA-defined. |
| CSS Fonts 4 (`css-fonts-4`) | `css-fonts-4/Overview.bs` (9710) | ED / **Revising** | — | `ef7bac0` 2026-09-13 | Matching algorithm stable since Fonts 3; `font-stretch` renamed **`font-width`** (alias kept). |
| CSS Text 3 (`css-text-3`) | `css-text-3/Overview.bs` (8805) | ED / **Testing** (CR) | — | `e2a76bd` 2026-08-14 | Stable. **Note:** letter-spacing model changed 2026-08-13 (commit `1fa76c0`, issue #10193) to "half on each side". |
| CSS Text 4 (`css-text-4`) — only for `hyphenate-character` | `css-text-4/Overview.bs` | ED / Refining | — | `1d1378d` 2026-08-14 | `hyphenate-character` lives here, not in Text 3. |
| CSS Tables 3 (`css-tables-3`) | `css-tables-3/Overview.bs` (3934) | **WD**, `Date: 2025-12-16`, Work Status **Exploring**, `Warning: not ready` | 2025-12-16 | `e13fe87` 2026-10-08 | Only spec that writes down de facto browser auto-layout; collapsed-border section is an explicit *proposal* ("implementations diverge very visibly"); height distribution partially "EDITORIAL TODO". |
| CSS 2 (2.2 ED; = CSS 2.1 + errata) (`css2`) | `css2/Overview.bs` (16511) | ED / **Stable** | — | `8b82486` 2025-12-30 | Normative baseline for §8–§10, §17. |

`css-lists-3`, `css-content-3`, `css-page-3`, `css-break-*` are covered in 05a.

ID scheme: `MC-n` multicol, `FN-n` fonts, `TX-n` text, `TB-n` tables, `V-n` CSS2 visual formatting.

---

## 1. CSS Multi-column Layout Level 1

- **MC-1 [stable]** (§the-multi-column-model L216) A block container with `column-width` or `column-count` ≠ auto is a **multicol container**; content flows into anonymous **column boxes** that are fragmentainers, each an independent BFC and the containing block for non-positioned children (so a first child's top margin does not collapse with the container's; `width:100%` resolves against the column). Floats position relative to their column. Column boxes are **not** containing blocks for abspos (the multicol container is, if positioned). Column boxes do not establish stacking contexts (L1037). Out-of-flow descendants affect balancing and block-size.
- **MC-2 [stable]** Columns arranged in **multicol lines** in the inline base direction; all columns in a line have equal width and height; gaps equal. Paginated multicol: column height constrained by page, content continues in a new line of columns on the next page; **a column box never splits across pages**.
- **MC-3 [stable]** `column-width: auto | <length [0,∞]>` (initial auto; applies to block containers except table wrappers; not inherited; used value clamped ≥ 1px). `column-count: auto | <integer [1,∞]>`. `columns: <'column-width'> || <'column-count'>`.
- **MC-4 [stable]** Pseudo-algorithm (§pseudo-algorithm L920), U = used content width of the container, gap = used `column-gap`:
  ```
  if width=auto and count=auto: not multicol
  if width=auto: N = count
  elif count=auto: N = max(1, floor((U + gap)/(width + gap)))
  else: N = min(count, max(1, floor((U + gap)/(width + gap))))
  W = max(0, (U + gap)/N − gap)
  ```
  Floor column size at ≤1px to avoid ÷0. May be computed per fragment in paged media. Used count ignores forced breaks/height constraints; *actual* count may be higher (forced column breaks → overflow columns inline-wise in continuous media / next fragment in paged media) or lower.
  Tests: `width:100px; column-width:45px; gap:0` ⇒ N=2, W=50px. `width:40px; column-width:45px` ⇒ N=1, W=40px.
- **MC-5 [stable]** (§column-gaps-and-rules L1048) `column-gap` from css-align; **`normal` = 1em** in multicol. `column-rule-color` (initial currentcolor), `column-rule-style: <line-style>` (initial none; `none`/`hidden` force used width 0; styles interpreted as in collapsing border model), `column-rule-width: <line-width>` (initial medium; snapped as border width), shorthand `column-rule`. Rule drawn in the **middle of the gap**, length = column height, takes **no space**, painted just above the container's border, only **between two columns that both have content**; may overflow if wider than gap.
- **MC-6 [stable]** (§column-span L1323) `column-span: none | all` (applies to in-flow block-level elements). `all`: forces a column break, element spans all columns of nearest multicol ancestor in the same BFC, establishes an **independent formatting context** (always, even outside multicol); content before is **balanced** across the preceding multicol line; content after starts a new multicol line.
- **MC-7 [stable]** (§cf L1759) `column-fill: auto | balance | balance-all`, initial **balance**: `balance` — balance; in fragmented contexts **only the last fragment** is balanced; `balance-all` — all fragments; `auto` — fill sequentially. Lines immediately preceding a spanner are always balanced. In continuous contexts no effect when there are overflow columns. Balancing should honour forced breaks, widows/orphans; algorithm unspecified ("minimize variations in column height"). Example: forced breaks + balance ⇒ shortest column height computed first, then fill sequentially.
- **MC-8 [stable]** Breaks inside multicol use css-break (`break-before: column`, `avoid-column`, etc.). Overflow inside multicol visible and not clipped to columns; clipping at container edges per container `overflow`. With constrained height (`height`/`max-height`) extra columns are created inline-wise (overflow columns) in continuous media; in paged media they move to the next page.

## 2. CSS Fonts Level 4

### 2.1 Font properties (property defs extracted from propdef blocks)

| Prop | Value | Initial | Inh | Computed |
|---|---|---|---|---|
| `font-family` (L151) | `[ <family-name> \| <generic-font-family> ]#` | UA | yes | list of strings/generics |
| `font-weight` (L855) | `<font-weight-absolute> \| bolder \| lighter`; absolute = `normal \| bold \| <number [1,1000]>` | normal (400) | yes | number |
| `font-width` (L1033; legacy alias `font-stretch`) | `normal \| <percentage [0,∞]> \| ultra-condensed … ultra-expanded` | normal | yes | percentage |
| `font-style` (L1205) | `normal \| italic \| left \| right \| oblique <angle [-90deg,90deg]>?` | normal | yes | keyword (+angle); bare `oblique` = 14deg |
| `font-size` (L1380) | `<absolute-size> \| <relative-size> \| <length-percentage [0,∞]> \| math` | medium | yes | absolute length; % of parent font-size |
| `font-size-adjust` (L1599) | `none \| <number [0,∞]>` | none | yes | — |
| `font` (L1823) | `[ [ <font-style> \|\| <font-variant-css2> \|\| <font-weight> \|\| <font-width-css3> ]? <font-size> [ / <line-height> ]? <font-family># ] \| <system-font-family-name>` | | | resets all font longhands incl. variant subprops, kerning, feature/variation settings etc. |
| `font-synthesis-weight` / `-style` / `-small-caps` / `-position` (L2126–2300) | `auto \| none` (style also `oblique-only`) | auto | yes | keyword |
| `font-synthesis` (L2304) | `none \| [ weight \|\| style \|\| small-caps \|\| position ]` | `weight style small-caps position` | yes | |
| `font-kerning` (L5076) | `auto \| normal \| none` | auto | yes | |
| `font-variant-ligatures` (L5170) | `normal \| none \| [ common/no-common \|\| discretionary \|\| historical \|\| contextual ]` | normal | yes | |
| `font-variant-position` (L5306) | `normal \| sub \| super` | normal | yes | |
| `font-variant-caps` (L5536) | `normal \| small-caps \| all-small-caps \| petite-caps \| all-petite-caps \| unicase \| titling-caps` | normal | yes | |
| `font-variant-numeric` (L5731) | `normal \| [ lining/oldstyle \|\| proportional/tabular \|\| diagonal/stacked-fractions \|\| ordinal \|\| slashed-zero ]` | normal | yes | |
| `font-variant-alternates`, `-east-asian`, `font-variant` (shorthand), `font-variant-emoji` | see L5908, L6484, L6627, L8233 | normal | yes | |
| `font-feature-settings` (L6691) | `normal \| <feature-tag-value>#`, `<feature-tag-value> = <opentype-tag> [ <integer [0,∞]> \| on \| off ]?` (on=1, off=0; omitted=1) | normal | yes | |
| `font-language-override` (L6943) | `normal \| <string>` | normal | yes | |
| `font-optical-sizing` (L7282) | `auto \| none` | auto | yes | |
| `font-variation-settings` (L7386) | `normal \| [ <opentype-tag> <number> ]#` | normal | yes | |
| `font-palette` (L7565) | `normal \| light \| dark \| <palette-identifier> \| palette-mix()` | normal | yes | |

- **FN-1 [stable]** Generic families (L403): complete — `serif, sans-serif, system-ui, cursive, fantasy, math, monospace`; incomplete — `ui-serif, ui-sans-serif, ui-monospace, ui-rounded`; script-specific — `generic(fangsong|kai|khmer-mul|nastaliq)`. System font keywords for `font`: `caption | icon | menu | message-box | small-caption | status-bar`.
- **FN-2 [stable]** Relative weights (§relative-weights L952), inherited w → bolder/lighter: w<100 → 400/no change; 100≤w<350 → 400/100; 350≤w<550 → 700/100; 550≤w<750 → 900/400; 750≤w<900 → 900/700; w≥900 → no change/700.
- **FN-3 [stable]** `font-width` keywords → %: ultra-condensed 50, extra-condensed 62.5, condensed 75, semi-condensed 87.5, normal 100, semi-expanded 112.5, expanded 125, extra-expanded 150, ultra-expanded 200.
- **FN-4 [guideline]** Absolute-size scaling factors (L1520): xx-small 3/5, x-small 3/4, small 8/9, medium 1, large 6/5, x-large 3/2, xx-large 2, xxx-large 3 (h6…h1 mapping). `larger/smaller`: next table entry or ratio ≈1.2–1.5 (UA). Recto must pick fixed values for determinism (medium = 16px is the de facto default).

### 2.2 `@font-face` (§font-face-rule L2633 …)

- **FN-5 [stable]** Requires `font-family` and `src`; otherwise ignored for matching. Last occurrence of a descriptor wins; unknown descriptors ignored. `@font-face` families are consulted **before** installed fonts and **hide** same-named platform fonts; if no face of an `@font-face` family loads, the family is missing — **must not** fall back to a platform font of the same name.
- **FN-6 [stable]** `src: <font-src-list>`; `<font-src> = <url> [ format(<font-format>) ]? [ tech(<font-tech>#) ]? | local(<family-name>)`.
  - `<font-format> = <string> | collection | embedded-opentype | opentype | svg | truetype | woff | woff2`; legacy strings `"woff2"`,`"woff"`,`"truetype"`,`"opentype"`,`"collection"` and `"*-variations"` (= `format(x) tech(variations)`).
  - `<font-tech> = features-opentype | features-aat | features-graphite | color-COLRv0 | color-COLRv1 | color-SVG | color-sbix | color-CBDT | variations | palettes | incremental`.
  - Parse as a list; drop entries that fail to parse or have unsupported format/tech; **if none remain, the descriptor is a parse error** (→ rule ignored).
  - Iterate entries in order; use the first that loads and parses; invalid data or missing local face → next entry. Skip download if format hint unsupported; no hint ⇒ try.
  - Relative URLs resolve against the stylesheet. Collections (`.ttc/.otc/woff2 collection`): fragment `#PostScriptName` selects the face; must exact-match; invalid PS name ⇒ skip.
  - `local(name)`: unquoted idents joined by single spaces; CSS-wide/generic keywords invalid. Matches **PostScript name or full font name** of installed fonts only; no platform substitutions.
- **FN-7 [stable]** `font-style`/`font-weight`/`font-width` descriptors (L3186): `auto | …{1,2}` ranges (inclusive; reversed ranges swapped; `bolder/lighter` disallowed; out-of-range → parse error). Initial `auto` ⇒ matches as `normal`, no variation clamping. Descriptors **override** the font file's own style data; synthesis must be based on descriptors, not file data. Variation values applied for matching are clamped to descriptor ranges and to the font's supported range.
- **FN-8 [stable]** `unicode-range: <urange>#` (initial `U+0-10FFFF`): single `U+416`, interval `U+400-4FF`, wildcard `U+4??`; >10FFFF or start>end invalid ⇒ declaration ignored. Faces with identical descriptors but different ranges form a **composite face**; overlapping ranges are checked in **reverse definition order** (last rule first).
- **FN-9 [stable]** `font-feature-settings` / `font-variation-settings` descriptors (L3637) set defaults on the face (don't affect selection). `font-named-instance: auto | <string>` (L3713). `font-language-override` descriptor. `ascent-override`, `descent-override`, `line-gap-override: normal | <percentage [0,∞]>` (L4117) — percentage × used font size replaces the font's metric (directly affects line height — very useful for metric-compatible fallback).
- **FN-10 [irrelevant for recto]** `font-display` (L3878) — loading timeline; recto loads synchronously from local/embedded resources, so treat as `block` with zero timeout.

### 2.3 Font matching algorithm (§font-matching-algorithm L4225, §font-style-matching L4349) — precise

For each character (cluster-aware, FN-13), with computed font properties:

1. Take the first family in `font-family`.
2. Generic keyword ⇒ map to a concrete family (may depend on `lang` / Unicode range).
3. Otherwise look up the name among `@font-face` families, then installed fonts (with localized-name matching, case-insensitive per §localized-name-matching). `@font-face` faces whose resources are unavailable/invalid are treated as absent; a family whose every face failed is missing (no platform fallback by name).
4. If found: assemble the family's faces; faces covering ranges are treated as one font per supported value; `unicode-range`-differing duplicates form one composite face. Narrow:
   1. **font-width**: if any face includes the desired value, drop faces that don't. Else: desired ≤100% → check narrower values descending, then wider ascending; desired >100% → wider ascending, then narrower descending. Keep only faces including the chosen value.
   2. **font-style**:
      - `italic`: faces whose italic value includes the mapped italic ⇒ keep; else italic values above desired ascending then below (positive only); else variable `ital` axis = 1; else oblique ≥11deg ascending then <11deg descending (positive only); else italic ≤0 descending; else oblique ≤0 descending.
      - `oblique a` with a ≥ 11deg: oblique values including a; else above ascending then below (positive only, down to 0); else `slnt` axis = a, or **synthetic shear** if `font-synthesis-style: auto` (ital axis never used for oblique); else italic ≥1 ascending then <1 descending; else oblique ≤0 descending; else italic ≤0 descending.
      - `oblique a` with 0 ≤ a < 11deg: oblique including a; else below descending to 0, then above; else `slnt`/synthesis; else italic <1 descending to 0 then >1 ascending; else oblique ≤0; else italic ≤0.
      - Negative angles: mirrored (−11 < a < 0 uses the "lesser" steps negated; a ≤ −11 uses the "greater" steps negated).
      - `normal`: oblique ≥0 ascending; else italic ≥0 ascending; else oblique <0 descending; else italic <0 descending.
      - Then drop faces not including the found oblique angle (or italic value). UAs may map italic and oblique onto one scale with italic 1 ≡ oblique 11deg; within `@font-face` families italic vs oblique must be distinguished via the descriptor. Synthetic oblique allowed per `font-synthesis`.
   3. **font-weight**: if a face includes the desired weight, keep only those. Else: desired in [400, 500] → weights ≥ desired ascending **up to 500**, then < desired descending, then > 500 ascending; desired < 400 → ≤ desired descending, then > desired ascending; desired > 500 → ≥ desired ascending, then < desired descending. Keep only faces including the chosen weight. (Synthetic bold faces count as existing for matching when allowed.) No rounding of fractional weights.
   4. **font-size**: matched within UA tolerance (scalable fonts: exact).
   If several faces remain, pick one deterministically (must not differ between elements of the same document).
5. If the face is from `@font-face`: if not loaded and `unicode-range` includes the char, load it; if its effective cmap supports the char, use it. For a composite face, try components in **reverse rule order**.
6. If no face or no glyph: next family (glyphs from *other faces of the same family* are not considered; exception: UA may use a synthetic-oblique of the family's default face).
7. Families exhausted ⇒ **installed font fallback** (UA-defined).
8. Still nothing ⇒ show missing-glyph (`.notdef`/last-resort).
- **FN-11 [stable]** **First available font** (used for `ex`, `ch`, line-height `normal`, the strut): first font in the list whose `unicode-range` includes U+0020 (installed fonts named directly count as full range), regardless of whether it actually has a space glyph; else UA default.
- **FN-12 [stable]** "Supports a character" = in cmap **and** shaping data available if the script requires it. PUA code points: only named (non-generic) families; never installed-font fallback ⇒ missing glyph. U+FFFD may short-circuit to missing glyph.
- **FN-13 [stable]** Cluster matching (§cluster-matching L4757): for base + combining marks, pick the first family (style-matched face) that supports the **whole** cluster; or a canonically-equivalent precomposed char; else if c1 is a variation selector, system fallback must find a font supporting b+VS (else ignore VS); else optional fallback for whole cluster; else longest supported prefix, remaining marks matched individually.

### 2.4 Synthesis, features, variations

- **FN-14 [stable]** Synthesis (§font-synthesis-intro L2098): bold (stroke emboldening), oblique (shear about glyph centre; positive angle = clockwise), small-caps, super/subscript. Variable-font axes are *not* synthesis. `font-synthesis-style: oblique-only` forbids using synthetic oblique as fallback for `italic`. `font-synthesis-position: auto` means synthesis is **required** when `font-variant-position` is set and the font lacks `sups`/`subs`.
- **FN-15 [stable]** Default features (§default-features L7060): always enable `rlig, liga, clig, calt, locl, ccmp, mark, mkmk` (+ script-required features; `vert` for upright in vertical), even with `normal`; disabled only by explicit author override.
- **FN-16 [stable]** Precedence (§feature-variation-precedence L7105), ascending: (1) defaults incl. script features; (2) variations from font-weight/width/style (only one of `ital`/`slnt`; clamp to `@font-face` descriptors, then to font); (3) language from `lang`; (4) `@font-face` `font-language-override`; (5) `@font-face` `font-named-instance`; (6) `@font-face` `font-variation-settings`; (7) `@font-face` `font-feature-settings`; (8) `font-language-override` property; (9) `font-optical-sizing` (`opsz`); (10) `font-variant-*` + `font-kerning`; (11) features from other properties (e.g. non-zero `letter-spacing` disables optional ligatures); (12) `font-variation-settings` property (clamped); (13) `font-feature-settings` property. Same feature multiple times ⇒ last wins. Missing feature ⇒ silently not applied (no fallback, no synthesis unless defined).
- **FN-17 [stable]** Mapping table for high-level properties → OpenType tags (L6700–6760): kern/vkrn ← font-kerning; liga/clig, dlig, hlig, calt ← ligatures; subs/sups ← position; smcp, c2sc, pcap, c2pc, unic, titl ← caps; lnum, onum, pnum, tnum, frac, afrc, ordn, zero ← numeric; hist/salt/cvNN/swsh/ornm/nalt ← alternates; jp78/83/90/04, smpl, trad, fwid, pwid, ruby ← east-asian.

## 3. CSS Text Level 3 (+ `hyphenate-character` from Text 4)

### 3.1 Properties (extracted propdefs)

| Prop | Value | Initial | Applies | Inh |
|---|---|---|---|---|
| `text-transform` (L598) | `none \| [capitalize \| uppercase \| lowercase] \|\| full-width \|\| full-size-kana` | none | text | yes |
| `white-space` (L1030) | `normal \| pre \| nowrap \| pre-wrap \| break-spaces \| pre-line` | normal | text | yes |
| `tab-size` (L2912) | `<number [0,∞]> \| <length [0,∞]>` | 8 | text | yes |
| `word-break` (L3381) | `normal \| keep-all \| break-all \| break-word` | normal | text | yes |
| `line-break` (L3804) | `auto \| loose \| normal \| strict \| anywhere` | auto | text | yes |
| `hyphens` (L4443) | `none \| manual \| auto` | **manual** | text | yes |
| `overflow-wrap` (alias `word-wrap`) (L4642) | `normal \| break-word \| anywhere` | normal | text | yes |
| `text-align` (shorthand, L5103) | `start \| end \| left \| right \| center \| justify \| match-parent \| justify-all` | start | block containers | yes |
| `text-align-all` / `text-align-last` (L5401/L5432) | … / `auto \| start \| end \| left \| right \| center \| justify \| match-parent` | start / auto | block containers | yes |
| `text-justify` (L5526) | `auto \| none \| inter-word \| inter-character` (+legacy `distribute`) | auto | text | yes |
| `word-spacing` (L5983) | `normal \| <length>` | normal (=0) | text | yes |
| `letter-spacing` (L6173) | `normal \| <length>` | normal (=0) | inline boxes and text | yes |
| `text-indent` (L6740) | `<length-percentage> && hanging? && each-line?` | 0 | block containers | yes; % of block's inner inline size |
| `hanging-punctuation` (L7137) | `none \| [ first \|\| [force-end \| allow-end] \|\| last ]` | none | text | yes |
| `hyphenate-character` (css-text-4 L7802) | `auto \| <string>` | auto | text | yes |

### 3.2 text-transform (§text-transform-property L598, §text-transform-order L998)

- **TX-1** `capitalize`: first typographic letter unit of each word → titlecase if lowercase; word boundaries UA-defined (UAX#29 suggested); **inline box boundaries and out-of-flow boxes do not create word boundaries**. `uppercase`/`lowercase`: **full** Unicode case mappings incl. conditional casing (Unicode Default Case Algorithms), plus language-specific rules (minimally SpecialCasing.txt, e.g. Turkish/Azeri dotted/dotless i) **only if the content language is known** (§text-transform-mapping L893). Order: case → full-width → full-size-kana. **Applied after white-space Phase I, before Phase II.** Must not affect copy/paste (→ in tagged PDF use `/ActualText` with the original text if transformed).

### 3.3 White space processing (§white-space-processing L1589, §white-space-rules L1785)

- **TX-2** Document white space = U+0020, U+0009, segment breaks (LF). CR (U+000D) is treated exactly like a space. *Other space separators* = Zs except U+0020/U+00A0.
- **TX-3 Phase I** (per inline in an IFC, before line breaking & bidi, ignoring Bidi_Control chars):
  - `normal | nowrap | pre-line` (collapsible): (1) remove collapsible spaces/tabs immediately before or after a segment break; (2) transform collapsible segment breaks per segment-break rules; (3) collapsible tab → space; (4) any collapsible space **immediately following another collapsible space — even across inline boundaries within the same IFC** — collapses to zero advance (keeps its soft-wrap opportunity).
  - `pre | pre-wrap | break-spaces`: spaces are treated as non-breaking spaces; `pre-wrap`: soft wrap opportunity at the **end** of each space/tab run; `break-spaces`: after **every** space and tab.
- **TX-4 Segment breaks** (§line-break-transform L2558): `pre, pre-wrap, break-spaces, pre-line` ⇒ preserved LF (forced break). Otherwise: drop a segment break following another; remaining ones become a space **or are removed — UA-defined in L3** (de facto: space, except Firefox removes between CJK; recto: always space, except optionally between two East Asian Wide characters).
- **TX-5 Phase II** (§white-space-phase-2 L2118), per line: (1) remove collapsible spaces at line start; (2) preserved tabs: tab-size 0 ⇒ not rendered; else advance to the next tab stop (multiples of tab size from the **start content edge of the nearest block container ancestor**), skipping to the next stop if the distance < 0.5ch; (3) remove collapsible spaces at line end (and trailing U+1680 for collapsible modes); (4) any remaining trailing white space / other space separators / preserved tabs: `normal|nowrap|pre-line` ⇒ **hang unconditionally**; `pre-wrap` ⇒ hang unconditionally unless followed by a forced break, then *conditionally* hang (may visually collapse overflowing advances); `break-spaces` ⇒ never hang, never collapse (they wrap like visible chars).
- **TX-6** `tab-size` number = multiples of the space advance of the nearest block container (incl. its letter-/word-spacing); negative invalid.
- **TX-7** (CSS2 / text note) Anonymous blocks consisting entirely of collapsible white space are removed (so whitespace between block elements disappears); line boxes with no text, no preserved white space, no inline elements with non-zero margins/padding/borders and no in-flow content are zero-height and "do not exist" (CSS2 §9.4.2, V-6).

### 3.4 Line breaking (§line-breaking L2981, §line-break-details L4808)

- **TX-8** Must wrap at a soft wrap opportunity to minimise inline overflow when wrapping is enabled. Forced breaks: preserved segment breaks and **any BK/NL-class char regardless of white-space**. Must honour WJ, ZW, GL, ZWJ classes (except `line-break:anywhere` / `overflow-wrap:anywhere`), never break within a typographic character unit (CM, SG). UAX #14 is the baseline. Punctuation-break prioritisation recommended ("check /etc" must not break after "/" when a space is available).
- **TX-9** Out-of-flow boxes and inline box boundaries do **not** create opportunities. There **is** an opportunity before and after every **atomic inline** (images, inline-blocks), even next to NBSP; but **not** between atomic inlines and adjacent GL/WJ/ZWJ characters (except U+00A0).
- **TX-10** For an opportunity created by a disappearing char (space), the properties of the box containing that char control it; for between-character opportunities, `white-space` of the nearest common ancestor controls; which element's `word-break`/`line-break`/`overflow-wrap` applies is undefined. A break at the first/last char of a box happens at the box's margin edge (box not split between content edge and content).
- **TX-11** Shaping scripts broken mid-word (break-all, anywhere, hyphenation) keep their joining forms as if unbroken. If the UA lacks a dictionary for a language needing one (Thai, Khmer, Lao…), it **must** assume opportunities between letters.
- **TX-12** `word-break`: `normal` customary (Korean: between Hangul/Hanja; Ethiopic: no intra-word); `break-all`: letters (and NU/AL/AI/ID chars) treated as ID ⇒ break between any letters, **no hyphenation**; `keep-all`: no breaks between typographic letter units (CJK text stays together, breaks at spaces/punct); `break-word` (legacy): = `normal` + `overflow-wrap: anywhere`.
- **TX-13** `line-break`: `auto | loose | normal | strict` choose CJK strictness (small kana, iteration marks, hyphens, etc.); `anywhere`: opportunity around **every** typographic character unit incl. punctuation and preserved spaces, ignoring GL/WJ/ZWJ and word-break; no prioritisation; no hyphenation.
- **TX-14** `overflow-wrap`: `normal` — only allowed breaks (keep-all may relax to normal if no break point); `anywhere` — break an otherwise-unbreakable sequence at arbitrary points (graphemes kept together, no hyphen inserted) **and these opportunities count for min-content size**; `break-word` — same but **not** considered for min-content (so tables/shrink-to-fit don't collapse to 1 char wide). Only effective when wrapping is allowed.
- **TX-15** `hyphens` (§hyphenation L4272): `none` — no hyphenation even at U+00AD (visible hyphens still break); `manual` (initial) — only at U+00AD (and similar), inserting language-appropriate hyphen char; `auto` — also dictionary-based, but if a word contains U+00AD, automatic points are ignored for that word unless a part still doesn't fit. Auto-hyphenate **only if the content language is known and a resource exists**. Inline element boundaries and out-of-flow elements are ignored for "word". Hyphen glyph from a soft hyphen is styled by the soft hyphen's properties.
- **TX-16** `hyphenate-character: auto | <string>` (Text 4): string shown at the break (before the break by default); UA may truncate to a limited number of typographic character units.

### 3.5 Alignment & justification (§text-align-property L5103 …)

- **TX-17** `text-align` shorthand sets `text-align-all` (and resets `text-align-last: auto`), except `justify-all` (both = justify) and `match-parent` (both = match-parent). `start/end` per direction; `left/right` = line-left/right; `match-parent` = inherit, but inherited `start`/`end` resolved against the **parent's** direction to `left`/`right`; on root computes to `start`.
- **TX-18** `text-align-last: auto` ⇒ last line / line before forced break aligned per `text-align-all`, **except `justify` ⇒ `start`**.
- **TX-19** If content (after justification) overflows the line box, it is **start-aligned** (overflows the end edge). Justification with non-collapsible white space may be skipped (UA not required); if done, tab stops must still align.
- **TX-20** Justification (§expanding-text L5745): distribute space at *justification opportunities* (word separators; between CJK letters…) — in addition to letter/word-spacing; distributed space at word separators follows word-spacing rules, between characters follows letter-spacing rules. If a line has an opportunity and is to be justified, **it must be justified**. Must not break required ligatures. `text-justify: none` disables; `inter-word` = expand word separators only; `inter-character` = between typographic character units; `auto` UA-chosen (recommended: word separators + CJK).
- **TX-21** `word-spacing` (L5983): extra spacing added to each word-separator remaining after white-space processing (U+0020, U+00A0, U+1361, U+10100/10101, U+1039F, U+1091F — **not** U+3000/U+2000–200A, not punctuation), "should" be half on each side; zero-advance separators (U+200B) get none. `normal` computes to 0.
- **TX-22** `letter-spacing` (L6173, changed 2026-08-13): added **half on each side of each typographic character unit**, **not applied at the start or end of a line**; applied after bidi reordering; between inlines with different values the effective gap is the average; runs of atomic inlines count as one unit; invisible Cf chars (ZWSP) ignored. Non-zero effective spacing (letter-spacing or justification) ⇒ **disable optional ligatures** (`font-feature-settings` overrides). Note this differs from Chromium/WebKit legacy behaviour (spacing appended after each character, incl. at line end) — **recto must pick one; compatibility with browser output suggests offering the legacy model** (UNVERIFIED how quickly browsers adopt the new model).
- **TX-23** `text-indent`: treated as a margin at the start edge of the first formatted line (only after a forced break with `each-line`; `hanging` inverts which lines). % of block's inner inline size.

## 4. Tables — CSS Tables 3 (de facto browser algorithm) + CSS 2.1 §17 (normative baseline)

### 4.1 Structure & anonymous-object fixup (tables-3 §table-structure L198, §fixup L442; CSS2 §anonymous-boxes L14021)

- **TB-1 [stable]** Display types: `table, inline-table, table-row, table-row-group, table-header-group, table-footer-group, table-column, table-column-group, table-cell, table-caption`. Only the **first** `table-header-group` is the header (displayed before all rows) and the first `table-footer-group` the footer (after all rows); additional ones act as row groups. Replaced elements with internal table display types are inline-level.
- **TB-2 [stable]** Fixup, three stages (out-of-flow children are treated as zero-size inlines):
  1. **Remove irrelevant boxes**: children of `table-column`; non-column children of `table-column-group`; anonymous whitespace-only inlines between two table-non-root siblings; whitespace-only anonymous inlines that are first/last child of a tabular container whose sibling (if any) is table-non-root. (CSS2 phrasing: whitespace between proper table descendants that are captions/internal boxes.)
  2. **Generate missing child wrappers**: anonymous `table-row` around consecutive non-proper-table-children of a table root; anonymous `table-row` around consecutive non-row children of a row group; anonymous `table-cell` around consecutive non-cell children of a row.
  3. **Generate missing parents**: anonymous `table-row` around consecutive `table-cell`s whose parent isn't a row; anonymous `table`/`inline-table` around consecutive misparented proper table children (inline-table if parent is inline/ruby/inlinifying); misparented = row not in row-group/table; column not in column-group/table; row-group/column-group/caption not in table. Then an anonymous **table-wrapper** box (block, or inline-block for inline-table) around each table root; it establishes a BFC, holds captions + table grid; its width = table grid's border-box width; percentages relative to the wrapper's containing block.
  Anonymous fixup boxes: transparent background, 0 padding, no border; inherit through the box tree. (`float`/`position` blockify internal table boxes before fixup.)
- **TB-3** Grid dimensioning uses the **HTML table formatting algorithm** (rowspan/colspan only from HTML `td/th` attributes — no CSS span property at this level); then **track merging** (auto mode: merge consecutive tracks spanned by exactly the same cells and not explicitly defined by a column/row box; fixed mode: rows only). Missing-cells fixup: append anonymous cells so each row fills all columns; those cells **don't paint backgrounds**.

### 4.2 Properties

- **TB-4** `table-layout: auto | fixed` (table grid boxes; not inh). **Fixed mode** iff `fixed` **and** table `width` ≠ `auto`/`max-content` (CSS2 also lets UAs apply fixed with auto width — tables-3 does not).
- **TB-5** `border-collapse: separate | collapse` (inherited!). `border-spacing: <length>{1,2}` (initial 0 0; inherited; separated mode only; non-negative).
- **TB-6** `caption-side: top | bottom` (inherited; applies to captions). Captions are between table margins and border; centered horizontally: left = caption margin-left + ½(table width − caption width − horizontal margins). Multiple captions stack with margin collapsing between them.
- **TB-7** `empty-cells: show | hide` (inherited; cells; separated mode only): `hide` ⇒ no borders/backgrounds for empty cells (no floats, no in-flow content other than collapsed white space), as if `visibility:hidden`.
- **TB-8** Style overrides (§style-overrides L1069): position/float/margins/top..left/overflow/opacity/filter/clip/transform/etc. on the table apply to the **wrapper**; table `overflow` other than visible/clip/hidden ⇒ visible; all properties of columns/column-groups ignored unless stated (width, background, border(collapsed), visibility:collapse used); margin/padding/overflow/z-index of tracks ignored; **cell margins ignored**; collapsed mode: table padding ignored, border-spacing ignored, **border-radius ignored** on all table boxes.

### 4.3 Table measures (§content-measure L1359) — auto mode

- **TB-9** Undistributable space = border-spacings between cells and between table border and edge cells + table padding.
- **TB-10** Cell intrinsic offsets: separated ⇒ cell horizontal padding+border; collapsed ⇒ padding + **half the winning border width**. Offsets-adjusted width/min/max of cells subtract border/padding per `box-sizing`.
- **TB-11** Cell outer min-content = `max(min-width, min-content)` + offsets. Cell outer max-content: non-constrained column: `max(min-width, width, min-content, min(max-width, max-content))`; constrained column: `max(min-width, width, min-content, min(max-width, width))`, + offsets. Column/colgroup: min = `max(min-width, width)`, max = `max(min-width, min(max-width, width))`. Percentage contribution = `min(% width, % max-width)` (non-% ⇒ 0% / ∞). Percent `min-width` ignored.
- **TB-12** Column measures: start with span-1 cells (min = max of column/colgroup outer min & span-1 cells' outer min; max likewise; intrinsic % = max of % contributions), then incorporate cells of span N=2,3,… using the proportional formulas at L1600–1700 (min-content distributes by (max−min) ratio up to baseline max, then by max-content ratio; max-content by max-content ratio; % by non-spanning max-content ratio among columns with 0%, else equally). Final column intrinsic % = min(its %, 100% − Σ % of **prior** columns) (order-dependent). A column is **constrained** if its column, colgroup or any span-1 cell has a non-auto, non-% width. Fixed mode: only first-row cells count, and cell min/max are 0 unless a length-percentage width is specified.
- **TB-13** Table width (§computing-the-table-width L1763): CAPMIN = max caption min-content contribution; GRIDMIN = Σ column min + spacing/borders; GRIDMAX = Σ column max + spacing/borders. used min-width = max(resolved min-width, CAPMIN, GRIDMIN). If `width` ≠ auto: used = max(resolved width, used min-width). If auto: used = max(min(GRIDMAX, containing block width), used min-width) — tables use **fit-content**, not stretch. Assignable width = used − total horizontal border spacing ((#cols + 1) × h-spacing in separated mode).
- **TB-14** Width distribution (§width-distribution-algorithm L1947): sizing types: percent-column (only % constraints ≠ 0%), pixel-column (lengths), auto-column. Four sizing guesses (non-decreasing): **min-content**; **min-content-percentage** (% cols get max(%·assignable, min)); **min-content-specified** (+ constrained cols get max-content); **max-content** (% cols as before, others max-content). If assignable ≤ Σ max-content guess: **linear interpolation between the two consecutive guesses** bracketing the assignable width. Else start from max-content guess and distribute excess (§distributing-width-to-columns L2088): (1) non-constrained cols with 0% and max>0, ∝ max-content; (2) else non-constrained 0% cols, equally; (3) else constrained 0% cols with max>0, ∝ max-content; (4) else cols with % > 0, ∝ %; (5) else all cols with originating cells, equally; (6) else all cols equally.
- **TB-15** Fixed mode (§width-distribution-in-fixed-mode L2066 + CSS2 §17.5.2.1 L14576): column widths from `<col>` widths, else first-row cell widths (spanning cell width divided across), remaining columns share remaining space equally; % and auto columns have min 0; % cells ignore padding/border; % overflow ⇒ scale percentages to fit exactly; calc(%+px) counted as two columns. Excess: to columns with no width equally; else ∝ length widths; else ∝ %; else equally. Content of cells never affects widths; overflow handled per `overflow` (clip/visible).
- **TB-16 [underspecified, CSS2]** CSS 2.1 §17.5.2.2 (L14636) auto layout is **non-normative** ("UAs are not required to implement this algorithm"), with MCW/max per cell, spanning-cell widening "by approximately the same amount", colgroup min widths. tables-3 TB-12–TB-14 is the de facto browser (Gecko/Blink/WebKit) behaviour and should be recto's reference.

### 4.4 Heights, rows, vertical-align (§height-distribution L2174)

- **TB-17** Table height = Σ row heights + spacing/borders; specified `height` is a **minimum** for the grid. Row min height = max(row's definite height (% → 0), definite heights of cells spanning only that row, ROWMIN from first-pass layout). Percent heights inside cells: first pass treat as auto (overflow visible/clip/hidden or replaced) or 0; second pass after distribution resolves them **if the cell has a length height or the table has a length/% height**.
- **TB-18** Row layout: cells laid out at their column widths with auto height; cell baseline = first in-flow line box or first in-flow table-row, else bottom content edge (may lie below the border). `vertical-align` on cells: `baseline` (align with first spanned row's baseline), `top` (top of first spanned row), `bottom` (bottom of last spanned row), `middle` (centre of spanned rows); other values → baseline. Row baseline = max(top-to-baseline) over baseline cells; no baseline cells ⇒ bottom content edge of lowest cell. Table baseline = first row's baseline, else bottom content edge. Order: baseline cells → top cells → grow row for bottom/middle cells → position the rest. Cells shorter than their row(s) get extra top/bottom padding (content doesn't move).
- **TB-19** Row-spanning cells distribute height using the column-measure algorithm on rows; height on row groups ignored. Height distribution: base size vs reference size (second pass with % resolved); if table height ≤ Σ reference: weighted mean of base/reference; else auto-height rows (only content-sized) get the excess equally; else all rows equally. (Partly "EDITORIAL TODO" — browser behaviours differ; recto: implement this text.)

### 4.5 Borders & backgrounds

- **TB-20 [CSS2, normative & what browsers do]** Collapsed conflict resolution (§border-conflict-resolution L15110): (1) `hidden` wins and suppresses; (2) `none` lowest; (3) wider wins; equal width ⇒ `double > solid > dashed > dotted > ridge > outset > groove > inset`; (4) differing only in colour ⇒ cell > row > row group > column > column group > table; same type ⇒ the one further **left (ltr) / right (rtl) and further top** wins. Borders are centred on grid lines; table's left/right border width = ½ of first row's first/last cell collapsed border (excess spills into margin); top/bottom = ½ max collapsed border of edge cells. Row width equation with half borders (L15060).
- **TB-21 [tables-3 proposal]** Harmonization algorithm (L1181–L1358): per cell, gather the set of borders sharing an edge (transitively through rowspans), pick most "specific" (hidden > wider > style order double, solid, dashed, dotted, ridge, outset, groove, inset, none), also considering contiguous column/colgroup/row/rowgroup borders; then **halve** used widths for layout; table border = ½ max width, painted by cells; cells paint borders at 2× clipped to their border box (contested pixels go to top-left cell). Explicitly a breaking-change proposal (ISSUE 604/606). Recto: implement CSS2 rule semantics (TB-20) with the tables-3 geometry (half widths) — that's what produces browser-matching output.
- **TB-22** Table background/border paint area excludes captions (grid + spacings, + padding, + border). Collapsed mode: non-empty table's own borders are **not painted** (cells paint them) unless `border-image`.
- **TB-23** Cell background layers (bottom→top): table (painted by table), column group, column, row group, row, cell — each group background positioned/sized against the **group's** area (not the cell's), painted within each cell. Cells paint in DOM order.
- **TB-24** `visibility: collapse` on rows/columns removes the track from layout (issue 478: semantics unresolved).
- **TB-25** Fragmentation of tables — see 05a BRK-21…BRK-23 (rows < ½ fragmentainer kept whole; freely-fragmentable rows split cell-by-cell with no repainted top border; repeat header/footer groups ≤ ¼ page each).

## 5. CSS 2.1 visual formatting essentials (css2 §8–§10)

- **V-1 Margin collapsing** (§collapsing-margins L5424): only vertical; root margins don't collapse; adjoining iff in-flow block-level boxes in the same BFC, no line boxes/clearance/padding/border between, and edges are: parent top + first in-flow child top; bottom + next sibling top; last child bottom + parent bottom **if parent `height:auto`** (and min-height 0); a box's own top+bottom if it doesn't establish a BFC, min-height 0, height 0/auto, no in-flow children (or all collapse through) and contains no line box. Result = max(positives) + min(negatives) (i.e. max positive − max |negative|; all negative ⇒ −max |neg|). Floats, abspos, inline-blocks, BFC roots don't collapse with children. Clearance blocks parent-bottom collapsing. Collapse-through element position: same as parent top if collapsed with parent top; else as if it had a non-zero bottom border.
- **V-2 BFC** (§block-formatting L6691): established by floats, abspos, non-block block containers (inline-block, table-cell, table-caption), and blocks with overflow ≠ visible. Children's left outer edge touches containing block left even with floats (line boxes shorten), unless the child is a BFC root/table/replaced block — whose **border box must not overlap float margin boxes** (L7005; may be narrowed or placed below).
- **V-3 Width equation** (§blockwidth L8652): `ml + bl + pl + width + pr + br + mr = cb width`; if width non-auto and too big, auto margins → 0; over-constrained ⇒ ignore `margin-right` (ltr) / `margin-left` (rtl); one auto ⇒ solve; `width:auto` ⇒ other autos 0, solve width; both margins auto ⇒ equal (centering). Shrink-to-fit = `min(max(preferred minimum, available), preferred)` (L8836).
- **V-4 Abspos** (§abs-non-replaced-width L8730): `left + ml + bl + pl + width + pr + br + mr + right = cb width`; six-case rule table (all three auto ⇒ static position + shrink-to-fit; over-constrained ⇒ ignore `right` in ltr; both margins auto with fixed left/width/right ⇒ equal unless negative). Static position from hypothetical static box; fixed elements use the ICB for static position. Vertical analog §10.6.4. **Paged media: `position: fixed` boxes are repeated on every page**; those larger than the page area are clipped; parts outside the ICB don't print (§fixed-positioning L7506) — the classic way to put a footer/signature/watermark on every page in browser-targeted templates.
- **V-5 BFC root auto height** (§root-height L9420): only inline children ⇒ top of first line box to bottom of last; block children ⇒ top margin edge of first to bottom margin edge of last child; abspos ignored; relpos offsets ignored; **then extended to include floats' bottom margin edges** (only floats participating in this BFC).
- **V-6 IFC** (§inline-formatting L6720): line boxes stacked without gaps, width from containing block minus floats; `text-align` distributes; `justify` may stretch spaces in inline boxes but **not inline-blocks/inline-tables**; split inline boxes get no margin/border/padding at split points (`box-decoration-break: slice`); lines with no text, no preserved white space, no inline with non-zero margin/padding/border, no in-flow content, not ending in a preserved newline ⇒ **zero-height and treated as non-existent** (matters for margin collapsing).
- **V-7 Line box height** (§line-height L9545, §leading L9583): (1) each inline-level box height: replaced/inline-block/inline-table = margin box; inline box = its `line-height`; (2) align per `vertical-align` (top/bottom aligned to minimise line height); (3) line height = top-most box top to bottom-most box bottom, **including the strut**. Empty inline elements still contribute. Per glyph: A, D from font (recommend OS/2 `sTypoAscender`/`sTypoDescender`, else hhea `ascent`/`descent` — note browsers actually use hhea or `USE_TYPO_METRICS` flag; UNVERIFIED cross-engine); L = line-height − (A+D); A' = A + L/2, D' = D + L/2 (L may be negative); inline box height = exactly `line-height`. Backgrounds/borders of inline boxes may bleed into adjacent lines; paint in document order.
- **V-8 Strut** (L9600+): each line box starts with a zero-width inline box with the block container's **first available font** and `line-height` — so the block's own line-height is the minimum line height. `line-height: normal` ⇒ "reasonable" value from font metrics (≈1.0–1.2; de facto: ascent+descent+lineGap of the first available font — or `line-gap-override` etc.), computed stays `normal`; `<number>` inherits as the number; `%`/length compute to absolute.
- **V-9 vertical-align** (inline): `baseline` (no baseline ⇒ bottom margin edge on parent baseline), `middle` (midpoint at parent baseline + ½ parent x-height), `sub`/`super` (UA offsets, font size unchanged), `text-top`/`text-bottom` (parent content area), `<percentage>` of own line-height, `<length>` raise/lower; `top`/`bottom` align the **aligned subtree** (box + descendants not top/bottom aligned) to line box top/bottom. inline-table baseline = first row; **inline-block baseline = its last line box, or bottom margin edge if none or overflow ≠ visible**.
- **V-10 Floats** (§float-position L7159): nine precise rules — float outer edge within containing block; left floats stack left-to-right or below earlier left floats; left float right edge not past an adjacent right float's left edge; float top not above containing block top nor above earlier blocks/floats' outer tops nor above line boxes containing earlier content; a left float with another left float to its left may not stick out of the right edge; **as high as possible, then as far left/right as possible** (higher preferred). Floats between collapsing margins are positioned as if in an empty anonymous block parent. `clear` (L7278): clearance = enough to put the border edge below the relevant floats' bottom outer edge (two allowed computations; clearance may be negative/zero); clearance inhibits margin collapsing.
- **V-11 display/position/float interplay** (§dis-pos-flo L7586): `display:none` ⇒ nothing; abspos/fixed ⇒ float computes to none and display is blockified; float ⇒ blockified; root ⇒ blockified. Blockification table: inline-table → table; inline, table-*, inline-block → block.

---

## Findings that affect recto's design

1. **Font matching must be a deterministic pure function** over (computed style, char/cluster, font database). The spec allows UA choice only in tie-breaks and fallback; recto should fix both (sorted by family name + file hash) so output is byte-identical across machines. With `--no-system-fonts` (scratch container), the "installed fonts" set is exactly the embedded/bundled fonts — specify which bundled faces back each generic family.
2. **`@font-face` `src` parsing is list-based with skip-on-unsupported** (FN-6): recto should support `truetype/opentype/woff/woff2/collection` + `tech(variations)` (and `color-COLRv0/1`, `color-CBDT` if the rasteriser/PDF writer can embed them) and reject the rest at parse time — a whole `src` with no supported entry invalidates the rule.
3. **`unicode-range` composite faces and reverse-order lookup** (FN-8) are commonly used by Google-Fonts CSS (subset per script); support is required for real-world stylesheets.
4. **Synthesis is needed for PDF output too**: synthetic bold (stroke via PDF text render mode 2 + line width) and oblique (text matrix shear) are cheap in PDF; implement both, gated by `font-synthesis`. Synthetic small-caps/super/sub are optional.
5. **Default OpenType features + 13-step precedence** (FN-15/FN-16) are one function building the HarfBuzz/rustybuzz feature list; tabular numerals (`font-variant-numeric: tabular-nums` → `tnum`) are heavily used in invoices — must be supported.
6. **White space Phase I/II + segment-break transformation + hanging** (TX-3…TX-5) determine trailing-space behaviour that affects right/justified alignment in invoices; Phase I collapsing crosses inline boundaries (needs IFC-level text buffer, not per-element).
7. **Line breaking = UAX#14 + CSS overlays** (atomic-inline opportunities, `word-break`, `line-break`, `overflow-wrap`); `overflow-wrap: anywhere` vs `break-word` differ only in min-content contribution — critical for table column sizing with long IDs/URLs/IBANs.
8. **Hyphenation**: default `hyphens: manual` means only soft hyphens; `auto` requires a dictionary per language (bundling patterns increases binary size — make it optional feature/data).
9. **letter-spacing model changed in Aug 2026** (TX-22): spec now = half on each side and none at line edges; browsers (which users diff against) still append trailing spacing (UNVERIFIED current status). Recommend implementing the spec model but keep a compat flag.
10. **Tables: implement tables-3 auto layout (TB-11…TB-14) and fixed layout (TB-15) exactly**; CSS2's auto algorithm is non-normative. Use CSS2 border-conflict precedence (TB-20) — tables-3's harmonization is an unadopted proposal. Rows/height distribution per TB-17…TB-19.
11. **The table wrapper box** (TB-2/TB-8) must be a real box: margins/position/float go to the wrapper; captions live in it; table backgrounds exclude captions. Header/footer groups are reordered (TB-1) — affects repetition across pages (05a BRK-23).
12. **Line box height = strut + aligned subtrees with half-leading** (V-7/V-8). Use the font's ascent/descent consistently (choose hhea vs OS/2 typo per `USE_TYPO_METRICS` like browsers) and honour `ascent-/descent-/line-gap-override` — this is what makes recto's line positions match Chrome's to sub-pixel.
13. **Multicol for v1 is cheap if limited**: columns are just fragmentainers of fixed width; `column-fill: balance` needs a balancing search (binary search on column height with re-layout) — acceptable for short multicol blocks (receipts, labels); spanners and nested multicol can be deferred.
14. **Margin collapsing + clearance + zero-height line boxes** (V-1/V-6) interplay with fragmentation margin truncation (05a BRK-16) — collapse first, then truncate at breaks.

## Recommendation — "Requirements recto v1 must implement" vs "defer"

### Must implement in v1
| Req | Justification |
|---|---|
| FN-1…FN-9, FN-11…FN-13 font properties, `@font-face` (url/local/format/tech/unicode-range/descriptors/metric overrides), full matching algorithm incl. cluster matching | Every document; deterministic output depends on it. |
| FN-14 synthetic bold/oblique; FN-15…FN-17 default features, precedence, `font-variant-numeric/-caps/-ligatures/-position`, `font-feature-settings`, `font-kerning` | Tabular figures, small caps, kerning in invoices/contracts. |
| `font-variation-settings`, `font-optical-sizing`, `font-named-instance` | Variable fonts are now the default from Google Fonts; low cost with a shaping engine that supports variations. |
| TX-1 text-transform (case + full-width) | Headings/labels. |
| TX-2…TX-7 white-space incl. `pre-wrap`, `pre-line`, `break-spaces`, tab-size | Addresses, code snippets, pre-formatted receipts. |
| TX-8…TX-15 UAX#14 line breaking, `word-break`, `line-break`, `overflow-wrap`, `hyphens: none/manual` (+ `auto` behind a feature with bundled patterns for a few languages) | Long tokens in tables; CJK invoices. |
| TX-16 `hyphenate-character` | Trivial once hyphens exist. |
| TX-17…TX-23 text-align (all values incl. match-parent, justify, justify-all), text-align-last, text-justify (none/inter-word/auto), word-/letter-spacing, text-indent | Core typography. |
| TB-1…TB-20, TB-22…TB-25 complete table model, auto & fixed layout, collapsed/separated borders with CSS2 precedence, captions, empty-cells, vertical-align in cells, row/col spans, table fragmentation & header repetition | Tables are the backbone of invoices/statements/reports. |
| V-1…V-11 CSS2 block/inline/float/positioning core | Foundation. |
| MC-1…MC-5, MC-7, MC-8 basic multicol (count/width/gap/rule, fill auto/balance, column breaks, paged continuation) | Brief says "multicol where cheap": labels, receipts, glossaries. |

### Defer (post-v1)
| Req | Justification |
|---|---|
| MC-6 `column-span: all` + nested multicol | Requires splitting multicol into lines/spanners; rare in generated documents. |
| `column-fill: balance-all` | Rare. |
| FN-10 `font-display`, `font-palette`/`@font-palette-values`, `font-variant-emoji`, `@font-feature-values` + `font-variant-alternates` named values | Not needed for static PDFs / rare. |
| `font-size-adjust` | Rare in documents; cheap later. |
| TX-21/TX-22 language-specific justification (`inter-character` nuances, cursive elongation), `hanging-punctuation` | Typographic polish; post-v1. |
| `text-transform: full-size-kana`, `line-break` strictness levels beyond UAX#14 defaults | CJK polish; implement `normal` mapping first. |
| TB-21 tables-3 harmonization proposal | Not adopted; would diverge from browsers. |
| TB-24 `visibility: collapse` on tracks | Unresolved semantics. |
| `caption-side` Gecko `left/right` | Non-standard. |

## Open questions / UNVERIFIED items

1. **UNVERIFIED**: whether Chromium/WebKit/Gecko have shipped the 2026-08 letter-spacing "half on each side" model (TX-22); affects pixel-compat with Chrome print output.
2. (resolved) text-transform mappings: full Unicode case mappings + SpecialCasing language rules when language known (L893).
3. (resolved) CSS2 §9.6.1: fixed boxes repeat on every page in paged media (L7506) — recto v1 must implement this (wkhtmltopdf/Chrome templates rely on it).
4. Ascent/descent source: CSS2 recommends OS/2 typo metrics; browsers commonly use hhea unless `USE_TYPO_METRICS` (and Chrome/Skia differ per platform) — needs a decision and a reference test set (see fonts research file if any).
5. Segment-break transformation (TX-4) is UA-defined; recto's choice (space everywhere vs CJK removal) must be documented.
6. tables-3 height distribution is partly "EDITORIAL TODO" and browsers differ (cases 1–13 in the source notes) — recto should snapshot-test against Chromium for the common cases (percentage rows, rowspans).
7. tables-3 `Status: WD` + `Warning: not ready` — the auto-layout text is nonetheless the only precise reference; WPT `css/css-tables/` should be the conformance oracle.
8. `hyphens: auto` dictionaries: licensing/size of hyphenation patterns (TeX `hyph-utf8` patterns are mostly MIT/LPPL) — not investigated here.
