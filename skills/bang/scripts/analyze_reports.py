#!/usr/bin/env python3
"""Analyze BANG internal/external XLSX reports without third-party packages."""

from __future__ import annotations

import argparse
import json
import math
import os
import posixpath
import re
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse
from xml.etree import ElementTree as ET


AI_PLATFORMS = ["豆包", "DeepSeek", "元宝", "千问", "Kimi"]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ALIASES = SCRIPT_DIR.parent / "references" / "source-aliases.json"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference.upper())
    if not letters:
        raise ValueError(f"invalid cell reference: {reference}")
    result = 0
    for char in letters.group(0):
        result = result * 26 + ord(char) - 64
    return result - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t")) for item in root]


def _sheet_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in relations.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        if sheet.attrib.get("name") != sheet_name:
            continue
        relation_id = sheet.attrib.get(f"{{{REL_NS}}}id")
        target = targets.get(relation_id or "")
        if not target:
            break
        if target.startswith("/"):
            return target.lstrip("/")
        return posixpath.normpath(posixpath.join("xl", target))
    raise ValueError(f"worksheet not found: {sheet_name}")


def _cell_value(cell: ET.Element, shared: list[str]) -> Any:
    kind = cell.attrib.get("t")
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value_node = cell.find(f"{{{MAIN_NS}}}v")
    if value_node is None or value_node.text is None:
        return ""
    raw = value_node.text
    if kind == "s":
        return shared[int(raw)]
    if kind in {"str", "e"}:
        return raw
    if kind == "b":
        return raw == "1"
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def read_sheet(path: Path, sheet_name: str) -> list[list[Any]]:
    with zipfile.ZipFile(path) as archive:
        shared = _shared_strings(archive)
        root = ET.fromstring(archive.read(_sheet_path(archive, sheet_name)))
    rows: list[list[Any]] = []
    for row_node in root.findall(f".//{{{MAIN_NS}}}sheetData/{{{MAIN_NS}}}row"):
        values: list[Any] = []
        for cell in row_node.findall(f"{{{MAIN_NS}}}c"):
            index = column_index(cell.attrib.get("r", ""))
            if len(values) <= index:
                values.extend([""] * (index + 1 - len(values)))
            values[index] = _cell_value(cell, shared)
        rows.append(values)
    return rows


def text(value: Any) -> str:
    return str(value or "").strip()


def ratio(value: Any) -> float | None:
    if value in (None, ""):
        return None
    percent_string = isinstance(value, str) and value.strip().endswith("%")
    raw = value.strip().rstrip("%").replace(",", "") if isinstance(value, str) else value
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    if percent_string or number > 1:
        number /= 100
    return number if number <= 1 else None


def nonnegative_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    raw = value.replace(",", "").strip() if isinstance(value, str) else value
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def average(values: Iterable[float]) -> float | None:
    clean = list(values)
    return sum(clean) / len(clean) if clean else None


def find_header(rows: list[list[Any]], required: set[str]) -> int:
    for index, row in enumerate(rows[:30]):
        values = {text(value) for value in row}
        if required.issubset(values):
            return index
    raise ValueError("missing required headers: " + ", ".join(sorted(required)))


