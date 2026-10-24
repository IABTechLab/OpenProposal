# Inspect creative without reporting live delivery

This contribution implements the proposed wording in
[#42](https://github.com/IABTechLab/OpenProposal/issues/42) and supplies synthetic
fixtures that exercise it. It also supports the distinction raised in
[#32](https://github.com/IABTechLab/OpenProposal/issues/32): resolving a format,
fetching a document, checking conformance and receiving seller approval are
separate results.

The normative change adds the inspection subsection to section 5.4 and a note
to the CTV example. It adds no fields or enum values. The appendix field
indexes therefore remain unchanged.

## Reproduce the document inspection

```
python3 scripts/check_creative_fixtures.py
python3 scripts/check_creative_fixtures.py --json
```

The standard-library runner starts a loopback HTTP server. The server records
every request, including requests to synthetic notification traps. Nothing
loads a campaign URL. The two VAST templates use fixture substitution tokens
that the runner replaces with the server's loopback address.

The reference inspector retrieves only document request identities listed by
the test harness. It follows a single-ad wrapper chain, hashes retrieved bytes and
parses XML. It does not execute code, fetch media, probe event URLs, expand
macros, use proxy environment variables, or automatically follow redirects.
An HTTP redirect can itself target an event endpoint. It must not become an
unchecked route around the retrieval policy.

The allowlist, event guard and cycle detection share one HTTP URL identity
function. It removes fragments, normalizes scheme/host spelling, IPv6 spelling
and default ports, and supplies `/` for an empty path. The transport sends that
same normalized URL. Path spelling, query order, percent encodings and an empty
query delimiter are preserved. A receipt retains both the supplied document URL
and the actual request URL. Unsupported schemes, credentials, control characters
and non-ASCII URLs are blocked in this deliberately limited fixture profile.

The event-role set includes linear, companion, non-linear and icon tracking,
viewability, verification and error URIs. Clickthrough destinations are also
excluded from wrapper retrieval. Regression cases deliberately allowlist targets
that are also declared as events, so an absent allowlist entry cannot hide a
broken event guard. Fragment aliases are tested on both sides of that comparison.
This does not infer server-side URL aliases, custom extension semantics or
resource intent. The caller must establish that its initial resource allowlist
is appropriate. It is not a production fetch policy.

Successful wrapper traversal reaches the inline document with no requests to
its impression, playback, click, viewability, verification or error endpoints.
Failure cases include cycles, missing documents, malformed XML, a redirect to
an event URL, excessive size, excessive depth and an event URL also used as a
wrapper target. Unresolved macros, unsupported encodings, DTDs and ad pods are
reported as not checked within this limited profile. Missing wrapper targets
and malformed XML fail their specific structural checks.

The server-side positive control deliberately sends GET and HEAD to a local
notification trap and verifies both are recorded. This establishes that zero
notification requests in the inspection cases is an observable test result.
Neither response availability nor HTTP method makes an event request safe.

## Reproduce the browser preview

Requires Node.js 22 or later and an installed Chrome or Chromium executable.
Set `CHROME_BIN` if it is not at one of the common paths checked by the runner.
`CREATIVE_CACHE_DIR` can place the temporary browser profile in a chosen cache
directory. The directory must already exist. The profile is removed on exit.

```
node scripts/check_creative_preview.mjs
node scripts/check_creative_preview.mjs --json
node scripts/check_preview_observations.mjs
```

The browser runs synthetic creative that attempts a GET, HEAD, POST, beacon,
XHR, image, script, nested frame, CSS image, video poster, form submission,
navigation and WebSocket connection. Each mechanism has a positive control
that must reach its loopback notification trap using the expected method.
Each isolated case must execute the same attempt and produce zero requests
at that trap. A receipt includes the browser version, attempted operation,
server observations, blocked requests and a 500 ms observation interval
after the synchronous attempt.

The assertion checks the entire notification-trap log for that case, including
unexpected paths and methods. The receipt preserves every observation and its
full URL. Control cases must reach only their expected notification endpoint;
isolated cases must produce no notification at all. The assertion regression
tests run without a browser and are included in CI.

An integration negative control checks that an unexpected notification cannot
disappear from the result:

```
node scripts/check_creative_preview.mjs --json --inject-notification-canary
```

That command intentionally exits with status 1. The test driver injects one
loopback event at an unexpected path in `fetch-get/isolated`; that case must
fail and its receipt must contain the event. This is a check of the assertion,
not a browser escape or a live campaign notification.

The isolated preview combines a sandboxed frame, a restrictive Content
Security Policy, browser request interception and an independent HTTP proxy
that permits only the exact preview-document request. Proxy bypass for
loopback is disabled. The proxy rejects CONNECT except for the WebSocket
positive control's loopback tunnel. It permits a control's specific loopback
event URL only while that control runs. It never forwards to external
destinations. A separate navigation case disables CSP and browser interception
to verify that the independent gate itself blocks the notification.

The independent gate is essential to this demonstration. An initial test
using CSP and target-scoped browser interception alone allowed frame
navigation to reach the synthetic event endpoint in Chrome. The navigation
case remains in the suite and must be blocked outside the renderer too.
This finding supports a requirement about observable notifications rather
than prescribing a particular browser API as sufficient isolation.

These are finite synthetic tests, not proof that this harness safely executes
arbitrary third-party code. It is not a production sandbox. Delayed traffic,
all possible protocols, browser vulnerabilities, WebRTC, native applications
and real verification SDKs are outside the test coverage. A production
inspector needs enforcement for its entire execution environment and must
decline a check it cannot isolate. The browser fixture demonstrates request
suppression; it does not demonstrate video decoding or playback conformance.

## Report the exact check and its evidence

The JSON receipt is a non-normative sidecar for these tests, not a new
OpenProposal object or an adopted readiness protocol. Each result names the
check, its outcome and its reason. Retrieved documents carry their SHA-256
hash, URL and byte count. The receipt also identifies the asset, inspection
time, root URL, depth/size limits, redirect policy and macro context.

- `passed`: the named check ran and met that check's condition. Parsing XML
  does not pass VAST schema validation. Reaching `InLine` does not pass
  playback, media decode, seller specs or seller approval.
- `failed`: the named check ran and found a concrete violation, such as
  malformed XML or a cycle in the retrieved wrapper chain.
- `not_checked`: the check did not establish an outcome. The receipt states
  whether data was missing, retrieval failed, policy blocked it or the
  implementation did not support the check. These reasons do not establish
  that the creative itself is invalid.

A required check set is satisfied only if every named check has at least one
result and all its results passed. Missing, failed or not-checked results
cannot satisfy it. An empty requirement list cannot establish satisfaction.
Even satisfied inspection checks do not establish seller acceptance.
`readiness` remains `not_assessed` in this first profile.

The inspector leaves VAST schema conformance, resolved format membership,
seller-spec conformance, media decode, verification execution, live playback
and seller approval explicitly not checked. A minimal `<InLine/>` fixture is
included to prove that successful traversal never becomes a schema pass.

## Boundaries for the next creative contribution

Readiness needs a declared check set for the resolved format and delivery
protocol. An audit needs the exact asset bytes, resolved wrapper documents,
seller-spec version, execution context, checker version and evidence expiry.
Mutable URLs or changed specifications cannot inherit an earlier pass without
a revalidation rule. Those are follow-up decisions, not implicit guarantees
of this fixture receipt.

This proposal does not require inspectors to fetch documents or offer a
preview. It does not change VAST's live-delivery tracking requirements.
Synthetic event delivery to a documented receiver test mode would need its
own evidence that the receiver excludes it from production measurement.
An inspector-owned `test=true` parameter cannot establish that fact.

References: [VAST 4.3, sections 2.3.4 and 2.3.6](https://iabtechlab.com/wp-content/uploads/2022/09/VAST_4.3.pdf),
[Content Security Policy](https://www.w3.org/TR/CSP3/), and
[Chrome DevTools Fetch domain](https://chromedevtools.github.io/devtools-protocol/tot/Fetch/).
