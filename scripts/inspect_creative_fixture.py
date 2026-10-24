#!/usr/bin/env python3
"""Bounded, fixture-only document inspection supporting OpenProposal #42.

Not a production fetcher, player, VAST validator or creative-readiness service.
"""

import hashlib
import ipaddress
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

EVENT_ELEMENTS = {"Impression", "Error", "Tracking", "ClickTracking", "ClickThrough",
                  "CustomClick", "Viewable", "NotViewable", "ViewUndetermined",
                  "CompanionClickTracking", "CompanionClickThrough",
                  "NonLinearClickTracking", "NonLinearClickThrough",
                  "IconViewTracking", "IconClickTracking", "IconClickThrough"}


class Unchecked(Exception):
    """The check could not run within the fixture's retrieval policy."""


def request_url(url):
    """Canonicalize the HTTP request identity used by this fixture transport.

    Fragments never reach the server. Preserve path/query spelling because
    application routing and signatures can depend on it. This cannot identify
    arbitrary server-side aliases, redirects or the meaning of a resource.
    """
    if not isinstance(url, str) or not url.isascii() or any(ord(c) <= 32 or ord(c) == 127 for c in url):
        raise Unchecked("URL is outside the ASCII fixture profile")
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username is not None or parts.password is not None:
            raise ValueError("unsupported authority")
        host = parts.hostname.lower()
        if ":" in host:
            host = "[" + ipaddress.IPv6Address(host).compressed + "]"
        port = parts.port
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("invalid port")
        authority = host
        if port is not None and port != (80 if parts.scheme == "http" else 443):
            authority += ":" + str(port)
        normalized = urlunsplit((parts.scheme, authority, parts.path or "/", parts.query, ""))
        if not parts.query and "?" in url.split("#", 1)[0]:
            normalized += "?"
        return normalized
    except ValueError as error:
        raise Unchecked("URL is outside the HTTP fixture profile") from error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class FixtureTransport:
    def __init__(self, documents, max_bytes=65536):
        # Explicit document URLs come from the local fixture server, not the XML.
        # Callers must establish each URL is a document resource, not an event.
        self.documents = frozenset(request_url(url) for url in documents)
        self.max_bytes = max_bytes
        self.requests = []
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(self, url):
        url = request_url(url)
        if url not in self.documents:
            raise Unchecked("document URL is outside the fixture allowlist")
        self.requests.append({"method": "GET", "url": url})
        try:
            with self.opener.open(url, timeout=2) as response:
                data = response.read(self.max_bytes + 1)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise Unchecked("document retrieval failed or redirected: " + type(error).__name__) from error
        if len(data) > self.max_bytes:
            raise Unchecked("document exceeds the inspection byte limit")
        return data


def inspect(root_url, transport, *, asset_id="fixture-asset", max_documents=5):
    checks, documents, event_urls, visited = [], [], set(), set()
    event_requests = set()

    def record(name, outcome, reason, url=None):
        check = {"check": name, "outcome": outcome, "reason": reason}
        if url:
            check["document_url"] = url
        checks.append(check)

    url = root_url
    for _ in range(max_documents):
        try:
            identity = request_url(url)
        except Unchecked as error:
            record("document_retrieval", "not_checked", str(error), url)
            record("wrapper_resolution", "not_checked", "target URL is unsupported", url)
            break
        if identity in event_requests:
            record("wrapper_resolution", "not_checked", "target is also identified as an event URL", url)
            break
        if identity in visited:
            record("wrapper_resolution", "failed", "wrapper cycle in retrieved documents", url)
            break
        visited.add(identity)
        try:
            data = transport.get(url)
        except Unchecked as error:
            record("document_retrieval", "not_checked", str(error), url)
            record("wrapper_resolution", "not_checked", "a required document was not retrieved", url)
            break
        record("document_retrieval", "passed", "retrieved the requested document bytes", url)
        documents.append({"url": url, "request_url": identity,
                          "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        try:
            xml = data.decode("utf-8")
        except UnicodeDecodeError:
            record("xml_well_formedness", "not_checked", "fixture reader supports UTF-8 only", url)
            record("wrapper_resolution", "not_checked", "document was not parsed", url)
            break
        if "\x00" in xml or "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
            record("xml_well_formedness", "not_checked", "DTD, entities or unsupported encoding blocked", url)
            record("wrapper_resolution", "not_checked", "document was not parsed", url)
            break
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            record("xml_well_formedness", "failed", "XML parser rejected these bytes", url)
            record("wrapper_resolution", "not_checked", "document was not parsed", url)
            break
        record("xml_well_formedness", "passed", "XML parsed; no schema validation was performed", url)
        if root.tag != "VAST":
            record("vast_root", "failed", "root element is not VAST", url)
            record("wrapper_resolution", "not_checked", "document is not a supported VAST root", url)
            break
        for element in root.iter():
            if element.tag in EVENT_ELEMENTS and element.text and element.text.strip():
                event_url = element.text.strip()
                event_urls.add(event_url)
                try:
                    event_requests.add(request_url(event_url))
                except Unchecked:
                    # Unsupported event URIs are never retrieval candidates.
                    # This does not validate them or expand their macros.
                    pass
        ads = root.findall("Ad")
        if len(ads) != 1:
            record("wrapper_resolution", "not_checked", "fixture profile requires exactly one Ad", url)
            break
        children = list(ads[0])
        if len(children) != 1 or children[0].tag not in ("Wrapper", "InLine"):
            record("wrapper_resolution", "failed", "Ad does not contain exactly one Wrapper or InLine", url)
            break
        if children[0].tag == "InLine":
            record("wrapper_resolution", "passed", "single-ad chain reached an InLine document", url)
            break
        targets = children[0].findall("VASTAdTagURI")
        if len(targets) != 1 or not (targets[0].text or "").strip():
            record("wrapper_resolution", "failed", "Wrapper lacks one nonempty VASTAdTagURI", url)
            break
        url = targets[0].text.strip()
    else:
        record("wrapper_resolution", "not_checked", "document-count limit reached", url)

    for name, reason in (
        ("vast_schema_conformance", "no VAST schema or semantic validator was run"),
        ("format_membership", "no resolved proposal selection was supplied"),
        ("seller_spec_conformance", "no pinned seller specification was supplied"),
        ("media_decode", "media files were not fetched or decoded"),
        ("verification_execution", "verification code was not executed"),
        ("live_playback", "no live delivery was performed"),
        ("seller_approval", "no seller decision was supplied"),
    ):
        record(name, "not_checked", reason)
    return {"receipt_profile": "creative-inspection-discussion-2", "asset_id": asset_id,
            "inspected_at": datetime.now(timezone.utc).isoformat(),
            "context": {"root_url": root_url, "scope": "single-ad UTF-8 fixture document inspection",
                        "max_documents": max_documents, "max_document_bytes": transport.max_bytes,
                        "redirect_policy": "blocked", "macro_expansion": "not_performed",
                        "url_identity": "HTTP authority and default port normalized; fragments removed; path and query preserved"},
            "documents": documents, "identified_event_urls": sorted(event_urls),
            "requests": transport.requests, "checks": checks, "readiness": "not_assessed"}


def checks_satisfied(receipt, required):
    """A missing, skipped or failed required check cannot satisfy a check set.

    This helper does not turn satisfied checks into seller approval/readiness.
    """
    return bool(required) and all(
        any(check["check"] == name for check in receipt["checks"]) and
        all(check["outcome"] == "passed" for check in receipt["checks"] if check["check"] == name)
        for name in required
    )
