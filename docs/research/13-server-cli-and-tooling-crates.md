# 13 — Server, CLI, networking, barcode, test and runtime tooling crates

Date: 2026-10-14. Topic slug: `misc`. Scope: the "everything around the engine" crates for recto: HTTP server mode, the optional `net` feature's HTTP client (SSRF-safe), CLI and compat shims, `recto watch`, barcodes/QR, test/bench/fuzz tooling, and runtime utilities.

Method: latest non-yanked version taken from `https://index.crates.io/` (sparse index, includes `rust_version`), then a shallow clone of the source repo at the matching tag. File refs are relative to the clone root under `/tmp/claude-0/src/misc/<dir>/`. Rows marked "meta" were checked only via `git show HEAD:Cargo.toml` on a blob-less clone at the tag (version, license and MSRV verified, API not inspected).

## Sources inspected

| Crate | Version (index) | Tag / commit inspected | License (Cargo.toml) | MSRV | Last commit at tag | Maintenance |
|---|---|---|---|---|---|---|
| axum | 0.8.9 | `axum-v0.8.9` c59208c86fde | MIT | 1.80 | 2026-04-06 | Active (tokio-rs) |
| tower-http | 0.7.1 | `tower-http-0.7.1` c9414514a421 | MIT | 1.65 | 2026-08-31 | Active |
| tower | 0.5.3 | `tower-0.5.3` 4b0a6b0e688b (meta + 1 file) | MIT | 1.64 | 2026-01-12 | Active |
| tokio | 1.53.3 | `tokio-1.53.3` a85c3f5baa29 (meta) | MIT | 1.71 | 2026-10-13 | Active |
| hyper | 1.12.0 | `v1.12.0` 7f67699ce32d (meta) | MIT | 1.63 | 2026-10-06 | Active |
| hyper-util / multer / async-compression | 0.1.21 / 3.1.0 / 0.4.50 | index only | — | 1.85 / — / 1.83 | — | transitive |
| tiny_http | 0.12.0 | index only | — | — | — | Stale (brief note only) |
| may_minihttp | 0.1.11 | index only | — | — | — | Niche (brief note only) |
| ureq | 3.4.2 | `3.4.2` 2e9ef24a80e1 | MIT OR Apache-2.0 | 1.85 | 2026-09-13 | Active (algesten) |
| reqwest | 0.13.5 | `v0.13.5` de55373434f0 | MIT OR Apache-2.0 | 1.85.0 | 2026-09-08 | Active |
| rustls / ring / aws-lc-rs | 0.23.46 / 0.17.14 / 1.18.2 | index only | — | 1.71 / 1.66 / 1.71 | — | Active |
| clap | 4.6.7 | `v4.6.7` 13f2db5072d6 | MIT OR Apache-2.0 | 1.85 | 2026-09-14 | Active |
| clap_complete | 4.6.11 | `clap_complete-v4.6.11` 2cb76fdf3853 (meta). API read at v4.6.7 tree, where it is 4.6.10 | MIT OR Apache-2.0 (workspace) | 1.85 | 2026-09-15 | Active |
| clap_mangen | 0.3.3 | in `v4.6.7` tree | MIT OR Apache-2.0 | 1.85 | — | Active |
| lexopt | 0.3.2 | `v0.3.2` f52c6a6 | MIT | none declared | 2026-02-28 | Low-churn, stable |
| notify | 8.2.0 | `notify-8.2.0` a1d7c2d8f807 | **CC0-1.0** | 1.77 (1.85 at debouncer tag) | 2025-08-03 | Active. 9.0.0-rc.1..rc.5 tags exist |
| notify-debouncer-full | 0.7.0 | `debouncer-full-0.7.0` e4a0ea8 | MIT OR Apache-2.0 | 1.85 | 2026-01-23 | Active. 0.8.0-rc.2 exists |
| qrcode | 0.14.1 | `v0.14.1` 0695f037c5b4 | MIT OR Apache-2.0 | 1.67.1 | 2024-07-06 | Slow (no commits for about 2 years) |
| fast_qr | 0.14.0 | HEAD 53e8c9930e98 | MIT | 1.59 | 2026-09-01 | Active |
| qrcodegen | 1.8.0 | HEAD 3c6d0b3cefb4 (`rust/`) | MIT | none | 2026-08-31 | Reference implementation (Nayuki) |
| barcoders | 2.0.0 | `v2.0.0` 05122c29ca08 | MIT OR Apache-2.0 | none | 2024-04-04 | Slow |
| rxing | 0.9.3 | `v0.9.3` de4497be20a7 | Apache-2.0 | 1.85 (edition 2024) | 2026-09-16 | Active (ZXing port) |
| datamatrix | 0.3.3 | HEAD af18953 (jannschu/datamatrix-rs) | Apache-2.0 OR MIT | none | 2026-06-04 | Low-churn |
| insta | 1.49.0 | `1.49.0` 5df39ceafc8a | Apache-2.0 | 1.66.0 | 2026-10-02 | Active |
| libtest-mimic | 0.8.2 | `v0.8.2` 8aca207b0e3c | MIT/Apache-2.0 | 1.65 | 2026-03-16 | Active |
| trycmd / snapbox | 1.2.1 / 1.2.2 | `snapbox-v1.2.2` b274dcb7bf8f (meta) | (workspace; not read) | 1.85 | 2026-05-26 | Active (assert-rs) |
| criterion | 0.8.2 | `criterion-v0.8.2` 7f0d745532e3 (repo moved to `criterion-rs/criterion.rs`) | Apache-2.0 OR MIT | 1.86 | 2026-02-04 | Active again |
| divan | 0.1.21 | `v0.1.21` 52f9d4983e68 | MIT OR Apache-2.0 | 1.80.0 | 2025-04-09 | **Stalled** (18 months) |
| libfuzzer-sys | 0.4.13 | `0.4.13` 719e4efb9b88 | (MIT OR Apache-2.0) AND NCSA | none | 2026-06-04 | Active |
| arbitrary | 1.5.0 | `v1.5.0` 9807b599146c (meta) | MIT OR Apache-2.0 | 1.71.0 | 2026-10-06 | Active |
| proptest | 1.12.0 | `v1.12.0` 70cf37d46b7d (meta) | MIT OR Apache-2.0 | 1.88 | 2026-10-10 | Active |
| hayro | 0.8.0 | `hayro-v0.8.0` ea9c81dc70cd | Apache-2.0 OR MIT | **1.92** | 2026-10-04 | Very active (LaurenzV) |
| hayro-syntax | 0.8.0 | same workspace | Apache-2.0 OR MIT | 1.92 | — | — |
| image-compare | 0.5.0 | HEAD 1bcd983 (ChrisRega/image-compare) | MIT | none | 2025-08-18 | Low-churn |
| lopdf | 0.45.0 | `v0.45.0` e6a0cfbf837d | MIT | 1.88 | 2026-09-08 | Active |
| mimalloc | 0.1.52 (libmimalloc-sys 0.1.49) | `v0.1.52` abcd2be6171e | MIT | none | 2026-05-22 | Active |
| tracing / tracing-subscriber | 0.1.44 / 0.3.23 | `tracing-0.1.44` 2d55f6faf9be (meta) / `tracing-subscriber-0.3.23` 54ede4d5d85a | MIT | 1.65.0 | 2025-12-18 / 2026-03-13 | Active |
| blake3 | 1.8.7 | `1.8.7` f3149ec5bb54 | CC0-1.0 OR Apache-2.0 OR Apache-2.0 WITH LLVM-exception | none (edition 2024, so 1.85 or later) | 2026-08-20 | Active |
| sha2 | 0.11.1 | `sha2-v0.11.1` 138dc5a05b93 | MIT OR Apache-2.0 | 1.88 | 2026-10-12 | Active |
| rayon | 1.12.0 | `v1.12.0` c9ced185ae35 (meta) | MIT OR Apache-2.0 | 1.80 | 2026-04-14 | Active |
| crossbeam-channel | 0.5.17 | `crossbeam-channel-0.5.17` 2920c9842902 (meta) | MIT OR Apache-2.0 | 1.60 | 2026-09-06 | Active |
| parking_lot | 0.12.5 | `parking_lot-v0.12.5` d7828fff7b5d (meta) | MIT OR Apache-2.0 | 1.71 | 2025-10-04 | Active |
| smallvec | 1.16.3 | `v1.16.3` 7ad35d20ad4c (meta) | MIT OR Apache-2.0 | none | 2026-10-06 | Active |
| indexmap | 2.14.2 | `2.14.2` 41a870887c4c (meta) | Apache-2.0 OR MIT | 1.85 | 2026-09-05 | Active |
| rustc-hash | 2.1.3 | `v2.1.3` c13e7ccca705 (meta) | Apache-2.0 OR MIT | 1.77 | 2026-07-02 | Active |
| thiserror | 2.0.21 | `2.0.21` b1827ee06f81 (meta) | MIT OR Apache-2.0 | 1.77 | 2026-09-23 | Active |
| serde / serde_json | 1.0.229 / 1.0.154 | `v1.0.229` 7fc3b4c30c94 / `v1.0.154` 20572a6d0669 (meta) | MIT OR Apache-2.0 | 1.56 / 1.71 | 2026-07-18 / 2026-10-11 | Active |
| schemars | 1.2.3 | `v1.2.3` 4791bb735255 | MIT | 1.74 | 2026-10-12 | Active |
| metrics / metrics-exporter-prometheus | 0.24.6 / 0.18.3 | `metrics-exporter-prometheus-v0.18.3` 9e387a41fa20. The tree holds metrics 0.24.5 | MIT (workspace) / **"MIT AND Apache-2.0"** | 1.71.1 | 2026-04-30 | Active |
| prometheus-client | 0.25.1 | `v0.25.1` 3e3d55cda6d1 | Apache-2.0 OR MIT | none | 2026-09-01 | Active (official Prometheus org) |
| landlock | 0.4.7 | `v0.4.7` 62fec0f1521e (meta) | MIT OR Apache-2.0 | 1.71 | 2026-07-27 | Active |
| seccompiler | 0.5.0 | `v0.5.0` c3cf77d65815 (meta) | Apache-2.0 OR BSD-3-Clause | none | 2025-03-07 | Stable (rust-vmm) |

