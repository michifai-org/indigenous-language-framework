#!/usr/bin/env python3
"""Tests for validate_content.py.

Each test copies the fictional demo into a temporary folder, breaks one thing, and
checks that the checker notices. Run from the repository root:

    python tools/test_validate_content.py
"""
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_content as vc  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEMO = REPO / "examples" / "demo-language"


def run(content_dir, *flags):
    out = io.StringIO()
    argv = ["validate_content.py", str(content_dir), *flags]
    old = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(out):
            code = vc.main()
    finally:
        sys.argv = old
    return code, out.getvalue()


class DemoCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.dir = self.tmp / "demo"
        shutil.copytree(DEMO, self.dir)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit(self, name, old, new):
        path = self.dir / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"test setup: '{old}' not in {name}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def assertFails(self, expected, *flags):
        code, out = run(self.dir, *flags)
        self.assertEqual(code, 1, out)
        self.assertIn(expected, out)

    # --- the demo itself -------------------------------------------------
    def test_demo_is_clean(self):
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("0 error(s), 0 warning(s)", out)

    # --- table structure -------------------------------------------------
    def test_dangling_reference(self):
        self.edit("sentences.csv", "w001;w004", "w001;w999")
        self.assertFails("'w999', which is not in words.csv")

    def test_duplicate_id(self):
        self.edit("words.csv", "w002,sira", "w001,sira")
        self.assertFails("duplicate id 'w001'")

    def test_bad_id_characters(self):
        self.edit("words.csv", "w003,nako", "W 003,nako")
        self.assertFails("should use lowercase letters")

    def test_missing_required_value(self):
        self.edit("words.csv", "w004,pelu,pelu,,describing word,big", "w004,pelu,pelu,,describing word,")
        self.assertFails("'gloss' is empty")

    def test_missing_required_column(self):
        self.edit("words.csv", ",gloss,", ",meaning,")
        self.assertFails("missing required column 'gloss'")

    def test_bad_access_value(self):
        self.edit("words.csv", "src001,open,\nw005", "src001,public,\nw005")
        self.assertFails("allowed: open, program, restricted")

    # --- protocol rules --------------------------------------------------
    def test_withdrawn_consent_must_be_restricted(self):
        self.edit("sources.csv", "confirmed", "withdrawn")
        self.assertFails("withdrawn consent")

    def test_open_with_unknown_consent_warns(self):
        self.edit("sources.csv", "confirmed", "unknown")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("consent for source 'src001' is unknown", out)
        self.assertEqual(run(self.dir, "--strict")[0], 1)

    def test_open_without_teaching_permission_warns(self):
        self.edit("sources.csv", "teaching;internal;public", "internal")
        code, out = run(self.dir)
        self.assertIn("does not list 'teaching'", out)

    def test_open_item_with_stricter_audio_warns(self):
        self.edit("audio.csv", "src001,open", "src001,program")
        code, out = run(self.dir)
        self.assertIn("its audio 'a001' is 'program'", out)

    # --- writing systems and encoding -----------------------------------
    def test_undeclared_writing_system(self):
        self.edit("words.csv", "w001,tumo,tumo,,", "w001,tumo,tumo,tumó,")
        self.assertFails("'form_3' has text in words/sentences but is not declared")

    def test_unnormalised_text_warns(self):
        decomposed = "tumo" + "́"  # letter + combining accent, not NFC
        self.edit("words.csv", "w004,pelu,pelu", f"w004,pelu,{decomposed}")
        code, out = run(self.dir)
        self.assertIn("not Unicode-normalised", out)

    # --- lessons ---------------------------------------------------------
    def test_lesson_assumes_pattern_not_yet_taught(self):
        self.edit("lessons/001-house-and-river.md", "assumes_grammar: \n", "assumes_grammar: g02\n")
        self.assertFails("assumes grammar 'g02' but no earlier lesson introduces it")

    def test_lesson_uses_sentence_with_untaught_word(self):
        self.edit("lessons/001-house-and-river.md", "uses_sentences: s001;s002", "uses_sentences: s001;s003")
        code, out = run(self.dir)
        self.assertIn("sentence 's003' uses grammar 'g02'", out)
        self.assertIn("sentence 's003' uses word 'w005'", out)

    def test_restricted_item_cannot_be_in_lesson(self):
        text = (self.dir / "sentences.csv").read_text(encoding="utf-8").splitlines()
        text[1] = text[1].replace(",open,", ",restricted,")
        (self.dir / "sentences.csv").write_text("\n".join(text) + "\n", encoding="utf-8")
        self.assertFails("uses restricted sentence 's001'")

    def test_duplicate_lesson_order(self):
        self.edit("lessons/002-i-see-you-see.md", "order: 2", "order: 1")
        self.assertFails("order 1 also used")

    def test_lesson_without_front_matter(self):
        (self.dir / "lessons" / "003-broken.md").write_text("# no front matter\n", encoding="utf-8")
        self.assertFails("no front matter")

    def test_word_taught_twice_warns(self):
        self.edit("lessons/002-i-see-you-see.md", "introduces_words: w005;w006;w007", "introduces_words: w001;w006;w007")
        code, out = run(self.dir)
        self.assertIn("word 'w001' was already introduced", out)

    def test_prerequisite_not_yet_taught_warns(self):
        # lesson 1 now introduces g02, whose prerequisite g01 comes only later
        self.edit("lessons/001-house-and-river.md", "introduces_grammar: g01", "introduces_grammar: g02")
        code, out = run(self.dir)
        self.assertIn("prerequisite 'g01' has not been introduced earlier", out)

    # --- audio files -----------------------------------------------------
    def test_missing_audio_file_only_flagged_on_request(self):
        code, out = run(self.dir)
        self.assertNotIn("audio file not found", out)
        code, out = run(self.dir, "--check-files")
        self.assertIn("audio file not found", out)


class Init(unittest.TestCase):
    def test_init_creates_all_tables_and_does_not_overwrite(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            target = tmp / "new"
            out = io.StringIO()
            old = sys.argv
            sys.argv = ["validate_content.py", "--init", str(target)]
            try:
                with contextlib.redirect_stdout(out):
                    self.assertEqual(vc.main(), 0)
            finally:
                sys.argv = old
            files = sorted(p.name for p in target.iterdir())
            self.assertEqual(files, sorted(["sources.csv", "audio.csv", "grammar.csv", "words.csv", "sentences.csv", "texts.csv", "sounds.csv"]))
            (target / "words.csv").write_text("keep me", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                sys.argv = ["validate_content.py", "--init", str(target)]
                try:
                    vc.main()
                finally:
                    sys.argv = old
            self.assertEqual((target / "words.csv").read_text(encoding="utf-8"), "keep me")
        finally:
            shutil.rmtree(tmp)

    def test_blank_tables_in_repo_match_schema(self):
        import json
        schema = json.loads(vc.SCHEMA_PATH.read_text(encoding="utf-8"))
        for spec in schema["tables"].values():
            header = (REPO / "schema" / "blank" / spec["file"]).read_text(encoding="utf-8").strip()
            self.assertEqual(header, ",".join(c["name"] for c in spec["columns"]), spec["file"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
