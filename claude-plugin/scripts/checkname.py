#!/usr/bin/env python3
"""checkname: domain and social namespace triage with conservative heuristics."""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from dataclasses import dataclass
from typing import Callable, Iterable
from urllib import error, request

DEFAULT_TLDS = ["com", "io", "ai", "org", "net"]
DEFAULT_PLATFORMS = [
    "github",
    "x",
    "instagram",
    "tiktok",
    "youtube",
    "bluesky",
    "reddit",
    "linkedin",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class FetchResult:
    status_code: int
    body: str
    url: str
    final_url: str | None = None


PLATFORM_RULES = {
    "github": {
        "url": "https://github.com/{handle}",
        "available_statuses": {404},
        "available_patterns": ["not found"],
        "blocked_patterns": [],
    },
    "x": {
        "url": "https://x.com/{handle}",
        "available_statuses": {404},
        "available_patterns": ["this account doesn't exist", "account doesn't exist"],
        "blocked_patterns": ["log in to x", "something went wrong", "rate limit exceeded"],
    },
    "instagram": {
        "url": "https://www.instagram.com/{handle}/",
        "available_statuses": {404},
        "available_patterns": ["sorry, this page isn't available"],
        "blocked_patterns": ["login", "log in", "suspended"],
    },
    "tiktok": {
        "url": "https://www.tiktok.com/@{handle}",
        "available_statuses": {404},
        "available_patterns": ["couldn't find this account", "page not available"],
        "blocked_patterns": ["verify to continue", "login", "log in"],
    },
    "youtube": {
        "url": "https://www.youtube.com/@{handle}",
        "available_statuses": {404},
        "available_patterns": ["this page isn't available", "404 not found"],
        "blocked_patterns": [],
    },
    "bluesky": {
        "url": "https://bsky.app/profile/{handle}.bsky.social",
        "available_statuses": {404},
        "available_patterns": ["page not found", "profile not found"],
        "blocked_patterns": [],
    },
    "reddit": {
        "url": "https://www.reddit.com/user/{handle}/",
        "available_statuses": {404},
        "available_patterns": ["nobody on reddit goes by that name", "page not found"],
        "blocked_patterns": ["blocked", "rate limit", "sign up to continue"],
    },
    "linkedin": {
        "url": "https://www.linkedin.com/company/{handle}/",
        "available_statuses": {404},
        "available_patterns": ["page not found", "this page doesn't exist"],
        "blocked_patterns": ["authwall", "sign in", "join now"],
    },
}


def generate_checkname_variants(name: str, explicit_variants: Iterable[str] | None = None) -> list[str]:
    variants: list[str] = []
    if explicit_variants:
        for variant in explicit_variants:
            cleaned = variant.strip().lower()
            if cleaned and cleaned not in variants:
                variants.append(cleaned)
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    if not tokens:
        return variants
    compact = "".join(tokens)
    slug = "-".join(tokens)
    underscored = "_".join(tokens)
    for candidate in (compact, slug, underscored):
        if candidate and candidate not in variants:
            variants.append(candidate)
    return variants


def build_checkname_uspto_queries(query: str, variants: list[str]) -> dict:
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    exact_queries: list[str] = []
    broad_queries: list[str] = []

    normalized_phrase = " ".join(tokens).strip()
    if normalized_phrase:
        if len(tokens) > 1:
            exact_queries.append(f'CM:"{normalized_phrase}"')
            broad_queries.append(
                "CM:(" + " AND ".join(f"/.*{re.escape(token)}.*/" for token in tokens) + ")"
            )
        else:
            exact_queries.append(f"CM:{tokens[0]}")
            broad_queries.append(f"CM:/.*{re.escape(tokens[0])}.*/")

    for variant in variants:
        cleaned_variant = variant.strip().lower()
        if not cleaned_variant:
            continue
        exact_query = f'CM:"{cleaned_variant}"' if re.search(r"[^a-z0-9]", cleaned_variant) else f"CM:{cleaned_variant}"
        broad_query = f"CM:/.*{re.escape(cleaned_variant)}.*/"
        if exact_query not in exact_queries:
            exact_queries.append(exact_query)
        if broad_query not in broad_queries:
            broad_queries.append(broad_query)

    return {
        "status": "manual_review_needed",
        "source": "USPTO Trademark Search system",
        "search_url": "https://tmsearch.uspto.gov/",
        "exact_queries": exact_queries,
        "broad_queries": broad_queries,
        "review_focus": [
            "live marks first",
            "similar wording, sound, and commercial impression",
            "related goods and services, not just identical classes",
        ],
        "note": (
            "USPTO support in checkname is trademark triage only. Run the queries in the "
            "official Trademark Search system and review the live results manually."
        ),
    }


def fetch_checkname_url(url: str, timeout: int = 10) -> FetchResult:
    req = request.Request(url, headers=HEADERS)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read(65536).decode("utf-8", errors="ignore")
            return FetchResult(
                status_code=response.getcode(),
                body=body,
                url=url,
                final_url=response.geturl(),
            )
    except error.HTTPError as exc:
        body = exc.read(65536).decode("utf-8", errors="ignore")
        return FetchResult(
            status_code=exc.code,
            body=body,
            url=url,
            final_url=getattr(exc, "url", url),
        )
    except Exception as exc:  # pragma: no cover - transport edge
        return FetchResult(status_code=0, body=str(exc), url=url, final_url=url)


def classify_checkname_rdap_response(status_code: int, body: str) -> tuple[str, str]:
    lowered = body.lower()
    if status_code == 200 and any(key in body for key in ('"ldhName"', '"handle"', '"objectClassName"')):
        return "taken", "rdap_record_found"
    if status_code in {404, 410}:
        return "available", f"rdap_http_{status_code}"
    if "not found" in lowered or "no match" in lowered:
        return "available", "rdap_not_found_text"
    if status_code in {401, 403, 429, 500, 502, 503, 504}:
        return "uncertain", f"rdap_http_{status_code}"
    if status_code == 0:
        return "error", "transport_error"
    return "uncertain", f"rdap_http_{status_code or 'unknown'}"


def classify_checkname_profile_response(platform: str, status_code: int, body: str) -> tuple[str, str]:
    rules = PLATFORM_RULES[platform]
    lowered = body.lower()
    if status_code in rules["available_statuses"]:
        return "available", f"http_{status_code}"
    if any(pattern in lowered for pattern in rules["available_patterns"]):
        return "available", "not_found_text"
    if any(pattern in lowered for pattern in rules["blocked_patterns"]):
        return "uncertain", "blocked_or_login_wall"
    if status_code in {401, 403, 429, 999}:
        return "uncertain", f"http_{status_code}"
    if status_code == 0:
        return "error", "transport_error"
    if 200 <= status_code < 400:
        return "taken", f"http_{status_code}"
    return "uncertain", f"http_{status_code or 'unknown'}"


def probe_checkname_domain(domain: str, fetch: Callable[[str, int], FetchResult], timeout: int) -> dict:
    rdap_url = f"https://rdap.org/domain/{domain}"
    response = fetch(rdap_url, timeout)
    status, reason = classify_checkname_rdap_response(response.status_code, response.body)
    dns_hint = False
    try:
        socket.getaddrinfo(domain, 80)
        dns_hint = True
    except socket.gaierror:
        dns_hint = False
    return {
        "candidate": domain,
        "status": status,
        "reason": reason,
        "rdap_url": rdap_url,
        "http_status": response.status_code,
        "has_dns_hint": dns_hint,
    }


def probe_checkname_handle(
    platform: str,
    handle: str,
    fetch: Callable[[str, int], FetchResult],
    timeout: int,
) -> dict:
    url = PLATFORM_RULES[platform]["url"].format(handle=handle)
    response = fetch(url, timeout)
    status, reason = classify_checkname_profile_response(platform, response.status_code, response.body)
    return {
        "platform": platform,
        "handle": handle,
        "status": status,
        "reason": reason,
        "url": url,
        "http_status": response.status_code,
        "final_url": response.final_url,
    }


def summarize_checkname_variants(variants: list[str], domains: list[dict], handles: list[dict]) -> list[dict]:
    summary = []
    for variant in variants:
        variant_domains = [row for row in domains if row["candidate"].startswith(f"{variant}.")]
        variant_handles = [row for row in handles if row["handle"] == variant]
        summary.append(
            {
                "variant": variant,
                "available_domains": sum(1 for row in variant_domains if row["status"] == "available"),
                "taken_domains": sum(1 for row in variant_domains if row["status"] == "taken"),
                "available_handles": sum(1 for row in variant_handles if row["status"] == "available"),
                "taken_handles": sum(1 for row in variant_handles if row["status"] == "taken"),
                "uncertain_checks": sum(
                    1 for row in [*variant_domains, *variant_handles] if row["status"] == "uncertain"
                ),
            }
        )
    return sorted(
        summary,
        key=lambda item: (
            -item["available_domains"],
            -item["available_handles"],
            item["uncertain_checks"],
            item["variant"],
        ),
    )


def render_checkname_markdown(report: dict) -> str:
    lines = [
        f"# checkname report for {report['query']}",
        "",
        "## Recommended variants",
        "",
        "| Variant | Available domains | Available handles | Uncertain checks |",
        "|---|---:|---:|---:|",
    ]
    for item in report["summary"]["variants"][:5]:
        lines.append(
            f"| `{item['variant']}` | {item['available_domains']} | {item['available_handles']} | {item['uncertain_checks']} |"
        )
    lines.extend(
        [
            "",
            "## Domain checks",
            "",
            "| Candidate | Status | Reason |",
            "|---|---|---|",
        ]
    )
    for row in report["domains"]:
        lines.append(f"| `{row['candidate']}` | {row['status']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Social checks",
            "",
            "| Platform | Handle | Status | Reason |",
            "|---|---|---|---|",
        ]
    )
    for row in report["handles"]:
        lines.append(f"| {row['platform']} | `{row['handle']}` | {row['status']} | {row['reason']} |")
    if report.get("trademark_uspto"):
        trademark = report["trademark_uspto"]
        lines.extend(
            [
                "",
                "## USPTO trademark triage",
                "",
                f"- Status: `{trademark['status']}`",
                f"- Search system: {trademark['search_url']}",
                "- This is not trademark clearance. Review live federal results manually.",
                "",
                "### Exact wording queries",
                "",
            ]
        )
        lines.extend(f"- `{query}`" for query in trademark["exact_queries"])
        lines.extend(
            [
                "",
                "### Broadened wording queries",
                "",
            ]
        )
        lines.extend(f"- `{query}`" for query in trademark["broad_queries"])
    lines.extend(
        [
            "",
            "> checkname is namespace triage, not trademark or legal clearance.",
        ]
    )
    return "\n".join(lines)