MSRV note: the highest MSRVs in this set are hayro (1.92, dev-only), proptest (1.88), sha2 (1.88), lopdf (1.88, dev-only) and criterion (1.86, dev-only). For production deps the floor is **1.88** (sha2), or **1.85** without sha2 (clap, ureq, indexmap, notify-debouncer-full, rxing).

---

## 1. HTTP server (`recto serve`)

### axum 0.8.9
- Features (`axum/Cargo.toml:14-38`): default = `form, http1, json, matched-path, original-uri, query, tokio, tower-log, tracing`. Opt-in: `http2`, `multipart` (pulls `multer`), `ws` (pulls `tokio-tungstenite 0.29`, `sha1`, `base64`), `macros`. For recto, use `default-features = false, features = ["http1", "json", "tokio", "multipart", "query", "tracing"]`, plus `ws` only if live reload uses WebSockets (SSE does not need it).
- Serving: `axum::serve(listener, make_service)` (`axum/src/serve/mod.rs:97`). `Serve::with_graceful_shutdown(signal: impl Future<Output=()> + Send + 'static)` (`:151`).
  - The shutdown loop (`:275-303`) stops accepting on the signal, drops the listener, then `close_tx.closed().await` waits for **all in-flight connections with no deadline**. recto must wrap it in `tokio::time::timeout(grace, …)` to cap drain time.
- Listeners (`axum/src/serve/listener.rs:26,46`): `impl Listener for TcpListener` and `for tokio::net::UnixListener`. Unix-socket serving is therefore built in, which is useful for sidecar deployment. `ListenerExt::tap_io` (`:66-89`) sets per-socket options such as TCP_NODELAY.
- Body limits: `DefaultBodyLimit::max(n)` / `::disable()` (`axum-core/src/extract/default_body_limit.rs:78,119,150`).
  - The implicit default is **2 MiB**: `const DEFAULT_LIMIT: usize = 2_097_152` (`axum-core/src/ext_traits/request.rs:319`). It applies to `Bytes`, `Json`, `Form`, `Multipart` and others via `with_limited_body()`.
  - recto's HTML+asset uploads need an explicit `DefaultBodyLimit::max(cfg.max_request_bytes)` on the render route.
- Multipart (`axum/src/extract/multipart.rs`):
  - `Multipart` wraps `multer::Multipart<'static>` over `req.with_limited_body()` (`:64-80`), so the DefaultBodyLimit covers the whole stream.
  - API: `next_field()` (`:108`), `Field::file_name()` (`:158`), `content_type()` (`:164`), `bytes()` (`:175`), `chunk()` (`:225`). `impl Stream for Field` (`:135`) allows streaming fields.
  - Body-limit overflow is detected and mapped to 413 (`is_body_limit_error`, `:247,296`).
  - Per-field size and count limits (multer `Constraints`) are **not exposed** by axum's extractor. To enforce per-asset caps, count bytes while reading `chunk()`, or build `multer::Multipart::with_constraints` directly (multer API **UNVERIFIED**, not cloned).
