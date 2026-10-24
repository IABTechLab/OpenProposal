#!/usr/bin/env python3
"""Exercise inspection against local resources and local notification traps."""

import argparse
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from inspect_creative_fixture import FixtureTransport, Unchecked, checks_satisfied, inspect, request_url

ROOT = Path(__file__).resolve().parents[1]


def run():
    requests, routes = [], {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append({"method": "GET", "path": self.path})
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/events/redirect")
                self.end_headers()
                return
            status, body = routes.get(self.path, (404, b"not found"))
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_HEAD(self):
            requests.append({"method": "HEAD", "path": self.path})
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:" + str(server.server_port)
    inline = (ROOT / "fixtures/creative/inline.xml").read_text().replace("{{BASE}}", base)
    wrapper = (ROOT / "fixtures/creative/wrapper.xml").read_text().replace("{{BASE}}", base)

    def wrap(target):
        return wrapper.replace("{{TARGET}}", base + target).encode()

    routes.update({
        "/inline": (200, inline.encode()), "/wrapper": (200, wrap("/inline")),
        "/cycle": (200, wrap("/cycle")), "/broken-wrapper": (200, wrap("/missing")),
        "/external": (200, wrapper.replace("{{TARGET}}", "https://unreachable.example.test/ad").encode()),
        "/macro": (200, wrap("/inline?context=[PAGEURL]")),
        "/malformed": (200, b"<VAST><Ad></VAST>"),
        "/not-vast": (200, b"<html/>"),
        "/doctype": (200, b'<!DOCTYPE VAST [<!ENTITY x "unsafe">]><VAST>&x;</VAST>'),
        "/utf16": (200, inline.encode("utf-16")),
        "/large": (200, b" " * 65537), "/empty": (200, b'<VAST version="4.2"/>'),
        "/pod": (200, b'<VAST version="4.2"><Ad><InLine/></Ad><Ad><InLine/></Ad></VAST>'),
        "/missing-target": (200, b'<VAST><Ad><Wrapper/></Ad></VAST>'),
        "/both": (200, b'<VAST><Ad><Wrapper/><InLine/></Ad></VAST>'),
        "/dual-role": (200, wrap("/events/wrapper-impression")),
        "/events/wrapper-impression": (200, inline.encode()),
        "/inline-minimal": (200, b'<VAST version="4.2"><Ad><InLine/></Ad></VAST>'),
    })
    allowed = {base + path for path in routes if not path.startswith("/events/")} | {base + "/missing", base + "/redirect"}
    definitions = [
        ("wrapper-to-inline", "/wrapper", "wrapper_resolution", "passed", ["/wrapper", "/inline"], 5),
        ("inline-document", "/inline", "wrapper_resolution", "passed", ["/inline"], 5),
        ("wrapper-cycle", "/cycle", "wrapper_resolution", "failed", ["/cycle"], 5),
        ("wrapper-http-failure", "/broken-wrapper", "document_retrieval", "not_checked", ["/broken-wrapper", "/missing"], 5),
        ("redirect-to-event-blocked", "/redirect", "document_retrieval", "not_checked", ["/redirect"], 5),
        ("external-target-blocked", "/external", "document_retrieval", "not_checked", ["/external"], 5),
        ("unresolved-macro-blocked", "/macro", "document_retrieval", "not_checked", ["/macro"], 5),
        ("malformed-xml", "/malformed", "xml_well_formedness", "failed", ["/malformed"], 5),
        ("wrong-root", "/not-vast", "vast_root", "failed", ["/not-vast"], 5),
        ("doctype-not-executed", "/doctype", "xml_well_formedness", "not_checked", ["/doctype"], 5),
        ("unsupported-encoding", "/utf16", "xml_well_formedness", "not_checked", ["/utf16"], 5),
        ("document-size-limit", "/large", "document_retrieval", "not_checked", ["/large"], 5),
        ("empty-response-not-conformance", "/empty", "wrapper_resolution", "not_checked", ["/empty"], 5),
        ("ad-pod-outside-profile", "/pod", "wrapper_resolution", "not_checked", ["/pod"], 5),
        ("wrapper-target-missing", "/missing-target", "wrapper_resolution", "failed", ["/missing-target"], 5),
        ("ambiguous-ad-shape", "/both", "wrapper_resolution", "failed", ["/both"], 5),
        ("document-count-limit", "/wrapper", "wrapper_resolution", "not_checked", ["/wrapper"], 1),
        ("event-also-used-as-wrapper-target", "/dual-role", "wrapper_resolution", "not_checked", ["/dual-role"], 5),
        ("minimal-inline-is-not-schema-validation", "/inline-minimal", "vast_schema_conformance", "not_checked", ["/inline-minimal"], 5),
    ]
    dual_allowed = {"/dual-role": {base + "/events/wrapper-impression"}}
    expected_event_guard = set()

    def add_guard_case(name, xml, target):
        path = "/" + name
        routes[path] = (200, xml.encode())
        allowed.add(base + path)
        dual_allowed[path] = {target}
        expected_event_guard.add(path)
        definitions.append((name, path, "wrapper_resolution", "not_checked", [path], 5))

    event = base + "/events/wrapper-impression"
    add_guard_case("fragment-on-wrapper-target", wrapper.replace("{{TARGET}}", event + "#inspection"), event + "#inspection")
    add_guard_case("fragment-on-event-url", wrapper.replace(event, event + "#measurement").replace("{{TARGET}}", event), event)
    add_guard_case("scheme-case-event-alias", wrapper.replace("{{TARGET}}", event.replace("http:", "HTTP:")), event.replace("http:", "HTTP:"))
    routes["/cycle-fragment"] = (200, wrap("/cycle-fragment#again"))
    allowed.update({base + "/cycle-fragment", base + "/cycle-fragment#again"})
    definitions.append(("fragment-alias-cycle", "/cycle-fragment", "wrapper_resolution", "failed", ["/cycle-fragment"], 5))

    # Fixed VAST roles, intentionally independent of the inspector's role set.
    # Each target is allowlisted to prove the semantic guard, not a missing
    # allowlist entry, prevents the request.
    tracking = base + "/events/shared"
    routes["/events/shared"] = (200, inline.encode())
    resource = f'<StaticResource creativeType="image/png"><![CDATA[{base}/resource.png]]></StaticResource>'
    for role in ("CompanionClickTracking", "CompanionClickThrough",
                 "NonLinearClickTracking", "NonLinearClickThrough",
                 "IconViewTracking", "IconClickTracking", "IconClickThrough"):
        tag = f'<{role}><![CDATA[{tracking}]]></{role}>'
        xml = wrapper.replace("{{TARGET}}", tracking)
        if role.startswith("Companion"):
            extra = f'<Creative><CompanionAds><Companion width="300" height="250">{resource}{tag}</Companion></CompanionAds></Creative>'
            xml = xml.replace("</Creatives>", extra + "</Creatives>")
        elif role.startswith("NonLinear"):
            extra = f'<Creative><NonLinearAds><NonLinear width="300" height="50">{resource}{tag}</NonLinear></NonLinearAds></Creative>'
            xml = xml.replace("</Creatives>", extra + "</Creatives>")
        else:
            if role != "IconViewTracking":
                tag = "<IconClicks>" + tag + "</IconClicks>"
            extra = f'<Icons><Icon program="fixture" width="20" height="20" xPosition="left" yPosition="top">{resource}{tag}</Icon></Icons>'
            xml = xml.replace("</Linear>", extra + "</Linear>")
        add_guard_case("event-role-" + role, xml, tracking)

    results = []
    try:
        for name, path, check, outcome, expected_requests, limit in definitions:
            requests.clear()
            # Dual-role case deliberately allows the URL to prove the semantic
            # event guard stops it before the transport allowlist is consulted.
            permitted = allowed | dual_allowed.get(path, set())
            receipt = inspect(base + path, FixtureTransport(permitted), max_documents=limit)
            matches = [item for item in receipt["checks"] if item["check"] == check]
            notifications = [item for item in requests if item["path"].startswith("/events/")]
            passed = (bool(matches) and matches[-1]["outcome"] == outcome and not notifications
                      and [item["path"] for item in requests] == expected_requests
                      and not checks_satisfied(receipt, ["vast_schema_conformance"])
                      and not checks_satisfied(receipt, ["unknown_required_check"])
                      and not checks_satisfied(receipt, []) and receipt["readiness"] == "not_assessed")
            if path == "/wrapper" and limit == 5:
                passed = passed and checks_satisfied(receipt, ["document_retrieval", "xml_well_formedness", "wrapper_resolution"])
                passed = passed and len(receipt["identified_event_urls"]) == 13
            if path in expected_event_guard:
                passed = passed and matches[-1]["reason"] == "target is also identified as an event URL"
                passed = passed and not checks_satisfied(receipt, ["document_retrieval", "xml_well_formedness", "wrapper_resolution"])
            results.append({"id": name, "passed": bool(passed), "expected_check": check,
                            "expected_outcome": outcome, "server_requests": requests.copy(), "receipt": receipt})
        # A positive control proves the trap records notifications, including HEAD.
        # These endpoints are synthetic and loopback-only, never campaign URLs.
        requests.clear()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for method in ("GET", "HEAD"):
            try:
                with opener.open(urllib.request.Request(base + "/events/control", method=method)):
                    pass
            except urllib.error.HTTPError:
                pass
        results.append({"id": "notification-trap-positive-control", "passed": requests == [
            {"method": "GET", "path": "/events/control"}, {"method": "HEAD", "path": "/events/control"}],
            "server_requests": requests.copy()})
        url_cases = [
            ("url-fragment-removed", "http://example.test/events/x#preview", "http://example.test/events/x"),
            ("url-http-authority-normalized", "HTTP://EXAMPLE.TEST:80/events/x", "http://example.test/events/x"),
            ("url-https-default-port", "https://EXAMPLE.TEST:443/events/x", "https://example.test/events/x"),
            ("url-empty-path", "http://example.test", "http://example.test/"),
            ("url-ipv6-normalized", "http://[0:0:0:0:0:0:0:1]:80/x", "http://[::1]/x"),
            ("url-query-preserved", "http://example.test/x?signature=%7e&b=2&a=1#preview", "http://example.test/x?signature=%7e&b=2&a=1"),
            ("url-empty-query-preserved", "http://example.test/x?#preview", "http://example.test/x?"),
        ]
        for name, value, expected in url_cases:
            actual = request_url(value)
            results.append({"id": name, "passed": actual == expected, "input": value, "expected": expected, "actual": actual})
        for name, value in (("url-credentials-blocked", "http://user:password@example.test/x"),
                            ("url-non-http-blocked", "file:///events/x"),
                            ("url-control-character-blocked", "http://example.test/\nx")):
            try:
                request_url(value)
                blocked = False
            except Unchecked:
                blocked = True
            results.append({"id": name, "passed": blocked, "expected": "not_checked"})
        return {"profile": "creative-inspection-discussion-2", "passed": sum(item["passed"] for item in results),
                "total": len(results), "cases": results}
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for case in report["cases"]:
            print(("PASS " if case["passed"] else "FAIL ") + case["id"])
        print(f'{report["passed"]}/{report["total"]} creative inspection cases pass')
    raise SystemExit(report["passed"] != report["total"])