def analyze_keyword_rows(rows: list[list[Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    header_index = find_header(rows, {"关键词名称", "AI平台名称", "AI平台的可见占比"})
    if header_index == 0:
        raise ValueError("keyword report is missing the grouped brand header")
    headers = [text(value) for value in rows[header_index]]
    groups = [text(value) for value in rows[header_index - 1]]
    keyword_index = headers.index("关键词名称")
    platform_index = headers.index("AI平台名称")
    visibility_indices = [index for index, value in enumerate(headers) if value == "AI平台的可见占比"]
    customer_indices = [
        index for index in visibility_indices
        if index < len(groups) and ("(客户)" in groups[index] or "（客户）" in groups[index])
    ]
    competitor_indices = [
        index for index in visibility_indices
        if index < len(groups) and ("(核心竞品)" in groups[index] or "（核心竞品）" in groups[index])
    ]
    if len(customer_indices) != 1:
        raise ValueError(f"expected one customer visibility column, found {len(customer_indices)}")
    if not competitor_indices:
        raise ValueError("no core competitor visibility columns found")

    grouped: dict[str, dict[str, Any]] = {}
    for row in rows[header_index + 1:]:
        keyword = text(row[keyword_index] if keyword_index < len(row) else "")
        platform = text(row[platform_index] if platform_index < len(row) else "")
        if not keyword or not platform:
            continue
        current = grouped.setdefault(keyword, {
            "customer": [],
            "competitors": [[] for _ in competitor_indices],
        })
        customer_value = ratio(row[customer_indices[0]] if customer_indices[0] < len(row) else None)
        if customer_value is not None:
            current["customer"].append(customer_value)
        for position, index in enumerate(competitor_indices):
            competitor_value = ratio(row[index] if index < len(row) else None)
            if competitor_value is not None:
                current["competitors"][position].append(competitor_value)

    weak: list[dict[str, Any]] = []
    advantage: list[dict[str, Any]] = []
    for keyword, values in grouped.items():
        customer_average = average(values["customer"])
        competitor_averages = [average(items) for items in values["competitors"]]
        competitor_average = average(value for value in competitor_averages if value is not None)
        if customer_average is None or competitor_average is None:
            continue
        difference = competitor_average - customer_average
        base = {
            "keyword": keyword,
            "customer_visibility": round(customer_average, 6),
            "competitor_visibility": round(competitor_average, 6),
        }
        if difference > 0:
            weak.append({**base, "gap": round(difference, 6)})
        elif difference < 0:
            advantage.append({**base, "advantage": round(-difference, 6)})
    weak.sort(key=lambda item: (-item["gap"], item["keyword"]))
    advantage.sort(key=lambda item: (item["advantage"], item["keyword"]))
    return weak, advantage


def canonical_platform(value: Any) -> str | None:
    raw = text(value)
    folded = raw.casefold().replace(" ", "")
    aliases = {
        "豆包": "豆包",
        "deepseek": "DeepSeek",
        "元宝": "元宝",
        "千问": "千问",
        "通义千问": "千问",
        "kimi": "Kimi",
    }
    return aliases.get(folded)


def source_key(value: str) -> str:
    raw = value.strip()
    candidate = raw if re.match(r"^https?://", raw, re.I) else f"https://{raw}"
    host = (urlparse(candidate).hostname or "").casefold()
    if "." in host:
        return host.removeprefix("www.").removeprefix("m.")
    return raw


def normalize_source(value: Any, aliases: dict[str, str]) -> str:
    raw = text(value)
    if not raw:
        return ""
    probes = [raw, raw.casefold(), source_key(raw)]
    for probe in probes:
        if probe in aliases:
            return aliases[probe]
    return source_key(raw) or raw


def analyze_source_rows(
    reports: list[list[list[Any]]], aliases: dict[str, str], top_n: int = 20
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    counts: dict[str, dict[str, float]] = {platform: defaultdict(float) for platform in AI_PLATFORMS}
    for rows in reports:
        header_index = find_header(rows, {"信源平台名称", "AI平台名称", "AI平台的信源文章数"})
        headers = [text(value) for value in rows[header_index]]
        source_index = headers.index("信源平台名称")
        platform_index = headers.index("AI平台名称")
        count_index = headers.index("AI平台的信源文章数")
        for row in rows[header_index + 1:]:
            platform = canonical_platform(row[platform_index] if platform_index < len(row) else "")
            source = normalize_source(row[source_index] if source_index < len(row) else "", aliases)
            count = nonnegative_number(row[count_index] if count_index < len(row) else None)
            if platform and source and count is not None and count > 0:
                counts[platform][source] += count

    rankings: dict[str, list[dict[str, Any]]] = {}
    appearances: dict[str, int] = defaultdict(int)
    for platform in AI_PLATFORMS:
        total = sum(counts[platform].values())
        ranked = sorted(counts[platform].items(), key=lambda item: (-item[1], item[0]))[:top_n]
        rankings[platform] = [
            {
                "source": source,
                "article_count": int(count) if count.is_integer() else round(count, 4),
                "share": round(count / total, 8) if total else 0,
            }
            for source, count in ranked
        ]
        for source, _ in ranked:
            appearances[source] += 1
    return rankings, dict(sorted(appearances.items()))


def load_aliases(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError("source alias file must be a JSON string-to-string object")
    expanded: dict[str, str] = {}
    for key, value in data.items():
        expanded[key] = value
        expanded[key.casefold()] = value
        expanded[source_key(key)] = value
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--internal", type=Path, required=True)
    parser.add_argument("--external", type=Path, action="append", required=True)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be at least 1")

    weak, advantage = analyze_keyword_rows(read_sheet(args.internal, "关键词数据分析"))
    external_rows = [read_sheet(path, "AI平台的信源分析") for path in args.external]
    rankings, appearances = analyze_source_rows(external_rows, load_aliases(args.aliases), args.top)
    result = {
        "meta": {
            "external_report_count": len(args.external),
            "weak_keyword_count": len(weak),
            "small_advantage_keyword_count": len(advantage),
            "top_n": args.top,
        },
        "weak_keywords": weak,
        "small_advantage_keywords": advantage,
        "source_rankings": rankings,
        "source_appearances": appearances,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".bang-analysis-", dir=args.output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        temporary.replace(args.output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