- SSE: `axum::response::Sse` is always compiled, with no feature gate (`axum/src/response/mod.rs:7,29`). `Sse::keep_alive(KeepAlive)` (`sse.rs:74`), `Event` (`:173`).
- WebSocket: `#[cfg(feature = "ws")]` (`extract/mod.rs:10,78`), with `WebSocketUpgrade::max_message_size` / `max_frame_size` / `on_upgrade` (`extract/ws.rs:195,201,347`).
- Live-reload preview: SSE is enough. It is one-directional (server says "re-render, here is the new PDF hash"), needs no extra deps, and works through proxies.

### tower-http 0.7.1 / tower 0.5.3
- All features are opt-in (`tower-http/Cargo.toml` `[features] default = []`). Relevant ones: `limit`, `timeout`, `trace`, `catch-panic`, `request-id`, `sensitive-headers`, `compression-gzip|br|deflate|zstd`, `metrics`.
- `RequestBodyLimitLayer::new(limit: usize)` (`src/limit/layer.rs:18`) returns 413 (`limit/body.rs:99`). It also checks `Content-Length` up front (`limit/mod.rs` docs).
- `TimeoutLayer::new` is **deprecated since 0.6.7**. Use `TimeoutLayer::with_status_code(StatusCode, Duration)` (`src/timeout/service.rs:29-35`). Separate `RequestBodyTimeoutLayer::new(d)` and `ResponseBodyTimeoutLayer::new(d)` exist (`timeout/service.rs:156,221`), plus `RequestBodyDeadlineLayer` (`timeout/mod.rs:27-28`). A response-body timeout matters for slow-reader clients of large PDFs.
- `metrics::InFlightRequestsLayer` (`src/metrics/in_flight_requests.rs:74`) provides an in-flight gauge.
- Concurrency lives in **tower**, not tower-http:
  - `tower::limit::ConcurrencyLimitLayer::new(max)` (`tower/src/limit/concurrency/layer.rs:16`) creates a semaphore **per wrapped service**. Under axum `Router::layer` that is per route.
  - `GlobalConcurrencyLimitLayer::new(max)` (`:38-44`) shares one `Arc<Semaphore>`: "Cloning this layer will not create a new semaphore".
  - Use the global one, or a hand-rolled `Arc<Semaphore>` sized to the render worker pool, combined with `tower::load_shed::LoadShedLayer::new()` (`tower/src/load_shed/layer.rs:16`) so excess requests return 503 instead of queueing unbounded.
- Compression: `compression-zstd` maps to `async-compression?/zstd`, which uses the C library zstd-sys. **Avoid it for clean static musl.** gzip/deflate (flate2, pure-Rust miniz_oxide backend by default) and br (pure-Rust `brotli`) are fine. PDFs are already Flate-compressed internally, so response compression has little value. Recommendation: do not enable it at all.

### Static musl concerns
- tokio, hyper, axum, tower and tower-http are pure Rust. Avoiding `compression-zstd` keeps them C-free.
- `tokio` is needed with `rt-multi-thread, net, macros, signal, time, sync`. Rendering is CPU-bound and synchronous, so run it on a dedicated rayon pool or `spawn_blocking`, never on the reactor.
- The binary-size cost of axum, hyper and tokio is real (roughly 1–2 MB, **UNVERIFIED**, not measured here). Put the server behind a cargo feature `server` so the library and CLI-only builds do not carry it.

### Alternatives (brief)
- `tiny_http 0.12.0`: synchronous, thread-per-connection. It has no rust_version in the index and its last release is old. Smaller, but has no streaming multipart, timeouts or HTTP/1.1 hardening.
- `may_minihttp 0.1.11`: coroutine runtime (`may`) built for benchmarks. Not suitable.
- Neither is worth the security risk versus axum + hyper for an internet-facing render service.

---

## 2. HTTP client for the `net` feature (SSRF-safe)

### ureq 3.4.2 (recommended)
- Features (`ureq/Cargo.toml`):
  - default = `["rustls", "gzip"]`.
  - `rustls = ["rustls-no-provider", "_ring", "rustls-webpki-roots"]`, so **ring is the default crypto provider**. The comment reads "Ring has a higher chance of compiling cleanly without additional developer environment".
  - `rustls-no-provider` exists for supplying your own.
  - Also: `brotli`, `charset`, `json`, `cookies`, `socks-proxy`, `platform-verifier`, `native-tls`.
- Provider selection (`src/tls/rustls.rs:140-157`): the explicit provider on TlsConfig, else `CryptoProvider::get_default()`, else `ring_if_enabled()` → `rustls::crypto::ring::default_provider()`.
- **Custom resolver (DNS pinning)**:
  - `unversioned::resolver::Resolver` trait (`src/unversioned/resolver.rs:29-41`): `fn resolve(&self, uri: &Uri, config: &Config, timeout: NextTimeout) -> Result<ResolvedSocketAddrs, Error>`.
  - `ResolvedSocketAddrs = ArrayVec<SocketAddr, 16>` (`:56-59`).
  - Wire it with `Agent::with_parts(config, connector, resolver)` (`src/agent.rs:130`), using `DefaultConnector::new()` (`src/unversioned/transport/mod.rs:341+`).
  - The resolved addrs flow into `ConnectionDetails.addrs` (`transport/mod.rs:183-194`). The TCP connector connects **only** to `details.addrs` (`transport/tcp.rs:38-59`), while TLS SNI and Host still use the URI host.
  - So a resolver that calls `DefaultResolver`, then **rejects** loopback, private (RFC1918), link-local (169.254/16 including cloud metadata), ULA, CGNAT, multicast, unspecified and IPv4-mapped forms, gives check-and-pin with no TOCTOU between check and connect. Resolver-trait SSRF filtering is therefore solid.
  - Caveat: it lives under `unversioned` (lib.rs:456-476: "these parts are not yet solidified"). Pin `ureq = "=3.4.x"` (exact or tilde).
- **Connector chain**: `trait Connector<In: Transport>` with `connect(...)` and `chain(next)` (`transport/mod.rs:120-144`). This is the place to add a byte-counting or deadline-enforcing transport if needed.
- **Redirects**: `ConfigBuilder::max_redirects(u32)` (`src/config.rs:554`). Doc: "If `max_redirects` is 0, no redirects are followed and the response is always returned (never a `TooManyRedirects` error)". Default 10 (`config.rs:948+`).
  - Recommended: set 0 and follow redirects manually, re-running URL policy (scheme allow-list, host allow-list) on each `Location`. Even with ureq's own following, each hop goes through the custom Resolver, so the IP check still applies.
  - `redirect_auth_headers` defaults to `Never`.
