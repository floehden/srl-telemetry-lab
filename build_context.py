#!/usr/bin/env python3
"""Build a single context file containing st.clab.yml and fabric startup configs."""

from __future__ import annotations

import argparse
import os
import textwrap
import sys


def block_scalar(value: str) -> str:
    """Return a YAML block scalar with preserved newlines."""
    # Use | for trailing newline semantics. Keep empty string with "|" as a value.
    if value == "":
        return "|"

    # Normalize line endings, strip only last newline for consistent output
    text = value.replace("\r\n", "\n").rstrip("\n")
    lines = text.split("\n")
    result = "|\n"
    for line in lines:
        result += "  " + line + "\n"
    return result


def render_context(st_content: str, fabric_map: dict[str, str], cluster_map: dict[str, str], testing_map: dict[str, str], setup_content: str) -> str:
    """Render the combined context as YAML text."""
    out = []
    out.append("# Generated context file")
    out.append("# Includes st.clab.yml, configs/fabric/*.cfg, configs/cluster/*.yaml, testing/*.yaml, and setup-kind-ips.sh")
    out.append("")
    out.append("st_clab:")
    out.append(block_scalar(st_content))
    out.append("fabric_configs:")
    if not fabric_map:
        out.append("  {}")
    else:
        for name in sorted(fabric_map):
            out.append(f"  {name}:")
            out.append(block_scalar(fabric_map[name]))
    out.append("cluster_configs:")
    if not cluster_map:
        out.append("  {}")
    else:
        for name in sorted(cluster_map):
            out.append(f"  {name}:")
            out.append(block_scalar(cluster_map[name]))
    out.append("testing_configs:")
    if not testing_map:
        out.append("  {}")
    else:
        for name in sorted(testing_map):
            out.append(f"  {name}:")
            out.append(block_scalar(testing_map[name]))
    out.append("setup_script:")
    out.append(block_scalar(setup_content))
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a combined context file for srl-telemetry-lab")
    parser.add_argument("--topology", default="st.clab.yml", help="containerlab topology file (default: st.clab.yml)")
    parser.add_argument("--fabric-dir", default="configs/fabric", help="directory with fabric startup config files")
    parser.add_argument("--cluster-dir", default="configs/cluster", help="directory with cluster config files")
    parser.add_argument("--testing-dir", default="testing", help="directory with testing config files")
    parser.add_argument("--setup-script", default="setup-kind-ips.sh", help="setup script file")
    parser.add_argument("--output", default="context.yml", help="output context file (default: context.yml)")
    args = parser.parse_args()

    if not os.path.exists(args.topology):
        print(f"ERROR: topology file not found: {args.topology}", file=sys.stderr)
        return 2

    if not os.path.isdir(args.fabric_dir):
        print(f"ERROR: fabric directory not found: {args.fabric_dir}", file=sys.stderr)
        return 3

    if not os.path.isdir(args.cluster_dir):
        print(f"ERROR: cluster directory not found: {args.cluster_dir}", file=sys.stderr)
        return 4

    if not os.path.isdir(args.testing_dir):
        print(f"ERROR: testing directory not found: {args.testing_dir}", file=sys.stderr)
        return 5

    if not os.path.exists(args.setup_script):
        print(f"ERROR: setup script not found: {args.setup_script}", file=sys.stderr)
        return 6

    with open(args.topology, "r", encoding="utf-8") as f:
        st_data = f.read()

    fabric_map = {}
    for root, _, files in os.walk(args.fabric_dir):
        for fname in sorted(files):
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, args.fabric_dir)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    fabric_map[rel] = f.read()
            except UnicodeDecodeError:
                print(f"WARNING: skipping non-text file {path}", file=sys.stderr)

    cluster_map = {}
    for root, _, files in os.walk(args.cluster_dir):
        for fname in sorted(files):
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, args.cluster_dir)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cluster_map[rel] = f.read()
            except UnicodeDecodeError:
                print(f"WARNING: skipping non-text file {path}", file=sys.stderr)

    testing_map = {}
    for root, _, files in os.walk(args.testing_dir):
        for fname in sorted(files):
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, args.testing_dir)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    testing_map[rel] = f.read()
            except UnicodeDecodeError:
                print(f"WARNING: skipping non-text file {path}", file=sys.stderr)

    with open(args.setup_script, "r", encoding="utf-8") as f:
        setup_data = f.read()

    context_yaml = render_context(st_data, fabric_map, cluster_map, testing_map, setup_data)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(context_yaml)

    print(f"Wrote context file: {args.output} ({len(fabric_map)} fabric configs, {len(cluster_map)} cluster configs, {len(testing_map)} testing configs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
