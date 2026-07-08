#!/usr/bin/env python3
"""Print a compact summary of a TaskDefinition XML file."""

from __future__ import annotations

import argparse
import collections
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Sequence


CONTROL_TAGS = {"Procedure", "Sequence", "OrderAny", "Unordered", "Option", "Alternative"}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a TaskDefinition XML file.")
    parser.add_argument("xml_file", type=Path)
    args = parser.parse_args(argv)

    try:
        root = ET.parse(args.xml_file).getroot()
    except Exception as exc:
        print(f"Failed to parse {args.xml_file}: {exc}", file=sys.stderr)
        return 1

    synthesis = root.find("Synthesis")
    if synthesis is None:
        print("No Synthesis section found.")
        return 1

    devices = [node.attrib.get("type", "") for node in synthesis.findall("./Device/Device")]
    containers = [node.attrib.get("id", "") for node in synthesis.findall("./Container/Container")]
    declared_metaops = [node.attrib.get("type", "") for node in synthesis.findall("./MetaOperation/MetaOperation")]

    procedure = synthesis.find("Procedure")
    op_counts = collections.Counter()
    control_counts = collections.Counter()
    if procedure is not None:
        for elem in procedure.iter():
            if elem is procedure:
                continue
            if elem.tag in CONTROL_TAGS:
                control_counts[elem.tag] += 1
            else:
                op_counts[elem.tag] += 1

    print(f"Task: {root.attrib.get('name', '<unnamed>')} version={root.attrib.get('version', '<missing>')}")
    start = root.find("./MetaData/StartDateTime")
    if start is not None:
        print(f"StartDateTime: {start.attrib.get('value', '<missing>')}")
    print(f"Devices ({len([d for d in devices if d])}): {', '.join(d for d in devices if d) or '<none>'}")
    print(f"Containers ({len([c for c in containers if c])}): {', '.join(c for c in containers if c) or '<none>'}")
    print(f"Declared MetaOps ({len([m for m in declared_metaops if m])}): {', '.join(m for m in declared_metaops if m) or '<none>'}")
    print("Control nodes:")
    for name, count in sorted(control_counts.items()):
        print(f"  {name}: {count}")
    if not control_counts:
        print("  <none>")
    print("Leaf operations:")
    for name, count in sorted(op_counts.items()):
        print(f"  {name}: {count}")
    if not op_counts:
        print("  <none>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