- **Proxy env pickup is ON by default**: `proxy: Proxy::try_from_env()` in `Config::default()` (`config.rs:948`). recto must set `.proxy(None)`. Otherwise a stray `HTTPS_PROXY` / `ALL_PROXY` sends resource fetches to a proxy that resolves the target itself (`Proxy::resolve_target` defaults to false except SOCKS4, `proxy.rs:313-319`), **bypassing the IP filter**.
- **Response size limit**: `Body::with_config().limit(u64)` (`src/body/mod.rs:421,502`). Default cap for `read_to_vec`/`read_to_string` is **10 MiB** (`MAX_BODY_SIZE`, `body/mod.rs:30`). `into_reader()` (`:260`) is uncapped, so wrap it in `Read::take`.
  - `max_response_header_size` (`config.rs:643`).
- **Timeouts per phase** (`config.rs:726-821`): `timeout_global`, `timeout_per_call`, `timeout_resolve`, `timeout_connect`, `timeout_send_request`, `timeout_await_100`, `timeout_send_body`, `timeout_recv_response`, `timeout_recv_body`.
  - Note: `DefaultResolver` with a resolve timeout spawns a thread (`resolver.rs:142`, `resolve_async`). With no timeout it calls blocking `to_socket_addrs`.
  - On musl, `getaddrinfo` is musl's resolver. It reads `/etc/resolv.conf` and does not exist in `scratch` images unless provided. Document: `net` in a scratch container needs resolv.conf, or a pure-Rust resolver (hickory, not evaluated) behind the Resolver trait.
- Other: `https_only(bool)` (`config.rs:499`), `ip_family` (`:509`), `http_status_as_error` default true.
- ureq is synchronous, which fits a synchronous layout and resource-fetch pipeline with no runtime coupling.

### reqwest 0.13.5 (comparison)
- `default = ["default-tls", "charset", "http2", "system-proxy"]`, `default-tls = ["rustls"]`, `rustls = ["__rustls-aws-lc-rs", "dep:rustls-platform-verifier", "__rustls"]` (`Cargo.toml` features). **The default provider is aws-lc-rs** (C + cmake, sometimes Go/NASM; harder for static musl). `rustls-no-provider` exists. `system-proxy` is on by default.
- `ClientBuilder::dns_resolver(R: Resolve)` (`src/async_impl/client.rs:2327`, trait in `src/dns/resolve.rs:21`), `resolve()` / `resolve_to_addrs()` overrides (`:2308,2316`), `redirect(Policy)` with `Policy::none()` / `limited()` / `custom()` (`src/redirect.rs:51,58,102`), `no_proxy()` (`:1436`), `timeout` / `connect_timeout` / `read_timeout` (`:1450-1475`).
- There is no built-in body size cap; you stream `chunk()` and count.
- Requires tokio. The blocking client spins its own runtime thread.
- Verdict: equivalent SSRF capability, but heavier, async-only internals, and aws-lc-rs by default. **Choose ureq.**

---

## 3. CLI

### clap 4.6.7 (+ clap_complete 4.6.11, clap_mangen 0.3.3)
- Builder APIs verified in `clap_builder/src/builder/`:
  - `command.rs`: `Command::multicall` `:3568`, `allow_external_subcommands` `:3209`, `args_override_self` `:1249`, `infer_long_args` `:1786`, `subcommand_precedence_over_arg` `:3371`.
  - `arg.rs`: `Arg::trailing_var_arg` `:580`, `last` `:689`, `action` `:986`, `value_parser` `:1048`, `num_args` `:1209`, `allow_hyphen_values` `:1541`, `allow_negative_numbers` `:1575`.
  - `ArgAction` enum `action.rs:34`.
- **multicall** (doc `command.rs:3490-3560`): "The names of the immediate subcommands of the Command are matched against the basename of the first argument". Example: `Command::new("hostname").multicall(true).subcommand(..."hostname").subcommand(..."dnsdomainname")`, where `/usr/bin/dnsdomainname` dispatches to that subcommand.
  - For recto: `Command::new("recto").multicall(true).subcommand(recto_cli).subcommand(Command::new("recto-wkhtmltopdf")...)`. This works, but makes the main CLI a nested subcommand. It is simpler and equivalent to `match Path::new(&argv0).file_stem()` before invoking clap.
- clap_complete: `generate()` / `generate_to()` (`clap_complete/src/aot/generator/mod.rs:229,284`). Dynamic `CompleteEnv` is re-exported (`clap_complete/src/lib.rs:80`).
- clap_mangen: `Man::new(cmd).render(&mut w)` (`clap_mangen/src/lib.rs:18,151`), `generate_to` (`:128`). Run these from an `xtask` or a hidden `recto completions` subcommand, not `build.rs`.
- **wkhtmltopdf shim suitability**: wkhtmltopdf's grammar is `wkhtmltopdf [GLOBAL OPTION]... [OBJECT]... <output file>`, where OBJECT = `cover <url> [PAGE OPTS]` | `toc [TOC OPTS]` | `[page] <url> [PAGE OPTS]` (see doc 02). Page options are **position-scoped**: they apply to the preceding object. Some options take two values (`--custom-header <name> <value>`, `--replace <name> <value>`, `--cookie`, `--post`), and some have `--no-` negations.
  - clap's model is flat: options are global to a (sub)command and positionals are ordered. It cannot naturally attach `--zoom` to the 2nd of 3 page objects. Workarounds (`allow_external_subcommands`, `trailing_var_arg` + manual re-parse, `ArgMatches::indices_of`) would be awkward.
  - Short `-O Landscape`, `-s A4` and `--page-size A4` are standard and fine for both. wkhtmltopdf does not use single-dash long options, so that is not a problem.
  - **Recommendation**: the main `recto` CLI uses clap derive. The `recto-wkhtmltopdf` shim uses a hand-written state machine on **lexopt 0.3.2**: `Parser::from_env()` `:727`, `from_args` `:767`, `next()` `:166` yielding `Short`/`Long`/`Value`, `value()` `:407`, `values()` `:459` (multi-value options), `optional_value()` `:657`, `next_if` `:902`, `raw_args` `:554`, `bin_name()` `:651`.
  - lexopt is MIT, zero deps, and lets the parser switch "current object" whenever a `Value` equals `cover` / `toc` / `page` or looks like a URL or path. The Puppeteer-options shim is JSON (serde), not argv.

---

## 4. File watching (`recto watch`)

- **notify 8.2.0**: license **CC0-1.0** (`notify/Cargo.toml:7`). Linux backend = `inotify` crate (`default-features = false`) + `mio` + `libc` (`notify/Cargo.toml:31-37`). These are raw syscalls, so they are musl-compatible with no C build.
  - `PollWatcher` is the documented fallback where inotify is unavailable, such as some container and emulation cases (`notify/src/lib.rs:37-42`). Expose `--poll`.