def run_checkname_report(
    query: str,
    variants: list[str],
    tlds: list[str],
    platforms: list[str],
    timeout: int,
    fetch: Callable[[str, int], FetchResult],
    trademark_uspto: bool = False,
) -> dict:
    domains = [
        probe_checkname_domain(f"{variant}.{tld}", fetch=fetch, timeout=timeout)
        for variant in variants
        for tld in tlds
    ]
    handles = [
        probe_checkname_handle(platform, variant, fetch=fetch, timeout=timeout)
        for variant in variants
        for platform in platforms
    ]
    report = {
        "query": query,
        "variants": variants,
        "domains": domains,
        "handles": handles,
        "summary": {
            "variants": summarize_checkname_variants(variants, domains, handles),
            "note": "checkname is triage only. Confirm final availability manually.",
        },
    }
    if trademark_uspto:
        report["trademark_uspto"] = build_checkname_uspto_queries(query, variants)
    return report


def parse_checkname_csv(values: str | None, default: list[str]) -> list[str]:
    if not values:
        return list(default)
    parsed = [item.strip().lower() for item in values.split(",") if item.strip()]
    return parsed or list(default)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Brand or product name to normalize into namespace variants")
    parser.add_argument("--variants", help="Comma-separated explicit variants to include")
    parser.add_argument("--tlds", help="Comma-separated TLDs", default=",".join(DEFAULT_TLDS))
    parser.add_argument(
        "--platforms",
        help="Comma-separated platforms",
        default=",".join(DEFAULT_PLATFORMS),
    )
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument(
        "--trademark-uspto",
        action="store_true",
        help="Include official USPTO federal trademark search queries for manual review",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Emit JSON")
    output.add_argument("--markdown", action="store_true", help="Emit markdown")
    args = parser.parse_args(argv)

    variants = generate_checkname_variants(args.query, parse_checkname_csv(args.variants, []))
    if not variants:
        print("No usable variants generated from query.", file=sys.stderr)
        return 1
    tlds = parse_checkname_csv(args.tlds, DEFAULT_TLDS)
    platforms = parse_checkname_csv(args.platforms, DEFAULT_PLATFORMS)
    unknown_platforms = [item for item in platforms if item not in PLATFORM_RULES]
    if unknown_platforms:
        print(f"Unsupported platforms: {', '.join(unknown_platforms)}", file=sys.stderr)
        return 1

    report = run_checkname_report(
        query=args.query,
        variants=variants,
        tlds=tlds,
        platforms=platforms,
        trademark_uspto=args.trademark_uspto,
        timeout=args.timeout,
        fetch=fetch_checkname_url,
    )

    if args.markdown:
        print(render_checkname_markdown(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
