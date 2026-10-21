# Content schema (v0.1)

This describes how a community's language material is organised so the toolkit can turn it into lessons. It is a draft. Pilot communities should expect to change it.

**Nothing in this folder is language content.** The files in `blank/` are empty tables with column headings. Real content belongs only in your own private copy (see [PROTOCOLS.md](../PROTOCOLS.md)).

## The idea in one paragraph

Every word, sentence, recording and grammar pattern gets a row in a simple table (a spreadsheet saved as CSV) and a permanent **id**. Lessons then refer to things by id rather than copying them. So you correct a word once and every lesson that uses it is correct. It also lets the toolkit check the things that quietly go wrong in a curriculum: a lesson that uses a sentence built on a word nobody has taught yet, or a recording used without permission.

## The tables

| File | One row is | Why it exists |
|---|---|---|
| `sources.csv` | where material came from (a recording session, an archive, a book, a speaker, a staff member) | Provenance and permission. Every other table points here. |
| `audio.csv` | one recording | Keeps sound files separate from text so they can have their own permissions. |
| `grammar.csv` | one pattern you teach (a word order, a verb form, a question type) | The backbone of the scope and sequence. Written in **your** terms, not ours. |
| `words.csv` | one word or short phrase | Vocabulary. |
| `sentences.csv` | one sentence | Practice material, tied to the words and patterns it uses. |
| `texts.csv` | one longer text (story, dialogue, short essay) | The reading and writing goals at higher levels. |
| `sounds.csv` | one letter or sound, in teaching order | Feeds the opening sound routine at the start of every lesson. |

Plus `community.yaml` (about your program) and a `lessons/` folder of lesson files made from the [lesson template](../templates/lesson/lesson.md).

The exact columns are in [`tables.json`](tables.json), which is also what the checker reads. Blank tables you can copy are in [`blank/`](blank/).

## Design choices and the reasons for them

**Spreadsheets, not a database.** The people running programs know spreadsheets. CSV opens in Excel, Google Sheets or LibreOffice, can be edited by anyone, and keeps working offline.

**Save as "CSV UTF-8".** Writing systems with special letters, glottal marks or accents break in older encodings. UTF-8 keeps them intact. The checker also warns when the same letter has been typed two different ways (Unicode normalisation), because that makes two identical-looking words fail to match.

**Several writing systems, no assumed standard.** Words and sentences have `form_1`, `form_2`, `form_3`. `community.yaml` says which writing system each column holds. A language with one agreed spelling uses one column. A language with several uses several. The toolkit never decides which is correct.

**Ids never change.** Use short, lowercase ids (`w014`, `s203`, `g07`). Once a lesson uses an id, do not reuse or renumber it. Change the row, not the id.

**Lists use semicolons.** A cell such as `grammar_ids` can hold several ids: `g01;g03`.

**Every row names its source.** `source_id` is required on words, sentences, texts and audio. This is deliberate friction. It is easier to record where material came from when it is added than to find out years later. If a lot of rows share a source, create one source row ("program staff, original examples") and reuse it. The `sources.csv` columns `consent_status` and `permitted_uses` are how PROTOCOLS.md becomes something the toolkit can act on.

**Three access levels.** Every item is marked:
- `open`: fine to use in learner materials.
- `program`: teachers and program staff only; the builder should keep it out of learner handouts.
- `restricted`: never used in generated material. It stays in the table so it is not lost, and so nobody wonders whether it was forgotten.

The checker enforces three rules here. A source with `consent_status: withdrawn` makes its items `restricted` or the checker fails. An item marked `open` whose source has no consent, or no `teaching` permission, gets a warning. A lesson that uses a restricted item fails.

**Speakers appear as codes only.** `audio.csv` has `speaker_code`, never a name. The list linking codes to people stays outside this folder, in a place your community controls.

**Grammar belongs to you.** `grammar.csv` has no preset list. The `name`, `description` and `pattern` are written in your community's terms. The `prerequisite_ids` column records which patterns must be taught first. That is the part of the sequencing logic the toolkit uses.

## What the checker does

`tools/validate_content.py` reads a content folder and reports:
- missing required columns or values, duplicate ids, ids with odd characters
- references that point at nothing (a sentence naming a word that isn't in `words.csv`)
- the permission rules above
- a writing system used in the tables but not declared in `community.yaml`
- in lessons: a lesson that assumes a pattern no earlier lesson teaches, a sentence that uses a word or pattern not yet taught, a restricted item in a lesson, a word taught twice

It runs on your own computer, reads only the folder you give it and sends nothing anywhere. See the docstring at the top of the script for usage.

## Not decided yet

- How to model words whose forms change (verb forms, plurals) without making the table unusable. For now, each form is its own row, linked by `notes`. A real language will test this quickly.
- Where large audio files should live, and how the builder finds them.
- Whether `topic_tags` need a shared list or stay free text.
- How to mark a sentence that is correct only in one variety.
- Whether `sounds.csv` can describe a language whose "alphabet" is a syllabic writing system.

Feedback on these from people running real programs is the most useful thing this version can get.
