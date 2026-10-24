#!/usr/bin/env python3
"""Exercise inspection against local resources and local notification traps."""

import argparse
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from inspect_creative_fixture import FixtureTransport, checks_satisfied, inspect

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
    results = []
    try:
        for name, path, check, outcome, expected_requests, limit in definitions:
            requests.clear()
            # Dual-role case deliberately allows the URL to prove the semantic
            # event guard stops it before the transport allowlist is consulted.
            permitted = allowed | ({base + "/events/wrapper-impression"} if path == "/dual-role" else set())
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
        return {"profile": "creative-inspection-discussion-1", "passed": sum(item["passed"] for item in results),
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
