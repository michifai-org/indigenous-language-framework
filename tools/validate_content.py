#!/usr/bin/env python3
"""Check a community's content folder against the framework schema.

Usage
    python tools/validate_content.py CONTENT_DIR
    python tools/validate_content.py CONTENT_DIR --check-files --strict
    python tools/validate_content.py --init NEW_DIR      # create blank tables

Why this exists
    Lessons refer to words, sentences and grammar by id. If an id is mistyped or a
    row is deleted, a lesson silently breaks. The checker catches that, plus the
    rules in PROTOCOLS.md that a machine can check: every item names its source,
    withdrawn consent is never usable, and restricted material never reaches a
    lesson.

It runs entirely on your own computer, reads only the folder you give it, and
sends nothing anywhere. Needs Python 3.8+. PyYAML is optional (used only to read
community.yaml).
"""
import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "tables.json"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
ACCESS_RANK = {"open": 0, "program": 1, "restricted": 2}


class Report:
    def __init__(self):
        self.errors, self.warnings, self.notes = [], [], []

    def error(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")

    def note(self, where, msg):
        self.notes.append(f"{where}: {msg}")


def split_list(value):
    return [v.strip() for v in value.split(";") if v.strip()]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        return [], []
    header = [h.strip() for h in rows[0]]
    data = []
    for lineno, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        row = (row + [""] * len(header))[: len(header)]
        data.append((lineno, dict(zip(header, (c.strip() for c in row)))))
    return header, data


def init_blank(schema, target):
    target.mkdir(parents=True, exist_ok=True)
    for spec in schema["tables"].values():
        path = target / spec["file"]
        if path.exists():
            print(f"left alone (already exists): {path}")
            continue
        with open(path, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow([c["name"] for c in spec["columns"]])
        print(f"created: {path}")


def load_tables(schema, content_dir, report):
    tables = {}  # name -> {"rows": [(lineno, row)], "ids": {id: row}, "present": bool}
    for name, spec in schema["tables"].items():
        path = content_dir / spec["file"]
        info = {"rows": [], "ids": {}, "present": path.exists(), "file": spec["file"]}
        tables[name] = info
        if not path.exists():
            report.warn(spec["file"], "file not found; skipped")
            continue
        header, rows = read_csv(path)
        info["rows"] = rows
        known = {c["name"] for c in spec["columns"]}
        for col in spec["columns"]:
            if col.get("required") and col["name"] not in header:
                report.error(spec["file"], f"missing required column '{col['name']}'")
        extra = [h for h in header if h and h not in known]
        if extra:
            report.note(spec["file"], f"extra columns kept as-is: {', '.join(extra)}")
        for lineno, row in rows:
            where = f"{spec['file']} line {lineno}"
            for col in spec["columns"]:
                cname, val = col["name"], row.get(col["name"], "")
                if col.get("required") and not val:
                    report.error(where, f"'{cname}' is empty")
                if val and unicodedata.normalize("NFC", val) != val:
                    report.warn(where, f"'{cname}' is not Unicode-normalised (NFC); the same letter typed two ways may not match. Re-save or normalise the text")
                if val and "enum" in col and val not in col["enum"]:
                    report.error(where, f"'{cname}' is '{val}'; allowed: {', '.join(col['enum'])}")
                if val and "list_enum" in col:
                    for item in split_list(val):
                        if item not in col["list_enum"]:
                            report.error(where, f"'{cname}' has '{item}'; allowed: {', '.join(col['list_enum'])}")
                if val and col.get("access") and val not in schema["access_levels"]:
                    report.error(where, f"'{cname}' is '{val}'; allowed: {', '.join(schema['access_levels'])}")
            rid = row.get("id", "")
            if rid:
                if not ID_RE.match(rid):
                    report.error(where, f"id '{rid}' should use lowercase letters, digits, - or _ only")
                if rid in info["ids"]:
                    report.error(where, f"duplicate id '{rid}'")
                info["ids"][rid] = row
            if name == "sounds" and row.get("order") and not row["order"].isdigit():
                report.error(where, "'order' must be a whole number")
            if name == "texts" and row.get("word_count") and not row["word_count"].isdigit():
                report.error(where, "'word_count' must be a whole number")
    return tables


def check_refs(schema, tables, report):
    for name, spec in schema["tables"].items():
        for lineno, row in tables[name]["rows"]:
            where = f"{spec['file']} line {lineno}"
            for col in spec["columns"]:
                target = col.get("ref")
                val = row.get(col["name"], "")
                if not target or not val:
                    continue
                for ref in (split_list(val) if col.get("list") else [val]):
                    if ref not in tables[target]["ids"]:
                        report.error(where, f"'{col['name']}' refers to '{ref}', which is not in {schema['tables'][target]['file']}")


def check_protocols(tables, report):
    sources = tables["sources"]["ids"]
    audio = tables["audio"]["ids"]
    for tname in ("audio", "words", "sentences", "texts"):
        for lineno, row in tables[tname]["rows"]:
            where = f"{tables[tname]['file']} line {lineno}"
            access = row.get("access", "")
            src = sources.get(row.get("source_id", ""))
            if src:
                consent = src.get("consent_status", "")
                uses = split_list(src.get("permitted_uses", ""))
                if consent == "withdrawn" and access != "restricted":
                    report.error(where, f"source '{src['id']}' has withdrawn consent; this item must be 'restricted' (or removed)")
                if access == "open" and consent in ("pending", "unknown"):
                    report.warn(where, f"marked 'open' but consent for source '{src['id']}' is {consent}")
                if access == "open" and "teaching" not in uses:
                    report.warn(where, f"marked 'open' but source '{src['id']}' does not list 'teaching' as a permitted use")
            aud = audio.get(row.get("audio_id", ""))
            if aud and access in ACCESS_RANK and aud.get("access") in ACCESS_RANK:
                if ACCESS_RANK[access] < ACCESS_RANK[aud["access"]]:
                    report.warn(where, f"is '{access}' but its audio '{aud['id']}' is '{aud['access']}'; the audio may reach people the item should not")


def check_files(tables, content_dir, report):
    for lineno, row in tables["audio"]["rows"]:
        f = row.get("file", "")
        if f and not (content_dir / f).exists():
            report.warn(f"audio.csv line {lineno}", f"audio file not found at '{f}' (fine if recordings are stored elsewhere; omit --check-files)")


def check_orthographies(schema, tables, content_dir, report):
    path = content_dir / "community.yaml"
    used = set()
    for tname in ("words", "sentences"):
        for _, row in tables[tname]["rows"]:
            for col in schema["forms_columns"]:
                if row.get(col):
                    used.add(col)
    if not path.exists():
        report.warn("community.yaml", "not found; it declares which writing system each form_N column holds")
        return
    try:
        import yaml
    except ImportError:
        report.note("community.yaml", "PyYAML not installed; skipped orthography check (pip install pyyaml)")
        return
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        report.error("community.yaml", f"could not be read: {exc}")
        return
    declared = {o.get("column") for o in data.get("orthographies") or [] if isinstance(o, dict)}
    for col in sorted(used - declared):
        report.error("community.yaml", f"'{col}' has text in words/sentences but is not declared under orthographies")
    for col in sorted(d for d in declared if d and d not in schema["forms_columns"]):
        report.error("community.yaml", f"orthography column '{col}' is not one of {', '.join(schema['forms_columns'])}")


def parse_lesson(path):
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return meta
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, val = line.partition(":")
            meta[key.strip()] = val.split("  #")[0].strip()
    return None


def check_lessons(schema, tables, content_dir, report):
    spec = schema["lesson"]
    lesson_dir = content_dir / spec["directory"]
    if not lesson_dir.is_dir():
        report.note(spec["directory"], "no lessons folder; lesson checks skipped")
        return
    lessons = []
    for path in sorted(lesson_dir.glob("*.md")):
        where = f"{spec['directory']}/{path.name}"
        meta = parse_lesson(path)
        if meta is None:
            report.error(where, "no front matter (the block between two '---' lines at the top)")
            continue
        ok = True
        for key in spec["required_keys"]:
            if not meta.get(key):
                report.error(where, f"front matter is missing '{key}'")
                ok = False
        if not ok:
            continue
        if not meta["order"].isdigit():
            report.error(where, "'order' must be a whole number")
            continue
        lessons.append((int(meta["order"]), where, meta))
    seen_ids, seen_orders = {}, {}
    for order, where, meta in lessons:
        if meta["id"] in seen_ids:
            report.error(where, f"lesson id '{meta['id']}' also used in {seen_ids[meta['id']]}")
        if order in seen_orders:
            report.error(where, f"order {order} also used in {seen_orders[order]}")
        seen_ids[meta["id"]], seen_orders[order] = where, where
    lessons.sort(key=lambda t: t[0])

    introduced_grammar, introduced_words, introduced_sounds = {}, {}, {}
    for order, where, meta in lessons:
        for key, target in spec["list_keys"].items():
            for ref in split_list(meta.get(key, "")):
                if ref not in tables[target]["ids"]:
                    report.error(where, f"'{key}' refers to '{ref}', which is not in {schema['tables'][target]['file']}")
                if target == "sentences" and ref in tables["sentences"]["ids"]:
                    if tables["sentences"]["ids"][ref].get("access") == "restricted":
                        report.error(where, f"uses restricted sentence '{ref}'")
                if target == "texts" and ref in tables["texts"]["ids"]:
                    if tables["texts"]["ids"][ref].get("access") == "restricted":
                        report.error(where, f"uses restricted text '{ref}'")
                if target == "words" and ref in tables["words"]["ids"]:
                    if tables["words"]["ids"][ref].get("access") == "restricted":
                        report.error(where, f"introduces restricted word '{ref}'")

        earlier_grammar = set(introduced_grammar)
        for g in split_list(meta.get("assumes_grammar", "")):
            if g not in earlier_grammar:
                report.error(where, f"assumes grammar '{g}' but no earlier lesson introduces it")
        for g in split_list(meta.get("introduces_grammar", "")):
            for pre in split_list(tables["grammar"]["ids"].get(g, {}).get("prerequisite_ids", "")):
                if pre not in earlier_grammar and pre not in split_list(meta.get("introduces_grammar", "")):
                    report.warn(where, f"introduces '{g}' but its prerequisite '{pre}' has not been introduced earlier")
            if g in introduced_grammar:
                report.warn(where, f"grammar '{g}' was already introduced in {introduced_grammar[g]}")
        for w in split_list(meta.get("introduces_words", "")):
            if w in introduced_words:
                report.warn(where, f"word '{w}' was already introduced in {introduced_words[w]}")

        available_grammar = earlier_grammar | set(split_list(meta.get("introduces_grammar", "")))
        available_words = set(introduced_words) | set(split_list(meta.get("introduces_words", "")))
        for sid in split_list(meta.get("uses_sentences", "")):
            row = tables["sentences"]["ids"].get(sid)
            if not row:
                continue
            for g in split_list(row.get("grammar_ids", "")):
                if g not in available_grammar:
                    report.warn(where, f"sentence '{sid}' uses grammar '{g}' which this lesson and earlier ones have not introduced")
            for w in split_list(row.get("word_ids", "")):
                if w not in available_words:
                    report.warn(where, f"sentence '{sid}' uses word '{w}' which this lesson and earlier ones have not introduced")

        for g in split_list(meta.get("introduces_grammar", "")):
            introduced_grammar.setdefault(g, where)
        for w in split_list(meta.get("introduces_words", "")):
            introduced_words.setdefault(w, where)
        for s in split_list(meta.get("introduces_sounds", "")):
            introduced_sounds.setdefault(s, where)

    if lessons:
        for g in tables["grammar"]["ids"]:
            if g not in introduced_grammar:
                report.note("grammar.csv", f"'{g}' is not introduced by any lesson yet")
        untaught = [w for w in tables["words"]["ids"] if w not in introduced_words]
        if untaught:
            shown = ", ".join(untaught[:10]) + (" ..." if len(untaught) > 10 else "")
            report.note("words.csv", f"{len(untaught)} word(s) not introduced by any lesson yet: {shown}")


def main():
    parser = argparse.ArgumentParser(description="Check a content folder against the framework schema.")
    parser.add_argument("content_dir", nargs="?", help="folder holding sources.csv, words.csv, community.yaml, lessons/ ...")
    parser.add_argument("--init", metavar="DIR", help="create blank tables in DIR and exit")
    parser.add_argument("--check-files", action="store_true", help="also check that audio files exist on disk")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if args.init:
        init_blank(schema, Path(args.init))
        return 0
    if not args.content_dir:
        parser.error("give a content folder, or use --init DIR")
    content_dir = Path(args.content_dir)
    if not content_dir.is_dir():
        print(f"not a folder: {content_dir}", file=sys.stderr)
        return 2

    report = Report()
    tables = load_tables(schema, content_dir, report)
    check_refs(schema, tables, report)
    check_protocols(tables, report)
    check_orthographies(schema, tables, content_dir, report)
    check_lessons(schema, tables, content_dir, report)
    if args.check_files:
        check_files(tables, content_dir, report)

    for label, items in (("ERROR", report.errors), ("WARNING", report.warnings), ("note", report.notes)):
        for item in items:
            print(f"{label}: {item}")
    counts = {n: len(t["rows"]) for n, t in tables.items() if t["present"]}
    print(f"\nChecked: {', '.join(f'{n} {c}' for n, c in counts.items()) or 'no tables found'}")
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
