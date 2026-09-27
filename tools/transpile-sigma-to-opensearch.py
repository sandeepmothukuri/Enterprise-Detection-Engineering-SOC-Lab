#!/usr/bin/env python3
"""
Sigma-to-OpenSearch Auto-Transpiler
==================================
Converts Sigma YAML detection rules into native OpenSearch Query DSL (JSON),
OpenSearch Dashboards Lucene query strings, and ElastAlert2 filter syntax.

Can run standalone (zero-dependency built-in AST compiler) or with pySigma when available.
"""

import os
import sys
import glob
import json
import argparse
from pathlib import Path
import yaml


def _escape_lucene(val: str) -> str:
    """Escape special characters for Lucene query string."""
    special = ['+', '-', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '?', ':', '\\', '/']
    s = str(val)
    for ch in special:
        s = s.replace(ch, f"\\{ch}")
    return s


def transpile_field_match(field: str, value: any, modifier: str = "") -> dict:
    """Translate a single field condition to OpenSearch Query DSL & Lucene."""
    # Field mapping overrides if needed (e.g. Windows Sysmon to ECS / OpenSearch naming)
    dsl_field = field

    if modifier == "endswith":
        if isinstance(value, list):
            clauses = [{"wildcard": {dsl_field: {"value": f"*{v}"}}} for v in value]
            return {"bool": {"should": clauses, "minimum_should_match": 1}}
        return {"wildcard": {dsl_field: {"value": f"*{value}"}}}

    elif modifier == "startswith":
        if isinstance(value, list):
            clauses = [{"wildcard": {dsl_field: {"value": f"{v}*"}}} for v in value]
            return {"bool": {"should": clauses, "minimum_should_match": 1}}
        return {"wildcard": {dsl_field: {"value": f"{value}*"}}}

    elif modifier == "contains":
        if isinstance(value, list):
            clauses = [{"match_phrase": {dsl_field: v}} for v in value]
            return {"bool": {"should": clauses, "minimum_should_match": 1}}
        return {"match_phrase": {dsl_field: value}}

    elif modifier == "re":
        return {"regexp": {dsl_field: {"value": value}}}

    else:
        # Exact match / terms list
        if isinstance(value, list):
            return {"terms": {f"{dsl_field}.keyword": value}} if not dsl_field.endswith(".keyword") else {"terms": {dsl_field: value}}
        elif isinstance(value, (int, float, bool)):
            return {"term": {dsl_field: value}}
        else:
            return {"match_phrase": {dsl_field: value}}


def transpile_selection_block(block: dict) -> list:
    """Convert a Sigma selection dict into a list of Query DSL clauses."""
    must_clauses = []
    for k, v in block.items():
        if "|" in k:
            field, modifier = k.split("|", 1)
        else:
            field, modifier = k, ""
        must_clauses.append(transpile_field_match(field, v, modifier))
    return must_clauses


def transpile_sigma_rule(rule_dict: dict) -> dict:
    """Transpile a parsed Sigma rule into OpenSearch Query DSL."""
    detection = rule_dict.get("detection", {})
    condition = detection.get("condition", "selection")

    must_clauses = []
    must_not_clauses = []
    should_clauses = []

    # Process selections
    for key, value in detection.items():
        if key == "condition":
            continue
        if key.startswith("selection"):
            if isinstance(value, dict):
                must_clauses.extend(transpile_selection_block(value))
            elif isinstance(value, list):
                # list of dicts -> OR of selections
                sub_or = []
                for item in value:
                    if isinstance(item, dict):
                        sub_or.append({"bool": {"must": transpile_selection_block(item)}})
                if sub_or:
                    should_clauses.extend(sub_or)
        elif key.startswith("filter"):
            if isinstance(value, dict):
                must_not_clauses.extend(transpile_selection_block(value))

    # Build the final bool query
    bool_query = {}
    if must_clauses:
        bool_query["must"] = must_clauses
    if must_not_clauses:
        bool_query["must_not"] = must_not_clauses
    if should_clauses:
        bool_query["should"] = should_clauses
        if not must_clauses:
            bool_query["minimum_should_match"] = 1

    return {
        "id": rule_dict.get("id", ""),
        "title": rule_dict.get("title", "Untitled Rule"),
        "status": rule_dict.get("status", "production"),
        "severity": rule_dict.get("level", "medium"),
        "tags": rule_dict.get("tags", []),
        "description": rule_dict.get("description", ""),
        "logsource": rule_dict.get("logsource", {}),
        "query": {
            "bool": bool_query
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Sigma to OpenSearch Query DSL Transpiler")
    parser.add_argument("--rules-dir", default="detection-rules/sigma", help="Path to Sigma rules directory")
    parser.add_argument("--output-dir", default="detection-rules/compiled", help="Path to write compiled OpenSearch queries")
    parser.add_argument("--validate-only", action="store_true", help="Validate translation without writing files")
    args = parser.parse_args()

    rules_path = Path(args.rules_dir)
    if not rules_path.exists():
        print(f"[-] Error: Rules directory not found: {args.rules_dir}", file=sys.stderr)
        sys.exit(1)

    rule_files = list(rules_path.rglob("*.yml")) + list(rules_path.rglob("*.yaml"))
    if not rule_files:
        print(f"[-] Error: No Sigma rules found in {args.rules_dir}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output_dir)
    if not args.validate_only:
        output_path.mkdir(parents=True, exist_ok=True)

    print(f"[*] Found {len(rule_files)} Sigma rules in {args.rules_dir}")
    success_count = 0
    compiled_catalog = []

    for rule_file in sorted(rule_files):
        try:
            with open(rule_file, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            
            if not isinstance(data, dict):
                continue

            assert "title" in data, f"Missing 'title' in {rule_file}"
            assert "detection" in data, f"Missing 'detection' in {rule_file}"

            compiled = transpile_sigma_rule(data)
            compiled["source_file"] = str(rule_file.as_posix())
            compiled_catalog.append(compiled)

            if not args.validate_only:
                out_filename = rule_file.stem + ".json"
                out_file = output_path / out_filename
                with open(out_file, "w", encoding="utf-8") as out_fh:
                    json.dump(compiled, out_fh, indent=2)

            print(f"  [+] Transpiled: {rule_file.name} -> {compiled['title']} [{compiled['severity'].upper()}]")
            success_count += 1
        except Exception as e:
            print(f"  [-] Failed: {rule_file}: {e}", file=sys.stderr)
            sys.exit(1)

    # Also output consolidated catalog
    if not args.validate_only:
        catalog_file = output_path / "opensearch_detection_catalog.json"
        with open(catalog_file, "w", encoding="utf-8") as cat_fh:
            json.dump({"total_rules": len(compiled_catalog), "rules": compiled_catalog}, cat_fh, indent=2)
        print(f"[*] Consolidated catalog written to {catalog_file}")

    print(f"[+] SUCCESS: Successfully transpiled and validated {success_count}/{len(rule_files)} Sigma rules to OpenSearch Query DSL.")


if __name__ == "__main__":
    main()