- **notify-debouncer-full 0.7.0** (pairs with notify 8.2.0, `Cargo.toml:39-41` at `debouncer-full-0.7.0`): `new_debouncer(timeout: Duration, tick_rate: Option<Duration>, handler: impl DebounceEventHandler) -> Result<Debouncer<RecommendedWatcher, RecommendedCache>, Error>` (`notify-debouncer-full/src/lib.rs:719-727`), `new_debouncer_opt` for a custom watcher such as PollWatcher (`:633` at 0.6 tree). `Debouncer::watch`, `stop` (`:594,549` at 0.6 tree). It handles rename stitching and file-id tracking, which suits editors that save via rename.
  - Optional `crossbeam-channel` feature.
- notify 9.0.0-rc.5 is tagged. Stay on 8.2 / debouncer 0.7 until 9.0 is final.

---

## 5. Barcodes / QR

recto draws symbols as **vector rectangles in the PDF content stream**, never raster. So what we need from each crate is the **module matrix / bar pattern**, not its SVG or image renderer. Every crate below exposes that, and all are pure Rust.

| Crate | License | Symbologies | Matrix access | SVG | Deps / notes |
|---|---|---|---|---|---|
| qrcode 0.14.1 | MIT/Apache | QR 1–40, **Micro QR** (`Version::Micro`, `src/types.rs:128`) | `QrCode::to_colors()` (`src/lib.rs:218`), `with_version` / `with_error_correction_level` (`:92,115`) | `svg` feature (`render/svg.rs`) | default features pull `image` 0.25, so use `default-features=false`. Stale since 2024-07. |
| fast_qr 0.14.0 | MIT | QR only | `QRBuilder::new(..).ecl().version()` (`src/qr.rs:211-234`) | `svg` feature (`src/convert/svg.rs`). `image` pulls resvg | zero deps by default. Active. |
| qrcodegen 1.8.0 | MIT | QR only | `QrCode::encode_text` / `encode_binary` / `size` / `get_module(x,y)` (`rust/src/lib.rs:159,173,337,359`) | no (example only) | zero deps. Nayuki reference code. Single file. |
| barcoders 2.0.0 | MIT/Apache | Code128 (A/B/C via `À`/`Ɓ`/`Ć`, FNC1 = `Ź`, `sym/code128.rs:1-50`), Code39, Code93, Code11, Codabar, EAN-13 + **UPC-A** (`sym/ean13.rs:7,94`), EAN-8, EAN-2/5 supplements, ITF / 2-of-5 (`sym/tf.rs`) | `.encode() -> Vec<u8>` (one byte per module), e.g. `code128.rs:364` | `generators/svg.rs` `SVG::new(height).generate()` | default = ascii, json, svg, std. `image` optional. Code128 **does not auto-select code sets**, so recto must add an optimiser (or use rxing's). Stale since 2024-04. |
| rxing 0.9.3 | Apache-2.0 | Writers (`src/multi_format_writer.rs:27-54`): QR, DataMatrix, PDF417, Aztec, Code128, Code39, Code93, Codabar, EAN-8/13, UPC-A/E, ITF, Telepen. MaxiCode is decode-only | `Writer::encode(...)` → `BitMatrix` (`src/writer.rs:40,57`) | `svg_write` feature | Default features are heavy (`image`, `imageproc`, chrono-tz, fancy-regex). **Use `default-features=false, features=["encoders","qrcode","datamatrix","pdf417","aztec","oned"]`.** Unconditional deps remain: regex, chrono (clock), num, once_cell, unicode-segmentation, thiserror. Edition 2024, MSRV 1.85. |
| datamatrix 0.3.3 | Apache/MIT | DataMatrix ECC200 (square + rectangular), optimising shortest-path encoder | `DataMatrix::encode(...)` / `encode_str` → `.bitmap()`, `Bitmap::pixels()` iterator (`src/lib.rs:164-183,291-300`, `src/placement.rs:169,642`) | via `Bitmap::path` helper (not verified) | deps: arrayvec, flagset, optional encoding_rs. Tiny. |

Recommendation:
- **QR**: `qrcodegen` or `fast_qr`, both zero-dep and MIT. `fast_qr` is actively maintained; `qrcodegen` is the reference implementation. Pick **fast_qr**; keep `qrcode` only if Micro QR is wanted.
- **Swiss QR-bill**: QR with ECL M, plus the Swiss cross overlay drawn by recto at 7 mm. **EPC/SEPA QR**: ECL M, max version 13. Both are payload formatting done in recto.
- **Linear (Code128, EAN-13/UPC-A, EAN-8, Code39, ITF)**: barcoders is small, but its Code128 needs manual code sets and it is stale. The alternative is rxing's `oned`, which auto-optimises Code128 and is active.
- **DataMatrix**: `datamatrix` (tiny, best encoder).
- **PDF417 / Aztec**: only rxing has encoders.
- Final pick, since PDF417 forces rxing in anyway: one `barcode` cargo feature with **rxing (encoders only, trimmed features) + datamatrix + fast_qr**, and drop barcoders. An alternative minimal set without PDF417: fast_qr + barcoders + datamatrix, all tiny.
- Map a CSS-ish API (e.g. `<img src="barcode:code128?data=...">` or a `recto-barcode` custom element) to these crates. That is a design decision for the lead.

---

## 6. Test / bench / fuzz tooling

- **insta 1.49.0** (Apache-2.0): `assert_snapshot!`, `assert_binary_snapshot!` (`insta/src/macros.rs:463,410`), `glob!` (`:561`, feature `glob`). Features: `redactions`, `filters` (regex), `json`, `yaml`, `glob`. Use for display-list / layout-tree text dumps and PDF structural dumps.
- **libtest-mimic 0.8.2**: `Arguments::from_args()` (`src/args.rs:144`), `Trial::test(name, runner)` (`src/lib.rs:135`), `.with_kind()`, `.with_ignored_flag()` (`:205,221`), `run(&args, trials) -> Conclusion` (`:491`). This is the harness for data-driven WPT-style and fixture corpora (`harness = false`).
- **trycmd 1.2.1 / snapbox 1.2.2** (assert-rs): CLI golden tests (`*.trycmd` files). Use for the wkhtmltopdf shim flag matrix. API not read here.
- **criterion 0.8.2** vs **divan 0.1.21**: criterion moved to the `criterion-rs` org, released 2026-02, MSRV 1.86. divan's last commit was 2025-04-09 (stalled), though its API (`divan::main()`, `src/lib.rs:156`) is nicer and supports allocation counting. **Use criterion** for maintenance reasons. For CI regression tracking, instruction-count benches via iai-callgrind/gungraun are worth a separate look (**UNVERIFIED**).
- **cargo-fuzz / libfuzzer-sys 0.4.13**: license `(MIT OR Apache-2.0) AND NCSA` (vendored LLVM libFuzzer). Builds C++ with `cc` (`Cargo.toml:25-30`, default feature `link_libfuzzer`). Nightly + `-Zsanitizer` via cargo-fuzz. Dev-only, so NCSA does not affect the shipped binary. **arbitrary 1.5.0** (`derive` feature) produces structured inputs (CSS/HTML ASTs, option objects).
- **proptest 1.12.0**: MSRV 1.88. Good for the layout invariants (no overflow of fragmentainer, monotonic page numbers).
- **hayro 0.8.0** (PDF rasteriser, pure Rust, `#![forbid(unsafe_code)]` at `hayro/src/lib.rs:33`):
  - The crate set is `hayro` (render), `hayro-syntax` (parse), `hayro-interpret`, `hayro-svg`, `hayro-write`, plus codec crates (`hayro-jbig2`, `hayro-jpeg2000`, `hayro-ccitt`, `hayro-cmap`). There is **no `hayro-render` crate** (not in the index).
  - API: `hayro_syntax::Pdf::new(data)` (`hayro-syntax/src/pdf.rs:36`), `pdf.pages()` (`:95`), `hayro::render(page, &RenderCache, &InterpreterSettings, &RenderSettings, &PixmapSettings{x_scale,y_scale,bg_color}) -> vello_cpu::Pixmap` (`hayro/src/lib.rs:197-239`), `render_into` for custom transform (`:273`), `Pixmap::into_png()` (`hayro/examples/render.rs`).
  - Fonts are resolved via `InterpreterSettings.font_resolver` (example `render.rs:36+`). Features `embed-fonts`, `embed-cmaps`, `simd` (default).
  - Pixmap dims are cast to **u16**, so the max is 65535 px per side (`lib.rs` `render`).
  - **Determinism**: `GlobalState` uses `fearless_simd::Level::new()` (runtime CPU detection, `hayro/src/lib.rs:72-81`). The `simd` feature enables pic-scale SSE/AVX/NEON. Output may differ across CPUs, which is **UNVERIFIED**. hayro's own tests fail on any non-zero pixel diff vs references (`hayro-tests/tests/mod.rs:100-129`), but those references are produced on one platform.
  - For recto CI: build hayro with `default-features=false, features=["embed-fonts","embed-cmaps"]` (no `simd`), render at fixed scale, and compare with a small tolerance via image-compare. MSRV 1.92 is dev-only, but the workspace toolchain must be at least 1.92 to run tests.
- **image-compare 0.5.0** (MIT; deps image 0.25 with no default features, rayon, itertools): `rgba_hybrid_compare`, `rgb_hybrid_compare`, `rgba_blended_hybrid_compare`, `gray_similarity_structure` (MSSIM), `rgb_similarity_structure`, `gray_similarity_histogram` (`src/lib.rs:137-234`). Returns a score plus a diff image, which is good for CI artifacts.
- **lopdf 0.45.0** (MIT, MSRV 1.88): `Document::load`, `load_from(Read)`, `load_from_with_options` (`src/reader.rs:34,60,66`), `get_pages() -> BTreeMap<u32, ObjectId>` (`src/document.rs:533`). Default features `chrono-clock, rayon`, so set `default-features=false` in dev-deps. Use for structural asserts (object counts, StructTreeRoot, /Outlines, font subsets embedded, no /JavaScript, PDF/A metadata), dev-only. A second parser (hayro-syntax) cross-checks that recto's output parses in two independent readers.

---

## 7. Runtime misc

- **mimalloc 0.1.52** (MIT; libmimalloc-sys 0.1.49):
  - **Defaults to mimalloc v3** C sources unless feature `v2` is enabled (`libmimalloc-sys/build.rs:9-11`).
  - Builds C via `cc`, so the musl target needs `musl-gcc` or `zig cc` or a cross C toolchain.
  - TLS model: `-ftls-model=initial-exec` unless `local_dynamic_tls` (`build.rs:89-95`). initial-exec is right for a static executable. Use `local_dynamic_tls` only when building recto as a cdylib for bindings that are dlopen'ed (Python/Node).
  - Features: `secure`, `no_thp`, `override`, `extended`.
  - Recommendation: enable `#[global_allocator] MiMalloc` only in the `recto` binary crate behind a `mimalloc` feature (on by default for musl builds, where musl's malloc is slow). Never set it in the library crate.
- **tracing 0.1.44 / tracing-subscriber 0.3.23** (MIT): subscriber default features `smallvec, fmt, ansi, tracing-log, std` (`tracing-subscriber/Cargo.toml:27`). `json = ["tracing-serde","serde","serde_json"]` (`:34`). Use `default-features=false, features=["fmt","json","env-filter","std"]` (`env-filter` pulls `regex`. **UNVERIFIED** whether the lighter `Targets` filter suffices; prefer `filter::Targets` to avoid regex).
- **blake3 1.8.7**: feature `pure` (`Cargo.toml:85`, `build.rs:8,345,353`) skips C/asm compilation and uses Rust intrinsics or portable code. **The hash value is identical regardless of backend** (it is a defined function), so `pure` is about **build simplicity** for musl and cross targets, not determinism. Enable `pure` to drop the `cc` step for asm. `rayon` and `mmap` are optional.
- **sha2 0.11.1**: no `asm` feature any more. Backends are chosen via `--cfg sha2_backend="soft"` and similar RUSTFLAGS (`sha2/README.md:87-97`, `Cargo.toml:34-40`). Intrinsics-based, pure Rust. MSRV 1.88. Only needed if PDF signatures or legacy IDs require SHA-256. For content hashing (cache keys, the PDF `/ID` derivation for deterministic output), **use blake3**.
- **rayon 1.12.0, crossbeam-channel 0.5.17, parking_lot 0.12.5, smallvec 1.16.3, indexmap 2.14.2, rustc-hash 2.1.3, thiserror 2.0.21, serde 1.0.229, serde_json 1.0.154**: all MIT/Apache, pure Rust, and active (see table). Determinism notes:
  - Never iterate a `HashMap`/`FxHashMap` into output order. Use `IndexMap`/`BTreeMap` for anything serialised into the PDF.
  - With rayon, collect results in input order (`par_iter().map().collect::<Vec<_>>()` preserves order).
- **schemars 1.2.3** (MIT): `#[derive(JsonSchema)]` (`derive` default), `schema_for!` (`src/macros.rs:19`), `SchemaSettings::draft2020_12()` (`src/generate.rs:108`), `.for_deserialize()` (`:176`), `into_root_schema_for::<T>()` (`:480`). The `preserve_order` feature keeps field order (useful for docs). Generate `options.schema.json` for the render-options object in an xtask and publish it with the server's OpenAPI. It honours serde attributes (`rename_all`, `deny_unknown_fields`), so one struct drives CLI JSON, HTTP JSON and bindings.
- **Metrics exposition**:
  - `metrics 0.24.6` + `metrics-exporter-prometheus 0.18.3`:
    - **Default features `http-listener` + `push-gateway`**, and push-gateway enables `hyper-rustls/aws-lc-rs` (`metrics-exporter-prometheus/Cargo.toml` features). This drags in aws-lc-rs (a C build).
    - License string "MIT AND Apache-2.0".
    - API: `PrometheusBuilder::with_http_listener` / `install` / `install_recorder() -> PrometheusHandle` / `build_recorder` (`src/exporter/builder.rs:122,456,506,605`), `PrometheusHandle::render()` (`src/recorder.rs:413`).
    - It must be used with `default-features=false`, serving `handle.render()` from recto's own axum `/metrics` route.
  - `prometheus-client 0.25.1` (official Prometheus org, Apache/MIT): `Registry::register(name, help, metric)` (`src/registry.rs:123`), `encoding::text::encode(&mut String, &Registry)` (`src/encoding/text.rs:89`). Explicit registry, no global recorder, no runtime or TLS deps.
  - **Recommend prometheus-client**: smaller, explicit, OpenMetrics-correct, and no global state in the library. Metrics live only in the server crate.
- **landlock 0.4.7** (MIT/Apache, MSRV 1.71) and **seccompiler 0.5.0** (Apache-2.0 OR BSD-3-Clause, last commit 2025-03): versions recorded. API is covered in doc 10.

---

## Recommended `[workspace.dependencies]`

```toml
[workspace.dependencies]
# --- server (crate `recto-server`, feature `server` on the binary) ---
axum        = { version = "0.8.9", default-features = false, features = ["http1", "json", "query", "tokio", "multipart", "tracing"] }
tokio       = { version = "1.53", default-features = false, features = ["rt-multi-thread", "net", "macros", "signal", "time", "sync"] }
tower       = { version = "0.5.3", default-features = false, features = ["limit", "load-shed", "timeout", "util"] }
tower-http  = { version = "0.7.1", default-features = false, features = ["limit", "timeout", "trace", "catch-panic", "request-id", "sensitive-headers"] }
prometheus-client = "0.25.1"

# --- optional `net` feature (resource fetching) ---
ureq = { version = "~3.4.2", default-features = false, features = ["rustls"] }   # rustls+ring+webpki-roots; unversioned::resolver used => tilde pin

# --- CLI ---
clap          = { version = "4.6.7", features = ["derive", "env", "wrap_help"] }
clap_complete = "4.6.11"
clap_mangen   = "0.3.3"
lexopt        = "0.3.2"           # wkhtmltopdf shim parser

# --- watch ---
notify                = { version = "8.2.0", default-features = false }
notify-debouncer-full = { version = "0.7.0", default-features = false }

# --- barcodes (feature `barcode`) ---
fast_qr    = { version = "0.14.0", default-features = false }
datamatrix = { version = "0.3.3", default-features = false }
rxing      = { version = "0.9.3", default-features = false, features = ["encoders", "oned", "pdf417", "aztec"] }

# --- runtime ---
mimalloc   = { version = "0.1.52", default-features = false }        # binary crate only
tracing    = { version = "0.1.44", default-features = false, features = ["std", "attributes"] }
tracing-subscriber = { version = "0.3.23", default-features = false, features = ["std", "fmt", "json", "ansi"] }
blake3     = { version = "1.8.7", default-features = false, features = ["std", "pure"] }
rayon      = "1.12.0"
crossbeam-channel = "0.5.17"
parking_lot = "0.12.5"
smallvec   = { version = "1.16.3", features = ["const_generics", "union"] }
indexmap   = "2.14.2"
rustc-hash = "2.1.3"
thiserror  = "2.0.21"
serde      = { version = "1.0.229", features = ["derive"] }
serde_json = "1.0.154"
schemars   = { version = "1.2.3", features = ["preserve_order"] }
landlock   = "0.4.7"
seccompiler = "0.5.0"

# --- dev / test / bench ---
insta         = { version = "1.49.0", features = ["glob", "json", "filters"] }
libtest-mimic = "0.8.2"
trycmd        = "1.2.1"
snapbox       = "1.2.2"
criterion     = { version = "0.8.2", default-features = false, features = ["cargo_bench_support"] }
proptest      = "1.12.0"
arbitrary     = { version = "1.5.0", features = ["derive"] }
libfuzzer-sys = "0.4.13"           # fuzz/ crate only
hayro         = { version = "0.8.0", default-features = false, features = ["embed-fonts", "embed-cmaps"] }
hayro-syntax  = "0.8.0"
image-compare = "0.5.0"
lopdf         = { version = "0.45.0", default-features = false }
```

Feature names used above (axum, tower, tower-http, ureq, rxing, blake3, mimalloc, tracing-subscriber, schemars, hayro, insta) were read from the inspected Cargo.toml files or the index feature lists. `criterion`'s `cargo_bench_support` and smallvec's `const_generics` / `union` come from the index feature list. `tracing`'s `attributes` and `std` are in the index list.

---

## Findings that affect recto's design

1. **axum's 2 MiB implicit body limit** (`axum-core/src/ext_traits/request.rs:319`) silently caps Multipart/Json. The render route must set `DefaultBodyLimit::max(cfg.max_request_bytes)` and also apply `RequestBodyLimitLayer` (413 on Content-Length before reading). Per-asset limits must be counted manually in the `Field::chunk()` loop.
2. **Graceful shutdown waits forever** for in-flight connections (`axum/src/serve/mod.rs:296-303`). Wrap it in `tokio::time::timeout(drain_grace)`, and make renders cancellable via a deadline token checked between pages.
3. **Use `GlobalConcurrencyLimitLayer` + `LoadShedLayer`**, not `ConcurrencyLimitLayer`, which is per-route under `Router::layer`. Size it to the render worker count and return 503 fast. Renders run on a dedicated rayon/blocking pool, never on tokio workers.
4. **`TimeoutLayer::new` is deprecated**. Use `with_status_code`, and add `ResponseBodyTimeoutLayer` for streaming PDF responses to slow clients.
5. **No zstd in tower-http**. It is the only C dependency in the HTTP stack. Skip response compression entirely, since PDFs are already compressed.
6. **ureq 3 supports correct SSRF pinning** via a custom `unversioned::resolver::Resolver` + `Agent::with_parts`. Connections go only to `ConnectionDetails.addrs`, while TLS still verifies the hostname. Because this API is "unversioned", pin `~3.4`. Also:
   - **Must call `.proxy(None)`**: the default `Proxy::try_from_env()` bypasses the IP filter.
   - Set `max_redirects(0)` and follow redirects manually with per-hop URL policy.
   - Use `Body::with_config().limit(cap)`, never uncapped `into_reader()`.
   - Set every `timeout_*` phase, and `https_only` if policy says so.
7. **TLS crypto provider**: ureq defaults to **ring**, reqwest 0.13 to **aws-lc-rs**, and metrics-exporter-prometheus' default push-gateway also pulls aws-lc-rs. Audit `cargo tree -i aws-lc-rs` in CI and fail if present, to keep the musl build to one small C dependency (ring), or to zero if `net` is off.
8. **DNS in `scratch`**: the default ureq resolver uses libc `getaddrinfo` (musl), which needs `/etc/resolv.conf` in the container. Document this, or ship a pure-Rust resolver behind the same Resolver trait (future).
9. **wkhtmltopdf shim = hand-written lexopt state machine**. wkhtmltopdf page options are scoped per object (`cover` / `toc` / `page`), which clap's flat model cannot express cleanly. The main CLI uses clap derive. argv[0] dispatch is a plain `file_stem()` match; `Command::multicall` works but adds nothing.
10. **Barcodes are emitted as vector PDF paths** from module matrices: fast_qr (QR), datamatrix (DataMatrix), and rxing with trimmed features (Code128 with auto code-set, EAN/UPC, Code39, ITF, PDF417, Aztec). This makes them crisp at any zoom and deterministic. Swiss QR-bill and EPC are payload builders plus the overlay in recto. Gate it all behind a `barcode` feature.
11. **Visual regression**: hayro (pure Rust) renders recto PDFs in CI with no pdfium/poppler dependency. Build it without `simd` to avoid CPU-dependent output (risk **UNVERIFIED**), and compare with image-compare plus a tolerance. hayro's MSRV is 1.92, so the repo's `rust-toolchain.toml` for tests must be at least 1.92 even if the library MSRV is lower.
12. **Two independent parsers in tests**: lopdf (structural asserts) and hayro-syntax (parse/render). recto's output must load cleanly in both, as a cheap conformance smoke test before veraPDF.
13. **blake3 with `pure`** for content hashes, cache keys and the deterministic `/ID`. The output is identical across backends, and `pure` only removes the C/asm build step.
14. **mimalloc only in the binary**, with the initial-exec TLS default for the static exe and `local_dynamic_tls` for dlopen'ed binding cdylibs. It defaults to the v3 C sources, which need a musl C cross-compiler (`zig cc` or `musl-gcc`) in the release pipeline.
15. **prometheus-client over metrics + exporter**: no global recorder, no TLS deps, served on axum `/metrics`. Keep metrics out of the library crate; the library exposes counters via a callback or stats struct instead.
16. **MSRV**: production deps imply at least 1.85 (clap, ureq, indexmap, rxing, notify-debouncer-full), or 1.88 if sha2 is used. Dev deps need 1.92 (hayro). Propose library MSRV 1.85, binary/tooling toolchain pinned to the latest stable.
17. **License inventory**: everything here is MIT/Apache/BSD/CC0. Exceptions to note in `deny.toml`: notify is **CC0-1.0**; blake3 is `CC0-1.0 OR Apache-2.0 …`; libfuzzer-sys includes **NCSA** (dev-only); seccompiler is `Apache-2.0 OR BSD-3-Clause`; metrics-exporter-prometheus declares **"MIT AND Apache-2.0"** (not used). rxing is Apache-2.0-only (fine, with a NOTICE obligation).

## Recommendation

- **Server**: axum 0.8 + hyper 1 + tokio + tower 0.5 (`GlobalConcurrencyLimitLayer`, `LoadShedLayer`) + tower-http 0.7 (`limit`, `timeout`, `trace`, `catch-panic`, `request-id`). SSE for live reload. prometheus-client for `/metrics`. Everything behind a `server` feature.
- **Net**: ureq 3.4 with ring, a custom pinning Resolver, `proxy(None)`, `max_redirects(0)`, body limit and phase timeouts. Behind the `net` feature, off by default.
- **CLI**: clap 4 derive + clap_complete + clap_mangen via xtask. lexopt for the `recto-wkhtmltopdf` shim. argv[0] dispatch by `file_stem`.
- **Watch**: notify 8.2 + notify-debouncer-full 0.7, with a `--poll` fallback.
- **Barcodes**: fast_qr + datamatrix + rxing (encoders, oned, pdf417, aztec) as vector output.
- **Tests**: insta, libtest-mimic (fixture corpora), trycmd (CLI), proptest, cargo-fuzz + arbitrary, criterion, hayro (no simd) + image-compare (visual), lopdf (structural).
- **Runtime**: mimalloc (binary only), tracing + tracing-subscriber json, blake3 `pure`, rayon, indexmap / rustc-hash, thiserror, serde, schemars.

## Open questions / UNVERIFIED items

- multer `Constraints` / per-field size limits API (multer 3.1.0 not cloned). Decide between manual byte counting and using multer directly.
- Binary-size cost of the axum/tokio/hyper server feature on x86_64-musl. It needs a measured `cargo bloat` in Phase 1.
- Whether hayro output is bit-identical across SIMD levels (`fearless_simd::Level::new()` runtime dispatch) with the `simd` feature disabled. Test on two CPUs in CI.
- `tracing-subscriber` `env-filter` vs `filter::Targets`: the regex dependency size was not measured.
- trycmd/snapbox and criterion/divan APIs were not read beyond Cargo metadata and entry points. iai-callgrind/gungraun (instruction-count benches) were not evaluated.
- Exact rxing transitive footprint with trimmed features (regex, chrono, num still unconditional). Needs a `cargo tree` once crate downloads are possible. If it is too heavy, fall back to barcoders (linear) and drop PDF417/Aztec.
- `datamatrix` `Bitmap::path` and SVG helper not verified, but the `pixels()` iterator suffices.
- Pure-Rust DNS resolver (hickory-resolver) for `scratch` images was not evaluated.
- notify 9.0 (rc.5 tagged) API changes: re-check before 1.0.
- Licenses of trycmd/snapbox, multer, hyper-util and async-compression were not read from source (index only).
