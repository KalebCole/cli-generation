#!/usr/bin/env python3
"""Automate the evidence-to-spec handoff into Printing Press."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def derive_name(url: str) -> str:
    host = urlparse(url).hostname or "site"
    labels = host.lower().split(".")
    if labels and labels[0] == "www":
        labels = labels[1:]
    base = labels[0] if labels else "site"
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "site"


def run_command(command: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, text=True, capture_output=True)


def write_json(path: Path, value: Dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def fail_command(label: str, result: subprocess.CompletedProcess) -> None:
    detail = result.stderr.strip() or result.stdout.strip() or "no output"
    raise RuntimeError("{} failed: {}".format(label, detail))


def inspect_spec_quality(spec_text: str) -> List[str]:
    """Catch browser-sniff output that parses but cannot map cleanly to CLI flags."""
    findings: List[str] = []
    for line_number, line in enumerate(spec_text.splitlines(), start=1):
        if re.match(r"^\s*-\s+name:\s*['\"]?\s*[\{\[]", line):
            findings.append(
                "line {}: request body JSON document was emitted as a parameter name".format(
                    line_number
                )
            )
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe a website, convert a HAR to a Printing Press spec, and validate the handoff."
    )
    parser.add_argument("url", help="Website or web-app URL")
    parser.add_argument("--name", help="CLI/spec name (derived from hostname by default)")
    parser.add_argument("--har", type=Path, help="HAR or enriched browser capture")
    parser.add_argument("--run-dir", type=Path, help="Durable evidence directory")
    parser.add_argument("--pp-bin", default="cli-printing-press", help="Printing Press binary")
    parser.add_argument("--min-samples", type=int, default=1)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    parsed = urlparse(args.url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        print("error: url must be an absolute http(s) URL", file=sys.stderr)
        return 2
    if args.har is not None and not args.har.is_file():
        print("error: HAR does not exist: {}".format(args.har), file=sys.stderr)
        return 2
    if args.min_samples < 1:
        print("error: --min-samples must be at least 1", file=sys.stderr)
        return 2

    name = args.name or derive_name(args.url)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", name):
        print(
            "error: --name must be a lowercase slug (letters, digits, hyphens; max 63)",
            file=sys.stderr,
        )
        return 2
    run_dir = args.run_dir or Path(".cli-pipeline") / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "run.json"
    spec_path = run_dir / "{}.yaml".format(name)
    analysis_path = run_dir / "traffic-analysis.json"

    manifest: Dict[str, Any] = {
        "schema_version": 1,
        "target_url": args.url,
        "name": name,
        "started_at": utc_now(),
        "status": "probing",
        "artifacts": {},
    }
    write_json(manifest_path, manifest)

    probe = run_command([args.pp_bin, "probe-reachability", args.url, "--json"])
    if probe.returncode != 0:
        manifest["status"] = "failed"
        manifest["error"] = "probe-reachability failed"
        write_json(manifest_path, manifest)
        fail_command("probe-reachability", probe)
    (run_dir / "reachability.json").write_text(probe.stdout)
    manifest["artifacts"]["reachability"] = str(run_dir / "reachability.json")

    if args.har is None:
        manifest["status"] = "capture_required"
        manifest["next_action"] = "Resume with --har PATH after browser traffic capture."
        write_json(manifest_path, manifest)
        print("capture required: resume this run with --har PATH", file=sys.stderr)
        return 2

    sniff = run_command([
        args.pp_bin,
        "browser-sniff",
        "--har", str(args.har),
        "--name", name,
        "--output", str(spec_path),
        "--analysis-output", str(analysis_path),
        "--samples-output", str(run_dir / "samples"),
        "--min-samples", str(args.min_samples),
        "--preserve-hosts",
    ])
    if sniff.returncode != 0:
        manifest["status"] = "failed"
        manifest["error"] = "browser-sniff failed"
        write_json(manifest_path, manifest)
        fail_command("browser-sniff", sniff)
    if not spec_path.is_file():
        raise RuntimeError("browser-sniff succeeded but did not write {}".format(spec_path))

    manifest["artifacts"].update({
        "spec": str(spec_path),
        "traffic_analysis": str(analysis_path),
    })
    quality_findings = inspect_spec_quality(spec_path.read_text())
    if quality_findings:
        manifest["status"] = "spec_needs_review"
        manifest["quality_findings"] = quality_findings
        manifest["next_action"] = (
            "Refine request-body modeling or capture a cleaner endpoint sample, then rerun."
        )
        write_json(manifest_path, manifest)
        print("spec needs review: {}".format(quality_findings[0]), file=sys.stderr)
        return 3

    validate = run_command([
        args.pp_bin,
        "generate",
        "--spec", str(spec_path),
        "--spec-source", "browser-sniffed",
        "--traffic-analysis", str(analysis_path),
        "--dry-run",
        "--json",
    ])
    (run_dir / "dry-run.json").write_text(validate.stdout)
    if validate.returncode != 0:
        manifest["status"] = "failed"
        manifest["error"] = "Printing Press dry-run validation failed"
        write_json(manifest_path, manifest)
        fail_command("generate --dry-run", validate)

    manifest["status"] = "spec_validated"
    manifest["completed_at"] = utc_now()
    manifest["artifacts"].update({
        "spec": str(spec_path),
        "traffic_analysis": str(analysis_path),
        "dry_run": str(run_dir / "dry-run.json"),
    })
    manifest["handoff_command"] = (
        "cli-printing-press generate --spec {} --spec-source browser-sniffed "
        "--traffic-analysis {} --research-dir {}"
    ).format(spec_path, analysis_path, run_dir)
    write_json(manifest_path, manifest)
    print(str(spec_path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        raise SystemExit(1)
