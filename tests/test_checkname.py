import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "claude-plugin" / "scripts" / "checkname.py"
SPEC = importlib.util.spec_from_file_location("checkname", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ChecknameTests(unittest.TestCase):
    def test_generate_checkname_variants(self):
        variants = MODULE.generate_checkname_variants("Acme Labs", None)
        self.assertEqual(variants[:3], ["acmelabs", "acme-labs", "acme_labs"])

    def test_generate_checkname_variants_keeps_explicit_first(self):
        variants = MODULE.generate_checkname_variants("Acme Labs", ["getacme", "acme"])
        self.assertEqual(variants[0], "getacme")
        self.assertIn("acmelabs", variants)

    def test_classify_checkname_rdap_taken(self):
        status, reason = MODULE.classify_checkname_rdap_response(200, '{"ldhName":"acme.com"}')
        self.assertEqual(status, "taken")
        self.assertEqual(reason, "rdap_record_found")

    def test_classify_checkname_rdap_available(self):
        status, reason = MODULE.classify_checkname_rdap_response(404, "not found")
        self.assertEqual(status, "available")
        self.assertTrue(reason.startswith("rdap_"))

    def test_classify_checkname_rdap_uncertain(self):
        status, reason = MODULE.classify_checkname_rdap_response(429, "rate limited")
        self.assertEqual(status, "uncertain")
        self.assertEqual(reason, "rdap_http_429")

    def test_classify_checkname_profile_available(self):
        status, reason = MODULE.classify_checkname_profile_response("github", 404, "Not Found")
        self.assertEqual(status, "available")
        self.assertEqual(reason, "http_404")

    def test_classify_checkname_profile_taken(self):
        status, reason = MODULE.classify_checkname_profile_response("github", 200, "<title>repo</title>")
        self.assertEqual(status, "taken")
        self.assertEqual(reason, "http_200")

    def test_classify_checkname_profile_uncertain(self):
        status, reason = MODULE.classify_checkname_profile_response("x", 200, "Log in to X")
        self.assertEqual(status, "uncertain")
        self.assertEqual(reason, "blocked_or_login_wall")

    def test_run_checkname_report_shape(self):
        def fake_fetch(url, timeout):
            if "rdap.org" in url:
                if "acmelabs.com" in url:
                    return MODULE.FetchResult(404, "not found", url, url)
                return MODULE.FetchResult(200, '{"ldhName":"taken.io"}', url, url)
            if "github.com" in url:
                return MODULE.FetchResult(404, "not found", url, url)
            return MODULE.FetchResult(200, "Log in to X", url, url)

        report = MODULE.run_checkname_report(
            query="Acme Labs",
            variants=["acmelabs"],
            tlds=["com", "io"],
            platforms=["github", "x"],
            timeout=5,
            fetch=fake_fetch,
        )
        self.assertEqual(report["query"], "Acme Labs")
        self.assertEqual(len(report["domains"]), 2)
        self.assertEqual(len(report["handles"]), 2)
        self.assertEqual(report["summary"]["variants"][0]["variant"], "acmelabs")

    def test_build_checkname_uspto_queries(self):
        queries = MODULE.build_checkname_uspto_queries("Acme Labs", ["acmelabs", "acme-labs"])
        self.assertEqual(queries["status"], "manual_review_needed")
        self.assertIn('CM:"acme labs"', queries["exact_queries"])
        self.assertIn("CM:(/.*acme.*/ AND /.*labs.*/)", queries["broad_queries"])
        self.assertIn("CM:acmelabs", queries["exact_queries"])

    def test_run_checkname_report_includes_uspto_section(self):
        def fake_fetch(url, timeout):
            if "rdap.org" in url:
                return MODULE.FetchResult(404, "not found", url, url)
            return MODULE.FetchResult(404, "not found", url, url)

        report = MODULE.run_checkname_report(
            query="Acme Labs",
            variants=["acmelabs"],
            tlds=["com"],
            platforms=["github"],
            trademark_uspto=True,
            timeout=5,
            fetch=fake_fetch,
        )
        self.assertIn("trademark_uspto", report)
        self.assertEqual(report["trademark_uspto"]["status"], "manual_review_needed")
        self.assertIn("tmsearch.uspto.gov", report["trademark_uspto"]["search_url"])


if __name__ == "__main__":
    unittest.main()
