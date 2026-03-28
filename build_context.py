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


def render_context(plan_content: str, st_content: str, configs_map: dict[str, str], makefile_content: str, setup_content: str) -> str:
    """Render the combined context as YAML text."""
    out = []
    out.append("# Generated context file")
    out.append("# Includes Plan.MD, st.clab.yml, configs/*, Makefile, and setup-kind-ips.sh")
    out.append("")
    out.append("plan:")
    out.append(block_scalar(plan_content))
    out.append("st_clab:")
    out.append(block_scalar(st_content))
    out.append("configs:")
    if not configs_map:
        out.append("  {}")
    else:
        for name in sorted(configs_map):
            out.append(f"  {name}:")
            out.append(block_scalar(configs_map[name]))
    out.append("Makefile:")
    out.append(block_scalar(makefile_content))
    out.append("setup_script:")
    out.append(block_scalar(setup_content))
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a combined context file for srl-telemetry-lab")
    parser.add_argument("--topology", default="st.clab.yml", help="containerlab topology file (default: st.clab.yml)")
    parser.add_argument("--configs-dir", default="configs", help="directory with all configs (default: configs)")
    parser.add_argument("--makefile", default="Makefile", help="Makefile path (default: Makefile)")
    parser.add_argument("--plan", default="Plan.MD", help="Plan file path (default: Plan.MD)")
    parser.add_argument("--setup-script", default="setup-kind-ips.sh", help="setup script file")
    parser.add_argument("--output", default="context.yml", help="output context file (default: context.yml)")
    args = parser.parse_args()

    if not os.path.exists(args.topology):
        print(f"ERROR: topology file not found: {args.topology}", file=sys.stderr)
        return 2

    if not os.path.isdir(args.configs_dir):
        print(f"ERROR: configs directory not found: {args.configs_dir}", file=sys.stderr)
        return 3

    if not os.path.exists(args.makefile):
        print(f"ERROR: Makefile not found: {args.makefile}", file=sys.stderr)
        return 4

    if not os.path.exists(args.plan):
        print(f"ERROR: Plan file not found: {args.plan}", file=sys.stderr)
        return 5

    if not os.path.exists(args.setup_script):
        print(f"ERROR: setup script not found: {args.setup_script}", file=sys.stderr)
        return 6

    with open(args.plan, "r", encoding="utf-8") as f:
        plan_data = f.read()

    with open(args.topology, "r", encoding="utf-8") as f:
        st_data = f.read()

    configs_map = {}
    for root, _, files in os.walk(args.configs_dir):
        for fname in sorted(files):
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, args.configs_dir)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    configs_map[rel] = f.read()
            except UnicodeDecodeError:
                print(f"WARNING: skipping non-text file {path}", file=sys.stderr)

    with open(args.makefile, "r", encoding="utf-8") as f:
        makefile_data = f.read()

    with open(args.setup_script, "r", encoding="utf-8") as f:
        setup_data = f.read()

    context_yaml = render_context(plan_data, st_data, configs_map, makefile_data, setup_data)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(context_yaml)

    print(f"Wrote context file: {args.output} ({len(configs_map)} configs entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
